"""Driver: long-horizon all-time historical collection (see plan file).

- BTC  -> Binance **spot** 1m, from the earliest bar Binance serves (~2017-08-17). No funding.
- 29 alts -> Binance USDⓈ-M **perp** 1m, all-time from each symbol's onboard -> now/delist,
  plus funding.

Resumable: collect.collect_klines is gap-aware (backfills older + extends newer) and flushes
to parquet every FLUSH_EVERY requests, so re-running the driver continues an interrupted pull.
NOTE: _missing_ranges fills only leading/trailing gaps, not interior holes — so pull onto
single contiguous files (don't seed disjoint slices), which `start=0` from onboard guarantees.

Usage (run the full pull in the background — it takes hours):
  python -m quant_system.collect_history            # full all-time pull
  python -m quant_system.collect_history --smoke    # fast bounded validation
"""

from __future__ import annotations

import sys
import time

import pandas as pd

from . import config
from . import collect as C

BTC = "BTCUSDT"


def _now_ms() -> int:
    return int(time.time() * 1000)


def universe_symbols() -> list[str]:
    uni = pd.read_parquet(config.UNIVERSE_PATH)
    return sorted(uni["binance_symbol"].dropna().unique().tolist())


def collect_btc_spot(start_ms: int = 0, end_ms: int | None = None) -> None:
    end_ms = end_ms or _now_ms()
    C.collect_klines([BTC], start_ms, end_ms, market="spot")
    kl = C.load_klines(BTC, market="spot")
    print(f"[BTC spot] {len(kl):,} bars [{kl.index.min()} .. {kl.index.max()}]", flush=True)


def collect_alts(symbols: list[str], start_ms: int = 0, end_ms: int | None = None) -> None:
    end_ms = end_ms or _now_ms()
    for i, sym in enumerate(symbols, 1):
        t0 = time.time()
        C.collect_klines([sym], start_ms, end_ms, market="perp")
        C.collect_funding([sym], start_ms, end_ms)
        kl = C.load_klines(sym)
        print(f"[{i}/{len(symbols)}] {sym}: {len(kl):,} bars "
              f"[{kl.index.min()} .. {kl.index.max()}] "
              f"last_tradeable={C.last_tradeable_bar(sym)} ({time.time() - t0:.0f}s)",
              flush=True)


def main(smoke: bool = False) -> None:
    syms = universe_symbols()
    alts = [s for s in syms if s != BTC]
    print(f"universe: {len(syms)} symbols -> BTC spot + {len(alts)} perp alts", flush=True)

    if smoke:
        # bounded BTC spot (extends forward cleanly; safe) + report planned alt spans only,
        # so we never seed a disjoint slice into a real alt file.
        s0 = int(pd.Timestamp("2017-08-17", tz="UTC").value // 1_000_000)
        collect_btc_spot(s0, s0 + 2 * 86_400_000)
        print(f"planned all-time alt pull: {len(alts)} perps from onboard -> now", flush=True)
        return

    collect_btc_spot()
    collect_alts(alts)
    print("ALL-TIME COLLECTION COMPLETE", flush=True)


if __name__ == "__main__":
    main(smoke="--smoke" in sys.argv)
