import numpy as np
import pandas as pd

from quant_system import backtest as B
from quant_system import config
from quant_system import factors as F


def _one_spike_panel():
    """Two symbols whose only non-zero return is a single end-of-window spike:
    DNUSDT down, UPUSDT up — so downside vs upside semivariance is unambiguous."""
    w = config.SEMIVAR_WINDOW
    idx = pd.date_range("2025-01-01", periods=w + 2, freq="1min", tz="UTC", name="open_time")
    flat = np.full(len(idx), 100.0)
    down = flat.copy(); down[-1] = 100.0 * np.exp(-0.05)
    up = flat.copy(); up[-1] = 100.0 * np.exp(+0.05)
    frames = {}
    for name, cl in (("DNUSDT", down), ("UPUSDT", up)):
        s = pd.Series(cl, index=idx)
        frames[("close", name)] = s
        frames[("high", name)] = s
        frames[("low", name)] = s
        frames[("volume", name)] = pd.Series(1.0, index=idx)
    panel = pd.DataFrame(frames)
    panel.columns = pd.MultiIndex.from_tuples(panel.columns, names=["field", "symbol"])
    return panel


def test_semivar_imbalance_sign_and_bounds():
    si = F.compute_factors(_one_spike_panel())["semivar_imbalance"]
    last = si.iloc[-1]
    assert last["DNUSDT"] > 0          # downside semivariance dominates -> positive
    assert last["UPUSDT"] < 0          # upside semivariance dominates -> negative
    # normalized imbalance is bounded in [-1, 1] and finite where defined
    defined = si.iloc[config.SEMIVAR_WINDOW:]
    assert np.isfinite(defined.to_numpy()).all()
    assert (defined.to_numpy() >= -1.0 - 1e-9).all() and (defined.to_numpy() <= 1.0 + 1e-9).all()


def test_factor_values_are_causal_under_truncation():
    panel = F._synthetic_panel(["AAAUSDT", "BBBUSDT", "CCCUSDT"], 800)
    full = F.compute_factors(panel)
    t = panel.index[500]
    trunc = F.compute_factors(panel.loc[:t])

    for name in full:
        assert full[name].loc[t].isna().equals(trunc[name].loc[t].isna())
        assert np.array_equal(full[name].loc[t].dropna().values, trunc[name].loc[t].dropna().values)


def test_backtest_delisted_name_is_not_held_after_stop():
    score, panel, universe, funding, delist_bar = B._synth_inputs(n_bars=600, n_syms=8)
    cost = config.CostModel(taker_bp=5.0, slippage_bp=2.0, apply_funding=True, verified=False)
    cost._funding_override = funding

    result = B.run_backtest(score, panel, universe, cost)

    held_after = result.weights.loc[result.weights.index > delist_bar, "SYM00USDT"]
    assert (held_after == 0.0).all()


def test_cost_sweep_sharpe_decreases_with_higher_costs():
    score, panel, universe, funding, _ = B._synth_inputs(n_bars=600, n_syms=8)
    config.COST._funding_override = funding

    sweep = B.cost_sweep(score, panel, universe)
    sharpes = sweep["Sharpe"].to_list()

    assert all(x > y for x, y in zip(sharpes, sharpes[1:]))
