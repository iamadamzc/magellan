# Strategy Parameters - Complete Audit

**Date**: 2026-01-18  
**Critical Finding**: Parameters ARE captured but scattered across multiple locations

---

## ✅ Crown Jewels Location Analysis

### Bear Trap - COMPLETE ✅

**Parameters documented in 3 places (all identical):**
1. `research/Perturbations/bear_trap/PARAMETERS.md` ✅
2. `research/Perturbations/bear_trap/bear_trap.py` (lines 26-53) ✅
3. `research/new_strategy_builds/BEAR_TRAP_PARAMETERS.md` ✅ (DUPLICATE - can archive)

**Hash verification**: Perturbations and new_strategy_builds versions are IDENTICAL

**Parameters captured**:
```python
params = {
    # Entry Filters
    'RECLAIM_WICK_RATIO_MIN': 0.15,
    'RECLAIM_VOL_MULT': 0.2,
    'RECLAIM_BODY_RATIO_MIN': 0.2,
   'MIN_DAY_CHANGE_PCT': 15.0,
    
    # Support
    'SUPPORT_MODE': 'session_low',
    
    # Exit
    'STOP_ATR_MULTIPLIER': 0.45,
    'ATR_PERIOD': 14,
    'SCALE_TP1_PCT': 40,
    'SCALE_TP2_PCT': 30,
    'RUNNER_PCT': 30,
    'MAX_HOLD_MINUTES': 30,
    
    # Position Sizing
    'PER_TRADE_RISK_PCT': 0.02,
    'MAX_POSITION_DOLLARS': 50000,
    
    # Risk Gates
    'MAX_DAILY_LOSS_PCT': 0.10,
    'MAX_TRADES_PER_DAY': 10,
    'MAX_SPREAD_PCT': 0.02,
    'MIN_BID_ASK_SIZE': 50,
}
```

---

### GSB - COMPLETE ✅

**Parameters documented in:**
1. `research/Perturbations/GSB/gsb_strategy.py` (lines 35-47) ✅
2. `research/Perturbations/GSB/README.md` ✅ (documentation)

**Parameters captured**:
```python
params = {
    'OR_MINUTES': 10,              # 10-minute opening range
    'VOL_MULT': 1.8,               # Volume spike threshold
    'PULLBACK_ATR': 0.15,          # Pullback zone (15% ATR)
    'HARD_STOP_ATR': 0.4,          # Hard stop loss (40% ATR)
    'BREAKEVEN_TRIGGER_R': 0.8,    # Move stop to BE at 0.8R
    'PROFIT_TARGET_R': 2.0,        # Profit target at 2R
    'TRAIL_ATR': 1.0,              # Trailing stop (1 ATR)
    'MIN_PRICE': 0.01,
    'SESSION_HOUR': <varies by asset>,
    'SESSION_MIN': <varies by asset>,
}
```

---

### Daily Trend Hysteresis - COMPLETE ✅

**Parameters documented in:**
1. `research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py` (lines 30-42) ✅
2. `docs/operations/strategies/MAGELLAN_STRATEGY_PARAMETERS_EXTRACTED.md` (lines 8-14) ✅

**Per-asset optimized parameters in code**:
```python
VALIDATED_CONFIGS = {
    "AAPL": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "AMZN": {"rsi_period": 21, "upper_band": 55, "lower_band": 45},
    "GOOGL": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
    "META": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
    "MSFT": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "NVDA": {"rsi_period": 28, "upper_band": 58, "lower_band": 42},
    "TSLA": {"rsi_period": 28, "upper_band": 58, "lower_band": 42},
    "SPY": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "QQQ": {"rsi_period": 21, "upper_band": 60, "lower_band": 40},
    "IWM": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "GLD": {"rsi_period": 21, "upper_band": 65, "lower_band": 35},
}
```

**Also in**: `/config/mag7_daily_hysteresis/*.json` (JSON configs for deployment)

---

### Hourly Swing - COMPLETE ✅

**Parameters documented in:**
1. `research/Perturbations/hourly_swing/test_gap_reversal.py` (embedded in code) ✅
2. `docs/operations/strategies/MAGELLAN_STRATEGY_PARAMETERS_EXTRACTED.md` (lines 39-45) ✅

**Base parameters**:
```python
# RSI(28) hysteresis bands: 60 / 40
# Entry: RSI crosses above 60
# Exit: RSI crosses below 40
# Timeframe: Hourly bars
```

**Also in**: `/config/hourly_swing/*.json` (JSON configs for deployment)

---

### FOMC Straddles - COMPLETE ✅

