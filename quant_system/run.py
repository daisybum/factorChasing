"""Orchestrate the 4-factor seed end-to-end: data -> factors -> backtest.

Serial wave (per the plan): build universe + collect data, compute factors,
run the bias-aware backtest, print (split, cost)-tagged metrics + the fee sweep.

Usage:  /home/sanghyun/quant/.venv/bin/python -m quant_system.run
"""

from __future__ import annotations

import time

from . import config
from . import universe as U
from . import collect as C
from . import factors as F
from . import protocol as P
from . import backtest as B


def main(lookback_days: int = config.LOOKBACK_DAYS) -> None:
    # 1. survivorship-free point-in-time universe
    uni = U.build_universe(lookback_days=lookback_days)
    symbols = sorted(uni["binance_symbol"].dropna().unique().tolist())
    print(f"[universe] {len(symbols)} symbols, {uni['date'].nunique()} dates")

    # 2. collect 1m klines + funding for every symbol that ever entered the universe
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - lookback_days * 86_400_000
    C.collect_klines(symbols, start_ms, end_ms)
    C.collect_funding(symbols, start_ms, end_ms)

    # 3. factors -> composite score (causal, cross-sectional within PIT universe)
    panel = F.build_panel(symbols)
    factor_dfs = F.compute_factors(panel)
    mask = F.pit_membership(uni, panel.index).reindex(
        index=panel.index, columns=panel["close"].columns, fill_value=False
    )
    candidate_scores = {name: df.where(mask) for name, df in factor_dfs.items()}

    # 3b. protocol layer: train-only IC gate, then ridge over passed factors.
    target = P.future_returns(
        panel,
        execution_lag=config.EXECUTION_LAG_BARS,
        holding_period=config.HOLDING_PERIOD_BARS,
    )
    train_index = B.chronological_split(panel.index)["train"]
    gate = P.GateThresholds(
        min_ic=config.IC_MIN_MEAN,
        min_t=config.IC_MIN_T,
    )
    diagnostics = P.evaluate_candidates(candidate_scores, target, train_index, gate)
    print("[protocol] train-only IC diagnostics")
    print(diagnostics.to_string())
    passed = diagnostics.index[diagnostics["passed"]].tolist()
    if passed:
        model = P.fit_ridge(
            {name: candidate_scores[name] for name in passed},
            target,
            train_index,
            alpha=config.RIDGE_ALPHA,
        )
        print(f"[protocol] ridge alpha={model.alpha}, train_rows={model.train_rows}")
        print(f"[protocol] ridge beta={model.beta.to_dict()}")
        score = P.ridge_score({name: candidate_scores[name] for name in passed}, model)
    else:
        print("[protocol] no factor passed the configured gate; using equal-weight fallback")
        score = F.composite_score(factor_dfs, uni)

    # 4. bias-aware backtest, reported per split with (split, cost) tags
    result = B.run_backtest(score, panel, uni, config.COST)
    for split in ("train", "valid", "oos"):
        print(f"[metrics] {B.metrics(result, split, config.COST)}")

    # 5. fee-sensitivity sweep — fills the contradictions.md §1 "re-cost the headline" gap
    print("[cost sweep]")
    print(B.cost_sweep(score, panel, uni).to_string())

    if not config.COST.verified:
        print("\n[WARN] cost model is UNVERIFIED placeholder — supply real Binance "
              "maker/taker/BNB/VIP schedule before trusting net metrics (_adaptation.md §4).")


if __name__ == "__main__":
    main()
