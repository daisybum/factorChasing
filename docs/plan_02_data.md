# Plan 02 — Data Collection (survivorship-bias-free)

**Module:** `quant_system/universe.py` + `quant_system/collect.py`
**Goal:** a point-in-time top-30-by-market-cap Binance USDⓈ-M perp universe (BTC always
in) and 1m kline + funding history for it, with survivorship bias designed out.

## Inputs / outputs
| | source | output |
|---|---|---|
| Universe | CoinGecko `/coins/markets` + `/coins/{id}/market_chart`; Binance `/fapi/v1/exchangeInfo` | `data/universe.parquet` (long: date, coingecko_id, binance_symbol, market_cap, rank, listed, delisted_after) |
| Klines | Binance `/fapi/v1/klines` interval=1m | `data/klines/<SYMBOL>.parquet` (open_time idx; open,high,low,close,volume,quote_volume,trades) |
| Funding | Binance `/fapi/v1/fundingRate` | `data/funding/<SYMBOL>.parquet` (funding_time idx; funding_rate) |

## Key functions
- `universe.build_universe(lookback_days)` → writes + returns the membership table.
- `universe.binance_symbol_for(coingecko_id)` → perp symbol via base-asset match (incl. delisted seed).
- `collect.collect_klines / collect_funding(symbols, start_ms, end_ms)` → incremental, idempotent.
- `collect.load_klines / load_funding(symbol)` → read back.
- `collect.last_tradeable_bar(symbol)` → last bar with `volume>0` (before frozen post-delist bars).

## Survivorship — enforced as a mechanism
Membership on date `d` requires the perp to have been tradeable on `d`, from the Binance
**point-in-time calendar**: `onboard_day ≤ d ≤ delist_day`. `delist_day` is taken from
`deliveryDate` of non-`TRADING` contracts whose delivery is in the past — **not** from the
last kline, because Binance keeps emitting frozen `volume=0` bars after a delist (verified:
MKRUSDT frozen at its last price from 2025-09-08 onward). A name that delists *within* the
window is therefore retained on its pre-delist dates with `delisted_after` set, and exits
cleanly downstream — never silently dropped (`wiki/concepts/survivorship-and-universe.md`).

Verified example: **MKRUSDT** last tradeable bar (volume>0) = `2025-09-08 08:59 UTC`, with
2341 frozen volume=0 bars after — the backtest closes its position there.

## Robustness
- On-disk JSON cache for every CoinGecko call (`data/cache/`) → re-runs don't re-hit the API.
- Exponential backoff (2→60s) on HTTP 429/418/5xx for both APIs.
- Klines/funding are **incremental & resumable**: resume one bar past the last stored
  timestamp; a re-run with no new data is a no-op (verified idempotent). No forward-fill
  across gaps; frozen post-delist bars persisted as-is and excluded via `volume>0`.

## Config knobs (`config.py`)
`UNIVERSE_SIZE=30`, `ALWAYS_INCLUDE=['bitcoin']`, `INTERVAL='1m'`, `LOOKBACK_DAYS=365`,
`KLINES_DIR/FUNDING_DIR/UNIVERSE_PATH`. Candidate breadth: `_candidate_coins(top_n=50)`.

## Documented limitations (per wiki honesty norms)
- CoinGecko free tier caps `market_chart` history at **365 days** and rate-limits hard →
  ranking uses best in-window mcap; full 2022-peak ranking needs a paid/archived source.
  No fabricated mcap.
- `_missing_ranges` fills leading and trailing gaps, so re-runs can backfill older history
  and extend newer history. Interior holes are still not repaired automatically; collect into
  contiguous files or rebuild the affected symbol file.

## Verification checklist
- [x] `build_universe(30)` writes a real parquet; BTC present every date; ≤30 members/day;
      ≥1 in-window delisting retained with `delisted_after` set.
- [x] `collect_*` for BTCUSDT/ETHUSDT (2 days) → 2881–2882 klines, 6 funding stamps;
      idempotent on re-run.
- [x] MKRUSDT over its pre-delist window → real bars then frozen volume=0; `last_tradeable_bar`
      = trading stop.
- [x] `load_klines/load_funding` round-trip the schema.
