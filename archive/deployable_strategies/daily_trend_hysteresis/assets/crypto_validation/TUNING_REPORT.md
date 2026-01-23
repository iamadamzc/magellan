# CRYPTO VALIDATION & TUNING REPORT

**Date**: 2026-01-16  
**Strategy**: Daily Trend Hysteresis (Tuning -> Hourly)  
**Status**: ✅ **PARTIALLY SUCCESSFUL (ETH ONLY)**

---

## EXECUTIVE SUMMARY

Testing confirmed that **ETH/USD** is a viable candidate for the Hysteresis strategy when converted to an **Hourly timeframe**, achieving a **Sharpe Ratio of 1.24**. However, **BTC/USD** failed all tuning attempts (Hourly, Filtered) and should be excluded.

| Asset | Timeframe | Sharpe | Return | Max DD | Status |
|-------|-----------|--------|--------|--------|--------|
| **ETH/USD** | **Hourly** | **1.24** | **+2,172%** | **-45.7%** | ✅ **DEPLOY** |
| ETH/USD | Hrly + Wk Filter | 0.93 | +265% | -35.3% | ❌ Worse |
| ETH/USD | Daily | 0.71 | +140% | -47.0% | ❌ Baseline |
| **BTC/USD** | **Hourly** | **0.42** | **+67%** | **-60.7%** | ❌ **FAIL** |
| BTC/USD | Hrly + Wk Filter | 0.02 | -15% | -48.8% | ❌ FAIL |
| BTC/USD | Daily | 0.65 | +144% | -54.4% | ⚠️ Marginal |

---

## DETAILED FINDINGS

### 1. ETH/USD Validation (Hourly) ✅
- **Performance**: The move to Hourly bars successfully captured ETH's high momentum.
- **Sharpe**: Improved from 0.71 (Daily) to **1.24 (Hourly)**.
- **Alpha**: The strategy captured **+2,172%** return, tracking Buy & Hold (+2,202%) closely but with significantly reduced downtime exposure (time in market).
- **Drawdown**: High (-45.7%) but typical for crypto.

### 2. BTC/USD Failure ❌
- **Performance**: Hourly timeframe made performance *worse* for BTC (0.65 -> 0.42).
- **Insight**: BTC exhibits more efficient/mean-reverting behavior on hourly timeframes compared to ETH. It does not sustain hourly momentum trends reliably enough for this logic.
- **Weekly Filter**: Adding a weekly trend filter destroyed performance (Sharpe 0.02), indicating that BTC moves often happen against the weekly trend (reversals) or the filter is too lagging.

### 3. Weekly Filter Impact
- **Hypothesis**: "Weekly filter will improve Sharpe by avoiding counter-trend trades."
- **Result**: **REJECTED**.
    - ETH Sharpe dropped (1.24 -> 0.93).
    - BTC Sharpe dropped (0.42 -> 0.02).
- **Reasoning**: The filter causes the strategy to miss the explosive initial moves of a trend reversal, which are critical for crypto returns.

---

## DEPLOYMENT RECOMMENDATION

1. **Deploy ETH/USD ONLY**:
   - **Timeframe**: 1-Hour
   - **Parameters**: RSI-14, Bands 55/45
   - **Logic**: Long only (no shorting validated here).
   - **Sizing**: Conservative (due to -45% DD).

2. **Abandon BTC/USD**:
   - BTC does not fit the Daily Trend Hysteresis logic on any tested timeframe.
   - Remove from strategy universe.

3. **Next Steps**:
   - Move ETH Hourly to **Paper Trading**.
   - Do NOT implement Weekly Filter.

---

**Artifacts**:
- `crypto_fmp_hourly_full.csv`: Full hourly backtest data (2020-2025).
- `crypto_filtered_results.csv`: Filtered backtest data.
