# Monte Carlo Simulation Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01  
**Simulations per Symbol:** 1,000

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Symbols Tested** | 14 |
| **Pass Rate** | 21.4% (3/14) |
| **Overall Status** | ❌ FAIL |

---

## Pass/Fail Criteria

| Criterion | Threshold | Description |
|-----------|-----------|-------------|
| 95% CI Lower Bound | > 0% | Bootstrap confidence interval must be positive |
| Sharpe Pass Rate | ≥ 90% | Sharpe > 0.5 in 90%+ of shuffled simulations |
| Luck Factor | < 40% | Less than 40% of shuffled runs beat baseline |

---

## Symbol Results

| Symbol | Baseline PnL | 95% CI Lower | Sharpe Pass Rate | Luck Factor | Status |
|--------|-------------|--------------|-----------------|-------------|--------|
| MULN | 30.0% | 2.6% | 100% | 0% | ✅ PASS |
| ONDS | 25.9% | 0.3% | 100% | 0% | ✅ PASS |
| NKLA | 19.4% | -3.2% | 100% | 0% | ❌ FAIL |
| ACB | 7.7% | -3.1% | 100% | 0% | ❌ FAIL |
| AMC | 18.1% | 0.6% | 100% | 0% | ✅ PASS |
| GOEV | -0.1% | -12.0% | 0% | 0% | ❌ FAIL |
| SENS | 9.1% | -7.7% | 0% | 0% | ❌ FAIL |
| BTCS | 5.4% | -2.5% | 100% | 0% | ❌ FAIL |
| WKHS | 20.1% | -0.5% | 100% | 0% | ❌ FAIL |
| RIOT | -2.1% | -4.4% | 0% | 100% | ❌ FAIL |
| MARA | 4.3% | -0.6% | 100% | 0% | ❌ FAIL |
| CLSK | 14.0% | -1.5% | 100% | 0% | ❌ FAIL |
| SNDL | 1.6% | -5.0% | 0% | 0% | ❌ FAIL |
| PLUG | 1.0% | -0.9% | 0% | 0% | ❌ FAIL |

---

## Interpretation

- **95% CI Lower > 0:** The strategy shows statistically significant positive returns with 21% confidence.
- **Sharpe Pass Rate:** Measures consistency - high rates indicate robust risk-adjusted returns.
- **Luck Factor:** Low values indicate skill-based edge rather than lucky trade sequencing.

---

## Conclusion

The strategy shows mixed results under Monte Carlo stress testing.

**Recommendation:** ⚠️ Further investigation recommended
