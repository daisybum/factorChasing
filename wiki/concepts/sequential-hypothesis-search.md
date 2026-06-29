---
title: Sequential Hypothesis Search
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, llm-agent, methodology, factor-discovery]
status: verified
last_reviewed: 2026-06-24
---

# Sequential Hypothesis Search

The paper's framing of factor discovery: an iterative loop in which an LLM agent
(GPT-5.4) **reads an append-only trace** of all prior experiments, proposes the next
batch of *falsifiable* hypotheses, and the deterministic engine scores them. The agent
steers *direction*; it cannot touch the *rules*.

## The loop (5 rounds total)
1. Read current append-only trace.
2. Generate a mixed candidate batch (hypotheses).
3. Translate each to a [[constrained-factor-dsl]] recipe.
4. Evaluate on the **train** window only.
5. Append {hypothesis, rationale, recipe, metrics, interpretation, next-round decision} to the log.
6. Interpret results, update the hold/reject pools.
7. After the final round: fit [[ridge-combination]], evaluate on train / valid / **OOS**.

## Why "constrained" matters
Verbatim: *"if an agent can freely change features, code, data splits, or evaluation
rules, strong results may reflect uncontrolled search rather than valid discovery."*
The engine freezes splits, the gate ([[ic-gating]]), costs, and the portfolio test for
the whole session. This is the paper's defence against agent-driven overfitting.

## My critical note
The append-only trace makes a *single run* auditable, but **5 rounds × multiple
candidates × 25 surviving factors = a real multiple-testing surface** ([[multiple-testing-snooping]]).
Auditability ≠ statistical control: nothing in the protocol corrects p-values for the
number of hypotheses tried. Treat the OOS Sharpe ranking as *in-sample to the search
process* even though it is out-of-sample to the price data. See [[contradictions]] §3.

Related: [[constrained-factor-dsl]] · [[ic-gating]] · [[lookahead-bias]] · [[reproducibility-risk]]
