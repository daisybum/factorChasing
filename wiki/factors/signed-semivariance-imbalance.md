---
title: signed_semivariance_imbalance
type: factor
source: "repo-original (not from arXiv:2604.26747v1)"
tags: [factor, semivariance, realized-vol, repo-original]
status: unverified
last_reviewed: 2026-06-30
---

# signed_semivariance_imbalance  (repo-original candidate #5)

> **Not a paper factor.** This is a repo-original candidate added to the Binance USDⓈ-M
> perp seed, *not* one of the paper's 25 ([[factors-index]]). Provenance is the codebase,
> not arXiv:2604.26747v1.

- **hypothesis:** Decomposing 1m returns into upside vs downside realized semivariance and
  trading the **normalized signed imbalance** carries cross-sectional information beyond a
  plain volatility level or raw reversal. Prior (UNVERIFIED): names whose recent variance is
  **downside-dominated** (RS⁻ ≫ RS⁺) short-term **revert up** after overcrowded/forced selling.
- **economic_rationale:** "Good vs bad volatility" (Patton & Sheppard 2015): the *asymmetry*
  of realized variance, not its level, holds the signal. The diffusive part cancels in
  RS⁺−RS⁻, so the imbalance isolates the directional/jump-like component. The opposite sign is
  plausible in crash-continuation regimes — so the sign is **pre-registered but not asserted**;
  the train-only IC gate ([[ic-gating]]) decides, and it must not be flipped post-hoc.
- **candidate_type:** exploratory (repo-original, no paper precedent).
- **dsl_recipe** *(implemented, causal / point-in-time)*:
  ```
  r_t        = log(close_t) - log(close_{t-1})
  RS_minus_t = sum_{s in (t-W, t]} r_s^2 * 1{r_s < 0}     # downside semivariance
  RS_plus_t  = sum_{s in (t-W, t]} r_s^2 * 1{r_s > 0}     # upside semivariance
  semivar_imbalance_t = (RS_minus_t - RS_plus_t) / (RS_minus_t + RS_plus_t + eps)
  inputs: close ;  W = SEMIVAR_WINDOW (120 bars = 2h) ;  eps = 1e-12
  ```
  Normalized to [-1, 1] on purpose — the raw difference `RS⁻ − RS⁺` is a volatility-*level*
  proxy and is kept diagnostic-only. Backward-only (`min_periods = W`); no look-ahead
  ([[lookahead-bias]]).
- **metrics:** IC_mean / t_IC / Sharpe_LS / coverage = **unverified** — to be filled only from
  the train-only gate + cost-sweep path, each tagged (split, cost). No number reported yet.
- **gate_pass:** pending (train-only IC gate; thresholds are repo placeholders, not paper values).
- **net_of_cost:** turnover is window-based (vol-factor-like), so the 1m cost profile is
  expected to be more benign than the price 1m factors — but this is a claim to be verified by
  the 5/10/20 bp `cost_sweep`, not assumed. See [[_adaptation]].
- **capacity_liquidity:** downside-variance asymmetry tends to concentrate in small/illiquid
  alts (forced-selling microstructure) → likely **capacity-constrained** ([[capacity-constraint]]).
- **orthogonality (must check):** report rank correlations vs `reversal`, `lowvol`, `range` on
  train/valid/oos. If `|corr|` is high, treat as redundant unless a residualized version
  survives train-only gating. Direction overlaps `reversal`; the edge, if any, is the
  *sign-split variance source*, not cumulative return.
- **microstructure caveat:** 1m noise biases realized (semi)variance. v1 uses raw 1m; a 1m vs
  5m sub-sampled robustness check is the guard (pre-averaging/sub-sampling if it collapses).
- **status:** unverified.

Related: [[factors-index]] · [[constrained-factor-dsl]] · [[binance-port-protocol]] · [[_adaptation]]
