# Project Magellan - Technical Backlog

## High Priority: Strategy Refinement

### ✅ 1. Adaptive Hysteresis Thresholds (COMPLETED 2026-01-14)
**Status**: ✅ **PRODUCTION READY**  
**Implementation**: `test_adaptive_hysteresis.py`  
**Results**: `ADAPTIVE_HYSTERESIS_RESULTS.md`

**Outcome**:
- Implemented ATR-based adaptive thresholds with 3 volatility regimes
- High Volatility (ATR > 1.5x): 60/40 bands (reduced whipsaw)
- Normal Volatility: 55/45 bands (base hysteresis)
- Low Volatility (ATR < 0.75x): 52/48 bands (increased participation)
- **Performance**: 1.31 Sharpe, +26.88% return, -7.88% max drawdown
- **Best Configuration**: Adaptive ATR outperforms all fixed-band variants

**Next Step**: Integrate into `src/features.py` for production use (Estimated: 2-3 hours)

---

### ✅ 2. Asymmetric Bands Testing (COMPLETED 2026-01-14)
**Status**: ✅ **VALIDATED**  
**Results**: Documented in `ADAPTIVE_HYSTERESIS_RESULTS.md`

**Tested Configurations**:
- 52/48 (Tight): +21.33% return, -11.52% drawdown → Too aggressive
- 55/48 (Conservative entry, fast exit): +24.89% return, -7.26% drawdown → Good risk control
- 55/45 (Symmetric, Original): +26.10% return, -7.88% drawdown → Better risk-adjusted return

**Verdict**: Symmetric 55/45 bands provide better **risk-adjusted returns** (Sharpe 1.28) than asymmetric variants. However, Adaptive ATR (1.31 Sharpe) outperforms both.

**Recommendation**: Use Adaptive ATR for SPY; symmetric 55/45 for simpler implementations on stable large-caps.

---

### ✅ 3. Baseline Comparison Test (COMPLETED 2026-01-14)
**Status**: ✅ **WHIPSAW COST QUANTIFIED**  
**Results**: Documented in `ADAPTIVE_HYSTERESIS_RESULTS.md`

**Findings**:
- **Baseline (No Hysteresis, RSI > 50)**:
  - 77 trades, $577.50 transaction costs, +16.57% return, -11.25% drawdown
- **Variant F (Hysteresis 55/45)**:
  - 37 trades, $277.50 transaction costs, +26.10% return, -7.88% drawdown
- **Whipsaw Savings**:
  - **52% trade reduction** (40 fewer trades)
  - **$300 cost savings**
  - **+9.53% return improvement**
  - **+3.37% drawdown improvement**

**Verdict**: Scientific proof that hysteresis is **essential** for daily trend-following strategies. The Schmidt Trigger eliminates whipsaw and improves both returns and risk metrics.

---

## Medium Priority: Infrastructure & Data

### 4. Split-Adjusted Price Handling (NVDA Fix)
**Context**: The NVDA backtest failed because the P&L calculation didn't account for the 10-for-1 stock split on June 10, 2024. Alpaca SIP data should be adjusted, or we need to handle it manually.
**Action**: Update `AlpacaDataClient` or the P&L logic to handle splits.
- Option A: Ensure `adjustment='all'` parameter works correctly in Alpaca SDK.
- Option B: Implement share-based tracking in the backtester instead of simple `% return` compounding.

**Status**: 🔴 **OPEN** (Required for NVDA validation)

---

### 5. Configurable Backtester (Timeframe Support)
**Context**: `backtester_pro.py` currently has `timeframe='1Min'` hardcoded on line 169.
**Action**: Update `run_rolling_backtest` to accept a `timeframe` argument (default to '1Min') so it can natively run Daily strategies without a separate test script.

**Status**: 🟡 **PARTIALLY ADDRESSED** (Test script works, but main backtester still needs update)

---

### 6. Share-Based P&L Tracking
**Context**: Current backtesters often use `(1 + ret).cumprod()` which breaks on large price discontinuities like splits.
**Action**: Refactor `backtester_pro.py` and test scripts to track `shares_held` and `cash_balance` explicitly. This is more robust for splits and dividends.

**Status**: 🔴 **OPEN** (Related to #4)

---

## Low Priority: Future Expansions

### 7. Multi-Timeframe Confirmation
**Context**: Daily signals can be noisy.
**Action**: Add logic to confirm Daily Hysteresis signals with Weekly trend checks.
- Only exit Long if Daily RSI < 45 AND Weekly RSI < 50.

**Status**: 🔴 **OPEN** (Recommended for further research)

---

### 8. Position Sizing Scaling
**Context**: Binary On/Off (100% / 0%) is harsh.
**Action**: Implement stepwise scaling.
- RSI > 55: 100% Long
- RSI 50-55: 50% Long
- RSI < 50: 0% Long

**Status**: 🔴 **OPEN** (Mentioned in ADAPTIVE_HYSTERESIS_RESULTS.md as follow-up work)

---

## New Items (Added 2026-01-14)

### 9. Production Integration: Adaptive ATR Hysteresis
**Context**: The Adaptive ATR configuration is validated and production-ready for SPY.
**Action**: Integrate into `src/features.py` for multi-ticker support.
- Port `calculate_atr()` into `add_technical_indicators()`
- Create `calculate_adaptive_thresholds_daily()` function
- Update `generate_master_signal()` to support hysteresis mode for daily timeframe
- Add config parameter: `"HYSTERESIS_MODE": "adaptive_atr"`

**Estimated Effort**: 2-3 hours  
**Priority**: 🟢 **HIGH** (Proven value, ready to deploy)

---

### 10. NVDA Re-Validation with Adaptive ATR
**Context**: Original NVDA test failed due to stock split data issues. With split-adjusted data (Backlog #4), re-run the optimization suite.
**Action**: 
1. Fix split-adjusted data handling (resolve Backlog #4 first)
2. Run `test_adaptive_hysteresis.py` with `SYMBOL = 'NVDA'`
3. Compare results to SPY to validate cross-asset performance

**Estimated Effort**: 1 hour (after #4 is resolved)  
**Priority**: 🟡 **MEDIUM**

---

## Archive (Completed Items)

### ✅ Daily Trend Hysteresis Implementation (Variant F)
**Completed**: 2026-01-14 (earlier session)  
**Status**: ✅ **VALIDATED** (SPY 2024-2026: -7.88% DD, +26.10% return)  
**Artifacts**: `VARIANT_F_RESULTS.md`, `test_daily_hysteresis.py`

---

**Last Updated**: 2026-01-14 22:30 ET  
**Outstanding High-Priority Items**: 1 (Production Integration #9)  
**Outstanding Medium-Priority Items**: 3 (#4, #5, #10)
