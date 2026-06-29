---
title: Capacity Constraint / Small-Token Concentration
type: concept
source: "arXiv:2604.26747v1"
tags: [concept, capacity, liquidity, small-cap, slippage]
status: verified
last_reviewed: 2026-06-24
---

# Capacity Constraint — where the alpha actually lives

The paper's most operationally important admission:

> *"The market-cap-weighted version performs poorly, indicating that the alpha is
> concentrated in smaller tokens and is capacity constrained."*

Equal-weight L-S works (Sharpe 1.551, train-selected, 5bp, OOS); **cap-weight does not**.
Mechanically the surviving factors all tilt toward `−log(mcap)` and `−volume`
(scarcity), so equal-weighting *over-samples exactly the illiquid names* that cap-weight
down-weights. The alpha **is** the small-cap tilt.

## Why this kills live deployment risk
1. **Slippage scales inversely with liquidity.** A 5bp one-way assumption is plausible
   for liquid majors and *implausible* for the micro-cap longs/shorts carrying the alpha.
2. **Equal weight = max exposure to the least tradeable names** — the opposite of what
   capacity wants.
3. The cap-weight failure is a direct signal that **as you scale AUM toward where
   liquidity is, the alpha disappears.** This is not a tuning issue; it is the location
   of the edge.

## Quantified concern (estimate path, not a verified number)
- Effective edge per trade ≈ gross spread − (2 × one-way cost) − slippage − funding.
- If true round-trip frictions on the micro-cap leg are 30–80 bp (realistic for tokens
  the paper's universe filter still admits) vs the assumed 10 bp round-trip, the L-S
  net return compresses sharply (see [[contradictions]] §2 and §5 for the recompute path).
- **Numeric estimate withheld** — requires the per-name turnover and the actual universe
  liquidity distribution, neither disclosed. Logged as follow-up.

## Binance USDⓈ-M perp overlap
The Binance perp universe (~20–40 liquid USDⓈ-M contracts I'd actually trade) is the
*high-cap, high-liquidity* slice — i.e. the part where the paper says alpha is weakest.
Porting the strategy to perps likely strands most of the edge. See
[[_adaptation]] and [[contradictions]] §2.

Related: [[ridge-combination]] · [[benchmarks-ctrend-ff]] · [[aggregated-portfolio]]
