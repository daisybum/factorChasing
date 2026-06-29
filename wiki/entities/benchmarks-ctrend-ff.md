---
title: Benchmarks — CTREND & Fama-French
type: entity
source: "arXiv:2604.26747v1"
tags: [entity, benchmark, ctrend, fama-french]
status: partial
last_reviewed: 2026-06-24
---

# Benchmarks referenced

| Benchmark | What it is | Head-to-head in paper? |
|---|---|---|
| **CTREND** | aggregated crypto **trend** factor (cited as related work) | ❌ no numbers reported |
| **Fama-French style** | market / size / momentum cross-sectional model | ❌ context only |

## Critical note
The paper **does not report a benchmark-relative comparison** — no CTREND Sharpe, no
market-index Sharpe, no FF alpha decomposition in the results tables (the "Alpha" column
in the fee table is *not* labelled against a disclosed benchmark; see [[contradictions]] §1).
So the 44.55% / Sharpe 1.55 headline is **absolute, not excess-of-benchmark**. Given the
size + momentum tilt, a non-trivial fraction could be a crypto size/trend premium already
captured by CTREND/FF — **unverified**, flagged as a follow-up in log.md.

Related: [[2604-26747]] · [[aggregated-portfolio]] · [[capacity-constraint]]
