# ML Model Stability Report - Bear Trap Disaster Filter

**Date:** 2026-01-19  
**Model:** bear_trap_disaster_filter.pkl

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Tests Passed** | 4/4 (100%) |
| **Overall Status** | ✅ PASS |

---

## Test 1: Temporal Decay

**Objective:** Verify model performance doesn't degrade significantly over time.

| Quarter | PnL |
|---------|-----|
| Q1_2024 | $13,771 |
| Q2_2024 | $14,133 |
| Q3_2024 | $12,571 |
| Q4_2024 | $13,822 |

**Decay Rate:** -0.4%  
**Status:** ✅ PASS

---

## Test 2: Calibration Drift

**Objective:** Verify model probability predictions remain accurate.

| Quarter | Brier Score | ECE |
|---------|-------------|-----|
| Q1_2024 | 0.181 | 0.039 |
| Q2_2024 | 0.199 | 0.028 |
| Q3_2024 | 0.209 | 0.026 |
| Q4_2024 | 0.194 | 0.062 |

**Calibration Drift:** +0.013  
**Status:** ✅ PASS

---

## Test 3: Feature Importance Stability

**Objective:** Verify top features remain consistent.

| Feature | Quarters in Top 3 |
|---------|-------------------|
| day_change_pct | 3/4 |
| wick_ratio | 3/4 |
| vwap_distance | 2/4 |
| atr | 2/4 |
| hour | 1/4 |

**Stability Rate:** 67%  
**Status:** ✅ PASS

---

## Test 4: Extended Threshold Sensitivity

**Objective:** Confirm baseline thresholds (0.6/0.4) are optimal.

| Config | AM | PM | PnL | vs Baseline |
|--------|----|----|-----|-------------|
| Relaxed- | 0.55 | 0.35 | $45,493 | -15.0% |
| Baseline | 0.6 | 0.4 | $53,521 | +0.0% |
| Strict+ | 0.65 | 0.45 | $47,098 | -12.0% |
| Very Strict | 0.7 | 0.5 | $38,535 | -28.0% |

**Baseline Optimal:** Yes  
**Graceful Degradation:** Yes  
**Status:** ✅ PASS

---

## Conclusion

The ML disaster filter shows stable performance across time periods and threshold variations.

**Recommendation:** ✅ Model stable for production
