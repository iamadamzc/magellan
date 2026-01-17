# CLEAN-ROOM TESTING PROTOCOL - EXECUTION LOG

**Date**: 2026-01-17  
**Researcher**: Independent Adversarial Quantitative Analyst  
**Purpose**: Independent validation of three trading strategies with zero prior knowledge

---

## CONTAMINATION MITIGATION

**Risk Identified**: Reference document (`TESTING_ASSESSMENT_MASTER.md`) contained performance metrics, rankings, and conclusions.

**Mitigation Actions**:
1. ✅ Stopped reading reference document immediately upon detecting contamination
2. ✅ Requested authoritative strategy rules separately
3. ✅ Implemented strategies from scratch using only provided rules
4. ✅ Used different code structure, variable names, and logic flow
5. ✅ Applied independent friction assumptions
6. ✅ Documented all assumptions explicitly

**Contamination Status**: MITIGATED - No performance data used in implementation

---

## STRATEGY DEFINITIONS (AUTHORITATIVE)

### Strategy A: Hourly Swing - MSI (Micro Silver Futures)
- **Instrument**: MSI (Micro Silver Futures)
- **Timeframe**: Hourly bars
- **Direction**: Long-only
- **Entry**: RSI(28)[t-1] ≤ 60 AND RSI(28)[t] > 60 (strict crossover)
- **Exit**: RSI(28)[t-1] ≥ 40 AND RSI(28)[t] < 40 (strict crossover)
- **Position**: 1 contract per trade
- **Friction**: 10 bps baseline, 20 bps degraded

### Strategy B: Daily Trend Hysteresis - TSLA (Equity)
- **Instrument**: TSLA common stock
- **Timeframe**: Daily bars
- **Direction**: Long-only
- **Entry**: RSI(28)[t-1] ≤ 55 AND RSI(28)[t] > 55 (strict crossover)
- **Exit**: RSI(28)[t-1] ≥ 45 AND RSI(28)[t] < 45 (strict crossover)
- **Position**: 100 shares per trade
- **Friction**: 1.5 bps baseline, 5 bps degraded

### Strategy C: Earnings Event - AAPL (Equity)
- **Instrument**: AAPL common stock
- **Type**: Event-driven (earnings announcements)
- **Entry**: Buy 100 shares at T-2 close (2 trading days before earnings)
- **Exit**: Sell 100 shares at T+1 open (1 trading day after earnings)
- **Position**: 100 shares per event
- **Friction**: 5 bps baseline, 10 bps degraded

---

## TEST DESIGN

### Test Periods
- **Primary**: 2024-01-01 to 2025-12-31 (2 years)
- **Secondary**: 2022-01-01 to 2023-12-31 (2 years, non-overlapping)

### Execution Scenarios
For each strategy and period:
1. **Baseline Friction**: Conservative friction assumptions
2. **Degraded Friction**: 2x friction to test robustness

**Total Tests**: 3 strategies × 2 periods × 2 friction scenarios = **12 independent backtests**

---

## ASSUMPTIONS DOCUMENTED

### General Assumptions
1. **RSI Calculation**: Standard Wilder's smoothing (EMA-based)
2. **Crossover Logic**: Strict crossover (requires previous bar below/above threshold)
3. **Position Sizing**: Fixed size per trade (no scaling)
4. **No Stop-Loss**: Exit only via signal
5. **No Take-Profit**: Exit only via signal

### Strategy-Specific Assumptions

**Strategy A (MSI Futures)**:
- Contract multiplier: Standard CME Micro Silver contract
- Data source: FMP API `/stable` endpoint for futures
- Hourly bars: Continuous contract data

**Strategy B (TSLA Equity)**:
- Data source: Alpaca SIP feed (daily bars)
- Corporate actions: Adjusted for splits/dividends

**Strategy C (AAPL Earnings)**:
- Earnings dates: Researched independently (quarterly, late Jan/Apr/Jul/Oct)
- Entry timing: Market close on T-2
- Exit timing: Market open on T+1
- ATM strike: Not applicable (equity only, no options)

---

## IMPLEMENTATION NOTES

### Code Structure
- **Independent implementation**: No code reuse from existing backtests
- **Clean-room files**: Stored in `clean_room_test/` subdirectories
- **Naming convention**: `backtest_[instrument]_[timeframe].py`

### Data Sources
- **Equities**: Alpaca Data API (SIP feed)
- **Futures**: FMP API (`/historical-chart/1hour/MSI`)
- **No cached data**: Fresh fetch for each test

### Metrics Calculated
1. Total Return (%)
2. Max Drawdown (%)
3. Sharpe Ratio (annualized)
4. Win Rate (%)
5. Profit Factor
6. Average Win/Loss (%)
7. Trade Count
8. Average Hold Period

---

## EXECUTION STATUS

### Strategy A: MSI Hourly Swing
- **Status**: ⚠️ DATA ISSUE - Empty DataFrame returned from FMP API
- **Issue**: FMP endpoint may not support MSI or hourly data unavailable
- **Next Steps**: Investigate FMP API response, verify symbol and endpoint

### Strategy B: TSLA Daily Trend
- **Status**: 🔄 RUNNING - Fetching data from Alpaca
- **Progress**: Data fetch in progress

### Strategy C: AAPL Earnings
- **Status**: 🔄 RUNNING - Fetching data from Alpaca
- **Progress**: Data fetch in progress

---

## NEXT STEPS

1. ✅ Complete Strategy B and C backtests
2. ⚠️ Debug Strategy A data issue (MSI futures)
3. 📊 Generate comprehensive results reports
4. 🔍 Perform robustness analysis
5. 📝 Classify each strategy (Robust/Conditionally Viable/Fragile/Reject)

---

**Last Updated**: 2026-01-17 02:35 AM  
**Status**: IN PROGRESS
