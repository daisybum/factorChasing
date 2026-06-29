---
title: Look-ahead Bias / Point-in-Time Discipline
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, lookahead, point-in-time, bias]
status: verified
last_reviewed: 2026-06-24
---

# Look-ahead Bias & Point-in-Time Discipline

How the paper claims to avoid trading on information not yet available.

## The three guards
1. **1-day execution lag.** Signal computed at close of day t; position entered at t+1.
2. **Forward, shifted label.** r_{i,t+1:t+2} = P_{i,t+2}/P_{i,t+1} − 1 — entry t+1, exit t+2.
   The day-t signal never touches the day-t+1→t+2 return except as predictor→target.
3. **Causal DSL.** [[constrained-factor-dsl]] time-series operators are backward-only;
   no operator can reference future bars.

## Status check (my verification)
- Lag + shifted label: **internally consistent** as written. ✅
- DSL causality: **asserted, not independently provable** from the text — I can't see the
  operator implementations, only their names. Marked partial. ⚠
- Universe filter applied with hindsight? The "<180 days history / below-threshold
  volume" filter — if applied using *full-sample* volume/history it is a mild
  **survivorship / look-ahead** leak ([[survivorship-and-universe]]). Paper does not say
  whether the filter is point-in-time. Flagged → [[contradictions]] §3.

## My critical note
The headline frictions look honest on the *time* axis (no future leakage). The bigger
unmodelled bias is on the *cross-section* axis: which tokens existed and were liquid at
each date. See [[survivorship-and-universe]].

Related: [[constrained-factor-dsl]] · [[ic-gating]] · [[survivorship-and-universe]] · [[multiple-testing-snooping]]
