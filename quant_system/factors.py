"""Point-in-time cross-sectional factors and their composite (signals stream).

Four causal, backward-only factors on a 1m Binance USDⓈ-M perp panel, plus an
equal-weight z-scored composite scored within each timestamp's point-in-time
universe. Every time-series operator looks strictly backward (see
wiki/concepts/constrained-factor-dsl.md and wiki/concepts/lookahead-bias.md):
the value at t uses only data <= t. Schemas/signatures per quant_system/INTERFACES.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

FIELDS = ("close", "high", "low", "volume")


# --- panel -------------------------------------------------------------------
def build_panel(symbols: list[str]) -> pd.DataFrame:
    """Wide OHLCV panel: index=open_time (1m), columns=MultiIndex (field, symbol).

    Built from collect.load_klines (imported lazily so this module imports even
    if collect.py is not finished). Backward-only: timestamps are the outer union
    of each symbol's bars; gaps are left as NaN (no forward-fill across listing gaps).
    """
    from .collect import load_klines  # lazy: parallel DATA stream may be unfinished

    frames: dict[tuple[str, str], pd.Series] = {}
    for sym in symbols:
        kl = load_klines(sym)
        for field in FIELDS:
            frames[(field, sym)] = kl[field]
    panel = pd.DataFrame(frames)
    panel.columns = pd.MultiIndex.from_tuples(panel.columns, names=["field", "symbol"])
    panel = panel.sort_index()
    panel.index.name = "open_time"
    return panel


def _log_returns(close: pd.DataFrame) -> pd.DataFrame:
    """Per-symbol log returns r_t = log(close_t) - log(close_{t-1}). Causal."""
    return np.log(close).diff()


# --- factors -----------------------------------------------------------------
def compute_factors(panel: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Four raw factors, each index=open_time, columns=symbol. Strictly causal.

    momentum : MA_{MOMENTUM_WINDOW} of log returns, lagged REVERSAL_WINDOW bars
               (skip most-recent bars -> disjoint from reversal). Long winners.
    lowvol   : -std_{LOWVOL_WINDOW} of log returns. Long low realized vol.
    range    : MA_{RANGE_WINDOW} of (high-low)/close. Persistent intraday range LEVEL.
    reversal : -sum_{REVERSAL_WINDOW} of log returns. Long recent losers.

    NaN where the trailing lookback is insufficient (min_periods = full window).
    """
    close = panel["close"]
    high = panel["high"]
    low = panel["low"]

    r = _log_returns(close)

    momentum = (
        r.rolling(config.MOMENTUM_WINDOW, min_periods=config.MOMENTUM_WINDOW)
        .mean()
        .shift(config.REVERSAL_WINDOW)
    )

    lowvol = -r.rolling(config.LOWVOL_WINDOW, min_periods=config.LOWVOL_WINDOW).std()

    hl_range = (high - low) / close
    range_ = hl_range.rolling(
        config.RANGE_WINDOW, min_periods=config.RANGE_WINDOW
    ).mean()

    reversal = -r.rolling(
        config.REVERSAL_WINDOW, min_periods=config.REVERSAL_WINDOW
    ).sum()

    return {
        "momentum": momentum,
        "lowvol": lowvol,
        "range": range_,
        "reversal": reversal,
    }


# --- composite ---------------------------------------------------------------
def pit_membership(universe: pd.DataFrame, index: pd.DatetimeIndex) -> pd.DataFrame:
    """Boolean membership mask (index=timestamps, columns=symbol) from the PIT
    universe long df. Each 1m timestamp inherits the membership of the most recent
    rebalance date on or before its UTC day (backward-only, merge_asof)."""
    uni = universe[universe["listed"]] if "listed" in universe.columns else universe
    uni = uni[["date", "binance_symbol"]].copy()
    uni["date"] = pd.to_datetime(uni["date"], utc=True).dt.tz_localize(None)

    rebal_dates = np.sort(uni["date"].unique())
    # normalize bar timestamps to tz-naive UTC days so they compare with rebal_dates
    bars = index.tz_convert("UTC").tz_localize(None) if index.tz is not None else index
    days = bars.normalize()  # UTC day of each bar
    # for each bar, the most recent rebalance date <= its day
    pos = np.searchsorted(rebal_dates, days.values, side="right") - 1

    symbols = sorted(uni["binance_symbol"].unique())
    members_by_date = {
        d: set(g["binance_symbol"]) for d, g in uni.groupby("date")
    }
    mask = pd.DataFrame(False, index=index, columns=symbols)
    for d in rebal_dates:
        rows = np.where(pos >= 0)[0]
        sel = rows[rebal_dates[pos[rows]] == d]
        present = members_by_date[pd.Timestamp(d)]
        for sym in present:
            if sym in mask.columns:
                mask.iloc[sel, mask.columns.get_loc(sym)] = True
    return mask


_pit_membership = pit_membership


