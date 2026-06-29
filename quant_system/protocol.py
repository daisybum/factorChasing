"""Train-only IC gating and ridge combination for the Binance-port research loop.

This module implements the deterministic evaluation layer the paper requires:
candidate scores are measured against a lagged forward target on the training
slice only, candidates pass an IC/t-stat gate, and passed scores can be combined
with a ridge fit trained only on that same slice. It does not generate LLM
hypotheses; it makes the gate/combiner explicit and testable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GateThresholds:
    min_ic: float
    min_t: float
    min_obs: int = 5


@dataclass(frozen=True)
class RidgeModel:
    alpha: float
    beta: pd.Series
    train_rows: int


def future_returns(
    panel: pd.DataFrame,
    execution_lag: int = 1,
    holding_period: int = 1,
) -> pd.DataFrame:
    """Return target for score@t: entry at t+lag, exit after holding_period bars."""
    if execution_lag < 0 or holding_period <= 0:
        raise ValueError("execution_lag must be >=0 and holding_period must be >0")
    close = panel["close"] if isinstance(panel.columns, pd.MultiIndex) else panel
    entry = close.shift(-execution_lag)
    exit_ = close.shift(-(execution_lag + holding_period))
    return exit_.div(entry) - 1.0


def _row_ic(score: pd.DataFrame, target: pd.DataFrame, min_names: int) -> pd.Series:
    score, target = score.align(target, join="inner", axis=0)
    score, target = score.align(target, join="inner", axis=1)
    out = {}
    for ts in score.index:
        pair = pd.concat([score.loc[ts], target.loc[ts]], axis=1).dropna()
        if len(pair) < min_names:
            out[ts] = np.nan
        else:
            out[ts] = pair.iloc[:, 0].corr(pair.iloc[:, 1])
    return pd.Series(out, name="ic").dropna()


def ic_diagnostics(
    score: pd.DataFrame,
    target: pd.DataFrame,
    train_index: pd.DatetimeIndex,
    thresholds: GateThresholds,
) -> dict:
    """Mean IC, IC t-stat, coverage, and pass/fail on the training slice only."""
    train_index = pd.DatetimeIndex(train_index)
    s = score.reindex(train_index)
    t = target.reindex(train_index)
    ic = _row_ic(s, t, min_names=thresholds.min_obs)
    mean_ic = float(ic.mean()) if len(ic) else float("nan")
    std_ic = float(ic.std(ddof=1)) if len(ic) > 1 else float("nan")
    if std_ic > 0:
        t_ic = float(mean_ic / (std_ic / np.sqrt(len(ic))))
    elif np.isfinite(mean_ic) and mean_ic != 0.0:
        t_ic = float(np.sign(mean_ic) * np.inf)
    else:
        t_ic = float("nan")
    coverage = float((s.notna() & t.notna()).sum().sum() / max(s.size, 1))
    passed = bool(
        len(ic) >= thresholds.min_obs
        and np.isfinite(mean_ic)
        and not np.isnan(t_ic)
        and mean_ic >= thresholds.min_ic
        and t_ic >= thresholds.min_t
    )
    return {
        "mean_ic": mean_ic,
        "t_ic": t_ic,
        "n_ic": int(len(ic)),
        "coverage": coverage,
        "passed": passed,
        "gate": f"IC>={thresholds.min_ic}, t>={thresholds.min_t}, n>={thresholds.min_obs}",
    }


def evaluate_candidates(
    scores: dict[str, pd.DataFrame],
    target: pd.DataFrame,
    train_index: pd.DatetimeIndex,
    thresholds: GateThresholds,
) -> pd.DataFrame:
    """Evaluate all candidate score frames with the same train-only gate."""
    rows = []
    for name, score in scores.items():
        row = ic_diagnostics(score, target, train_index, thresholds)
        row["candidate"] = name
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=["candidate", "mean_ic", "t_ic", "n_ic", "coverage", "passed", "gate"])
    return pd.DataFrame(rows).set_index("candidate").sort_index()


def _zscore_rows(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean(axis=1)
    sd = df.std(axis=1, ddof=0).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0)


def _stack_design(scores: dict[str, pd.DataFrame], target: pd.DataFrame, index) -> tuple[pd.DataFrame, pd.Series]:
    cols = []
    for name, score in scores.items():
        z = _zscore_rows(score.reindex(index))
        cols.append(z.stack().rename(name))
    x = pd.concat(cols, axis=1)
    y = target.reindex(index).stack().rename("target")
    xy = x.join(y).replace([np.inf, -np.inf], np.nan).dropna()
    return xy[list(scores)], xy["target"]


def fit_ridge(
    scores: dict[str, pd.DataFrame],
    target: pd.DataFrame,
    train_index: pd.DatetimeIndex,
    alpha: float = 1.0,
) -> RidgeModel:
    """Closed-form ridge beta fit on the training slice only."""
    if alpha < 0:
        raise ValueError("alpha must be non-negative")
    if not scores:
        raise ValueError("at least one score is required")
    x, y = _stack_design(scores, target, pd.DatetimeIndex(train_index))
    if len(x) == 0:
        raise ValueError("no finite train rows for ridge fit")
    xtx = x.to_numpy().T @ x.to_numpy()
    xty = x.to_numpy().T @ y.to_numpy()
    beta = np.linalg.solve(xtx + alpha * np.eye(xtx.shape[0]), xty)
    return RidgeModel(alpha=float(alpha), beta=pd.Series(beta, index=x.columns), train_rows=len(x))


def ridge_score(scores: dict[str, pd.DataFrame], model: RidgeModel) -> pd.DataFrame:
    """Apply a fitted ridge model to score frames and row-zscore the combined score."""
    missing = [name for name in model.beta.index if name not in scores]
    if missing:
        raise KeyError(f"missing scores for ridge beta columns: {missing}")
    first = scores[model.beta.index[0]]
    out = pd.DataFrame(0.0, index=first.index, columns=first.columns)
    valid = pd.DataFrame(True, index=first.index, columns=first.columns)
    for name, beta in model.beta.items():
        z = _zscore_rows(scores[name])
        out = out.add(z * beta, fill_value=np.nan)
        valid &= z.notna()
    out = out.where(valid)
    return _zscore_rows(out)
