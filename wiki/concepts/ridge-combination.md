---
title: Ridge Combination
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, ensemble, ridge, portfolio-construction]
status: partial
last_reviewed: 2026-06-29
---

# Ridge Combination

After the 5-round search stops, surviving factors are combined by **ridge regression**
into a single composite score, which then drives the equal-weight long-short portfolio.
Evaluated separately on train / valid / OOS.

## What is disclosed
- The combiner is **ridge** (L2-penalized linear).
- It produces the headline equal-weight L-S portfolio ([[aggregated-portfolio]]).

## What is NOT disclosed (unverified)
- The ridge penalty λ.
- Which of the 25 single factors entered the regression (hold pool membership).
- The fitted β weights.
- Whether ridge was fit on train only (consistent with the gate) or on train+valid.

Without β weights the composite is **not reproducible** from the paper alone. This is
the single biggest reproducibility gap → see [[reproducibility-risk]] and log.md.

## My critical note
Ridge on a small set of *already gate-selected* factors inherits the selection bias of
the gate: the combiner sees only winners, so its in-sample fit overstates OOS skill.
The reported OOS numbers partially guard against this (factors were selected on train,
not OOS) — but the *choice of which factors to feed ridge* was informed by the whole
trace, which includes information correlated with OOS performance via the author's
stopping decision. Treat the composite Sharpe with the same caution as the headline.

## Local implementation note
`quant_system/protocol.py` now has a closed-form ridge combiner for the Binance port,
fit on the train slice only over locally passed candidate scores. This is useful for
protocol alignment, but it does **not** recover the paper's λ, β, or hold pool.
Those remain undisclosed and unverified. See [[binance-port-protocol]].

Related: [[ic-gating]] · [[capacity-constraint]] · [[aggregated-portfolio]] · [[binance-port-protocol]]
