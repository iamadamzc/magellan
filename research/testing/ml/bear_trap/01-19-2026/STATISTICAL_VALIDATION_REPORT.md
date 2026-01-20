# Statistical Significance Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Symbols Tested** | 14 |
| **T-test Pass Rate** | 21.4% (3/14) |
| **Profit Factor Pass Rate** | 14.3% (2/14) |
| **Overall Pass Rate** | 14.3% (2/14) |

---

## Pass/Fail Criteria

| Test | Criterion | Threshold |
|------|-----------|-----------|
| T-test vs Zero | Mean return > 0 | p < 0.05 |
| Profit Factor | 95% CI > 1.0 | Lower bound not crossing 1.0 |
| Win Rate | Better than random | p < 0.05 |

---

## Aggregate Statistics


| Metric | Value |
|--------|-------|
| **Total Trades** | 1,546 |
| **Mean Trade PnL** | -0.013% |
| **Std Trade PnL** | 0.227% |
| **Aggregate T-stat** | -2.20 |
| **Aggregate P-value** | 0.9859 |
| **Aggregate Profit Factor** | 0.85 |
| **Aggregate Win Rate** | 42.2% |


---

## Symbol Results

| Symbol | Trades | PnL % | p-value | Profit Factor | PF CI | Status |
|--------|--------|-------|---------|---------------|-------|--------|
| MULN | 588 | 30.0% | 0.002 | 1.29 | [1.08, 1.52] | ✅ PASS |
| ONDS | 61 | 25.9% | 0.010 | 1.93 | [1.19, 3.24] | ✅ PASS |
| NKLA | 140 | 19.4% | 0.204 | 1.16 | [0.81, 1.62] | ❌ FAIL |
| ACB | 29 | 7.7% | 0.370 | 1.14 | [0.50, 2.54] | ❌ FAIL |
| AMC | 153 | 18.1% | 0.034 | 1.37 | [0.98, 1.96] | ❌ FAIL |
| GOEV | 182 | -0.1% | 1.000 | 0.36 | [0.26, 0.50] | ❌ FAIL |
| SENS | 22 | 9.1% | 0.561 | 0.93 | [0.32, 2.13] | ❌ FAIL |
| BTCS | 42 | 5.4% | 0.640 | 0.89 | [0.45, 1.66] | ❌ FAIL |
| WKHS | 73 | 20.1% | 0.060 | 1.49 | [0.95, 2.40] | ❌ FAIL |
| RIOT | 21 | -2.1% | 0.998 | 0.24 | [0.07, 0.58] | ❌ FAIL |
| MARA | 89 | 4.3% | 0.179 | 1.24 | [0.79, 1.93] | ❌ FAIL |
| CLSK | 64 | 14.0% | 0.161 | 1.31 | [0.78, 2.14] | ❌ FAIL |
| SNDL | 31 | 1.6% | 0.999 | 0.28 | [0.06, 0.63] | ❌ FAIL |
| PLUG | 51 | 1.0% | 0.775 | 0.79 | [0.39, 1.41] | ❌ FAIL |

---

## Interpretation

- **T-test p-value < 0.05:** Strategy returns are statistically significantly greater than zero.
- **Profit Factor CI > 1.0:** With 95% confidence, gross profits exceed gross losses.
- **Win Rate Test:** Tests if win rate is significantly better than 50% (random).

---

## Conclusion

The strategy shows mixed statistical significance.

**Recommendation:** ⚠️ Requires further analysis
