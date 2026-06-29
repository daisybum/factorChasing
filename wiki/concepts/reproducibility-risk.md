---
title: Reproducibility Risk (LLM backbone dependence)
type: concept
source: "arXiv:2604.26747v1 + my analysis"
tags: [concept, reproducibility, llm, gpt-5.4]
status: partial
last_reviewed: 2026-06-24
---

# Reproducibility Risk

## The good news
Once a factor is expressed as a [[constrained-factor-dsl]] recipe, the **deterministic
engine** reproduces its metrics exactly regardless of who/what proposed it. The recipe +
fixed splits + gate + cost model are model-agnostic. So *verification* is reproducible.

## The risk
**Discovery is not.** The agent backbone is **GPT-5.4** (the only model disclosed). The
*set of hypotheses generated* — and therefore which 25 factors exist and which ridge
composite results — depends on:
- the backbone version (GPT-5.4 specifically),
- sampling temperature / decoding (not disclosed),
- the exact trace prompt formatting (not disclosed).

Swap GPT-5.4 for another model and you likely get a **different factor set**. The
*framework* reproduces; the *specific factors* may not. The paper's own DSL recipes,
ridge λ, and β weights are **not disclosed** ([[ridge-combination]]), so even with
GPT-5.4 I cannot byte-reproduce the composite.

## Practical reading
- The portable artifact is the **method** (search loop + DSL + gate), not the factor list.
- For my book, treat the discovered factors as *hypotheses to re-test*, and rebuild the
  composite myself with disclosed-or-refit weights on my own OOS.

See [[contradictions]] §4.

Related: [[sequential-hypothesis-search]] · [[ridge-combination]] · [[multiple-testing-snooping]]
