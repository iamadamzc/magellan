# K-Fold Cross-Validation Report - Bear Trap Strategy

**Date:** 2026-01-19  
**Test Period:** 2022-01-01 to 2025-01-01

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Core Symbols** | 9 |
| **New Test Symbols** | 5 |
| **Overall Status** | ✅ PASS |

---

## Test 1: Leave-One-Out Cross-Validation

**Objective:** Verify strategy remains profitable when each symbol is excluded.

| Holdout Symbol | Fold PnL | Status |
|----------------|----------|--------|
| MULN | +105.61% | ✅ PASS |
| ONDS | +109.63% | ✅ PASS |
| NKLA | +116.22% | ✅ PASS |
| ACB | +127.84% | ✅ PASS |
| AMC | +117.46% | ✅ PASS |
| GOEV | +135.69% | ✅ PASS |
| SENS | +126.49% | ✅ PASS |
| BTCS | +130.15% | ✅ PASS |
| WKHS | +115.50% | ✅ PASS |

**Positive Folds:** 9/9  
**Status:** ✅ PASS

---

## Test 2: Leave-Two-Out Cross-Validation

**Objective:** Verify robustness when pairs of symbols are excluded.

| Holdout Pair | Fold PnL | Status |
|--------------|----------|--------|
| GOEV, BTCS | +130.27% | ✅ |
| ONDS, WKHS | +89.56% | ✅ |
| ONDS, NKLA | +90.27% | ✅ |
| ACB, WKHS | +107.77% | ✅ |
| ONDS, SENS | +100.54% | ✅ |
| MULN, ACB | +97.87% | ✅ |
| NKLA, BTCS | +110.80% | ✅ |
| BTCS, WKHS | +110.08% | ✅ |
| ACB, AMC | +109.72% | ✅ |
| NKLA, AMC | +98.10% | ✅ |

**Positive Folds:** 10/10

---

## Test 3: Symbol Dependency

**Objective:** No single symbol should drive > 40% of total PnL.

| Symbol | PnL | Contribution |
|--------|-----|--------------|
| MULN | +29.97% | 22.1%  |
| ONDS | +25.94% | 19.1%  |
| WKHS | +20.07% | 14.8%  |
| NKLA | +19.36% | 14.3%  |
| AMC | +18.12% | 13.4%  |
| SENS | +9.09% | 6.7%  |
| ACB | +7.73% | 5.7%  |
| BTCS | +5.42% | 4.0%  |
| GOEV | -0.12% | -0.1%  |

---

## Test 4: Universe Expansion

**Objective:** Edge should generalize to ≥3 of 5 new similar symbols.

| Symbol | PnL | Trades | Status |
|--------|-----|--------|--------|
| RIOT | -2.14% | 21 | ❌ Unprofitable |
| MARA | +4.30% | 89 | ✅ Profitable |
| CLSK | +13.97% | 64 | ✅ Profitable |
| SNDL | +1.60% | 31 | ✅ Profitable |
| PLUG | +1.05% | 51 | ✅ Profitable |

**Profitable New Symbols:** 4/5  
**Status:** ✅ PASS

---

## Conclusion

The Bear Trap strategy shows robust cross-validated performance across the symbol universe.

**Recommendation:** ✅ Symbol universe validated
