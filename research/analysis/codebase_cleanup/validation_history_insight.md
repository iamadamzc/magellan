# Critical Insight: Validation History & Code Traceability

**Date**: 2026-01-18  
**Key Finding**: `/docs/operations` is NOT superseded - it's validation history

---

## Understanding the Validation Journey

### The Path to Deployment

```
Step 1: docs/operations/strategies/
├── Initial validation & WFA testing
├── Clean room testing environment
├── Each strategy folder with validation artifacts
└── batch_test_*.py files for each strategy

Step 2: research/Perturbations/
├── Final perturbation testing framework
├── ALL tests passed with NO code changes
├── Validates deployment robustness
└── Contains deployment-ready strategy implementations

Step 3: Deployment
└── Strategies validated by Perturbations are production-ready
```

---

## Critical Understanding

**Perturbations tests passed with NO code changes**

This means:
1. ✅ The strategy `.py` files in `research/Perturbations/` ARE the validated implementations
2. ✅ `/docs/operations` documents the validation process that led there
3. ✅ This is **historical validation artifacts** - KEEP for audit trail
4. ❌ The batch_test files in docs/operations are NOT production code, but validation history

---

## Revised Classification

### ✅ KEEP - Validation History & Audit Trail

**Location**: `/docs/operations/strategies/`

**Contents**:
- Clean room WFA test documentation
- Batch validation tests (strategy logic embedded in test files)
- Strategy-specific validation folders:
  - `daily_trend_hysteresis/` (48 files)
  - `hourly_swing/` (28 files)
  - `fomc_event_straddles/` (15 files)
  - `earnings_straddles/` (29 files)
- Master reports showing validation path

**Value**:
- Documents the rigorous validation process
- Shows the path from concept → validation → deployment
- Audit trail for regulatory compliance
- Reference for future strategy development

**Action**: ✅ **KEEP ENTIRELY** - This is part of your intellectual property and validation rigor documentation

---

## Actual Production Strategy Code

Since Perturbations passed with no changes, the **deployed strategy implementations** are:

### ✅ Validated Strategy Files (Production Code)

```
research/Perturbations/
├── bear_trap/
│   └── bear_trap.py                    ← PRODUCTION (297 lines)
│
├── GSB/
│   └── gsb_strategy.py                 ← PRODUCTION (206 lines, ORB V23)
│
├── daily_trend_hysteresis/
│   └── (strategy logic embedded in test_friction_sensitivity.py)
│
├── hourly_swing/
│   └── (strategy logic embedded in test_gap_reversal.py)
│
├── fomc_straddles/
│   └── (strategy logic embedded in test_bid_ask_spread.py)
│
└── earnings_straddles/
    └── (strategy logic embedded in test_regime_normalization.py)
```

**Note**: Some strategies have logic embedded in test files (Daily Trend, Hourly Swing, FOMC, Earnings).  
Others have separate strategy files (Bear Trap, GSB).

---

## What Can Be Archived

### 🗑️ Development Iterations (NOT the validated versions)

**Location**: `research/new_strategy_builds/`

This folder has **development iterations** and earlier versions:
- 47 files in `strategies/` subfolder
- Multiple ORB versions (v13-v23)
- Bear Trap development files (duplicates of validated Perturbations version)
- Analysis and debugging scripts

**These are superseded by** the validated versions in `research/Perturbations/`

---

## Next Steps for Code Discovery

1. ✅ Keep `/docs/operations/` as validation history
2. ✅ Identify validated strategy files in `research/Perturbations/`
3. ⏭️ Cross-reference with `research/new_strategy_builds/strategies/` to find duplicates
4. ⏭️ Archive development iterations from `new_strategy_builds`
5. ⏭ ️ Keep only validated versions

---

## Updated Cleanup Plan

### KEEP (Validation & Production)
- `/docs/operations/` - Entire folder (validation history)
- `research/Perturbations/` - Entire folder (validated strategies + tests)
- `src/` - All production infrastructure

### ARCHIVE (Development Iterations)
- `research/new_strategy_builds/strategies/` - Development versions
- `research/new_strategy_builds/test_*.py` - Development tests
- `research/backtests/` - Old backtest experiments
- `research/high_frequency/` - Failed HFT experiments
- Root `test_*.py` files - ORB iteration tests

---

**Thank you for the clarification! This completely changes the archival strategy for `/docs/operations`.**

---

## Options Module Usage Discovery

**Found**: FOMC and Earnings strategies DO use `src/options/`:

**In validation history** (`docs/operations/strategies/`):
- `fomc_event_straddles/backtest.py` imports `OptionsFeatureEngineer`
- `earnings_straddles/backtest.py` imports `OptionsFeatureEngineer`
- `earnings_straddles/backtest_portfolio.py` imports `OptionsFeatureEngineer`

**Required src/options/ files:**
- ✅ `src/options/__init__.py` (package marker)
- ✅ `src/options/features.py` (OptionsFeatureEngineer - USED)
- ✅ `src/options/data_handler.py` (likely imported by features.py)
- ✅ `src/options/utils.py` (likely imported by features.py)
