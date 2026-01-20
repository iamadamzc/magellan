# Drawdown & Recovery Analysis Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Symbols Tested** | 9 |
| **Pass Rate** | 22.2% (2/9) |
| **Avg Max Drawdown** | 22.7% |
| **Avg Calmar Ratio** | 0.74 |
| **Avg Ulcer Index** | 11.8 |

---

## Pass/Fail Criteria

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Max Drawdown | < 30% | Worst peak-to-trough decline |
| Calmar Ratio | > 1.0 | Annualized return / max drawdown |
| Ulcer Index | < 15 | Severity of drawdown periods |
| Recovery Time | < 60 days | Avg days to recover from DD |

---

## Symbol Results

| Symbol | PnL % | Max DD | Calmar | Ulcer | Recovery Days | Status |
|--------|-------|--------|--------|-------|---------------|--------|
| MULN | 30.0% | 26.8% | 0.26 | 11.2 | 56 | ❌ FAIL |
| ONDS | 25.9% | 12.6% | 0.66 | 5.9 | 57 | ❌ FAIL |
| NKLA | 19.4% | 1.8% | 3.73 | 0.6 | 23 | ✅ PASS |
| ACB | 7.7% | 9.6% | 0.22 | 4.9 | 118 | ❌ FAIL |
| AMC | 18.1% | 26.6% | 0.10 | 15.6 | 102 | ❌ FAIL |
| GOEV | -0.1% | 0.1% | -0.29 | 0.1 | 367 | ❌ FAIL |
| SENS | 9.1% | 1.3% | 2.30 | 0.5 | 74 | ✅ PASS |
| BTCS | 5.4% | 92.6% | -0.36 | 48.7 | 149 | ❌ FAIL |
| WKHS | 20.1% | 33.3% | 0.06 | 18.8 | 335 | ❌ FAIL |

---

## Risk Metrics Explanation

| Metric | Description |
|--------|-------------|
| **Max Drawdown** | Largest peak-to-trough decline in equity |
| **Avg Drawdown** | Average magnitude of all drawdowns |
| **Calmar Ratio** | Risk-adjusted return (higher is better) |
| **Ulcer Index** | Measures pain of holding through drawdowns |
| **Underwater %** | Time spent below previous equity high |

---

## Interpretation

- **Max DD < 30%:** Strategy maintains reasonable risk limits.
- **Calmar > 1.0:** Returns justify the risk taken.
- **Ulcer Index < 15:** Drawdowns are not excessively painful.

---

## Conclusion

Some symbols show elevated drawdown risk.

**Recommendation:** ⚠️ Consider position sizing adjustments
