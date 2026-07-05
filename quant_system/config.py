"""Shared configuration and contracts for the 4-factor system.

Every module imports from here so the three build streams (data / factors / backtest)
agree on schemas, paths, windows, splits, and the cost model. Edit values here only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# --- paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
KLINES_DIR = DATA_DIR / "klines"          # one parquet per binance symbol
FUNDING_DIR = DATA_DIR / "funding"        # one parquet per binance symbol
UNIVERSE_PATH = DATA_DIR / "universe.parquet"

# --- universe ----------------------------------------------------------------
UNIVERSE_SIZE = 30                        # top-N by point-in-time market cap, BTC always eligible
ALWAYS_INCLUDE = ["bitcoin"]              # coingecko ids guaranteed eligible
# historically-large, now-delisted coins included so dead names are not silently dropped
# (the survivorship failure wiki/concepts/survivorship-and-universe.md warns of).
DELISTED_SEED = ["terra-luna", "ftx-token"]

# --- data --------------------------------------------------------------------
INTERVAL = "1m"                           # free minimum on USDⓈ-M futures klines
# default collection window: last 12 months (full range opt-in; 1m*30sym*5y is multi-GB)
LOOKBACK_DAYS = 365

# --- factor windows (in 1m bars; backward-only / causal) ---------------------
MOMENTUM_WINDOW = 240                     # 4h trend, positive tilt
LOWVOL_WINDOW = 120                       # 2h realized-vol (negated -> long low-vol)
RANGE_WINDOW = 60                         # 1h persistent (high-low)/close level
REVERSAL_WINDOW = 5                       # 5m short-term reversal (negated)
SEMIVAR_WINDOW = 120                      # 2h realized-semivariance imbalance lookback (signed)
# rebalance every N bars; signals are native 1m but turnover is capped here (honest cost knob)
REBALANCE_EVERY = 5

# --- portfolio ---------------------------------------------------------------
LONG_SHORT_QUANTILE = 0.2                 # long top 20% / short bottom 20% of composite
MAX_NAME_WEIGHT = 0.10                    # per-name cap (liquidation guard, _adaptation.md §5)
MAX_GROSS_LEVERAGE = 1.0                  # sum |w| cap

# --- chronological splits (no tuning on OOS; selection on train only) --------
# fractions of the collected window, in time order: train / valid / pure-OOS
SPLITS = {"train": 0.5, "valid": 0.2, "oos": 0.3}

# --- protocol layer (UNVERIFIED placeholders; paper thresholds undisclosed) ---
# The paper gates candidates on train-only mean IC and IC t-stat, but does not
# disclose numeric tau_IC / tau_t. These defaults are intentionally weak and should
# be replaced before treating passed factors as research evidence.
IC_MIN_MEAN = 0.0
IC_MIN_T = 0.0
RIDGE_ALPHA = 1.0
EXECUTION_LAG_BARS = 1
HOLDING_PERIOD_BARS = 1

# --- cost model (UNVERIFIED placeholders; user to supply real schedule) ------
# _adaptation.md §4 / contradictions.md §5. Funding is a SEPARATE P&L line, not a return.
@dataclass
class CostModel:
    taker_bp: float = 5.0                 # one-way, basis points  (placeholder, unverified)
    slippage_bp: float = 2.0              # per-side slippage estimate (placeholder)
    apply_funding: bool = True            # net price return minus funding paid/earned
    verified: bool = False                # flip True once user confirms real Binance fees


COST = CostModel()
# fee-sensitivity sweep used by the backtest (fills the "re-cost the headline" gap, §1)
COST_SWEEP_BP = [5.0, 10.0, 20.0]

BARS_PER_YEAR = 525_600                   # 1m bars per 365d, for annualization
