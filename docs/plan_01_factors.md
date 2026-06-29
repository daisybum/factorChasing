# Plan 01 — Four Factors (point-in-time, causal)

**Module:** `quant_system/factors.py`
**Goal:** four basic cross-sectional factors on the 1m perp panel + an equal-weight
z-scored composite scored within each timestamp's point-in-time universe. The portable
core from `wiki/factors/_adaptation.md` (momentum × range × low-vol) plus short-term
reversal — none require market cap, so all survive the spot→perp port.

## The four factors (windows in 1m bars, from `config.py`)
Per-symbol log returns `r_t = log(close_t) − log(close_{t−1})`.

| # | Factor | Formula | Window | Rationale (wiki) |
|---|---|---|---|---|
| 1 | **Momentum** | `MA(r).shift(REVERSAL_WINDOW)` | 240, skip 5 | long winners; lagged so it's disjoint from reversal (`h3-lag-momentum-highrange`) |
| 2 | **Low-Volatility** | `−rolling_std(r)` | 120 | long low realized vol (vol-management tilt) |
| 3 | **High-Low Range** | `MA((high−low)/close)` | 60 | persistent intraday range **level** (range *changes* are noise, levels stable) |
| 4 | **Short-term Reversal** | `−sum(r)` | 5 | long recent losers; disjoint window from momentum |

**Disjointness:** lagged momentum sees bars `[t−244 … t−5]`, reversal sees `[t−4 … t]` — no
overlap, so #1 and #4 cannot cancel. Verified: `momentum bars 1756..1995 vs reversal 1996..2000`.

## Functions (per `INTERFACES.md`)
- `build_panel(symbols)` → wide `(field, symbol)` MultiIndex panel from `collect.load_klines`
  (lazy import; no forward-fill across listing gaps).
- `compute_factors(panel)` → `{momentum, lowvol, range, reversal}`, each `index=open_time,
  columns=symbol`, NaN only in the warmup region.
- `composite_score(factors, universe)` → mask to each timestamp's PIT universe → cross-sectional
  z-score per factor per row → equal-weight mean → one score df, NaN outside the PIT universe.
- `pit_membership(universe, index)` → public PIT mask reused by the protocol layer so IC
  gating and ridge do not score out-of-universe names.

## Causality guarantee
Only trailing `.rolling()` + backward `.shift()`; row-wise cross-sectional z-score uses only
that row's values, so nothing leaks across time. The value at `t` uses only data `≤ t`; the
backtest adds the 1-bar execution lag on top (`wiki/concepts/lookahead-bias.md`,
`constrained-factor-dsl.md`).

## Config knobs
`MOMENTUM_WINDOW=240`, `LOWVOL_WINDOW=120`, `RANGE_WINDOW=60`, `REVERSAL_WINDOW=5`.

## Verification checklist
- [x] Clean import without `collect.py` present (lazy import).
- [x] **Causality:** delete all bars after `t`, recompute → factor value at `t` byte-identical
      (`np.array_equal`, max abs diff `0.0e+00`).
- [x] Warmup-only NaN per factor; shapes match the panel.
- [x] Composite: out-of-PIT-universe names are NaN; in-universe rows z-center to ~0 mean
      (1560 fully-populated rows on the synthetic panel).
- [x] Momentum and reversal windows strictly disjoint.
