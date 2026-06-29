---
title: h4_lag_mom_highrange_20d_range
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, momentum, range]
status: unverified
last_reviewed: 2026-06-24
---

# h4_lag_mom_highrange_20d_range  (Table 1 rank 8)

- **hypothesis:** Lagged momentum plus a high 20-day intraday range out-earns — longer-horizon twin of rank 5.
- **economic_rationale:** Paper — momentum × range level. *My take:* longer-window variant of [[h3-lag-momentum-highrange]]; collinear with it. The 20d range smooths noise but adds drift in signal lag.
- **candidate_type:** mechanical (momentum) + exploratory range overlay.
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( 0.5*MA_20(lag_1(log_return)) + 0.5*MA_20(high_low_range) )
  inputs: log_return, high_low_range
  ```
- **metrics:**
  - Sharpe_LS = **+1.728** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** medium — momentum scalable, range tilts small.
- **binance_perp_fit:** **good** — fully computable on perp OHLC; pairs with rank 5 as the deployable momentum×range candidate. Re-test priority. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[h3-lag-momentum-highrange]]
