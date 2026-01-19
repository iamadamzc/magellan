# Coverage Analysis Results

**Date**: 2026-01-18  
**Branch**: `codebase-cleanup-analysis`  
**Total Coverage**: 54% (617 / 1134 statements executed)

---

## Executive Summary

Ran runtime coverage analysis on **5 validated strategy tests** from the Perturbations folder to identify actively used code in the Magellan system.

### Tests Executed

| Strategy | Test File | Coverage | Status |
|----------|-----------|----------|--------|
| **Daily Trend Hysteresis** | `test_friction_sensitivity.py` | 89% | ✅ Complete |
| **Hourly Swing** | `test_gap_reversal.py` | 90% | ✅ Complete |
| **Bear Trap** | `test_slippage_tolerance.py` | 88% | ✅ Complete |
| **FOMC Straddles** | `test_bid_ask_spread.py` | 92% | ✅ Complete |
| **Earnings Straddles** | `test_regime_normalization.py` | 92% | ✅ Complete |
| **GSB** | N/A - No test file | - | ⚠️ Uses ORB V23 code |

**Note**: Bear Trap 4-year test (`test_bear_trap_4year.py`) has import issues and was skipped, but we already captured the strategy logic from `test_slippage_tolerance.py`.

---

## Core Infrastructure Usage

### `src/` Module Analysis

| Module | Statements | Executed | Coverage | Status |
|--------|-----------|----------|----------|--------|
| **src/\_\_init\_\_.py** | 0 | 0 | 100% | ✅ |
| **src/data_cache.py** | 123 | 33 | 27% | ⚠️ Partial |
| **src/data_handler.py** | 269 | 18 | 7% | ⚠️ Low |
| **src/logger.py** | 111 | 44 | 40% | ⚠️ Partial |

### Key Findings

#### ✅ **ACTIVELY USED** (Keep - Required for Deployment)

**1. `src/data_cache.py`** (27% coverage)
- **Used functions**:
  - `get_or_fetch_equity()` - All strategies use this for data retrieval
  - Cache initialization
  - Basic file operations
  
- **Why low coverage?**: 
  - Contains many data source implementations (FMP, Alpaca, etc.)
  - Strategies only use equity caching, not  options/futures features
  - Error handling paths not exercised

**2. `src/data_handler.py`** (7% coverage)
- **Used features**:
  - `AlpacaDataClient` for options data (FOMC/Earnings tests)
  - Basic data fetching
  
- **Why low coverage?**:
  - Large file (269 statements)
  - Contains websocket implementation (not used in backtests)
  - Multiple data source adapters (only subset used)
  - Real-time trading features (not tested)

**3. `src/logger.py`** (40% coverage)
- **Used features**:
  - Basic logging setup
  - Console output
  
- **Why partial**:
  - Advanced logging features (file rotation, remote logging) not used in tests
  - Error handling paths

---

## What This Coverage Tells Us

### ✅ **Strategies Are Self-Contained**

The high coverage in test files (88-92%) and low coverage in `src/` modules indicates:

1. **Good news**: Strategies have minimal external dependencies
2. **Most logic is in strategy files** - makes them portable
3. **Only use core infrastructure**: data fetching and basic logging

### ⚠️ **Large Portions of `src/` Are Unused**

- **73% of `data_cache.py`** is not touched by backtest
s
- **93% of `data_handler.py`** is not touched
- **60% of `logger.py`** is not touched

**This is EXPECTED and OKAY** because:
- Coverage tests run backtests, not live trading
- Live trading infrastructure (websockets, order execution) won't show up
- Options/futures infrastructure exists but not all strategies use it

---

## Modules NOT Captured in Coverage

Coverage **only shows files that were imported**. These modules exist but didn't appear in coverage because no test imported them:

### Potentially Critical (Need Manual Review)

Based on the system architecture, these are likely needed for deployment:

```
src/
├── order_manager.py          # Live order execution (not tested)
├── portfolio.py               # Position tracking (not tested)
├── risk_manager.py            # Risk controls (not tested)
├── broker/                    # Alpaca integration (not tested)
├── options/                   # Options features (partially tested)
│   ├── features.py           # Options greeks (used by FOMC/Earnings)
│   └── pricing.py            # Options pricing models
└── websocket/                 # Real-time data (not tested)
```

### Likely Experimental (Safe to Archive)

These are probably from old iterations:

```
research/
├── high_frequency/           # 40 files - Failed HFT experiments
├── backtests/                # 39 files - Old ad-hoc backtest results
├── congressional_trades/     # Alternative data experiments
├── insider_clustering/       # Alternative data experiments
├── earnings_momentum/        # Old earnings strategy experiments
└── websocket_poc/            # WebSocket proof-of-concept
```

---

## Recommendations

### Phase 1: Keep ALL `src/` Code ✅

**DO NOT** delete anything from `src/` even with low coverage because:
1. Live trading infrastructure won't show up in backtest coverage
2. Error handling and edge cases are important but not exercised
3. The modules are small and well-organized
4. Risk of breaking production deployment is too high

### Phase 2: Archive Experimental Code 🗑️

**SAFE TO ARCHIVE** to `archive/` folder:

```
research/
├── high_frequency/           # Documented as failed (see conversation history)
├── backtests/                # Ad-hoc backtest outputs (superseded by Perturbations)
├── alternative_data/         # Congressional/insider trading experiments
├── congressional_trades/
├── insider_clustering/
├── earnings_momentum/        # Old earnings approach (superseded)
└── websocket_poc/            # POC completed, integrated into src/
```

### Phase 3: Consolidate Strategy Code 📁

**Current state**: Strategies exist in multiple locations
- `research/Perturbations/` - Clean, validated, deployment-ready
- `research/new_strategy_builds/` - Development versions, may have duplicates

**Recommendation**: Create single source of truth in `research/Perturbations/`

### Phase 4: Clean Root Directory 🧹

**Archive these root-level files** (test outputs from old sessions):

```
Root files to archive (examples):
├── equity_curve_*.csv        # Old equity curves (superseded)
├── stress_test_*.csv         # Old stress test outputs
├── test_orb_v*.py            # Multiple ORB test iterations (v4-v12)
├── advanced_*_results.json   # Old optimization results
├── liquidity_grab_*.json     # Old strategy results
├── mean_reversion_*.json     # Old strategy results
└── *.txt reports             # Old session outputs
```

---

## Next Steps

1. **Review** this analysis with user
2. **Create detailed cleanup plan** specifying:
   - Exact files to archive
   - New directory structure
   - Migration steps
3. **Get approval** before moving any files
4. **Execute cleanup** safely with git tracking
5. **Verify** deployment still works

---

## Interactive Coverage Report

Full HTML coverage report available at:
```
file:///a:/1/Magellan/htmlcov/index.html
```

Open this in a browser to see:
- Line-by-line coverage highlighting
- Which branches were taken
- Which functions were called
- Detailed execution paths

---

**Generated**: 2026-01-18  
**Coverage Tool**: coverage.py v7.13.1  
**Total Runtime**: ~15 minutes  
**Confidence Level**: HIGH for strategy code, MEDIUM for infrastructure
