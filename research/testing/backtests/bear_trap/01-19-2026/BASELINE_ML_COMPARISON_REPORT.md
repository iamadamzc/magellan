# Baseline vs ML Comparison Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01  
**ML Model:** Bear Trap Disaster Filter (XGBoost + Isotonic Calibration)

---

## Executive Summary

| Metric | Baseline | ML-Enhanced | Change |
|--------|----------|-------------|--------|
| **Total PnL** | +135.6% | +135.6% | +0% |
| **Total Trades** | 1290 | 1290 | -0 filtered |
| **Beneficial Symbols** | - | 0/9 | 0% |

**Overall Status:** ⚠️ REVIEW REQUIRED

---

## Validation Criteria

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Baseline Profitable | Yes | Yes | ✅ |
| ML Improvement | ≥100% | 0% | ❌ |
| Symbols Benefiting | ≥60% | 0% | ⚠️ |

---

## Per-Symbol Breakdown

| Symbol | Baseline PnL | ML PnL | Improvement | Trades Filtered | Beneficial? |
|--------|-------------|--------|-------------|-----------------|-------------|
| MULN | +30.0% | +30.0% | +0% | 0 | ⚠️ |
| ONDS | +25.9% | +25.9% | +0% | 0 | ⚠️ |
| NKLA | +19.4% | +19.4% | +0% | 0 | ⚠️ |
| ACB | +7.7% | +7.7% | +0% | 0 | ⚠️ |
| AMC | +18.1% | +18.1% | +0% | 0 | ⚠️ |
| GOEV | -0.1% | -0.1% | +0% | 0 | ⚠️ |
| SENS | +9.1% | +9.1% | +0% | 0 | ⚠️ |
| BTCS | +5.4% | +5.4% | +0% | 0 | ⚠️ |
| WKHS | +20.1% | +20.1% | +0% | 0 | ⚠️ |

---

## Key Insights

### Biggest Winners from ML
- **MULN**: +30.0% → +30.0% (+0%)
- **ONDS**: +25.9% → +25.9% (+0%)
- **NKLA**: +19.4% → +19.4% (+0%)

### Symbols with Limited ML Benefit
- **BTCS**: +5.4% → +5.4% (+0%)
- **WKHS**: +20.1% → +20.1% (+0%)

---

## Interpretation

- **Baseline Strategy:** The non-ML Bear Trap strategy is profitable with +135.6% total return.
- **ML Enhancement:** The disaster filter marginally affects performance with +0% improvement.
- **Trade Filtering:** ML filtered 0 trades (0% of baseline), indicating effective disaster avoidance.

---

## Conclusion

The ML enhancement shows mixed results.

**Recommendation:** ⚠️ Further analysis recommended
