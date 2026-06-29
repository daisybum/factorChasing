---
title: h3_lag_momentum_highrange
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, momentum, range]
status: unverified
last_reviewed: 2026-06-24
---

# h3_lag_momentum_highrange  (Table 1 rank 5)

- **hypothesis:** Lagged positive momentum combined with high intraday range out-earns — trending tokens with active price discovery.
- **economic_rationale:** Paper — "behavior-driven momentum dominates risk-based anomalies" in crypto; positive trend + range. *My take:* the most economically standard signal here (crypto time-series/cross-sectional momentum is well documented); the range term is the novel tilt. Most likely to partially overlap CTREND ([[benchmarks-ctrend-ff]]).
- **candidate_type:** mechanical (momentum is a textbook anomaly) with exploratory range overlay.
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( 0.5*MA_10(lag_1(log_return)) + 0.5*MA_10(high_low_range) )
  inputs: log_return, high_low_range
  ```
- **metrics:**
  - Sharpe_LS = **+1.879** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** medium — momentum portable to large-caps, range tilt pulls toward small-caps.
- **binance_perp_fit:** **good** — momentum + range both native to perp OHLC; closest to a deployable cross-sectional perp factor. Re-test priority. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[benchmarks-ctrend-ff]]
