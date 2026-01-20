# Development Scripts - Final Analysis with Confidence Ratings

**Date**: 2026-01-18  
**Files Analyzed**: 34 (`test_*.py` excluded - already categorized)

---

## Executive Summary

**After detailed review:**

| Category | Total | ARCHIVE | KEEP | Review Decision |
|----------|-------|---------|------|-----------------|
| batch_test_*.py (docs/operations) | 6 | 6 | 0 | Archive - old validation tests, superseded by Perturbations |
| batch_test_*.py (new_strategy_builds) | 3 | 3 | 0 | Archive - development tests |
| analyze_*.py | 12 | 12 | 0 | Archive - all are analysis scripts for old strategies |
| debug_*.py | 7 | 7 | 0 | Archive - all are debugging/diagnostic scripts |
| check_*.py | 6 | 6 | 0 | Archive - all are data validation scripts |
| **TOTAL** | **34** | **34** | **0** | **100% can be safely archived** |

---

## Key Findings from File Review

### 1. `main.py` Analysis

**What production code actually uses:**
- **Imports**: `src/data_handler`, `src/features`, `src/discovery`, `src/validation`, `src/pnl_tracker`, `src/logger`, `src/backtester_pro`, `src/executor`, `src/optimizer`, `src/config_loader`, `src/hangar`
- **NO imports** from `research/` folder for strategies
- **NO imports** from any of these batch/analyze/debug scripts
- Trading logic is built into `main.py` directly with RSI Hysteresis
- Strategies appear to be configured via `config/nodes/master_config.json`

**Conclusion**: The batch_test, analyze, debug, and check scripts are **NOT used by production code**.

### 2. batch_test_*.py in docs/operations/strategies/

**Files:**
1. `batch_test_strategy1_mag7.py` - Tests Daily Trend on MAG7
2. `batch_test_strategy1_etf_crypto.py` - Tests Daily Trend on ETFs
3. `batch_test_strategy2_hourly_equities.py` - Tests Hourly Swing
4. `batch_test_strategy2_hourly_futures.py` - Tests Hourly Swing on futures
5. `batch_test_strategy3_earnings.py` - Tests Earnings straddles
6. `batch_test_strategy4_fomc.py` - Tests FOMC straddles

**Purpose**: Old validation tests from the original strategy documentation phase  
**Status**: SUPERSEDED by `research/Perturbations/` tests  
**Confidence**: **10/10 - Safe to archive**

**Rationale**:
- These duplicate testing done in Perturbations folder
- Located in `/docs/operations/` which is documentation, not production code
- Use simplified backtest logic (less sophisticated than Perturbations tests)
- Results are saved to local `batch_results/` folder (not referenced anywhere)

### 3. analyze_*.py Files (12 total)

**All HIGH CONFIDENCE (9-10/10) for archival:**

| File | Location | Purpose | Archive? |
|------|----------|---------|----------|
| analyze_congressional_trades.py | alternative_data/ | Alternative data experiment | ✅ YES |
| analyze_earnings.py | backtests/options/ | Old earnings analysis | ✅ YES |
| analyze_nvda.py | backtests/options/ | Old NVDA analysis | ✅ YES |
| analyze_premium_selling.py | backtests/options/ | Old premium selling analysis | ✅ YES |
| analyze_system3.py | backtests/options/ | Old system analysis | ✅ YES |
| analyze_system4.py | backtests/options/ | Old system analysis | ✅ YES |
| analyze_regimes.py | backtests/options/phase3/ | Old regime analysis | ✅ YES |
| analyze_2024_results.py | high_frequency/ | HFT analysis | ✅ YES |
| analyze_entry_times.py | new_strategy_builds/ | ORB development analysis | ✅ YES |
| analyze_ghost_trades.py | new_strategy_builds/ | ORB debugging analysis | ✅ YES |
| analyze_paradox_clean.py | new_strategy_builds/ | ORB paradox investigation | ✅ YES |
| analyze_winrate_paradox.py | new_strategy_builds/ | ORB winrate investigation | ✅ YES |