**Parameters documented in:**
1. `research/Perturbations/fomc_straddles/test_bid_ask_spread.py` (embedded in code) ✅
2. `docs/operations/strategies/MAGELLAN_STRATEGY_PARAMETERS_EXTRACTED.md` (lines 99-117) ✅

**Parameters**:
```python
# Buy equity proxy 5 minutes before FOMC
# Sell equity proxy 5 minutes after FOMC
# Hold time: ~10 minutes
# Primary instrument: SPY
# Secondary: QQQ
```

**Event calendar**: `research/Perturbations/fomc_straddles/economic_events_2024.json`

---

### Earnings Straddles - COMPLETE ✅

**Parameters documented in:**
1. `research/Perturbations/earnings_straddles/test_regime_normalization.py` (embedded in code) ✅
2. `docs/operations/strategies/MAGELLAN_STRATEGY_PARAMETERS_EXTRACTED.md` (lines 69-96) ✅

**Parameters**:
```python
# Buy equity 2 trading days before earnings
# Sell equity 1 trading day after earnings
# Event-based (quarterly earnings)
# Long-only

# Tier 1: TSLA, NVDA, GOOGL
# Tier 2: AAPL
# Tier 3: META, MSFT, AMZN, NFLX, AMD, COIN, PLTR
```

---

## Summary: Where Parameters Live

### ✅ Primary Source (KEEP - Source of Truth)

**In Perturbations strategy .py files:**
- Bear Trap: `bear_trap.py` lines 26-53
- GSB: `gsb_strategy.py` lines 35-47
- Daily Trend: `test_friction_sensitivity.py` lines 30-42
- Hourly Swing: `test_gap_reversal.py` (embedded)
- FOMC: `test_bid_ask_spread.py` (embedded)
- Earnings: `test_regime_normalization.py` (embedded)

**Documentation files in Perturbations:**
- Bear Trap: `PARAMETERS.md` ✅
- GSB: `README.md` ✅
- Others: Parameters embedded in test files

**Deployment configs in /config:**
- Daily Trend: `/config/mag7_daily_hysteresis/*.json`
- Hourly Swing: `/config/hourly_swing/*.json`
- Main: `/config/nodes/master_config.json`

### 📚 Secondary Documentation (Historical)

**In docs/operations:**
- `MAGELLAN_STRATEGY_PARAMETERS_EXTRACTED.md` - High-level summary (4 strategies only)

**In new_strategy_builds:**
- `BEAR_TRAP_PARAMETERS.md` - DUPLICATE of Perturbations version
- Can be archived

---

## 🚨 CRITICAL RECOMMENDATIONS

### 1. Create Parameter Files for Missing Strategies

**Currently missing dedicated PARAMETERS.md files:**
- ❌ Daily Trend Hysteresis
- ❌ Hourly Swing  
- ❌ FOMC Straddles
- ❌ Earnings Straddles
- ✅ Bear Trap (has it)
- ✅ GSB (has README with params)

**Action Required**: Create `PARAMETERS.md` in each Perturbations strategy folder

---

### 2. Extract Parameters from Test Files

**Parameters are currently embedded in test .py files** - this is risky because:
- Not easily discoverable
-Could be lost if test files are modified
- No unified documentation format

**Recommended action before archival**:
1. Create `PARAMETERS.md` for each strategy
2. Extract from .py files
3. Format consistently
4. Include:
   - All parameter values
   - Rationale for each
   - Per-asset variations
   - Date validated
   - Test results that validated them

---

### 3. Consolidate Config Files

**Current state**: Parameters exist in 3 places
- Strategy .py files (hardcoded params dict)
- `/config/*.json` files (deployment configs)
- Perturbations test files (validated values)

**Sync these** to ensure consistency!

---

## Final Answer to Your Question

### ✅ YES - Parameters are captured

**But they're in the .py files themselves, not separate parameter files**

**Current status**:
- Bear Trap: ✅ Has dedicated PARAMETERS.md
- GSB: ✅ Has README.md with params
- Other 4: ⚠️ **Parameters only in .py code** (test files)

**None are disconnected** - they're all in the Perturbations folder we're keeping

**BUT** - I strongly recommend creating dedicated PARAMETERS.md files for all 6 strategies **BEFORE** cleanup to make the crown jewels explicitly documented separately from code.

---

## Proposed Action

**Create 4 new PARAMETERS.md files**:
1. `research/Perturbations/daily_trend_hysteresis/PARAMETERS.md`
2. `research/Perturbations/hourly_swing/PARAMETERS.md`
3. `research/Perturbations/fomc_straddles/PARAMETERS.md`
4. `research/Perturbations/earnings_straddles/PARAMETERS.md`

**Should I create these now to protect the crown jewels?**
