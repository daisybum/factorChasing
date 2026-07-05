---
title: Factors Index
type: index
source: "arXiv:2604.26747v1"
tags: [index, factors]
status: ingested
last_reviewed: 2026-06-24
---

# Factors Index

**25 single factors** generated across 5 rounds; the paper tabulates the **top 9 by
pure-OOS Sharpe** (Table 1). ⚠ The paper discloses **only the name and OOS Sharpe** per
factor — **no DSL recipe, no IC̄, no t_IC, no gate pass/fail**. All recipe fields on the
factor pages below are therefore **reconstructed from the factor name + the paper's DSL
vocabulary**, and are marked `status: unverified`. Treat them as *my* hypotheses about
what the agent built, not as disclosed facts. See [[multiple-testing-snooping]] —
this OOS ranking is upward-biased by selection.

| Rank | Factor (page) | Pure OOS Sharpe | Archetype |
|---|---|---|---|
| 1 | [[h1-smallcap-lowvol-logret-vol]] | +2.412 | scarcity × low-vol × ret-vol |
| 2 | [[h5-smallcap-low-volume-range20]] | +2.410 | scarcity × range(20d) |
| 3 | [[h4-low-volume-smallcap-range5]] | +2.250 | scarcity × range(5d) |
| 4 | [[h1-highrange-lowvol-short-window]] | +2.151 | range × low-vol (short) |
| 5 | [[h3-lag-momentum-highrange]] | +1.879 | momentum × range |
| 6 | [[h4-smallcap-low-dollar-volume]] | +1.796 | scarcity (dollar-vol) |
| 7 | [[h5-highrange-low-dollar-volume]] | +1.730 | range × low dollar-vol |
| 8 | [[h4-lag-mom-highrange-20d-range]] | +1.728 | momentum × range(20d) |
| 9 | [[h2-momentum-lowvol-short-window]] | +1.700 | momentum × low-vol (short) |

Final combined book: [[aggregated-portfolio]] (ridge of survivors → equal-weight L-S).

## Common building blocks
- **Scarcity:** `−log(1+mcap)`, `−volume`, `−dollar_volume`, `−relative_volume`. (stable / level-based)
- **Range:** `MA_k(high_low_range)`, k ∈ {5,10,20} or short-window. (level stable; *changes* noisy)
- **Momentum/trend:** `lag`+`MA` of returns / log returns, positive tilt. (behavior-driven)
- **Vol management:** `−realized_volatility` or `−ret_vol`. (low-vol tilt)

Failed/noisy per paper: **range *changes*** and **volume *recoveries***. Stable:
**level scarcity** and **attention**.

## Repo-original factors (NOT from the paper)
Candidates added to the Binance USDⓈ-M perp seed, kept separate from the paper's Table 1 so
provenance is not confused. All `unverified` until the train-only gate + cost sweep run.

| Factor (page) | Source | Idea | Status |
|---|---|---|---|
| [[signed-semivariance-imbalance]] | repo-original | normalized signed realized-semivariance `(RS⁻−RS⁺)/(RS⁻+RS⁺)` | unverified |

Related: [[constrained-factor-dsl]] · [[ic-gating]] · [[capacity-constraint]]
