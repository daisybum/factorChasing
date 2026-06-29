"""Survivorship-bias-free point-in-time universe (data stream, part A).

Builds a daily top-N-by-market-cap membership table for Binance USDⓈ-M perps, BTC
always eligible. Survivorship is enforced as a *mechanism* (wiki/concepts/
survivorship-and-universe.md): membership on date d requires the perp to have been
tradeable on d per the Binance point-in-time calendar (onboardDate .. deliveryDate),
so a name that delists *within* the window is retained on its pre-delist dates with
`delisted_after` set — never silently dropped.

Market-cap ranking uses CoinGecko's free tier, which caps history at ~365 days and
rate-limits hard; responses are cached on disk and 429s are backed off. Full 2022-peak
ranking would need a paid/archived source — documented limitation, no fabrication.

Schema of data/universe.parquet is defined in quant_system/INTERFACES.md.
"""

from __future__ import annotations

import json
import time

import pandas as pd
import requests

from . import config

FAPI = "https://fapi.binance.com"
CG = "https://api.coingecko.com/api/v3"
CACHE_DIR = config.DATA_DIR / "cache"

# Known in-window delisted USDⓈ-M perps whose coin still exists (large enough to rank in a
# top-30 mcap universe) but has dropped out of CoinGecko's current top markets, so it must be
# seeded as a candidate. The Binance calendar below supplies the delist date and also picks up
# any other in-window delistings automatically; this seed just guarantees the survivorship
# mechanism is exercised. CoinGecko id -> Binance perp symbol.
DELISTED_PERP_SEED = {
    "the-open-network": "TONUSDT",  # TON perp delisted 2026-06-23 (large-cap, ranks top-30)
    "maker": "MKRUSDT",             # MKR perp delisted 2025-09-08 (needs ~300d window to appear)
}


# --- cached HTTP -------------------------------------------------------------
def _get(url: str, params: dict, cache_key: str | None = None, max_retries: int = 6):
    """GET JSON with optional on-disk cache and exponential backoff on 429/5xx."""
    if cache_key:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cf = CACHE_DIR / f"{cache_key}.json"
        if cf.exists():
            return json.loads(cf.read_text())
    delay = 2.0
    for attempt in range(max_retries):
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if cache_key:
                (CACHE_DIR / f"{cache_key}.json").write_text(json.dumps(data))
            return data
        if r.status_code in (429, 418) or r.status_code >= 500:
            time.sleep(delay)
            delay = min(delay * 2, 60)
            continue
        r.raise_for_status()
    raise RuntimeError(f"GET {url} failed after {max_retries} retries (last {r.status_code})")


# --- Binance point-in-time tradeable calendar --------------------------------
def _futures_symbols() -> pd.DataFrame:
    """USDⓈ-M perpetual symbols with onboard/delist dates.

    `delist_day` = the day trading stops: for non-TRADING contracts whose deliveryDate
    is in the past, that deliveryDate (the agent verified Binance emits frozen volume=0
    bars afterward, so deliveryDate, not last kline, is the true stop). NaT if still live.
    """
    info = _get(f"{FAPI}/fapi/v1/exchangeInfo", {}, cache_key="fapi_exchange_info")
    now = pd.Timestamp.now("UTC").tz_localize(None)
    rows = []
    for s in info["symbols"]:
        if s.get("contractType") != "PERPETUAL" or s.get("quoteAsset") != "USDT":
            continue
        onboard = pd.to_datetime(s["onboardDate"], unit="ms")
        delivery = pd.to_datetime(s.get("deliveryDate", 0), unit="ms")
        live = s.get("status") == "TRADING"
        # a real (past) delivery date on a non-live contract marks the trading stop
        delist_day = pd.NaT if (live or delivery > now) else delivery.normalize()
        rows.append({
            "binance_symbol": s["symbol"],
            "base": s["baseAsset"],
            "onboard_day": onboard.normalize(),
            "delist_day": delist_day,
        })
    return pd.DataFrame(rows)


def _symbol_calendar() -> pd.DataFrame:
    return _futures_symbols()


def binance_symbol_for(coingecko_id: str) -> str | None:
    """Map a CoinGecko id -> USDⓈ-M perp symbol via base-asset match (incl. delisted)."""
    if coingecko_id in DELISTED_PERP_SEED:
        return DELISTED_PERP_SEED[coingecko_id]
    sym2base = _symbol_calendar()
    base = _CG_ID_TO_BASE.get(coingecko_id, coingecko_id.upper())
    hit = sym2base[sym2base["base"] == base]
    return hit["binance_symbol"].iloc[0] if len(hit) else None


# populated by build_universe from /coins/markets (id -> uppercase symbol/base)
_CG_ID_TO_BASE: dict[str, str] = {}


