"""Vectorized long-short backtest engine (the evaluation stream).

Implements the INTERFACES.md backtest contract for the 4-factor Binance USDⓈ-M perp
seed. Design centers on quant fundamentals AND explicit bias controls — see the
BIAS-CONTROL MATRIX in docs/plan_03_backtest.md and:
  - wiki/concepts/lookahead-bias.md     (1-bar execution lag; score@t -> ret@t+1)
  - wiki/concepts/ic-gating.md          (selection on train only; OOS untouched)
  - wiki/concepts/multiple-testing-snooping.md
  - wiki/factors/_adaptation.md  §3 (funding = SEPARATE P&L line), §4 (cost UNVERIFIED),
                                 §5 (liquidation guard = per-name + gross caps)
  - wiki/contradictions.md  §1 (re-cost the headline -> cost_sweep), (split,cost) rule.

Cost numbers are UNVERIFIED placeholders (config.CostModel.verified is False) until the
user supplies the real Binance fee schedule. Vectorized pandas/numpy, no event loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config


# --- result container --------------------------------------------------------
@dataclass
class BacktestResult:
    """Per-bar series from one run. Funding is held as its OWN line (not folded
    into price returns) so the (price / fee / funding) decomposition stays auditable."""

    net_returns: pd.Series          # net = price_pnl - fees - funding_paid (per bar)
    price_pnl: pd.Series            # gross price P&L from lagged weights * fwd return
    fees: pd.Series                 # transaction cost line ((taker+slip) bp * turnover)
    funding_paid: pd.Series         # SEPARATE funding P&L line (signed_w * funding_rate)
    equity_curve: pd.Series         # cumulative (1 + net_returns).cumprod()
    turnover: pd.Series             # per-bar sum |w_t - w_{t-1}|
    weights: pd.DataFrame = field(repr=False, default=None)  # lagged weights actually held


# --- timeline split (chronological, no shuffle) ------------------------------
def chronological_split(index: pd.DatetimeIndex) -> dict[str, pd.DatetimeIndex]:
    """Split a sorted time index into train/valid/oos by config.SPLITS fractions,
    in time order with NO shuffle.

    Discipline note (wiki/concepts/ic-gating.md): any threshold / factor SELECTION
    must happen on the TRAIN slice only. valid is diagnostic; oos is never seen during
    selection. This engine performs no tuning itself — it only exposes the slices so a
    caller can honor that rule.
    """
    idx = pd.DatetimeIndex(index).sort_values()
    n = len(idx)
    n_train = int(n * config.SPLITS["train"])
    n_valid = int(n * config.SPLITS["valid"])
    return {
        "train": idx[:n_train],
        "valid": idx[n_train:n_train + n_valid],
        "oos": idx[n_train + n_valid:],
    }


# --- universe -> per-name last tradeable bar (delisting / survivorship guard) -
def _last_tradeable_bar(score: pd.DataFrame, panel: pd.DataFrame,
                        universe: pd.DataFrame | None) -> dict[str, pd.Timestamp]:
    """Per symbol: the last bar at which it may hold a position. Delisted names must
    EXIT here, never be silently dropped (wiki/concepts/survivorship-and-universe.md,
    _adaptation §5). Sources, in priority: universe `delisted_after`, else last bar with
    a finite close in the panel, else the score's last bar.
    """
    last: dict[str, pd.Timestamp] = {}
    close = panel["close"] if "close" in panel.columns.get_level_values(0) else None

    # match the bar index tz (real klines are tz-aware UTC; universe delisted_after may be
    # tz-naive) so the min() comparisons below don't raise.
    idx_tz = score.index.tz

    def _coerce(ts):
        ts = pd.Timestamp(ts)
        if idx_tz is not None and ts.tz is None:
            ts = ts.tz_localize(idx_tz)
        elif idx_tz is None and ts.tz is not None:
            ts = ts.tz_localize(None)
        return ts

    delist: dict[str, pd.Timestamp] = {}
    if universe is not None and "delisted_after" in universe.columns:
        u = universe.dropna(subset=["delisted_after"])
        for sym, ts in zip(u["binance_symbol"], u["delisted_after"]):
            ts = _coerce(ts)
            delist[sym] = min(delist.get(sym, ts), ts)

    for sym in score.columns:
        bar = score.index[-1]
        if close is not None and sym in close.columns:
            valid_close = close[sym].dropna()
            if len(valid_close):
                bar = valid_close.index[-1]
        if sym in delist:
            bar = min(bar, delist[sym])
        last[sym] = bar
    return last


# --- weight construction (legs -> caps) --------------------------------------
def _build_weights(score: pd.DataFrame, panel: pd.DataFrame,
                   universe: pd.DataFrame | None) -> pd.DataFrame:
    """Target weights per bar from the composite score.

    Steps (all cross-sectional, per timestamp):
      1. Rank valid scores (non-NaN -> already restricted to PIT universe upstream).
      2. Long top LONG_SHORT_QUANTILE fraction, short bottom fraction, equal-weight legs.
      3. Per-name cap |w| <= MAX_NAME_WEIGHT (liquidation guard).
      4. Scale each side so gross sum|w| <= MAX_GROSS_LEVERAGE.
      5. Rebalance only every REBALANCE_EVERY bars; hold (ffill) between (honest turnover).
      6. Force delisted names to 0 at/after their last tradeable bar.
    """
    q = config.LONG_SHORT_QUANTILE
    weights = pd.DataFrame(0.0, index=score.index, columns=score.columns)

    rebal_mask = np.zeros(len(score), dtype=bool)
    rebal_mask[::config.REBALANCE_EVERY] = True

    for i, ts in enumerate(score.index):
        if not rebal_mask[i]:
            continue
        row = score.loc[ts].dropna()
        if len(row) < 2:
            continue
        n_side = max(1, int(np.floor(len(row) * q)))
        order = row.sort_values()
        shorts = order.index[:n_side]
        longs = order.index[-n_side:]

        w = pd.Series(0.0, index=score.columns)
        w[longs] = 1.0 / len(longs)
        w[shorts] = -1.0 / len(shorts)

        # (3) per-name cap
        w = w.clip(lower=-config.MAX_NAME_WEIGHT, upper=config.MAX_NAME_WEIGHT)

        # (4) gross cap, scaling each side independently so net stays ~balanced
        long_gross = w[w > 0].sum()
        short_gross = -w[w < 0].sum()
        half = config.MAX_GROSS_LEVERAGE / 2.0
        if long_gross > half:
            w[w > 0] *= half / long_gross
        if short_gross > half:
            w[w < 0] *= half / short_gross

        weights.loc[ts] = w

    # (5) hold between rebalances: only rebalance bars carry targets; ffill the rest.
    # pandas .where needs a full-shape condition (no numpy-style row broadcast).
    rebal_2d = np.broadcast_to(rebal_mask[:, None], weights.shape)
    weights = weights.where(rebal_2d, np.nan).ffill().fillna(0.0)

    # (6) force-close delisted names at/after their last tradeable bar. Zero the TARGET
    # from `bar` onward (>=) so the held (shift(1)) position is flat for every bar past the
    # last tradeable price — a target set at `bar` would otherwise be held into bar+1, which
    # has no valid price.
    last = _last_tradeable_bar(score, panel, universe)
    for sym, bar in last.items():
        weights.loc[weights.index >= bar, sym] = 0.0

    return weights


# --- funding P&L line (SEPARATE; not folded into price returns) --------------
def _funding_line(weights: pd.DataFrame, cost) -> pd.Series:
    """Per-bar funding P&L = sum_name(signed_weight_held * funding_rate) applied at the
    8h funding stamps only (reindexed to 1m bars, 0 off-stamp). Sourced from
    collect.load_funding — imported LAZILY so this module imports even before the DATA
    stream's collect.py exists; synthetic funding is attached via `cost._funding_override`
    in self-test. POSITIVE means carry PAID (a drag); net subtracts it.
    """
    funding = pd.Series(0.0, index=weights.index)

    override = getattr(cost, "_funding_override", None)
    if override is not None:
        rates = override  # DataFrame: index=funding_time, columns=symbol
    else:
        try:
            from . import collect  # lazy: tolerate missing DATA stream
        except Exception:
            return funding
        frames = {}
        for sym in weights.columns:
            try:
                fdf = collect.load_funding(sym)
                frames[sym] = fdf["funding_rate"]
            except Exception:
                continue
        if not frames:
            return funding
        rates = pd.DataFrame(frames)

    # held weights are the lagged weights (entered at t, paying funding while held)
    held = weights.shift(1).fillna(0.0)
    rates = rates.reindex(columns=weights.columns)
    # align each funding stamp to the 1m bar at-or-after it, then to our index
    rates_on_bars = rates.reindex(weights.index, method=None).fillna(0.0)
    funding = (held * rates_on_bars).sum(axis=1)
    return funding


# --- core run ----------------------------------------------------------------
def run_backtest(score: pd.DataFrame, panel: pd.DataFrame,
                 universe: pd.DataFrame, cost) -> BacktestResult:
    """Vectorized long-short backtest.

    STRICT 1-bar execution lag: weights derived from score@t are SHIFTED forward one bar
    before multiplying the realized return, so score@t can only affect P&L@t+1. The
    forward return is fwd_return@t = close@t+1/close@t - 1; pairing it with weights.shift(1)
    means the realized contribution at bar t uses weights formed at t-1 from score@t-1
    against the t-1 -> t price move. By construction score@t never touches ret@t.

    net = price_pnl - fees - funding_paid, with funding kept as a SEPARATE line
    (_adaptation §3). cost.apply_funding toggles whether funding is netted; it is always
    reported regardless. Transaction cost = (taker_bp + slippage_bp) * turnover.
    """
    score = score.sort_index()
    close = panel["close"].reindex(columns=score.columns).reindex(score.index)

    # forward 1-bar simple return: known only at t+1, attributed to bar t+1 below.
    fwd_return = close.pct_change().fillna(0.0)  # ret@t = close@t/close@t-1 - 1

    weights = _build_weights(score, panel, universe)

    # 1-BAR LAG: weights formed from score@t are held into t+1; pair shift(1) weights with
    # the t-1->t return so the contribution at bar t comes from the prior bar's weights.
    held = weights.shift(1).fillna(0.0)
    price_pnl = (held * fwd_return).sum(axis=1)

    # turnover and transaction cost (charged when weights change)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    cost_bp = (getattr(cost, "taker_bp", 0.0) + getattr(cost, "slippage_bp", 0.0)) * 1e-4
    fees = turnover * cost_bp

    funding_paid = _funding_line(weights, cost)
    if not getattr(cost, "apply_funding", True):
        net_funding = pd.Series(0.0, index=weights.index)
    else:
        net_funding = funding_paid

    net_returns = price_pnl - fees - net_funding
    equity_curve = (1.0 + net_returns).cumprod()

    return BacktestResult(
        net_returns=net_returns,
        price_pnl=price_pnl,
        fees=fees,
        funding_paid=funding_paid,
        equity_curve=equity_curve,
        turnover=turnover,
        weights=held,
    )


# --- metrics (every dict tagged with split + cost) ---------------------------
def _cost_label(cost) -> str:
    taker = getattr(cost, "taker_bp", 0.0)
    slip = getattr(cost, "slippage_bp", 0.0)
    verified = getattr(cost, "verified", False)
    tag = "" if verified else " UNVERIFIED"
    return f"taker={taker}bp+slip={slip}bp{tag}"


def metrics(result: BacktestResult, split: str, cost) -> dict:
    """AnnRet/AnnVol/Sharpe/MaxDD/Calmar/Turnover for one run, TAGGED with (split, cost).

    The (split, cost) tag is mandatory (wiki/contradictions.md): backtest != live and no
    number is meaningful without knowing which window and which fee assumption produced it.
    `split` in {train, valid, oos} restricts to that chronological window; "full" uses all.
    Annualization uses config.BARS_PER_YEAR (1m bars per 365d).
    """
    r = result.net_returns.dropna()
    if split in ("train", "valid", "oos"):
        window = chronological_split(r.index)[split]
        r = r.reindex(window).dropna()
    bpy = config.BARS_PER_YEAR
    ann_ret = float(r.mean() * bpy)
    ann_vol = float(r.std(ddof=0) * np.sqrt(bpy))
    sharpe = float(ann_ret / ann_vol) if ann_vol > 0 else float("nan")

    # equity curve re-based within the split so drawdown is split-local
    eq = (1.0 + r).cumprod()
    drawdown = eq / eq.cummax() - 1.0
    max_dd = float(drawdown.min()) if len(drawdown) else float("nan")
    calmar = float(ann_ret / abs(max_dd)) if max_dd < 0 else float("nan")
    # per-bar turnover annualized to per-year for a comparable, honest cost knob
    turnover = float(result.turnover.reindex(r.index).mean() * bpy)

    return {
        "split": split,
        "cost": _cost_label(cost),
        "AnnRet": ann_ret,
        "AnnVol": ann_vol,
        "Sharpe": sharpe,
        "MaxDD": max_dd,
        "Calmar": calmar,
        "Turnover": turnover,
    }


# --- fee-sensitivity sweep (fills contradictions §1 "re-cost the headline") ---
def cost_sweep(score: pd.DataFrame, panel: pd.DataFrame,
               universe: pd.DataFrame) -> pd.DataFrame:
    """Re-cost the headline across config.COST_SWEEP_BP (fills contradictions §1, the
    gap where the paper never re-costs its EW L-S at 10/20/30 bp).

    CONVENTION: each swept bp is treated as the TOTAL one-way cost knob — taker_bp = bp,
    slippage_bp = 0 — so the sweep isolates a single clean fee parameter and maps directly
    onto the wiki's fee-sensitivity framing. (The headline run via run_backtest/COST still
    uses taker_bp + slippage_bp; only the sweep isolates bp-as-total.) Funding is held at
    config.COST.apply_funding. Sharpe should DECREASE as bp rises (linear cost drag).
    Every row is tagged (split, cost). Values UNVERIFIED until the real schedule is filled.
    """
    rows = []
    funding_override = getattr(config.COST, "_funding_override", None)
    for bp in config.COST_SWEEP_BP:
        c = config.CostModel(taker_bp=float(bp), slippage_bp=0.0,
                             apply_funding=config.COST.apply_funding, verified=False)
        if funding_override is not None:
            c._funding_override = funding_override  # carry self-test funding through
        res = run_backtest(score, panel, universe, c)
        m = metrics(res, split="full", cost=c)
        m["cost_bp"] = float(bp)
        rows.append(m)
    df = pd.DataFrame(rows)
    return df.set_index("cost_bp")


# --- self-test (synthetic inputs matching INTERFACES.md schemas) -------------
def _synth_inputs(n_bars: int = 2000, n_syms: int = 12, seed: int = 0):
    """Build synthetic score / panel / universe / funding matching INTERFACES schemas,
    including ONE delisted name, for offline verification."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-01", periods=n_bars, freq="1min", tz="UTC", name="open_time")
    syms = [f"SYM{i:02d}USDT" for i in range(n_syms)]

    # prices: geometric random walk with a faint momentum-correlated drift per name
    log_ret = rng.normal(0, 0.001, size=(n_bars, n_syms))
    close = pd.DataFrame(100 * np.exp(np.cumsum(log_ret, axis=0)), index=idx, columns=syms)
    high = close * (1 + np.abs(rng.normal(0, 0.0005, size=close.shape)))
    low = close * (1 - np.abs(rng.normal(0, 0.0005, size=close.shape)))
    volume = pd.DataFrame(rng.uniform(1e3, 1e5, size=close.shape), index=idx, columns=syms)
    panel = pd.concat({"close": close, "high": high, "low": low, "volume": volume}, axis=1)
    panel.columns = panel.columns.set_names(["field", "symbol"])

    # score: a causal signal (past return) — what matters here is the LAG, not the edge
    score = close.pct_change(5).shift(1)  # already causal; backtest adds its own lag too

    # ONE delisted name: SYM00USDT stops trading half-way; close goes NaN, delisted_after set
    delist_bar = idx[n_bars // 2]
    panel.loc[panel.index > delist_bar, ("close", "SYM00USDT")] = np.nan

    # universe long-df (one snapshot row per symbol is enough for the schema here)
    universe = pd.DataFrame({
        "date": idx[0].normalize(),
        "coingecko_id": [s.lower() for s in syms],
        "binance_symbol": syms,
        "market_cap": rng.uniform(1e8, 1e10, size=n_syms),
        "rank": range(1, n_syms + 1),
        "listed": True,
    })
    # tz-aware UTC column so assigning a tz-aware delist timestamp doesn't raise
    universe["delisted_after"] = pd.Series(pd.NaT, index=universe.index,
                                           dtype="datetime64[ns, UTC]")
    universe.loc[universe["binance_symbol"] == "SYM00USDT", "delisted_after"] = delist_bar

    # funding: 8h stamps, per-interval rate
    f_idx = pd.date_range(idx[0], idx[-1], freq="8h", tz="UTC", name="funding_time")
    funding = pd.DataFrame(rng.normal(0, 1e-4, size=(len(f_idx), n_syms)),
                           index=f_idx, columns=syms)

    return score, panel, universe, funding, delist_bar


def _selftest() -> None:
    score, panel, universe, funding, delist_bar = _synth_inputs()

    # attach synthetic funding via override so we don't need collect.py present
    cost = config.CostModel(taker_bp=5.0, slippage_bp=2.0, apply_funding=True, verified=False)
    cost._funding_override = funding
    config.COST._funding_override = funding  # so cost_sweep carries funding too

    # 1) imports cleanly is proven by reaching here. Run the engine.
    res = run_backtest(score, panel, universe, cost)
    assert np.isfinite(res.equity_curve).all(), "equity curve has non-finite values"
    print(f"[ok] finite equity curve, final equity = {res.equity_curve.iloc[-1]:.6f}")

    # 2) LOOK-AHEAD TEST: shifting the score forward by one bar MUST change results.
    #    (If score@t leaked into ret@t, an extra forward shift would be a no-op.)
    res_shift = run_backtest(score.shift(1), panel, universe, cost)
    a = res.net_returns.fillna(0.0).to_numpy()
    b = res_shift.net_returns.fillna(0.0).to_numpy()
    changed = not np.allclose(a, b)
    # And prove the contribution at bar t uses PRIOR-bar weights (held == weights.shift(1)).
    w_target = _build_weights(score, panel, universe)
    lag_ok = res.weights.shift(-1).fillna(0.0).iloc[:-1].equals(
        w_target.iloc[:-1].fillna(0.0)) or np.allclose(
        res.weights.to_numpy()[1:], w_target.to_numpy()[:-1])
    assert changed, "LOOK-AHEAD FAIL: forward-shifting score did not change results"
    assert lag_ok, "LOOK-AHEAD FAIL: held weights are not the 1-bar-lagged target weights"
    print(f"[ok] LOOK-AHEAD: shift changes results={changed}, held==target.shift(1)={lag_ok}")

    # 3) metrics dict carries (split, cost) tags
    m = metrics(res, split="oos", cost=cost)
    assert "split" in m and "cost" in m, "metrics missing (split,cost) tags"
    print(f"[ok] sample metrics dict: {m}")

    # 4) cost_sweep: rows for 5/10/20 bp, Sharpe DECREASING as cost rises
    sweep = cost_sweep(score, panel, universe)
    sharpes = sweep["Sharpe"].to_list()
    decreasing = all(x > y for x, y in zip(sharpes, sharpes[1:]))
    assert set(sweep.index) >= set(config.COST_SWEEP_BP), "sweep missing expected bp rows"
    assert decreasing, f"Sharpe not decreasing as cost rises: {sharpes}"
    print(f"[ok] cost_sweep Sharpe decreasing: {sharpes}")
    print(sweep[["split", "cost", "Sharpe", "AnnRet", "Turnover"]].to_string())

    # 5) delisted name closes its position at its last tradeable bar
    held_after = res.weights.loc[res.weights.index > delist_bar, "SYM00USDT"]
    assert (held_after == 0.0).all(), "delisted name still held after last tradeable bar"
    print(f"[ok] delisted SYM00USDT weight==0 for all {len(held_after)} bars after {delist_bar}")

    print("\nALL SELF-TESTS PASSED")


if __name__ == "__main__":
    _selftest()