**All are one-off analysis scripts for historical strategy development.**

### 4. debug_*.py Files (7 total)

**All HIGH CONFIDENCE (8-10/10) for archival:**

| File | Location | Purpose | Archive? |
|------|----------|---------|----------|
| debug_q1_discrepancy.py | high_frequency/ | HFT debugging | ✅ YES |
| debug_data_fetch.py | new_strategy_builds/ | Data fetching debug | ✅ YES |
| debug_fmp_api.py | new_strategy_builds/ | API debugging | ✅ YES |
| debug_futures_zero_trades.py | new_strategy_builds/ | Futures debugging | ✅ YES |
| debug_nvda.py | Perturbations/ | NVDA diagnostic | ✅ YES |
| debug_fmp_calendar.py | docs/operations/.../earnings_straddles/ | Calendar data debug | ✅ YES |
| debug_futures.py | docs/operations/.../crypto_validation/ | Crypto futures debug | ✅ YES |

**Even those in docs/operations are just diagnostic scripts for historical validation work.**

### 5. check_*.py Files (6 total)

**All HIGH CONFIDENCE (9-10/10) for archival:**

| File | Location | Purpose | Archive? |
|------|----------|---------|----------|
| check_nvda_rsi.py | backtests/options/ | RSI calculation verification | ✅ YES |
| check_alpaca_commodities.py | new_strategy_builds/ | Data availability check | ✅ YES |
| check_cached_data.py | new_strategy_builds/ | Cache diagnostic | ✅ YES |
| check_daily_data.py | new_strategy_builds/ | Data validation | ✅ YES |
| check_futures_data.py | new_strategy_builds/ | Futures data check | ✅ YES |
| check_hourly_data.py | new_strategy_builds/ | Hourly data check | ✅ YES |

**All are temporary data validation scripts.**

---

## Archival Plan for Development Scripts

### Immediate Actions

```bash
# 1. Archive all batch test scripts from docs/operations
mkdir -p archive/documentation/old_validation_tests
mv docs/operations/strategies/batch_test_*.py archive/documentation/old_validation_tests/

# 2. Archive analyze scripts (with their parent folders already being archived)
# These will be archived when we move their parent folders:
# - research/alternative_data/ → archive/research_archive/
# - research/backtests/ → archive/research_archive/
# - research/high_frequency/ → archive/research_archive/
# - research/new_strategy_builds/analyze_*.py → archive/strategy_development/

# 3. Archive debug scripts (same - will be archived with parent folders)

# 4. Archive check scripts (same - will be archived with parent folders)
```

---

## Summary: What's Actually Used in Production?

### ✅ Production Code (`main.py` imports these):

**Core Infrastructure** (`src/`):
- data_handler.py
- features.py
- discovery.py
- validation.py
- pnl_tracker.py
- logger.py
- backtester_pro.py
- executor.py
- optimizer.py
- config_loader.py
- hangar.py
- options/* (for options strategies)

**Configuration**:
- config/nodes/master_config.json

**No strategy .py files from research/** are imported by production!

### ❌ NOT Used in Production:

- ALL 78 test_*.py files (except 9 in Perturbations for validation)
- ALL 34 development scripts (batch/analyze/debug/check)
- Total: **103 Python files safe to archive**

---

## Final Cleanup Statistics

### Development Scripts
-  **Total**: 34 files
- **Archive**: 34 files (100%)
- **Keep**: 0 files

### Combined with Test Files
- **Test files**: 78 total, 69 to archive
- **Dev scripts**: 34 total, 34 to archive
- **TOTAL**: 112 total, **103 to archive** (92%)

---

## Next Steps

1. ✅ Test files categorized (69/78 to archive)
2. ✅ Development scripts categorized (34/34 to archive)
3. ⏭️ **Next**: Analyze the "OTHER" category (171 files) - the real mystery files
4. ⏭️ **Then**: Look at actual strategy .py files to find which ones are deployed

**Ready to proceed with analyzing the "OTHER" category?**
