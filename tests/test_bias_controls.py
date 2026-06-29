import numpy as np

from quant_system import backtest as B
from quant_system import config
from quant_system import factors as F


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
