"""Binance 1m klines + funding collection (data stream, part B).

Incremental, idempotent, rate-limit-safe. Per-symbol parquet caches. Gap-aware: re-runs
**backfill** older history and **extend** newer (not just forward), and long pulls flush to
disk every FLUSH_EVERY requests so they resume after interruption. `market` selects perp
(USDⓈ-M fapi, with funding) or spot (api, no funding). No forward-fill across listing gaps.
Schemas defined in quant_system/INTERFACES.md.

Note (from live probing): after a perp delists, Binance keeps emitting frozen bars with
volume=0/trades=0. Those are persisted as-is; the "last tradeable bar" is the last bar
with volume>0 (see last_tradeable_bar) so frozen prices are never treated as live.
"""

from __future__ import annotations

import time

import pandas as pd
import requests

from . import config

FAPI = "https://fapi.binance.com"          # USDⓈ-M perp
SPOT = "https://api.binance.com"           # spot
FUNDING_LIMIT = 1000
FLUSH_EVERY = 50                           # flush buffer to parquet every N requests (long pulls)

# market -> (base url, klines path, max page size). spot caps klines at 1000, futures at 1500;
# the page size doubles as the "short page = done" sentinel, so it must match the endpoint.
KLINE_ENDPOINT = {"perp": (FAPI, "/fapi/v1/klines", 1500),
                  "spot": (SPOT, "/api/v3/klines", 1000)}

_KCOLS = ["open", "high", "low", "close", "volume", "quote_volume", "trades"]


def _get(path: str, params: dict, base: str = FAPI, max_retries: int = 6):
    delay = 1.0
    for _ in range(max_retries):
        r = requests.get(f"{base}{path}", params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 418) or r.status_code >= 500:
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        r.raise_for_status()
    raise RuntimeError(f"GET {path} failed after {max_retries} retries (last {r.status_code})")


