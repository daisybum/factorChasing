---
title: Aggregated Portfolio (ridge-combined equal-weight L-S)
type: factor
source: "arXiv:2604.26747v1"
tags: [factor, portfolio, aggregated, ridge, long-short, headline]
status: suspect
last_reviewed: 2026-06-24
---

# Aggregated Portfolio — the headline result

Ridge-combined ([[ridge-combination]]) composite of the gate-surviving factors, traded as
an **equal-weight long-short** quintile portfolio. Trained on 2020–2022, evaluated OOS
2024–2026. **Status: suspect** — see the Table 2 vs Table 3 reconciliation failure below
and [[contradictions]] §1.

## Headline (abstract)
> **44.55% annualized return, Sharpe 1.55**, pure OOS 2024–2026, after **5 bp one-way** cost.

## Table 2 — equal-weight combo quintiles (cost label NOT printed; presumed 5 bp — *unverified*)
| Group | AnnRet | AnnVol | Sharpe | MaxDD | Calmar | Turnover |
|---|---|---|---|---|---|---|
| Q0 (short) | −0.529 | 0.688 | −0.769 | −0.876 | −0.604 | 0.351 |
| Q1 | −0.525 | 0.691 | −0.760 | −0.888 | −0.592 | 0.589 |
| Q2 | −0.470 | 0.626 | −0.750 | −0.854 | −0.550 | 0.639 |
| Q3 | −0.357 | 0.557 | −0.641 | −0.819 | −0.436 | 0.601 |
| Q4 (long) | −0.104 | 0.519 | −0.201 | −0.698 | −0.149 | 0.384 |
| **L-S** | **0.445** | **0.287** | **1.551** | **−0.236** | **1.886** | **0.368** |

Note: every quintile Q0–Q4 has **negative** standalone return (2024–2026 was a hard tape
for these names); the L-S is positive **only** because the short leg lost more than the
long. Monotonicity is in the *spread*, not in absolute quintile returns.

## Table 3 — "fee sensitivity" (equal-weighted)
| Fee | AnnRet | AnnVol | Sharpe | Alpha |
|---|---|---|---|---|
| 0.1% | 0.016 | 0.028 | 0.57 | 0.014 |
| 0.2% | 0.014 | 0.027 | 0.52 | 0.012 |
| 0.3% | 0.012 | 0.026 | 0.46 | 0.010 |

## 🚨 Reconciliation failure (why this is `suspect`)
Table 2 L-S: AnnRet **0.445**, AnnVol **0.287**, Sharpe **1.551**.
Table 3 at 0.1%: AnnRet **0.016**, AnnVol **0.028**, Sharpe **0.57**.
- AnnVol differs by **~10×**; AnnRet by **~28×**. A move from 5 bp → 10 bp one-way cost
  **cannot** do this. These are **not the same portfolio.**
- Most likely Table 3 is a **different construction** — a vol-scaled / cap-weighted /
  dollar-neutral residual ("Alpha" column hints at a regression residual), not the
  headline equal-weight L-S.
- Therefore the user's worry — "fees crush Sharpe 1.55 → 0.46" — is **not cleanly a fee
  effect**; the comparison is apples-to-oranges. The honest statement: *the paper never
  shows the headline EW L-S re-costed at 10/20/30 bp.* That table is missing.
- **Until the Table 2 cost label and the Table 3 portfolio definition are confirmed,
  the headline is suspect.** Full treatment: [[contradictions]] §1.

## Net-of-cost reasoning I *can* stand behind
- If Table 3 *is* the same strategy de-levered to ~10% the size, the **per-unit-risk**
  picture (Sharpe) still falls from 1.55 to ~0.57 going 5→10 bp — a ~63% Sharpe haircut,
  consistent with a high-turnover small-cap book. That direction is robust even if the
  levels aren't.
- Turnover 0.368 (Table 2) with daily rebalance → cost drag is **linear in fee**; doubling
  one-way fee roughly doubles the drag. See [[contradictions]] §5 for my Binance recompute path.

## Capacity
EW beats cap-weight → alpha in small/illiquid tokens, **capacity constrained**
([[capacity-constraint]]). The headline 5 bp cost is implausible for the names doing the
work → real net Sharpe likely well below 1.55. See [[contradictions]] §2.

## Binance perp fit
Low. The composite leans on `mcap`/dollar-volume scarcity legs that don't exist in the
USDⓈ-M perp universe. The portable sub-signals are momentum × range
([[h3-lag-momentum-highrange]], [[h4-lag-mom-highrange-20d-range]], [[h2-momentum-lowvol-short-window]]).
Design: [[_adaptation]].

Related: [[factors-index]] · [[ridge-combination]] · [[contradictions]]
