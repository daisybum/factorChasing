---
title: h4_low_volume_smallcap_range5
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, scarcity, range, low-volume]
status: unverified
last_reviewed: 2026-06-24
---

# h4_low_volume_smallcap_range5  (Table 1 rank 3)

- **hypothesis:** Low-volume small-caps with elevated **5-day** intraday range out-earn the cross-section (shorter-window twin of rank 2).
- **economic_rationale:** Paper — short-window range level predicts. *My take:* near-identical to [[h5-smallcap-low-volume-range20]] but k=5 → the two are likely highly collinear; their joint presence in the top list inflates the apparent breadth of evidence ([[multiple-testing-snooping]]).
- **candidate_type:** exploratory (round h4).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( -0.4*relative_volume - 0.4*log(1+mcap) + 0.4*MA_5(high_low_range) )
  inputs: relative_volume, mcap, high_low_range
  ```
- **metrics:**
  - Sharpe_LS = **+2.250** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** very low (low-volume + small-cap).
- **binance_perp_fit:** poor — same constraints as rank 2. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[h5-smallcap-low-volume-range20]]
