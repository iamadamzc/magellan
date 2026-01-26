# Volatility Expansion Strategy - Testing Summary

**Date**: January 25, 2026  
**Status**: 🔴 **EXIT LOGIC ISSUE IDENTIFIED**

---

## Executive Summary

After extensive testing, we have identified that the root cause of the performance gap is **the exit logic** (target/stop placement), NOT the feature calculation or entry signals.

---

## Test Results Summary

### Test 1: v1 Backtest (Wrong Features)
- Hit Rate: 42% (Expected: 58%)
- Issue: Feature calculation mismatch

### Test 2: Golden Source v1 (Raw Thresholds)
- Signal Frequency: 0.6% (Expected: 23.5%)
- Issue: Thresholds require standardization

### Test 3: Golden Source v2 (Scaled Thresholds)
- Signal Frequency: 0% 
- Issue: Scaler fitted on different population

### Test 4: Golden Source v3 (Cluster Assignment)
- **Signal Frequency: ~23% ✅** (Matches research!)
- Hit Rate: ~37% (vs cluster in-sample: ~58%)
- **Exit Breakdown:**
  - STOP_LOSS: 62.5% of exits (0% win rate)
  - TARGET_HIT: 36% of exits (100% win rate)
  - TIME_STOP: 1.5% of exits (74% win rate)

---

## Root Cause Analysis

### ✅ What Works:
1. **Feature Calculation** - Golden source features are correct
2. **Cluster Assignment** - Signal frequency matches research (~23%)
3. **Target Hits** - When targets hit, they're profitable

### ❌ What's Broken:
1. **Stop Loss Placement** - Too tight, hitting 62% of the time
2. **Asymmetric R:R** - 2.5 ATR target / 1.25 ATR stop = bad fill order

---

## The Problem with Exit Logic

The research reported win rates based on **cluster membership**, which only indicates the pattern is present. It does NOT simulate actual exits.

When we simulate with real exit logic:
- **2.5 ATR target** = Price must move 2.5x volatility UP
- **1.25 ATR stop** = Price must NOT drop 1.25x volatility FIRST

In reality, minute-by-minute price action often touches the stop BEFORE reaching the target, even if the overall direction is correct.

---

## Recommended Fixes

### Option 1: Widen Stop Loss
```python
# Current (fails):
target = entry + 2.5 * ATR  # 2.5x ATR target
stop = entry - 1.25 * ATR   # 1.25x ATR stop

# Fix (wider stop):
target = entry + 2.0 * ATR  # 2.0x ATR target  
stop = entry - 2.0 * ATR     # 2.0x ATR stop (1:1 R:R)
```

### Option 2: Trailing Stop
```python
# Use trailing stop instead of fixed stop
trailing_stop = max(entry - 2*ATR, highest_since_entry - 1*ATR)
```

### Option 3: Time-Based Only
```python
# No stop loss, just time exit
if bars_since_entry >= 30:
    exit("TIME")
```

### Option 4: Cluster-Based Exit
```python
# Exit when no longer in winning cluster
if not in_best_cluster(current_features):
    exit("SIGNAL_LOST")
```

---

## Next Steps

1. **Re-test with wider stops** (2x ATR or 3x ATR)
2. **Test trailing stop** approach
3. **Validate on OOS** after exit fix
4. **Paper trade** if OOS validates

---

## Files Created

| File | Purpose |
|------|---------|
| `validate_backtest.py` | Initial v1 backtest |
| `validate_backtest_v2.py` | Fixed ATR, research thresholds |
| `validate_golden_source.py` | Raw golden source test |
| `validate_golden_source_v2.py` | Scaled thresholds test |
| `validate_golden_source_v3.py` | Cluster assignment test |
| `THRESHOLD_MISMATCH_FINDING.md` | Scaling discovery |
| `BACKTEST_FINDINGS.md` | Results documentation |

---

## Conclusion

The Volatility Expansion Entry **pattern detection works correctly**. The failure is in the **exit logic** - specifically the stop loss is too tight for the actual price volatility, causing 62% of trades to hit stops before targets.

**Recommendation**: Test with 2:1 or 3:1 stop ratio (stop = 2-3x ATR) instead of 1.25x ATR.
