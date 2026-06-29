---
title: h5_smallcap_low_volume_range20
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, scarcity, range, low-volume]
status: unverified
last_reviewed: 2026-06-24
---

# h5_smallcap_low_volume_range20  (Table 1 rank 2)

- **hypothesis:** Small-cap, low-volume tokens that sustain a wide 20-day intraday range out-earn the cross-section.
- **economic_rationale:** Paper — *level* of intraday range is a stable predictor (range *changes* are noise); combined with scarcity. *My take:* persistent wide range = chronic illiquidity/price-discovery friction; the "alpha" rents that friction → not scalable.
- **candidate_type:** exploratory (round h5, scarcity × range).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( -0.5*log(1+mcap) - 0.3*relative_volume + 0.4*MA_20(high_low_range) )
  inputs: mcap, relative_volume, high_low_range
  ```
- **metrics:**
  - Sharpe_LS = **+2.410** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; per-factor IC/thresholds **unverified** ([[ic-gating]]).
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** very low — explicitly low-volume + small-cap. Highest slippage risk.
- **binance_perp_fit:** poor; needs `mcap`, targets low-volume names that won't have liquid perps. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[capacity-constraint]]
