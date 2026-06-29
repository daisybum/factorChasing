---
title: h1_smallcap_lowvol_logret_vol
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, scarcity, low-vol, return-vol]
status: unverified
last_reviewed: 2026-06-24
---

# h1_smallcap_lowvol_logret_vol  (Table 1 rank 1)

- **hypothesis:** Small-cap, low-volatility tokens with controlled log-return dispersion out-earn large/volatile peers cross-sectionally.
- **economic_rationale:** Paper — scarcity + vol-management premium in crypto small-caps. *My take:* this is a size × low-vol tilt; in crypto "low-vol small-cap" is unusual and likely proxies illiquidity/neglect rather than true defensiveness → edge is a liquidity premium ([[capacity-constraint]]).
- **candidate_type:** exploratory (scarcity hypothesis family, round h1).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( -0.5*log(1+mcap) - 0.3*realized_volatility - 0.2*MA_5(abs(log_return)) )
  inputs: mcap, realized_volatility, log_return  (derived panel)
  ```
- **metrics:**
  - Sharpe_LS = **+2.412** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (paper Table 1).
  - IC_mean / t_IC / coverage = **unverified** (not disclosed per factor).
- **gate_pass:** presumed **pass** (entered reporting) — thresholds τ_IC/τ_t and this factor's train IC **unverified**. See [[ic-gating]].
- **net_of_cost:** OOS Sharpe is already net of 5 bp one-way. 10 bp behaviour **not separately reported per factor** ([[contradictions]] §1).
- **capacity_liquidity:** high small-cap dependence; alpha sits in illiquid names → low capacity ([[capacity-constraint]]).
- **binance_perp_fit:** weak. Requires `mcap` (no perp native) and lives in micro-caps absent from the ~20–40 USDⓈ-M perp universe. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[constrained-factor-dsl]]