def _zscore_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional z-score within each timestamp (row). Uses only present
    (non-NaN) values in that row -> no leakage across time."""
    mu = df.mean(axis=1)
    sd = df.std(axis=1, ddof=0)
    return df.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)


def composite_score(
    factors: dict[str, pd.DataFrame], universe: pd.DataFrame
) -> pd.DataFrame:
    """Equal-weight composite of the 4 z-scored factors, per-timestamp z-scored
    within that timestamp's PIT universe. Index=open_time, columns=symbol.
    NaN outside the PIT universe.
    """
    keys = ["momentum", "lowvol", "range", "reversal"]
    index = factors["momentum"].index
    symbols = factors["momentum"].columns

    mask = pit_membership(universe, index).reindex(
        index=index, columns=symbols, fill_value=False
    )

    zs = []
    for k in keys:
        f = factors[k].where(mask)  # drop out-of-universe names before z-scoring
        zs.append(_zscore_rows(f))

    # equal-weight combine; require all 4 factors present for a name at t
    stacked = pd.concat([z.stack() for z in zs], axis=1)
    combined = stacked.mean(axis=1, skipna=False)
    score = combined.unstack()
    score = score.reindex(index=index, columns=symbols)
    return score.where(mask)


# --- self-test ---------------------------------------------------------------
def _synthetic_panel(symbols, n_bars, seed=0) -> pd.DataFrame:
    """Random-walk OHLCV panel in the build_panel wide layout, for self-testing."""
    rng = np.random.default_rng(seed)
    index = pd.date_range("2025-01-01", periods=n_bars, freq="1min", tz="UTC")
    index.name = "open_time"
    frames = {}
    for sym in symbols:
        close = np.exp(np.cumsum(rng.standard_normal(n_bars) * 0.001))
        spread = np.abs(rng.standard_normal(n_bars)) * 0.002 * close
        high = close + spread
        low = close - spread
        vol = np.abs(rng.standard_normal(n_bars)) * 100
        frames[("close", sym)] = pd.Series(close, index=index)
        frames[("high", sym)] = pd.Series(high, index=index)
        frames[("low", sym)] = pd.Series(low, index=index)
        frames[("volume", sym)] = pd.Series(vol, index=index)
    panel = pd.DataFrame(frames)
    panel.columns = pd.MultiIndex.from_tuples(panel.columns, names=["field", "symbol"])
    panel.index.name = "open_time"
    return panel


def _selftest() -> None:
    symbols = ["AAAUSDT", "BBBUSDT", "CCCUSDT"]
    n = 3000
    panel = _synthetic_panel(symbols, n)

    # --- shape + warmup-only-NaN ---
    factors = compute_factors(panel)
    assert set(factors) == {"momentum", "lowvol", "range", "reversal"}
    warmup = {
        "momentum": config.MOMENTUM_WINDOW + config.REVERSAL_WINDOW,
        "lowvol": config.LOWVOL_WINDOW,
        "range": config.RANGE_WINDOW,
        "reversal": config.REVERSAL_WINDOW,
    }
    for k, df in factors.items():
        assert list(df.columns) == symbols, k
        assert df.index.equals(panel.index), k
        # NaN only in the warmup region; clean thereafter
        assert df.iloc[warmup[k]:].notna().all().all(), f"{k} has NaN past warmup"
        assert df.iloc[: warmup[k] - 1].isna().all().all(), f"{k} non-NaN in warmup"
    print(f"shape/warmup test PASS ({warmup})")

    # --- CAUSALITY: delete bars after t, recompute, value at t must be identical ---
    t_pos = 2000
    t = panel.index[t_pos]
    trunc = panel.loc[:t]
    f_trunc = compute_factors(trunc)
    max_diff = 0.0
    for k in factors:
        full_row = factors[k].loc[t]
        trunc_row = f_trunc[k].loc[t]
        # NaN pattern must match and finite values must be byte-identical
        assert full_row.isna().equals(trunc_row.isna()), f"{k} NaN pattern changed at t"
        a = full_row.dropna().values
        b = trunc_row.dropna().values
        if len(a):
            d = np.max(np.abs(a - b))
            max_diff = max(max_diff, d)
            assert np.array_equal(a, b), f"{k} value changed at t (diff={d})"
    print(f"CAUSALITY test PASS: factor value at t={t} byte-identical after "
          f"truncation (max abs diff={max_diff:.1e})")

    # --- disjoint momentum vs reversal windows ---
    mom_window = set(range(t_pos - config.MOMENTUM_WINDOW - config.REVERSAL_WINDOW + 1,
                           t_pos - config.REVERSAL_WINDOW + 1))
    rev_window = set(range(t_pos - config.REVERSAL_WINDOW + 1, t_pos + 1))
    assert mom_window.isdisjoint(rev_window), "momentum/reversal windows overlap"
    print(f"disjoint-window test PASS: momentum bars {min(mom_window)}..{max(mom_window)}"
          f" vs reversal bars {min(rev_window)}..{max(rev_window)}")

    # --- composite: PIT universe masking + row z-score ---
    days = panel.index.normalize().unique()
    uni_rows = []
    for d in days:
        # AAA and BBB always in; CCC only from the 2nd day -> exercises PIT masking
        members = ["AAAUSDT", "BBBUSDT"] + (["CCCUSDT"] if d != days[0] else [])
        for i, sym in enumerate(members, 1):
            uni_rows.append({"date": d, "binance_symbol": sym, "market_cap": 1.0,
                             "rank": i, "listed": True})
    universe = pd.DataFrame(uni_rows)

    score = composite_score(factors, universe)
    assert list(score.columns) == symbols
    # CCC must be NaN on day 0 (outside PIT universe)
    day0_mask = score.index.normalize() == days[0]
    assert score.loc[day0_mask, "CCCUSDT"].isna().all(), "CCC leaked into day-0 universe"
    # where all factors present, in-universe rows z-score to ~0 mean across the cross-section
    valid = score.dropna(how="all")
    nz = valid.dropna()  # rows with all 3 names present (day>=1, past warmup)
    if len(nz):
        row_means = nz.mean(axis=1)
        assert np.allclose(row_means.values, 0.0, atol=1e-9), "composite row mean != 0"
    print(f"composite test PASS: PIT-masked (CCC NaN on day 0), rows z-centered "
          f"({len(nz)} fully-populated rows)")

    print("\nALL SELF-TESTS PASSED")


if __name__ == "__main__":
    _selftest()
