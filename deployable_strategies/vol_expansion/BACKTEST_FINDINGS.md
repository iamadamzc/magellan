# Backtest V2 Results - Still Failing

**Date**: January 25, 2026  
**Test Status**: ❌ **FAILED** - Features still not matching research

---

## Results Summary

### v2.0 Backtest Results

| Symbol | Hit Rate | Expectancy | Trades | Expected HR | Deviation |
|--------|----------|------------|--------|-------------|-----------|
| **SPY** | 35.2% | 0.009R | 3,522 | 57.9% | **-22.7pp** ❌ |
| **QQQ** | 35.0% | 0.000R | 4,193 | 57.0% | **-22.0pp** ❌ |
| **IWM** | N/A | N/A | 0 | 55.0% | **No signals** ❌ |

### What Was Fixed (v2.0)
1. ✅ Proper ATR calculation using True Range
2. ✅ VIX data loaded (21,423 bars)
3. ✅ Research thresholds from FINAL_STRATEGY_RESULTS.json
4. ✅ Added `effort_result_mean` (raw, not z-score)

### What Is Still Wrong

#### Issue 1: IWM Uses `autocorr_10_mean` Which We Don't Calculate
```json
// IWM feature_profile includes:
{
  "feature": "autocorr_10_mean",
  "threshold": -0.22080065134999194,
  "direction": "<"
}
```
We're not calculating `autocorr_10_mean` in our feature module.

#### Issue 2: Signal Frequency Still Off
- v1: 400 trades/month (too high)
- v2: ~88 trades/month for SPY (still not matching 23.5% signal frequency)

#### Issue 3: Feature Calculation Methodology Mismatch
The research features were calculated using specific lookback windows and aggregation methods that we haven't precisely replicated.

---

## Root Cause Analysis

The research used a specific feature engineering pipeline from Phase 2 that includes:
1. `effort_result_mean` - aggregated over specific window
2. `range_ratio_mean` - aggregated over specific window
3. `volatility_ratio_mean` - aggregated over specific window
4. `trade_intensity_mean` - aggregated over specific window
5. `body_position_mean` (SPY/QQQ) OR `autocorr_10_mean` (IWM)

**We need to extract the EXACT feature calculation code from the research scripts.**

---

## Recommended Next Steps

### Option A: Extract Research Feature Pipeline
1. Find the Phase 2 feature engineering script in `research/blind_backwards_analysis/`
2. Extract the exact calculation methods
3. Port to `src/vol_expansion_features.py`
4. Re-run validation

### Option B: Use Pre-Computed Feature Files
1. Use the `*_features.parquet` files from research outputs
2. These contain the EXACT features used for clustering
3. Merge with price data and run backtest

### Option C: Investigate SPY Further
Focus on SPY since it doesn't use autocorr:
- The 35% hit rate vs 58% expected suggests fundamental feature mismatch
- Need to compare our calculated features to the research feature files

---

## Files Changed

1. `src/vol_expansion_features.py` - Added `calculate_effort_result()` for raw values
2. `test/vol_expansion/validate_backtest_v2.py` - Corrected backtest script

---

## Conclusion

The v2.0 fixes addressed obvious issues (ATR, VIX, raw vs z-score) but the fundamental feature calculation methodology still doesn't match the research. 

**We need to directly compare our calculated features to the research feature files to identify the exact discrepancy.**
