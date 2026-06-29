---
title: Multiple Testing / Data Snooping
type: concept
source: "arXiv:2604.26747v1 + my analysis"
tags: [concept, bias, multiple-testing, snooping, overfit]
status: verified
last_reviewed: 2026-06-24
---

# Multiple Testing / Data Snooping

The bias the paper's protocol does **not** fully control.

## The exposure
- **5 search rounds**, each generating a *batch* of candidates → **25 single factors**
  survived to be reported (an unknown larger number were tried and rejected).
- Each candidate is gate-tested ([[ic-gating]]) on the same train window.
- Ranking the top 9 by **OOS** Sharpe ([[factors-index]]) is itself a selection on OOS —
  the reported "+2.412" top Sharpe is the **max of many draws**, upward-biased.

## Why "append-only trace" ≠ statistical control
The trace makes the search *auditable and reproducible* but applies **no
familywise / FDR correction**. With τ_IC, τ_t undisclosed I cannot compute the effective
number of independent tests or bound expected false survivors. The agent's stopping
decision (when to end round 5) is also informed by accumulated results → a soft form of
snooping.

## Practical reading
- Treat single-factor OOS Sharpes as **in-sample to the search process**.
- The ridge composite ([[ridge-combination]]) is the more trustworthy number because the
  *factors* were train-selected — but the *choice of which factors to combine* still saw
  the trace.
- For my own use: any port to Binance perps must be **re-validated on a fresh OOS window
  I hold out myself**, not on 2024–2026.

See [[contradictions]] §3.

Related: [[sequential-hypothesis-search]] · [[ic-gating]] · [[reproducibility-risk]]
