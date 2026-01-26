# CRITICAL FINDING: Threshold Mismatch Diagnosis

## Problem Identified

The FINAL_STRATEGY_RESULTS.json thresholds are in **STANDARDIZED (z-score) space**, not raw feature values!

## Evidence

From `strategy_synthesis.py` lines 67-83:
```python
# Scale features FIRST
all_feature_cols = [c for c in features_df.columns if '_mean' in c or '_std' in c]
X_full = features_df[all_feature_cols].fillna(0).values
X_scaled = scaler.transform(X_full)  # <-- STANDARDIZED!

# Apply rules to SCALED values
if rule['operator'] == '>':
    signals &= X_scaled[:, idx] > rule['threshold']  # <-- Threshold is in standardized space!
```

## Why This Matters

- **Threshold in JSON**: `effort_result_mean < -43.99` (standardized value)
- **Raw data mean**: `-32.4` (raw value)
- **We applied standardized threshold to raw data** = Wrong comparison

## The Fix

We need to either:
1. Apply the same StandardScaler to our raw features before comparing
2. OR reverse-engineer the raw thresholds from the standardized ones

## Golden Source Test Results

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Signal Frequency | 23.5% | **0.6%** | ❌ 40x fewer signals |
| Hit Rate | 57.9% | 36.0% | ❌ -22pp |
| Total Trades | ~197k | 5,347 | ❌ 40x fewer |

## Root Cause Confirmed

**The entry thresholds require standardization.** The research used `sklearn.StandardScaler` 
to normalize features before applying Boolean logic.

## Next Steps

1. Load or recreate the StandardScaler used in research
2. Apply scaler.transform() to features before threshold comparison
3. Re-run golden source validation with scaled features

## Code Fix Required

```python
# BEFORE (Wrong):
if row['effort_result_mean'] < -43.99:  # Raw comparison
    signal = True

# AFTER (Correct):
scaled_row = scaler.transform(row[feature_cols])  # Standardize first
if scaled_row[effort_idx] < threshold:  # Then compare
    signal = True
```
