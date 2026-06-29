---
title: Survivorship & Universe Construction
type: concept
source: "arXiv:2604.26747v1 + my analysis"
tags: [concept, bias, survivorship, universe, liquidity-filter]
status: suspect
last_reviewed: 2026-06-24
---

# Survivorship & Universe Construction

## What the paper says
- Source: CoinMarketCap daily, Jan 2020 – Dec 2025.
- Filter: exclude assets with **< 180 days** history or **below-threshold average daily
  volume**.

## The unresolved bias
The paper does **not state whether the filter is point-in-time**. Two regimes:
- **Point-in-time (good):** at each date, include only tokens that had ≥180 days *up to
  that date* and met the volume bar *as of then*. No leakage.
- **Full-sample (biased):** select tokens that *ended up* having ≥180 days / enough
  volume over 2020–2025. This bakes in **survivorship bias** — dead/delisted micro-caps
  (the natural shorts) are silently dropped, and the surviving small-caps are exactly the
  ones that didn't blow up. Given the alpha **is** the small-cap tilt
  ([[capacity-constraint]]), this bias would inflate the long leg specifically.

CoinMarketCap-sourced crypto panels are notoriously prone to this; absent an explicit
point-in-time statement, I mark **suspect**.

## Why it matters for me
Binance USDⓈ-M perps have *listing and delisting* events too (contracts get added/pulled).
Any port must use a **point-in-time tradeable-contract calendar**, or it inherits the
same bias in a more dangerous form (delisted perps = forced liquidation, not a clean exit).

See [[contradictions]] §3 and [[lookahead-bias]].

Related: [[capacity-constraint]] · [[multiple-testing-snooping]] · [[_adaptation]]
