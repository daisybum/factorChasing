# Repository Guidelines

## Project Structure & Module Organization

This repository has two coupled layers:

- `wiki/` is the epistemic layer for arXiv:2604.26747v1. Use `sources/` for
  primary-source notes, `concepts/` for method/risk pages, `factors/` for factor
  pages and Binance adaptation notes, and `entities/` for datasets/authors/benchmarks.
- `quant_system/` is the executable Binance USD-M port: `universe.py` builds the
  PIT universe, `collect.py` fetches klines/funding, `factors.py` builds causal
  signals, `protocol.py` owns IC gating/ridge combination, and `backtest.py`
  evaluates portfolios.
- `docs/plan_*.md` captures implementation plans; `data/` holds local parquet/cache
  artifacts and should be treated as generated research data.
- `tests/` contains non-destructive pytest coverage. Network or data-mutating checks
  must be opt-in, never the default test path.

Wikilinks use the basename only: `[[capacity-constraint]]`, not a relative path.
When a page becomes discoverable, add it to `wiki/index.md` and its Status board.

## Knowledge Architecture — Epistemic Layers

The folders are a topic split; the thing that actually governs every edit is a page's
**layer + status**, not its folder.

- **Layer 1 — `wiki/sources/`** = immutable, faithful pointers to the original paper.
  Do not paraphrase a number without its `(split, cost)` tag; keep verbatim quotes
  verbatim. Never "improve" the reported facts.
- **Derived layers — `wiki/concepts/ factors/ entities/`** = the user's compression and
  analysis built on Layer 1. Interpretation, reconstruction, and "my take" live here,
  always marked as such.
- **Audit layer — `wiki/contradictions.md`** = numbered flags (§1–§6) that *gate* the
  rest of the wiki. It is the source of truth for what may and may not be trusted.
  **§1 (the Table 2 vs Table 3 fee reconciliation) is why the headline is `suspect`.**

The headline result (EW ridge long-short → AnnRet 44.55% / Sharpe 1.55, pure OOS
2024–2026, 5 bp one-way) is **`suspect`, not verified** — gated by `contradictions` §1.
Do not present it as established.

## Status Taxonomy (front-matter `status:`)

Every page carries a status that means something specific; never silently upgrade it.

- `verified` / `partial` — method/concept claims supported by the paper text.
- `unverified` — **reconstructed**. All per-factor `dsl_recipe`, IC̄, t_IC, and gate
  pass/fail are *the user's hypotheses* about what the agent built, because the paper
  discloses only each factor's name + OOS Sharpe. Keep them flagged as hypotheses.
- `suspect` — contradicted or unreconcilable (the aggregated portfolio; the
  universe/survivorship question).
- `design` — forward-looking adaptation work (the Binance port), not a claim about the
  paper.

## The `(split, cost)` Tagging Rule

Backtest ≠ live. **Every numeric performance claim must carry its split (train / valid
2023 / pure OOS 2024–2026) and its cost (e.g. 5 bp one-way).** An untagged metric is a
defect — the post-ingest lint in `wiki/log.md` checks for exactly this. This is the
strictest standing rule.

## Page Schemas

- **Factor page** (`wiki/factors/h*-*.md`): `hypothesis`, `economic_rationale` (paper's
  + *my take:*), `candidate_type`, `dsl_recipe` *(reconstructed, unverified)*, `metrics`
  (Sharpe with split+cost; IC/t_IC = unverified), `gate_pass`, `net_of_cost`,
  `capacity_liquidity`, `binance_perp_fit`, `status`. See `wiki/factors/factors-index.md`
  for the catalogue and the shared DSL building blocks (scarcity / range / momentum /
  vol-management).
- **Concept / entity pages**: short, link-dense, every claim tied to a status word.

## Build, Test, and Development Commands

Use the checked-in virtualenv when available:

- `rg --files wiki` lists tracked content files by path.
- `rg "\\[\\[[^]]+\\]\\]" wiki` finds wikilinks for review.
- `.venv/bin/python -m quant_system.factors` runs the causal-factor self-test.
- `.venv/bin/python -m quant_system.backtest` runs the backtest self-test.
- `.venv/bin/python -m pytest` runs the non-destructive test suite.
- `.venv/bin/python -m quant_system.run` refreshes data and runs the pipeline; this
  may hit external APIs and mutate `data/`, so do not use it as a smoke test.

Run commands from the repository root (`/home/sanghyun/quant`).

## Coding Style & Naming Conventions

Use Markdown with YAML front matter matching existing pages:

```yaml
---
title: Example Title
type: concept
tags: [concept, risk]
status: living
last_reviewed: 2026-06-24
---
```

Name Markdown files in lowercase kebab case, for example `lookahead-bias.md`.
Python uses 4-space indentation, type hints where useful, and small pure functions
for bias-sensitive logic. Keep claims tied to source status such as `verified`,
`partial`, `suspect`, `unverified`, or `design`.

## Testing Guidelines

Before changing wiki pages, verify that `[[stem]]` links match real file basenames
and numerical claims carry split, cost, source, or uncertainty tags. Before changing
code, run pytest plus the affected module self-test. Tests must cover look-ahead
guards, PIT masking, split boundaries, delist exits, and cost sensitivity when the
change touches those areas.

## Commit & Pull Request Guidelines

This directory is not currently initialized as a Git repository, so no local commit convention is available. If Git is introduced, prefer concise imperative commits such as `Add factor risk notes` or `Update ingest log for arXiv source`. Pull requests should summarize changed pages, list source material used, call out uncertain or reconstructed claims, and mention any manual link checks performed.

## Source Handling & Agent-Specific Instructions

Preserve `wiki/log.md` as append-only. Do not silently upgrade `suspect` or `unverified` material to stronger statuses without evidence. Keep reconstructed factor recipes clearly marked as hypotheses unless the source discloses exact formulas or code.
Do not present Binance-port metrics as paper replication: the port changes venue,
frequency, universe, cost model, and funding treatment.
