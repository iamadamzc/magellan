# Regime Stress Test Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Symbols Tested:** 9  
**Regimes Tested:** 4

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Symbols Passing Regime Test** | 7/9 (77.8%) |
| **Overall Status** | ⚠️ PARTIAL |

---

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Profitable in ≥ N regimes | ≥ 3 of 4 |
| Max loss vs best gain | ≤ 50% |

---

## Regime Definitions

| Regime | Period | Description |
|--------|--------|-------------|
| BULL_2021 | 2021-01-01 to 2021-12-31 | Strong bull market, low VIX |
| BEAR_2022 | 2022-01-01 to 2022-12-31 | Bear market, high volatility |
| CHOPPY_2023 | 2023-01-01 to 2023-12-31 | Sideways/choppy market |
| BULL_2024 | 2024-01-01 to 2024-12-31 | Recovery bull market |

---

## Aggregate Performance by Regime

| Regime | Avg PnL | Total Trades | Profitable Symbols |
|--------|---------|--------------|-------------------|
| BULL_2021 | +4.42% | 236 | 7/9 ✅ |
| BEAR_2022 | +3.38% | 298 | 6/9 ✅ |
| CHOPPY_2023 | +5.25% | 503 | 8/9 ✅ |
| BULL_2024 | +7.17% | 516 | 8/9 ✅ |

---

## Symbol Results

| Symbol | BULL_2021 | BEAR_2022 | CHOPPY_2023 | BULL_2024 | Profitable Regimes | Status |
|--------|-----------|-----------|-------------|-----------|-------------------|--------|
| MULN | -3.0% | +14.3% | +2.0% | +15.7% | 3/4 | ✅ PASS |
| ONDS | +8.9% | +8.9% | +6.8% | +11.5% | 4/4 | ❌ FAIL |
| NKLA | +0.1% | +0.0% | +13.4% | +7.1% | 3/4 | ✅ PASS |
| ACB | +1.3% | -4.7% | +11.9% | +1.7% | 3/4 | ✅ PASS |
| AMC | +8.2% | +1.6% | +7.8% | +9.1% | 4/4 | ✅ PASS |
| GOEV | +1.2% | +1.1% | +4.3% | -4.9% | 3/4 | ❌ FAIL |
| SENS | +13.7% | +7.3% | +0.0% | +1.9% | 3/4 | ✅ PASS |
| BTCS | +0.0% | +3.1% | +0.3% | +2.1% | 3/4 | ✅ PASS |
| WKHS | +9.4% | -1.3% | +0.8% | +20.4% | 3/4 | ✅ PASS |

---

## Interpretation

- **Bull Markets (2021, 2024):** Strategy should capture reversals in volatile stocks during uptrends.
- **Bear Market (2022):** Strategy is designed for panic/selloff scenarios - expected to perform well.
- **Choppy Market (2023):** May underperform due to lack of clear directional moves.

---

## Conclusion

The strategy exhibits regime-dependent performance.

**Recommendation:** ⚠️ Consider regime filters
