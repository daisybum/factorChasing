---
title: h2_momentum_lowvol_short_window
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, momentum, low-vol]
status: unverified
last_reviewed: 2026-06-24
---

# h2_momentum_lowvol_short_window  (Table 1 rank 9)

- **hypothesis:** Short-window momentum with low realized volatility out-earns — risk-managed trend.
- **economic_rationale:** Paper — momentum with vol management is profitable. *My take:* a crypto "low-vol momentum" / quality-momentum hybrid; the most *transferable* signal because it carries no scarcity/volume term. Likely overlaps standard momentum factors.
- **candidate_type:** mechanical (momentum + low-vol, both established).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( 0.6*MA_3(lag_1(log_return)) - 0.4*MA_3(realized_volatility) )
  inputs: log_return, realized_volatility
  ```
- **metrics:**
  - Sharpe_LS = **+1.700** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** **highest of the set** — no scarcity term, can run on liquid names.
- **binance_perp_fit:** **best portability** — pure price/vol signal, no `mcap`/dollar-volume. Top candidate to lift onto the USDⓈ-M perp universe. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[h3-lag-momentum-highrange]]
