# Module Interfaces & Data Schemas (the shared contract)

All three build streams code against these signatures and schemas. Do not change a
schema without updating this file. Everything is point-in-time and causal.

## Parquet schemas

### `data/universe.parquet` — produced by `universe.py`, consumed by factors/backtest
Long format, one row per (date, member):
| col | type | notes |
|---|---|---|
| `date` | datetime64 (UTC, day) | rebalance date |
| `coingecko_id` | str | source id |
| `binance_symbol` | str | e.g. `BTCUSDT`; perp symbol tradeable on `date` |
| `market_cap` | float | point-in-time mcap used for ranking |
| `rank` | int | 1..UNIVERSE_SIZE within `date` |
| `listed` | bool | symbol tradeable on `date` (PIT calendar) |
| `delisted_after` | datetime64 or NaT | delist date if known (else NaT) |

### `data/klines/<SYMBOL>.parquet` — produced by `collect.py`
DatetimeIndex `open_time` (UTC, 1m), columns: `open, high, low, close, volume,
quote_volume, trades`. No forward-fill across listing gaps; gaps left as missing rows.

### `data/funding/<SYMBOL>.parquet` — produced by `collect.py`
DatetimeIndex `funding_time` (UTC, 8h), column: `funding_rate` (float, per-interval).

## Function signatures

### `universe.py`
```python
def build_universe(lookback_days: int = config.LOOKBACK_DAYS) -> pandas.DataFrame: ...
    # writes config.UNIVERSE_PATH and returns the long-format df above.
    # BTC always eligible; includes >=1 delisted name in some historical window.
def binance_symbol_for(coingecko_id: str) -> str | None: ...  # mapping incl. delisted
```

### `collect.py`
```python
def collect_klines(symbols: list[str], start_ms: int, end_ms: int) -> None: ...
    # incremental/resumable per-symbol parquet; safe to re-run (idempotent).
def collect_funding(symbols: list[str], start_ms: int, end_ms: int) -> None: ...
def load_klines(symbol: str) -> pandas.DataFrame: ...     # reads the parquet above
def load_funding(symbol: str) -> pandas.DataFrame: ...
```

### `factors.py`
```python
def build_panel(symbols: list[str]) -> pandas.DataFrame: ...
    # wide close/high/low/volume panel: index=open_time (1m), columns=MultiIndex
    # (field, symbol). Built from collect.load_klines. Backward-only.
def compute_factors(panel: pandas.DataFrame) -> dict[str, pandas.DataFrame]: ...
    # returns {"momentum":df, "lowvol":df, "range":df, "reversal":df, "semivar_imbalance":df}
    # each df: index=open_time, columns=symbol, values=raw factor (causal, NaN if short).
    # semivar_imbalance = (RS- - RS+)/(RS- + RS+ + eps) over SEMIVAR_WINDOW (normalized,
    # bounded [-1,1]); long/short sign is UNVERIFIED, left to the train-only IC gate.
def composite_score(factors: dict, universe: pandas.DataFrame) -> pandas.DataFrame: ...
    # cross-sectional z-score per timestamp within that ts's PIT universe, equal-weight
    # combine of ALL factors in the dict -> one score df (index=open_time, columns=symbol).
    # NaN outside PIT universe.
def pit_membership(universe: pandas.DataFrame, index: pandas.DatetimeIndex) -> pandas.DataFrame: ...
    # boolean PIT universe mask (index=open_time, columns=symbol).
```

### `protocol.py`
```python
def future_returns(panel, execution_lag: int = 1, holding_period: int = 1) -> pandas.DataFrame: ...
    # target for score@t: enter at t+execution_lag, exit after holding_period bars.
def evaluate_candidates(scores: dict, target, train_index, thresholds) -> pandas.DataFrame: ...
    # train-only IC mean/t-stat/coverage/pass diagnostics for candidate scores.
def fit_ridge(scores: dict, target, train_index, alpha: float = 1.0) -> RidgeModel: ...
    # closed-form ridge beta fit on the train slice only.
def ridge_score(scores: dict, model: RidgeModel) -> pandas.DataFrame: ...
    # row-zscored combined score from fitted beta.
```

### `backtest.py`
```python
def run_backtest(score: pandas.DataFrame, panel: pandas.DataFrame,
                 universe: pandas.DataFrame, cost) -> "BacktestResult": ...
    # long-short by config.LONG_SHORT_QUANTILE, 1-bar execution lag (score@t -> ret@t+1),
    # per-name + gross caps, taker+slippage cost, funding as SEPARATE P&L line.
def metrics(result, split: str, cost) -> dict: ...     # AnnRet/AnnVol/Sharpe/MaxDD/Calmar/Turnover
    # every returned metric dict is tagged with (split, cost) — the wiki strict rule.
def cost_sweep(score, panel, universe) -> pandas.DataFrame: ...  # over config.COST_SWEEP_BP
```

## Bias controls (each stream owns its row)
- universe.py: survivorship — PIT top-30 incl. delisted; never select on full-sample survival.
- factors.py: look-ahead — backward-only windows; rolling/expanding normalization only.
- protocol.py: selection — IC gate and ridge fit use the train slice only; thresholds are
  explicit and marked unverified until supplied.
- backtest.py: 1-bar lag, train/valid/OOS splits, selection on train only, cost sweep,
  delisted names exit at last tradeable bar, (split, cost) tags on every metric.
