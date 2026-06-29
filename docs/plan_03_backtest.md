# Plan 03 — Backtest (bias-aware long-short engine)

**Module:** `quant_system/backtest.py`
**Goal:** a vectorized cross-sectional long-short backtest whose design centers on quant
fundamentals **and** the bias controls the wiki repeatedly flags. Output: `(split, cost)`-
tagged metrics + a fee-sensitivity sweep.

## Quant fundamentals
PIT panel join → signal → **1-bar execution lag** → forward return; long top
`LONG_SHORT_QUANTILE` / short bottom, equal-weight within legs; per-name weight cap +
gross-leverage cap (liquidation guard, `_adaptation.md §5`); rebalance every
`REBALANCE_EVERY` bars; transaction cost = `(taker_bp + slippage_bp) × turnover`; **funding
as a separate P&L line** (`net = price_pnl − fees − funding`, never folded into returns,
`_adaptation.md §3`); equity curve; metrics AnnRet/AnnVol/Sharpe/MaxDD/Calmar/Turnover.

## Functions (per `INTERFACES.md`)
- `protocol.evaluate_candidates(...)` → train-only IC gate diagnostics for candidate factors.
- `protocol.fit_ridge(...)` / `ridge_score(...)` → train-only ridge combiner over passed
  factors; equal-weight composite remains the fallback if no factor passes configured gates.
- `run_backtest(score, panel, universe, cost)` → `BacktestResult` (net/price/fees/funding/
  equity/turnover/held-weights).
- `metrics(result, split, cost)` → dict, **tagged with `split` and `cost`**.
- `cost_sweep(score, panel, universe)` → metrics across `COST_SWEEP_BP=[5,10,20]`
  (bp-as-total-one-way), filling the "re-cost the headline" gap.
- `chronological_split(...)` → train/valid/oos by `config.SPLITS`, no shuffle; selection on
  train only.

## Bias-control matrix
| Bias | Mechanism in engine | Wiki ref |
|---|---|---|
| **Survivorship** | PIT universe + delisted names force-closed at last tradeable bar (`weights=0` from `delist_day` onward so the *held*, lag-shifted position is flat past the last valid price); never silently dropped | `survivorship-and-universe.md` |
| **Look-ahead** | strict 1-bar lag: `held = weights.shift(1)`, `pnl@t = held@t · ret@t`, so `score@t` can only touch `pnl@t+1`; backward-only factor windows; per-row z-score (no full-sample normalization) | `lookahead-bias.md` |
| **Train/valid/OOS** | fixed chronological split; any threshold/weight choice on **train only**; OOS untouched | `ic-gating.md` |
| **Multiple testing / overfit** | report on held-out OOS; only 4 fixed factors (low multiplicity); note to require survival on a 2nd time-disjoint slice before trusting | `multiple-testing-snooping.md` |
| **Cost realism** | taker + slippage + funding; **sweep at 5/10/20 bp** (Sharpe must fall as cost rises) | `contradictions.md §1, §5` |
| **Reporting discipline** | **every metric dict tagged `(split, cost)`** | wiki strict rule |

## Cost model — UNVERIFIED
`taker_bp=5`, `slippage_bp=2` are placeholders (`config.CostModel.verified=False`). Real
Binance maker/taker + BNB discount + VIP tier must be supplied before net metrics are
trusted (`_adaptation.md §4`). The headline run uses `taker+slippage`; the sweep isolates
`bp` as total one-way.

## Protocol thresholds — UNVERIFIED
`IC_MIN_MEAN=0`, `IC_MIN_T=0`, and `RIDGE_ALPHA=1` are implementation placeholders because
the paper does not disclose τ_IC, τ_t, λ, or β. Treat a pass as a software-path result, not
statistical evidence, until these thresholds are explicitly chosen and logged.

## Config knobs
`LONG_SHORT_QUANTILE=0.2`, `MAX_NAME_WEIGHT=0.10`, `MAX_GROSS_LEVERAGE=1.0`,
`REBALANCE_EVERY=5`, `SPLITS={train .5, valid .2, oos .3}`, `BARS_PER_YEAR=525600`,
`COST_SWEEP_BP=[5,10,20]`.

## Verification checklist
- [x] Clean import without `collect.py`.
- [x] **Look-ahead:** shifting the score forward by one bar changes results; `held ==
      target.shift(1)` holds by construction.
- [x] Finite equity curve; `metrics()` dict carries `(split, cost)` tags.
- [x] `cost_sweep` Sharpe strictly decreasing across 5/10/20 bp.
- [x] Delisted name weight `== 0` for every bar after its last tradeable bar.

> Note: on synthetic random-walk data with per-bar-ish rebalance the Sharpe/Turnover values
> are meaningless artifacts; the self-test asserts **structure and monotonicity**, not realism.
> Real metrics come from `run.py` on collected data.
