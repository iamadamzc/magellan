# Complete Production Code Dependency Map

**Date**: 2026-01-18  
**Method**: Traced from main.py + Perturbations strategies

---

## Executive Summary

**Confirmed Production Code:**
- **main.py** - Entry point
- **17 src/ files** - Core infrastructure (81% of src/)
- **4 src/ files** - Need investigation (19% of src/)
- **research/Perturbations/** - All 6 validated strategies
- **docs/operations/** - Validation history (audit trail)

---

## Complete src/ File Analysis

### ✅ DEFINITE KEEP (17 files = 81%)

**Core Infrastructure (used by main.py or strategies):**
1. `src/__init__.py` - Package marker
2. `src/backtester_pro.py` - Rolling backtest engine (main.py)
3. `src/config_loader.py` - Configuration management (main.py, backtester_pro)
4. `src/data_cache.py` ✅ **CRITICAL - Used by ALL 6 strategies!**
5. `src/data_handler.py` - Alpaca/FMP data client (main.py, backtester_pro)
6. `src/discovery.py` - Feature correlation & IC (main.py, backtester_pro)
7. `src/executor.py` - Trade execution (main.py)
8. `src/features.py` - Feature engineering (main.py, backtester_pro)
9. `src/hangar.py` - ORH observation mode (main.py)
10. `src/logger.py` - Logging system (main.py, features)
11. `src/optimizer.py` - Alpha weight optimization (main.py, backtester_pro, validation)
12. `src/pnl_tracker.py` - P&L simulation (main.py, backtester_pro)
13. `src/validation.py` - Walk-forward validation (main.py)

**Options Support (used by FOMC & Earnings validation):**
14. `src/options/__init__.py` - Package marker
15. `src/options/data_handler.py` - Options data handling
16. `src/options/features.py` - OptionsFeatureEngineer (used in docs/operations validation)
17. `src/options/utils.py` - Options utilities

### ⚠️ INVESTIGATE (4 files = 19%)

| File | Possible Purpose | Action |
|------|------------------|--------|
| `src/monday_release.py` | Deployment/release automation? | 🔍 READ |
| `src/monitor.py` | System monitoring/alerting? | 🔍 READ |
| `src/reconcile.py` | Trade reconciliation? | 🔍 READ |
| `src/risk_manager.py` | Risk controls/position limits? | 🔍 READ |

**Recommendation**: Read these 4 files to determine if they're:
- Live trading infrastructure (KEEP)
- Abandoned experiments (ARCHIVE)
- Planned features (KEEP with note)

---

## Import Dependency Chain

### From main.py

```
main.py
├── data_handler (AlpacaDataClient, FMPDataClient, force_resample_ohlcv)
├── features (FeatureEngineer, add_technical_indicators, merge_news_pit, generate_master_signal)
├── discovery (calculate_ic, check_feature_correlation, trim_warmup_period)
├── validation (run_walk_forward_check, run_optimized_walk_forward_check)
│   └── optimizer
├── pnl_tracker (simulate_portfolio, print_virtual_trading_statement)
├── logger (LOG, set_log_level)
├── backtester_pro (run_rolling_backtest, print_stress_test_summary, export_stress_test_results)
│   ├── config_loader
│   ├── data_handler
│   ├── discovery
│   ├── features
│   ├── optimizer
│   └── pnl_tracker
├── executor (async_execute_trade, AlpacaTradingClient)
├── optimizer (calculate_alpha_with_weights)
│   └── config_loader
├── config_loader (EngineConfig)
└── hangar (run_hangar_observation)
```

### From Perturbations Strategies

```
ALL 6 strategies
└── data_cache (cache) ✅ CRITICAL
```

**Strategies using data_cache:**
1. `research/Perturbations/bear_trap/bear_trap.py`
2. `research/Perturbations/GSB/gsb_strategy.py`
3. `research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py`
4. `research/Perturbations/hourly_swing/test_gap_reversal.py`
5. Additional diagnostic files in Perturbations/

### From Validation History (docs/operations)

```
FOMC & Earnings validation tests
└── options/features (OptionsFeatureEngineer)
    ├── options/data_handler (likely)
    └── options/utils (likely)
```

---

## Production Code Locations

### ✅ Core System

| Location | Purpose | Keep? |
|----------|---------|-------|
| `main.py` | Entry point & trading loop | ✅ KEEP |
| `src/` (17 files) | Core infrastructure | ✅ KEEP |
| `config/` | Configuration files | ✅ KEEP |

### ✅ Validated Strategies

| Location | Contains | Keep? |
|----------|----------|-------|
| `research/Perturbations/` | All 6 validated strategies + perturbation tests | ✅ KEEP |
| `docs/operations/` | Validation history & audit trail | ✅ KEEP |

### 🗑️ Development Artifacts

| Location | Contains | Action |
|----------|----------|--------|
| `research/new_strategy_builds/` | ORB development iterations, duplicates | 🗑️ ARCHIVE |
| `research/backtests/` | Old backtest experiments | 🗑️ ARCHIVE |
| `research/high_frequency/` | Failed HFT experiments | 🗑️ ARCHIVE |
| Root `test_*.py` (27 files) | ORB iteration tests | 🗑️ ARCHIVE |
| Various `test_*`, `analyze_*`, `debug_*` scripts (103 total) | Development/debugging scripts | 🗑️ ARCHIVE |

---

## Key Findings

### 1. data_cache.py is CRITICAL
**ALL 6 strategies** import `from src.data_cache import cache`

This was NOT in the coverage report because we only ran backtest harnesses, not the actual strategy files!

### 2. Options module IS used
FOMC and Earnings strategies use `src/options/features.py` (seen in validation history)

### 3. Only 4 src/ files uncertain
Out of 21 src/ files, we've confirmed 17 (81%) are needed.

---

## Next Steps

1. ✅ Keep all 17 confirmed src/ files
2. 🔍 Read the 4 uncertain files to determine purpose
3. ✅ Keep entire `research/Perturbations/` folder
4. ✅ Keep entire `docs/operations/` folder (validation history)
5. 🗑️ Archive `research/new_strategy_builds/` development iterations
6. 🗑️ Archive 103 identified test/dev/debug scripts

---

**Ready to read the final 4 src/ files?**