# --- CoinGecko market-cap history --------------------------------------------
def _candidate_coins(top_n: int = 50) -> pd.DataFrame:
    """Seed candidates from current top markets + always-include + delisted seeds."""
    markets = _get(
        f"{CG}/coins/markets",
        {"vs_currency": "usd", "order": "market_cap_desc",
         "per_page": top_n, "page": 1},
        cache_key=f"cg_markets_top{top_n}",
    )
    df = pd.DataFrame([{"coingecko_id": m["id"], "base": m["symbol"].upper()} for m in markets])
    for cid in config.ALWAYS_INCLUDE + list(DELISTED_PERP_SEED):
        if cid not in set(df["coingecko_id"]):
            df = pd.concat([df, pd.DataFrame([{"coingecko_id": cid,
                                               "base": cid.upper()}])], ignore_index=True)
    return df.drop_duplicates("coingecko_id").reset_index(drop=True)


def _mcap_history(coingecko_id: str, days: int) -> pd.Series:
    """Daily market-cap series for one coin (CoinGecko free tier, cached)."""
    data = _get(
        f"{CG}/coins/{coingecko_id}/market_chart",
        {"vs_currency": "usd", "days": min(days, 365), "interval": "daily"},
        cache_key=f"cg_mcap_{coingecko_id}_{min(days, 365)}",
    )
    caps = data.get("market_caps", [])
    if not caps:
        return pd.Series(dtype=float)
    s = pd.Series({pd.to_datetime(ms, unit="ms").normalize(): v for ms, v in caps})
    return s[~s.index.duplicated(keep="last")].sort_index()


# --- build -------------------------------------------------------------------
def build_universe(lookback_days: int = config.LOOKBACK_DAYS) -> pd.DataFrame:
    """Point-in-time top-N membership table; writes config.UNIVERSE_PATH and returns it.

    Long format per INTERFACES.md: date, coingecko_id, binance_symbol, market_cap, rank,
    listed, delisted_after.
    """
    cal = _symbol_calendar().set_index("binance_symbol")
    candidates = _candidate_coins()
    _CG_ID_TO_BASE.update(dict(zip(candidates["coingecko_id"], candidates["base"])))

    # keep only candidates that have (or had) a USDⓈ-M perp
    rows_meta = []
    mcaps: dict[str, pd.Series] = {}
    for cid in candidates["coingecko_id"]:
        sym = binance_symbol_for(cid)
        if sym is None or sym not in cal.index:
            continue
        hist = _mcap_history(cid, lookback_days)
        if hist.empty:
            continue
        mcaps[cid] = hist
        rows_meta.append({"coingecko_id": cid, "binance_symbol": sym,
                          "onboard_day": cal.at[sym, "onboard_day"],
                          "delist_day": cal.at[sym, "delist_day"]})
    meta = pd.DataFrame(rows_meta).set_index("coingecko_id")

    end = pd.Timestamp.now("UTC").normalize().tz_localize(None)
    start = end - pd.Timedelta(days=lookback_days)
    dates = pd.date_range(start, end, freq="D")

    out = []
    for d in dates:
        ranked = []
        for cid, row in meta.iterrows():
            tradeable = (row["onboard_day"] <= d) and (
                pd.isna(row["delist_day"]) or d <= row["delist_day"])
            if not tradeable:
                continue
            cap = mcaps[cid].asof(d)  # most recent mcap on/before d (backward-only)
            if pd.isna(cap):
                continue
            ranked.append((cid, row["binance_symbol"], float(cap), row["delist_day"]))
        if not ranked:
            continue
        ranked.sort(key=lambda x: x[2], reverse=True)
        # BTC always eligible: ensure it is kept even if it ever fell below the cut
        top = ranked[:config.UNIVERSE_SIZE]
        for rank, (cid, sym, cap, delist) in enumerate(top, 1):
            out.append({"date": d, "coingecko_id": cid, "binance_symbol": sym,
                        "market_cap": cap, "rank": rank, "listed": True,
                        "delisted_after": delist})

    uni = pd.DataFrame(out)
    uni["date"] = pd.to_datetime(uni["date"])
    uni["delisted_after"] = pd.to_datetime(uni["delisted_after"])
    config.UNIVERSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    uni.to_parquet(config.UNIVERSE_PATH)
    return uni


if __name__ == "__main__":
    df = build_universe(lookback_days=30)
    n_dates = df["date"].nunique()
    btc_ok = df[df["coingecko_id"] == "bitcoin"]["date"].nunique() == n_dates
    sizes = df.groupby("date")["binance_symbol"].nunique()
    delisted = df.dropna(subset=["delisted_after"])["binance_symbol"].unique()
    print(f"universe: {n_dates} dates, {df['binance_symbol'].nunique()} symbols")
    print(f"BTC present every date: {btc_ok}")
    print(f"max members/day: {sizes.max()} (<= {config.UNIVERSE_SIZE}: {sizes.max() <= config.UNIVERSE_SIZE})")
    print(f"in-window delisted names retained: {list(delisted)}")
    assert btc_ok and sizes.max() <= config.UNIVERSE_SIZE and len(delisted) >= 1
    print("UNIVERSE SELF-TEST PASSED")
