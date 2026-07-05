---
title: Binance Port Protocol Status
type: implementation
source: "repo implementation + arXiv:2604.26747v1 adaptation"
tags: [implementation, binance, protocol, audit]
status: partial
last_reviewed: 2026-06-29
---

# Binance Port Protocol Status

This page tracks what the executable Binance USD-M port implements relative to the
paper protocol. It is an implementation audit page, not a performance claim.

## Implemented
- **Point-in-time universe path:** `quant_system/universe.py` builds daily membership from
  Binance contract dates plus CoinGecko market-cap history; delisted names are retained
  before their stop date.
- **Causal factor path:** `quant_system/factors.py` computes backward-only momentum,
  low-vol, range, reversal, and a normalized signed realized-semivariance imbalance
  ([[signed-semivariance-imbalance]], a repo-original candidate, `unverified`), then masks
  scores to the PIT universe.
- **Deterministic protocol layer:** `quant_system/protocol.py` computes forward targets,
  train-only IC diagnostics, explicit IC/t-stat gates, and a train-only ridge combiner.
- **Evaluation path:** `quant_system/backtest.py` applies a 1-bar execution lag, transaction
  costs, funding as a separate P&L line, delist exits, and `(split, cost)` metric tags.
- **Verification:** non-destructive pytest coverage checks wikilinks/front matter,
  causality, delist exits, cost sweep monotonicity, future-return lagging, IC gate, and ridge.

## Not Implemented
- **No LLM hypothesis generator.** The code does not run the paper's 5-round agent loop or
  append candidate traces from an LLM.
- **No paper-factor reproduction.** Per-factor DSL recipes, train IC, gate thresholds,
  ridge λ, and β weights are undisclosed in the paper, so the local ridge output cannot be
  the paper headline portfolio.
- **Placeholder gates.** `IC_MIN_MEAN`, `IC_MIN_T`, and `RIDGE_ALPHA` are repo settings,
  not paper parameters. Any pass/fail result is a software-path result until thresholds
  are explicitly chosen and logged.
- **Different venue/frequency.** The code uses Binance 1m spot/perp data, not the paper's
  CoinMarketCap daily spot panel.

## Reading Rule
Treat `quant_system/` as a Binance research seed that borrows the paper's deterministic
evaluation discipline. Do not cite its outputs as replication of [[aggregated-portfolio]].

Related: [[_adaptation]] · [[ic-gating]] · [[ridge-combination]] · [[contradictions]]
