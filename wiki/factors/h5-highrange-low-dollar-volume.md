---
title: h5_highrange_low_dollar_volume
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, range, dollar-volume]
status: unverified
last_reviewed: 2026-06-24
---

# h5_highrange_low_dollar_volume  (Table 1 rank 7)

- **hypothesis:** High intraday range plus low dollar volume out-earns — illiquid names with persistent price swings.
- **economic_rationale:** Paper — range level + scarcity. *My take:* range × low-dollar-volume is almost a definition of "thinly traded and bouncing"; very likely the same underlying illiquidity premium as ranks 2/3/6 wearing different inputs ([[multiple-testing-snooping]]).
- **candidate_type:** exploratory (round h5).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( 0.5*MA_10(high_low_range) - 0.5*log(1+close*volume) )
  inputs: high_low_range, close, volume
  ```
- **metrics:**
  - Sharpe_LS = **+1.730** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** very low (low dollar volume by construction).
- **binance_perp_fit:** poor — low-dollar-volume leg absent from perp universe. Range term alone is portable. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[h4-smallcap-low-dollar-volume]]
