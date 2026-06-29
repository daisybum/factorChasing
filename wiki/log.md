---
title: Ingest Log
type: log
tags: [log, append-only]
status: living
last_reviewed: 2026-06-29
---

# Ingest Log (append-only)

## 2026-06-24 — Ingest arXiv:2604.26747v1
**Source:** *From Hypotheses to Factors: Constrained LLM Agents in Cryptocurrency Markets*
(Huang, Fan, Hu, Ye — HKUST/Rutgers/BNBU). Accessed via arXiv HTML, 2026-06-24. Backbone: GPT-5.4.

**Pages created (22):**
- sources: [[2604-26747]]
- concepts (9): [[sequential-hypothesis-search]], [[constrained-factor-dsl]], [[ic-gating]],
  [[ridge-combination]], [[capacity-constraint]], [[lookahead-bias]],
  [[survivorship-and-universe]], [[multiple-testing-snooping]], [[reproducibility-risk]]
- factors (12): [[factors-index]], [[aggregated-portfolio]], 9 individuals, [[_adaptation]]
- entities (3): [[huang-fan-hu-ye]], [[coinmarketcap-dataset]], [[benchmarks-ctrend-ff]]
- critical: [[contradictions]], [[index]]

**Headline (split, cost tagged):** EW ridge L-S → AnnRet 44.55% / Sharpe 1.55, pure OOS
2024–2026, 5 bp one-way. **Marked `suspect`** pending contradictions §1.

**Key findings filed:**
- Mechanism: small + illiquid + persistent intraday range + positive trend outperform;
  range *changes* and volume *recoveries* are noise; level scarcity + attention stable.
- Edge = illiquidity premium; cap-weight fails → capacity constrained.

### Lint (post-ingest auto-check)
- **(a) 5 verification points all present?** ✅
  - §1 fee 5 vs 10 bp reconciliation — [[contradictions]] §1 + [[aggregated-portfolio]]
  - §2 capacity / small-token vs Binance perp — [[contradictions]] §2 + [[capacity-constraint]]
  - §3 look-ahead / point-in-time / multiple testing — [[contradictions]] §3 + [[lookahead-bias]]/[[multiple-testing-snooping]]
  - §4 reproducibility / backbone — [[contradictions]] §4 + [[reproducibility-risk]]
  - §5 recompute under my Binance costs — [[contradictions]] §5 + [[_adaptation]]
- **(b) untagged numbers?** All metric figures carry (split, cost) tags; per-factor
  IC/t_IC/coverage marked `unverified` (not disclosed). ✅
- **(c) broken links / orphans / dup concepts?** See verification run below.

### Open follow-ups (unverified — do NOT estimate)
1. **[BLOCKER]** Resolve Table 2 cost label + Table 3 portfolio definition (contradictions §1).
   Without it the 5→10 bp decay is uninterpretable.
2. Obtain per-factor DSL recipes, train IC̄/t_IC, τ_IC/τ_t, ridge λ + β weights (email authors / check appendix/code release).
3. Confirm universe filter is point-in-time (survivorship).
4. Confirm turnover frequency (per-day vs per-rebalance) for cost recompute.
5. **User to supply** Binance cost inputs: maker/taker bp, BNB discount, VIP tier → then run §5 recompute for net Sharpe/MDD/Calmar.
6. Quantify Binance-perp ∩ alpha-universe overlap and slippage on the alpha leg.
7. Re-test portable momentum×range×low-vol factors on my own perp panel with fresh OOS.

## 2026-06-28 — Add verbatim full text of arXiv:2604.26747v1
Captured the original (arXiv LaTeXML HTML → Markdown) into [[2604-26747.fulltext]] so the
Layer-1 pointer's verbatim anchors have a local primary-source backing (link-rot insurance).
- **File:** `wiki/sources/2604-26747.fulltext.md` (`type: source-fulltext`, `status: verbatim`, 727 lines).
- **Conversion:** bs4 + markdownify; MathML replaced by source LaTeX (`alttext`), numbered-equation
  layout tables collapsed to `$$ … \tag{n} $$`. Data Table 2 (quintiles) + Table 3 (fee sensitivity)
  preserved as Markdown tables. No paraphrasing/editing — verbatim.
- **Wiring:** added `local_fulltext: 2604-26747.fulltext.md` to the [[2604-26747]] pointer frontmatter.
- **Lint note:** raw capture is intentionally not a curated page (no `[[wikilink]]` cross-refs beyond
  the back-pointer); excluded from orphan/dup checks by `type: source-fulltext`.

## 2026-06-29 — Refactor protocol/code alignment after audit
Added a deterministic `quant_system/protocol.py` layer for train-only IC diagnostics,
explicit gate thresholds, and ridge combination over passed factors. The Binance port still
does **not** implement LLM hypothesis generation; this is a protocol-alignment refactor, not
a paper reproduction.
- **Code:** `run.py` now reports train-only IC diagnostics and uses ridge over passed
  candidate factors, falling back to equal-weight composite if none pass.
- **Tests:** added non-destructive pytest coverage for wikilinks/front matter, causal factor
  truncation, delist exits, cost sweep monotonicity, future-return lagging, IC gate, and ridge.
- **Wiki hygiene:** fixed path-style wikilinks to obey the `[[stem]]` convention. No `suspect`
  or `unverified` claims were upgraded.

## 2026-06-29 — Add wiki implementation-status page
Added [[binance-port-protocol]] to separate the executable Binance port's current state
from the paper claims.
- **Implemented status documented:** PIT universe, causal factors, train-only IC diagnostics,
  ridge combiner, backtest cost/funding/delist handling, and non-destructive tests.
- **Non-implemented status documented:** no LLM 5-round generator, no paper-factor
  reproduction, placeholder IC/ridge settings, and different venue/frequency.
- **Index wiring:** added the page under Concepts and the Status board. No performance
  metric was added or upgraded.
