---
title: h4_smallcap_low_dollar_volume
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, scarcity, dollar-volume]
status: unverified
last_reviewed: 2026-06-24
---

# h4_smallcap_low_dollar_volume  (Table 1 rank 6)

- **hypothesis:** Pure scarcity — small market cap and low dollar volume jointly predict higher cross-sectional returns.
- **economic_rationale:** Paper — level-based scarcity is the *stable* driver. *My take:* this is the cleanest statement of the paper's core edge = an illiquidity premium. Also the clearest capacity warning: it explicitly longs the least tradeable names ([[capacity-constraint]]).
- **candidate_type:** exploratory (scarcity family, round h4).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( -0.5*log(1+mcap) - 0.5*log(1+close*volume) )   # close*volume ≈ dollar volume
  inputs: mcap, close, volume
  ```
- **metrics:**
  - Sharpe_LS = **+1.796** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way. *This factor is the one most fragile to a realistic cost model* — its longs are exactly where 5 bp is fiction ([[contradictions]] §2, §5).
- **capacity_liquidity:** **lowest of the set** — definitionally targets low dollar volume.
- **binance_perp_fit:** essentially **un-portable** — no perp lives in "low dollar volume small-cap." See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[capacity-constraint]]
