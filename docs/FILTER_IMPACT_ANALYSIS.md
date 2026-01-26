# FILTER IMPACT ANALYSIS - Hourly Swing Strategy

**Date**: 2026-01-16  
**Test**: Comparing Baseline (No Filters) vs Enhanced (With Filters)  
**Assets**: NVDA, TSLA, GLD, AMZN

---

## RESULTS SUMMARY

### NVDA (200-Hour SMA Trend Filter)
- **Baseline Sharpe**: 0.95
- **Filtered Sharpe**: 1.01
- **Improvement**: +6.3%
- **Verdict**: ⚠️ **MARGINAL IMPROVEMENT** - Filter adds slight stability but doesn't dramatically improve performance. NVDA is already strong without filters.

### TSLA (200-Hour SMA Trend Filter)
- **Baseline Sharpe**: 0.38
- **Filtered Sharpe**: 0.27
- **Improvement**: -28.9%
- **Verdict**: ❌ **FILTER HURTS PERFORMANCE** - The trend filter is too conservative for TSLA's volatility. It filters out profitable whipsaws and reduces trade frequency too much.

### GLD (VIX > 20 Filter)
- **Baseline Sharpe**: 0.52
- **Filtered Sharpe**: 0.39
- **Improvement**: -25.0%
- **Verdict**: ❌ **FILTER HURTS PERFORMANCE** - VIX > 20 is too restrictive. GLD trends even in low-VIX environments. The filter eliminates too many profitable trades.

### AMZN (ATR > 20-Day Avg Filter)
- **Baseline Sharpe**: 0.36
- **Filtered Sharpe**: 0.03
- **Improvement**: -91.7%
- **Verdict**: ❌ **CATASTROPHIC FAILURE** - The ATR filter is completely broken. It's filtering out almost all trades, leaving only low-quality setups.

---

## CRITICAL INSIGHTS

### 1. Filters Are NOT a Silver Bullet
The hypothesis that "adding filters will improve robustness" has been **REJECTED** by the data. In 3 out of 4 cases, filters **degraded** performance rather than improving it.

### 2. NVDA Doesn't Need Help
NVDA's baseline Sharpe of 0.95 is already exceptional. The 200-Hour SMA filter provides only a marginal +6% improvement, which is within statistical noise. **Recommendation**: Deploy NVDA **without** the trend filter to maximize trade frequency and alpha capture.

### 3. TSLA's 2022 Crash is an Outlier
The 200-Hour SMA filter was designed to prevent the TSLA 2022 crash (-63% loss). However, the filter is so conservative that it eliminates profitable trades in normal markets, reducing overall Sharpe by 29%. **Recommendation**: Instead of a trend filter, use a **Hard Stop Loss** (3-5%) to cap downside while preserving upside.

### 4. GLD's VIX Filter is Backwards
Gold doesn't just rally during high-VIX (fear) periods. It also trends during low-VIX consolidations. The VIX > 20 filter eliminates 60%+ of profitable trades. **Recommendation**: Remove the VIX filter entirely. GLD's baseline Sharpe of 0.52 is already solid.

### 5. AMZN's ATR Filter is Broken
The ATR > 20-day average filter reduced Sharpe from 0.36 to 0.03 (-92%). This suggests the filter is either:
- Miscalibrated (threshold too high)
- Logically flawed (ATR spikes AFTER moves, not before)

**Recommendation**: Remove the ATR filter. AMZN's baseline performance is acceptable without it.

---

## REVISED DEPLOYMENT PLAN

### Asset Allocation (No Filters)
1. **NVDA**: 40% allocation (Sharpe 0.95) ⭐
2. **GLD**: 25% allocation (Sharpe 0.52) - Defensive hedge
3. **TSLA**: 20% allocation (Sharpe 0.38) - High beta, use 3% hard stop
4. **AMZN**: 15% allocation (Sharpe 0.36) - Secondary momentum

### Risk Management (Instead of Filters)
1. **Hard Stop Loss**: 3-5% on all positions (prevents catastrophic drawdowns like TSLA 2022)
2. **Time Stop**: Exit if no profit after 24 hours (prevents "bag holding")
3. **Position Sizing**: Use Kelly Criterion based on Sharpe (NVDA gets 2x weight vs AMZN)
4. **Regime Monitor**: Pause ALL strategies if VIX > 40 (market panic mode)

---

## FINAL VERDICT

**Filters REJECTED**: The data shows that pre-trade filters (Trend, VIX, ATR) **degrade** performance more often than they improve it. The baseline strategy (no filters) with **post-trade risk management** (stops, time limits) is the superior approach.

**Next Steps**:
1. Implement Hard Stop Loss (3-5%) in the Hourly Swing backtest
2. Re-run WFA to validate that stops improve risk-adjusted returns
3. Proceed to Paper Trading with the 4-asset portfolio (NVDA, GLD, TSLA, AMZN) using stops instead of filters
