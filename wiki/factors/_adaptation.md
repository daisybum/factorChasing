---
title: Adaptation — porting to Binance USDⓈ-M perps
type: adaptation
source: "arXiv:2604.26747v1 + my analysis"
tags: [adaptation, binance, perp, funding, design]
status: design
last_reviewed: 2026-06-29
---

# Adaptation — (DSL + agent loop + gate) → Binance USDⓈ-M perp

Goal: port the *method* (not the disclosed factors, which aren't fully disclosed —
[[reproducibility-risk]]) to my venue. Below: deltas, risks, and a concrete design.

## 1. Universe delta (the killer)
- Paper: thousands of CMC spot tokens, alpha in the **small/illiquid tail**
  ([[capacity-constraint]]).
- Me: **~20–40 liquid USDⓈ-M perp contracts**. This is the *opposite* end of the liquidity
  distribution → **most of the paper's alpha is structurally unavailable.**
- Implication: drop scarcity/dollar-volume legs (un-portable); keep **momentum × range ×
  low-vol** signals that don't need `mcap`. Portable factors:
  [[h1-highrange-lowvol-short-window]], [[h3-lag-momentum-highrange]],
  [[h4-lag-mom-highrange-20d-range]], [[h2-momentum-lowvol-short-window]].
- `market_cap` has no perp native → either source off-exchange (circulating supply × mark)
  or **drop the input entirely** and let the DSL work on price/vol/OI only.

## 2. Spot daily → perp differences
| Axis | Paper (spot daily) | Binance USDⓈ-M perp |
|---|---|---|
| Instrument | spot | perpetual future (no expiry) |
| Carry | none | **funding rate** every 8h — must be modelled |
| Leverage | 1× implicit | up to N×, margin & **liquidation** risk |
| Session | daily close | 24/7, funding stamps at 00/08/16 UTC |
| Short leg | borrow-constrained | native short, but pays/earns funding |
| Data | close, volume, mcap | mark/index/last, contract volume, **open interest**, funding |

## 3. Funding carry as a separate state channel
Add **funding** as its own input column *and* its own P&L line — do NOT fold it into price
returns. Two uses:
- **As a cost:** holding a long that pays positive funding bleeds carry daily; the 1-day
  hold means ~1–3 funding stamps per position. Net return = price return − fees − funding.
- **As a signal:** extreme funding = crowded positioning → a candidate factor input
  (`-rank(funding)` as a contrarian carry/attention proxy). This is the perp-native
  replacement for the "attention/scarcity" channel the paper found stable.
- Recommend a **separate `funding_state` channel** in the trace so the agent can propose
  funding-based hypotheses without contaminating the price-DSL.

## 4. Cost model swap
Replace the paper's flat 5 bp with my real schedule (values **unverified — user to fill**):
maker {___} bp / taker {___} bp, BNB discount {Y/N}, VIP {___}, + funding. See
[[contradictions]] §5 for the recompute path. Crucially: with only ~30 names, the L-S
spread is far less diversified → higher vol, more sensitive to single-name funding spikes
and liquidation cascades.

## 5. Engine / gate port
- Keep the deterministic engine, fixed splits, [[ic-gating]] gate, append-only trace —
  these are the reproducible core.
- Current repo status: deterministic scoring, train-only IC diagnostics, explicit gate
  thresholds, and ridge combination now live in `quant_system/protocol.py`; see
  [[binance-port-protocol]]. This is still **not** the paper's LLM search loop.
- **Re-fit, don't reuse:** discover factors *on my own perp panel* with my own
  train/valid/OOS, because (a) factors are backbone-dependent, (b) I need a fresh holdout
  not contaminated by the paper's 2024–2026 OOS ([[multiple-testing-snooping]]).
- Set τ_IC, τ_t myself (paper's are undisclosed) and **correct for multiple testing** —
  e.g. require survival on a second, time-disjoint OOS slice.
- Liquidation guard: cap per-name weight and gross leverage so a small-name gap can't
  trigger forced exit — the perp analogue of capacity control.

## 6. Honest expectation
Stripped of the small-cap illiquidity premium, the portable momentum×range×low-vol core
will likely deliver a **much lower Sharpe than 1.55** even before my real costs — but it
will be *tradeable*, which the paper's headline book is not. Treat as a research seed, not
a strategy to lift.

Related: [[aggregated-portfolio]] · [[capacity-constraint]] · [[contradictions]] · [[binance-port-protocol]]
