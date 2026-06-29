---
title: h1_highrange_lowvol_short_window
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, range, low-vol]
status: unverified
last_reviewed: 2026-06-24
---

# h1_highrange_lowvol_short_window  (Table 1 rank 4)

- **hypothesis:** Tokens with high recent intraday range but low realized volatility (short window) out-earn — wide bars without trending vol.
- **economic_rationale:** Paper — range level stable, vol-managed. *My take:* "high range + low vol" is internally tense (range and vol co-move); the short window likely isolates choppy-but-not-trending names. Edge plausibly a microstructure/illiquidity artifact, not risk premium.
- **candidate_type:** exploratory (round h1, range × vol).
- **dsl_recipe** *(reconstructed, unverified)*:
  ```
  rank_t( 0.5*MA_3(high_low_range) - 0.5*MA_3(realized_volatility) )
  inputs: high_low_range, realized_volatility
  ```
- **metrics:**
  - Sharpe_LS = **+2.151** — split: **pure OOS 2024–2026**, cost: **5 bp one-way** (Table 1).
  - IC_mean / t_IC / coverage = **unverified**.
- **gate_pass:** presumed pass; **unverified**.
- **net_of_cost:** net of 5 bp one-way; 10 bp per-factor not reported ([[contradictions]] §1).
- **capacity_liquidity:** medium-low — no explicit mcap term, but high-range names skew small/illiquid in crypto.
- **binance_perp_fit:** **best of the set** — no `mcap` needed; range & realized vol compute directly on perp OHLC. Worth a standalone re-test on the perp universe. See [[_adaptation]].
- **status:** unverified.

Related: [[factors-index]] · [[constrained-factor-dsl]]
