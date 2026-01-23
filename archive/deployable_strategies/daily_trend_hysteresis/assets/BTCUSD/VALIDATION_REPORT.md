# BTC/USD VALIDATION REPORT

**Date**: 2026-01-16  
**Strategy**: Daily Trend Hysteresis (Hourly Tuned)  
**Status**: ❌ **FAILED / REJECTED**

---

## EXECUTIVE SUMMARY

The **BTC/USD** strategy failed validation on both Daily and Hourly timeframes. It utilizes mean-reverting behavior that fundamentally conflicts with the Hysteresis trend-following logic.

| Metric | Performance (2020-2025) | Status |
|--------|-------------------------|--------|
| **Hourly Sharpe** | **0.42** | ❌ Fail |
| **Filtered Sharpe** | **0.02** | ❌ Fail |
| **Daily Sharpe** | **0.65** | ⚠️ Marginal |
| **Max Drawdown** | **-60.7%** | ❌ High |

---

## FAILURE ANALYSIS

1.  **Timeframe Failure**: 
    - Moving from Daily to Hourly **degraded** performance (Sharpe 0.65 -> 0.42).
    - Unlike ETH, BTC does not sustain hourly momentum trends sufficient to overcome chop.

2.  **Filter Failure**:
    - Adding a Weekly RSI filter resulted in a Sharpe of 0.02.
    - This confirms that BTC price action is too noisy or efficient for simple RSI trend following.

---

## RECOMMENDATION

- **DO NOT DEPLOY** this strategy on BTC/USD.
- **Archive** this finding to prevent future redundant testing.
- **Pivot**: Explore Mean Reversion strategies for BTC instead of Trend Following.

---

**Verdict**: **ARCHIVED**
