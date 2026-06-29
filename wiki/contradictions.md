---
title: Contradictions & Critical Flags
type: contradictions
source: "arXiv:2604.26747v1 + my analysis"
tags: [contradictions, critical, audit]
status: open
last_reviewed: 2026-06-29
---

# Contradictions & Critical Flags

Backtest ≠ live. Every number carries a (split, cost) tag. Open items below gate the
headline result to `suspect`.

---

## §1 — Fee-sensitivity tables do not reconcile  🚨 (HEADLINE → suspect)
- **Table 2** (EW L-S, cost label *not printed*, presumed 5 bp): AnnRet **0.445**, AnnVol
  **0.287**, Sharpe **1.551**, MaxDD −0.236, Calmar 1.886, Turnover 0.368.
- **Table 3** "fee sensitivity" (EW) at 0.1%: AnnRet **0.016**, AnnVol **0.028**, Sharpe
  **0.57**; at 0.2%: 0.52; at 0.3%: 0.46.
- **The discrepancy:** AnnVol ~**10×** apart, AnnRet ~**28×** apart. A 5→10 bp one-way fee
  change *cannot* produce this. **The two tables are not the same portfolio.**
- **Likely cause:** Table 3 is a *different* construction — vol-scaled / dollar-neutral /
  cap-weighted residual (the "Alpha" column suggests a regression residual, not raw
  return). The paper **never re-costs the headline EW L-S at 10/20/30 bp.**
- **Decay I can defend:** *per-unit-risk*, Sharpe falls 1.55 → 0.57 (≈ −63%) going 5→10 bp
  *if* Table 3 is the same strategy down-scaled — direction robust, levels not.
- **Resolution needed:** (a) confirm Table 2's cost label; (b) get Table 3's exact
  portfolio definition. Until then: [[aggregated-portfolio]] = **suspect**.

## §2 — Capacity / small-token concentration vs Binance perp universe
- Paper: cap-weight **poor**, EW **good** → *"alpha is concentrated in smaller tokens and
  is capacity constrained."* The edge **is** an illiquidity premium ([[capacity-constraint]]).
- **Overlap with my venue:** the names carrying alpha (low mcap, low dollar volume) have
  **little/no overlap** with the ~20–40 liquid Binance USDⓈ-M perps. My universe is the
  high-liquidity slice where the paper says alpha is weakest.
- **Quantified risk (estimate path):** real round-trip friction on the alpha-bearing leg
  ≈ 30–80 bp (slippage on thin tokens) vs the assumed 10 bp round-trip → net edge
  compresses toward/through zero. Exact number **unverified** (needs per-name turnover +
  universe liquidity dist, undisclosed) → logged.
- **Verdict:** porting strands most of the edge. Keep only price/vol/range signals
  ([[_adaptation]]).

## §3 — Look-ahead / point-in-time / multiple testing
- **Time axis (good):** 1-day execution lag + forward-shifted label r=P_{t+2}/P_{t+1}−1 +
  backward-only DSL → internally consistent, no temporal leakage ([[lookahead-bias]]).
- **DSL causality:** asserted, operator *implementations* not shown → cannot independently
  verify. Partial.
- **Universe filter:** paper does **not** state the <180-day / volume filter is
  point-in-time. If full-sample → **survivorship bias** that specifically inflates the
  small-cap long leg ([[survivorship-and-universe]]). Suspect.
- **Multiple testing:** 5 rounds × candidate batches → 25 reported factors; **no
  familywise/FDR correction**; τ_IC, τ_t **undisclosed** so the per-test α can't be
  recovered. Top-9 ranked *on OOS* → max-of-many upward bias
  ([[multiple-testing-snooping]]). The OOS Sharpes are in-sample to the *search*.

## §4 — Reproducibility / LLM-backbone dependence
- Backbone = **GPT-5.4** (only spec disclosed). Discovery (which factors exist) is
  backbone- and decoding-dependent → swapping models likely changes the factor set.
- **Verification** *is* reproducible (deterministic engine), but per-factor **DSL recipes,
  ridge λ, β weights** are **not disclosed** → the headline composite is **not
  byte-reproducible** from the paper ([[ridge-combination]], [[reproducibility-risk]]).

## §5 — Recompute under MY Binance costs (assumptions + path)
**User-supplied inputs are blank → values below are placeholders / reference, NOT verified.**
Required from user (fill before any live read):
- maker = `{___}` bp · taker = `{___}` bp · BNB fee discount = `{Y/N}` · VIP tier = `{___}`
- perp → include **funding carry** (8h stamps) as a separate P&L line.

**Reference (Binance USDⓈ-M VIP0, *unverified for this account*):** maker ≈ 2.0 bp,
taker ≈ 5.0 bp; ~10% discount if fees paid in BNB → maker ≈ 1.8 / taker ≈ 4.5 bp.

**Recompute path (deterministic once inputs known):**
1. Per-rebalance one-way cost `c` = (fill-weighted blend of maker/taker, post-BNB).
2. Daily cost drag = `turnover_daily × 2 × c` (round-trip). Paper turnover 0.368 (per
   rebalance, frequency *unverified* — assume daily for daily signal).
3. Funding drag = Σ(funding_rate × signed_notional) over hold; net = price r − fee drag − funding.
4. Net Sharpe = (annualized net mean) / (annualized vol); MDD/Calmar from net equity curve.
5. **Sensitivity:** because cost drag is **linear in `c`**, going from 5 bp to my taker
   ~4.5–5 bp leaves liquid-name results ~unchanged — *but* on the illiquid alpha leg, true
   `c` (slippage-inclusive) ≫ 5 bp, which is where the headline dies (see §2).
- **Numeric net Sharpe/MDD/Calmar = unverified** until (a) cost inputs filled, (b) the
  Table 2/Table 3 portfolio definition (§1) is resolved, (c) turnover frequency confirmed.
  Logged as the top follow-up.
- Current code path for the Binance port is documented in [[binance-port-protocol]]; it is
  a local protocol implementation, not a recomputation of the paper headline.

## §6 — Minor: OOS label "2024–2026" vs data ending Dec 2025
Data span is Jan 2020–Dec 2025, yet OOS is labelled "2024–2026". At most ~half of 2026 (to
the 2026-04-29 submission) could be live-ish; likely loose labelling. Low severity, noted.

---
**Gating summary:** headline [[aggregated-portfolio]] = **suspect** (blocked by §1).
Method/concepts = verified. Individual factors = unverified (recipes reconstructed).
