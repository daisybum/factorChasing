---
title: IC Gating (selection gate)
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, selection, information-coefficient, gating]
status: verified
last_reviewed: 2026-06-29
---

# IC Gating — the selection gate

A factor candidate enters the hold pool **iff**:

> **IC̅ ≥ τ_IC  AND  t_IC ≥ τ_t**

Thresholds τ_IC, τ_t are *"fixed before the round and read from the experiment
configuration"* — **but the numeric values are not disclosed** in the paper (status:
unverified, see [[contradictions]] §3 and log.md follow-ups).

## How IC is computed
Daily cross-sectional Pearson information coefficient:

> IC_t = corr_{i∈I_t}( s_{i,t} , r_{i,t+1:t+2} )

where s is the factor score, r is the 1-day-lagged 1-day-hold forward return (see
[[lookahead-bias]]). Reported per factor: **mean IC, t_IC, long-short Sharpe, coverage**.

## Split discipline (the important part)
Verbatim: *"Selection uses the training window only. Validation statistics may be
recorded for diagnosis, but they do not determine whether a candidate enters the hold
pool."*
- **Train (2020–2022)** → gating decision.
- **Valid (2023)** → diagnostic only, no gating.
- **OOS (2024–2026)** → never seen during selection.

This is clean: it prevents validation leakage into selection. ✅

## My critical note
The gate controls *per-candidate* false positives but **not family-wide multiple
testing** across 5 rounds and ~25+ candidates ([[multiple-testing-snooping]]). With
τ_IC / τ_t unknown, I cannot reconstruct the effective per-test significance, so I
cannot bound the expected number of false-survivors. Flagged.

## Local implementation note
`quant_system/protocol.py` implements this gate mechanically for the Binance port:
forward target construction, train-only IC mean/t-stat diagnostics, and pass/fail
thresholds. The configured thresholds are local placeholders, not disclosed paper
parameters. See [[binance-port-protocol]].

Related: [[sequential-hypothesis-search]] · [[constrained-factor-dsl]] · [[multiple-testing-snooping]] · [[binance-port-protocol]]