def _missing_ranges(existing, start_ms: int, end_ms: int, step_ms: int):
    """Sub-windows of [start, end] not already covered by `existing` — both the backfill
    gap before the first stored row AND the forward gap after the last. Enables re-runs to
    extend history in either direction (the old forward-only resume could not backfill)."""
    if existing is None or len(existing) == 0:
        return [(start_ms, end_ms)]
    first = int(existing.index[0].value // 1_000_000)
    last = int(existing.index[-1].value // 1_000_000)
    ranges = []
    if start_ms < first:
        ranges.append((start_ms, first))            # backfill older
    if end_ms > last + step_ms:
        ranges.append((last + step_ms, end_ms))     # extend newer
    return ranges


# --- klines ------------------------------------------------------------------
def _kline_path(symbol: str, market: str = "perp"):
    suffix = "" if market == "perp" else f"_{market.upper()}"
    return config.KLINES_DIR / f"{symbol}{suffix}.parquet"


def _parse_kline(k: list) -> dict:
    return {"open_time": pd.to_datetime(k[0], unit="ms", utc=True),
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
            "close": float(k[4]), "volume": float(k[5]),
            "quote_volume": float(k[7]), "trades": int(k[8])}


def _flush_klines(path, buffer: list) -> None:
    """Merge a row buffer into the per-symbol parquet (dedupe + sort). Idempotent."""
    if not buffer:
        return
    existing = pd.read_parquet(path) if path.exists() else None
    df = pd.DataFrame(buffer).set_index("open_time")[_KCOLS]
    combined = pd.concat([x for x in (existing, df) if x is not None])
    combined = combined[~combined.index.duplicated(keep="last")].sort_index()
    combined.to_parquet(path)


def load_klines(symbol: str, market: str = "perp") -> pd.DataFrame:
    """Read the per-symbol 1m parquet (DatetimeIndex open_time UTC, _KCOLS)."""
    return pd.read_parquet(_kline_path(symbol, market))


def collect_klines(symbols: list[str], start_ms: int, end_ms: int,
                   market: str = "perp") -> None:
    """Fetch 1m klines into config.KLINES_DIR/<sym>[_MARKET].parquet.

    Gap-aware (backfills older + extends newer) and resumable: the buffer is flushed to the
    parquet every FLUSH_EVERY requests, so an interrupted multi-hour pull resumes within
    ~FLUSH_EVERY*KLINE_LIMIT bars. `market`: "perp" (fapi) or "spot" (api). `start_ms=0`
    pulls from the earliest bar Binance serves for the symbol.
    """
    base, endpoint, page = KLINE_ENDPOINT[market]
    config.KLINES_DIR.mkdir(parents=True, exist_ok=True)
    for sym in symbols:
        path = _kline_path(sym, market)
        existing = pd.read_parquet(path) if path.exists() else None
        buffer: list = []
        reqs = 0
        for lo, hi in _missing_ranges(existing, start_ms, end_ms, 60_000):
            cursor = lo
            while cursor < hi:
                data = _get(endpoint, {"symbol": sym, "interval": config.INTERVAL,
                                       "startTime": cursor, "endTime": hi,
                                       "limit": page}, base=base)
                if not data:
                    break
                buffer.extend(_parse_kline(k) for k in data)
                cursor = data[-1][0] + 60_000
                reqs += 1
                if reqs % FLUSH_EVERY == 0:
                    _flush_klines(path, buffer)
                    buffer = []
                if len(data) < page:
                    break
        _flush_klines(path, buffer)


# --- funding -----------------------------------------------------------------
def _funding_path(symbol: str):
    return config.FUNDING_DIR / f"{symbol}.parquet"


def load_funding(symbol: str) -> pd.DataFrame:
    """Read the per-symbol funding parquet (DatetimeIndex funding_time UTC, funding_rate)."""
    return pd.read_parquet(_funding_path(symbol))


def collect_funding(symbols: list[str], start_ms: int, end_ms: int) -> None:
    """Incrementally fetch 8h funding rates into config.FUNDING_DIR/<sym>.parquet."""
    config.FUNDING_DIR.mkdir(parents=True, exist_ok=True)
    for sym in symbols:
        path = _funding_path(sym)
        existing = pd.read_parquet(path) if path.exists() else None
        rows = []
        for lo, hi in _missing_ranges(existing, start_ms, end_ms, 1):
            cursor = lo
            while cursor < hi:
                data = _get("/fapi/v1/fundingRate", {"symbol": sym, "startTime": cursor,
                                                     "endTime": hi, "limit": FUNDING_LIMIT})
                if not data:
                    break
                for f in data:
                    rows.append({
                        "funding_time": pd.to_datetime(f["fundingTime"], unit="ms", utc=True),
                        "funding_rate": float(f["fundingRate"]),
                    })
                cursor = data[-1]["fundingTime"] + 1
                if len(data) < FUNDING_LIMIT:
                    break
        if not rows:
            continue  # nothing new (idempotent no-op, or delisted symbol with no data)
        existing = pd.read_parquet(path) if path.exists() else None
        df = pd.DataFrame(rows).set_index("funding_time")
        combined = pd.concat([x for x in (existing, df) if x is not None])
        combined = combined[~combined.index.duplicated(keep="last")].sort_index()
        combined.to_parquet(path)


def last_tradeable_bar(symbol: str, market: str = "perp"):
    """Last bar with volume>0 — i.e. before any frozen post-delist bars. NaT if none."""
    kl = load_klines(symbol, market)
    live = kl[kl["volume"] > 0]
    return live.index[-1] if len(live) else pd.NaT


if __name__ == "__main__":
    # live symbols over a recent window
    end = int(time.time() * 1000)
    start = end - 2 * 86_400_000  # last 2 days
    live = ["BTCUSDT", "ETHUSDT"]
    collect_klines(live, start, end)
    collect_funding(live, start, end)
    for s in live:
        kl, fu = load_klines(s), load_funding(s)
        print(f"{s}: {len(kl)} klines [{kl.index.min()} .. {kl.index.max()}], "
              f"{len(fu)} funding, last_tradeable={last_tradeable_bar(s)}")

    # delisted symbol over its PRE-delist window (proves Binance serves historical klines
    # for delisted perps, then frozen volume=0 bars after the trading stop).
    # collect_klines only resumes forward, so clear any stale recent-frozen file first.
    _kline_path("MKRUSDT").unlink(missing_ok=True)
    d_start = int(pd.Timestamp("2025-09-07", tz="UTC").value // 1_000_000)
    d_end = int(pd.Timestamp("2025-09-10", tz="UTC").value // 1_000_000)
    collect_klines(["MKRUSDT"], d_start, d_end)
    mkr = load_klines("MKRUSDT")
    ltb = last_tradeable_bar("MKRUSDT")
    frozen = mkr[mkr["volume"] == 0]
    print(f"MKRUSDT: {len(mkr)} klines [{mkr.index.min()} .. {mkr.index.max()}], "
          f"last_tradeable(vol>0)={ltb}, frozen vol=0 bars after stop={len(frozen)}")
    assert ltb is not pd.NaT and len(frozen) > 0, "delisted-symbol stop not detected"

    # idempotency: re-run must add no rows
    before = len(load_klines("BTCUSDT"))
    collect_klines(["BTCUSDT"], start, end)
    after = len(load_klines("BTCUSDT"))
    assert before == after, f"not idempotent: {before} -> {after}"
    print(f"idempotent re-run PASS (BTCUSDT stable at {after} rows)")

    # gap-range + flush units (fast, offline)
    assert _missing_ranges(None, 0, 100, 1) == [(0, 100)]
    seed = pd.DataFrame({c: [1.0] for c in _KCOLS},
                        index=pd.to_datetime([10 * 60_000, 12 * 60_000], unit="ms", utc=True))
    seed.index.name = "open_time"
    assert _missing_ranges(seed, 5 * 60_000, 20 * 60_000, 60_000) == \
        [(5 * 60_000, 10 * 60_000), (13 * 60_000, 20 * 60_000)], "missing_ranges wrong"
    print("missing_ranges PASS (backfill + forward gaps)")

    # BACKFILL: extend BTCUSDT perp 3 days older than whatever is currently stored
    old_first = load_klines("BTCUSDT").index.min()
    target = int(old_first.value // 1_000_000) - 3 * 86_400_000
    collect_klines(["BTCUSDT"], target, end)
    new_first = load_klines("BTCUSDT").index.min()
    assert new_first < old_first, f"backfill failed: {old_first} -> {new_first}"
    print(f"BACKFILL PASS: BTCUSDT first bar {old_first} -> {new_first}")

    # SPOT endpoint: BTC spot from 2017-08-17 (stored as BTCUSDT_SPOT, no collision with perp)
    s0 = int(pd.Timestamp("2017-08-17", tz="UTC").value // 1_000_000)
    s1 = int(pd.Timestamp("2017-08-19", tz="UTC").value // 1_000_000)
    collect_klines(["BTCUSDT"], s0, s1, market="spot")
    spot = load_klines("BTCUSDT", market="spot")
    print(f"SPOT PASS: BTCUSDT_SPOT {len(spot)} bars from {spot.index.min()}")
    assert spot.index.min() <= pd.Timestamp("2017-08-17 12:00", tz="UTC")

    print("COLLECT SELF-TEST PASSED")
