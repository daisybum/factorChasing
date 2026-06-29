---
title: Constrained Factor DSL (point-in-time)
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, dsl, point-in-time, factor-discovery]
status: verified
last_reviewed: 2026-06-24
---

# Constrained Factor DSL

The action space the agent is restricted to. **No arbitrary code, no look-ahead.**
Every recipe must use only approved point-in-time columns and **must include at least
one time-series or nonlinear transform** (pure cross-sectional rank of a raw column is
disallowed).

## Operator families (verbatim)
| Family | Operators |
|---|---|
| Cross-sectional (within each date) | percentile **rank**, **z-score** |
| Time-series (within each asset) | **lag**, rolling **mean** (MA), rolling **std**, **difference**, **pct change** (Δ) |
| Nonlinear | **log**, **abs**, **clip** |
| Combination | **linear combination** of transformed variables |

## Input columns (the `derived` panel)
open, high, low, close, **volume**, **market cap**, close-to-close returns, **log returns**,
**relative volume**, **realized volatility**, **price-to-moving-average**, **high-low range**,
**volume % change**.

## Canonical example (verbatim from paper)
```
rank_t( -0.6*log(1+mcap) + 0.5*MA_10(range) - 0.2*MA_3(Δvolume) )
```
Reads as: long small-cap (−log mcap), high persistent intraday range (+MA range),
fading recent volume spikes (−Δvolume). This single line encodes the paper's whole
thesis: **scarcity + range + (de-noised) flow**.

## Point-in-time guarantee
All time-series operators look *backward only*; the label is shifted forward by the
1-day execution lag (see [[lookahead-bias]]). The DSL is the structural enforcement of
no-look-ahead — provided the operator implementations are themselves causal (paper
asserts this; not independently re-derivable from the text → see [[contradictions]] §3).

## Portability note (Binance perp)
All operators are computable on a Binance USDⓈ-M daily perp panel **except `market cap`**,
which has no clean perp analogue → must be sourced off-exchange or proxied by
circulating-supply × mark price. See [[capacity-constraint]] and [[_adaptation]].

Related: [[sequential-hypothesis-search]] · [[ic-gating]] · [[lookahead-bias]]
