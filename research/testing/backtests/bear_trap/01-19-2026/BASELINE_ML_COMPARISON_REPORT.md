# Baseline vs ML Comparison Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01  
**ML Model:** Bear Trap Disaster Filter (XGBoost + Isotonic Calibration)

---

## Executive Summary

| Metric | Baseline | ML-Enhanced | Change |
|--------|----------|-------------|--------|
| **Total PnL** | +135.6% | +151.6% | +12% |
| **Total Trades** | 1290 | 963 | -327 filtered |
| **Beneficial Symbols** | - | 7/9 | 78% |

**Overall Status:** ⚠️ REVIEW REQUIRED

---

## Validation Criteria

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Baseline Profitable | Yes | Yes | ✅ |
| ML Improvement | ≥100% | 12% | ❌ |
| Symbols Benefiting | ≥60% | 78% | ✅ |

---

## Per-Symbol Breakdown

| Symbol | Baseline PnL | ML PnL | Improvement | Trades Filtered | Beneficial? |
|--------|-------------|--------|-------------|-----------------|-------------|
| MULN | +30.0% | +35.1% | +17% | 147 | ✅ |
| ONDS | +25.9% | +33.7% | +30% | 16 | ✅ |
| NKLA | +19.4% | +15.3% | -21% | 35 | ⚠️ |
| ACB | +7.7% | +9.7% | +25% | 8 | ✅ |
| AMC | +18.1% | +21.7% | +20% | 39 | ✅ |
| GOEV | -0.1% | +0.6% | +597% | 46 | ✅ |
| SENS | +9.1% | +10.4% | +15% | 6 | ✅ |
| BTCS | +5.4% | +6.0% | +10% | 11 | ✅ |
| WKHS | +20.1% | +19.1% | -5% | 19 | ⚠️ |

---

## Key Insights

### Biggest Winners from ML
- **GOEV**: -0.1% → +0.6% (+597%)
- **ONDS**: +25.9% → +33.7% (+30%)
- **ACB**: +7.7% → +9.7% (+25%)

### Symbols with Limited ML Benefit
- **WKHS**: +20.1% → +19.1% (-5%)
- **NKLA**: +19.4% → +15.3% (-21%)

---

## Interpretation

- **Baseline Strategy:** The non-ML Bear Trap strategy is profitable with +135.6% total return.
- **ML Enhancement:** The disaster filter marginally affects performance with +12% improvement.
- **Trade Filtering:** ML filtered 327 trades (25% of baseline), indicating effective disaster avoidance.

---

## Conclusion

The ML enhancement shows mixed results.

**Recommendation:** ⚠️ Further analysis recommended
