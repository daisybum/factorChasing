import numpy as np
import pandas as pd

from quant_system import protocol as P


def _panel(close: pd.DataFrame) -> pd.DataFrame:
    high = close * 1.001
    low = close * 0.999
    volume = close * 0 + 100.0
    panel = pd.concat({"close": close, "high": high, "low": low, "volume": volume}, axis=1)
    panel.columns = panel.columns.set_names(["field", "symbol"])
    return panel


def test_future_returns_respects_execution_lag_and_holding_period():
    idx = pd.date_range("2026-01-01", periods=5, freq="1min", tz="UTC")
    close = pd.DataFrame({"AAAUSDT": [100, 101, 103, 106, 110]}, index=idx)

    target = P.future_returns(_panel(close), execution_lag=1, holding_period=1)

    assert target.loc[idx[0], "AAAUSDT"] == (103 / 101) - 1
    assert target.loc[idx[1], "AAAUSDT"] == (106 / 103) - 1
    assert np.isnan(target.loc[idx[-1], "AAAUSDT"])


def test_ic_gate_uses_train_slice_only():
    idx = pd.date_range("2026-01-01", periods=8, freq="1min", tz="UTC")
    cols = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT"]
    base = pd.DataFrame([[-2, -1, 1, 2]] * len(idx), index=idx, columns=cols)
    target = base.copy()
    score = base.copy()
    score.iloc[4:] *= -1.0  # OOS inversion must not affect train-only gate.

    diagnostics = P.ic_diagnostics(
        score,
        target,
        train_index=idx[:4],
        thresholds=P.GateThresholds(min_ic=0.9, min_t=1.0, min_obs=3),
    )

    assert diagnostics["passed"] is True
    assert diagnostics["mean_ic"] > 0.99


def test_ridge_fit_and_score_are_train_only_and_finite():
    idx = pd.date_range("2026-01-01", periods=10, freq="1min", tz="UTC")
    cols = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT"]
    f1 = pd.DataFrame([[-2, -1, 1, 2]] * len(idx), index=idx, columns=cols)
    f2 = -f1
    target = f1 * 0.01

    model = P.fit_ridge({"f1": f1, "f2": f2}, target, train_index=idx[:6], alpha=1.0)
    score = P.ridge_score({"f1": f1, "f2": f2}, model)

    assert model.train_rows == 24
    assert set(model.beta.index) == {"f1", "f2"}
    assert score.shape == f1.shape
    assert np.isfinite(score.dropna().to_numpy()).all()
