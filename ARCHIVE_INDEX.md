# Archive Index - Magellan Codebase Cleanup

**Date:** January 18, 2026  
**Purpose:** Quick reference for locating archived files

---

## What Happened

On 2026-01-18, the Magellan codebase was cleaned to isolate production code. **~300 files** were moved to `archive/` to create a clear deployment baseline.

**Nothing was deleted** - everything is preserved in the archive.

---

## Quick Lookup Guide

### Looking for a specific file?

| File Type | Location |
|-----------|----------|
| **Test scripts** (test_*.py, analyze_*.py, debug_*.py) | `archive/test_outputs/root_test_files/` |
| **Old CSV results** (equity_curve, stress_test, etc.) | `archive/test_outputs/session_outputs/` |
| **Old JSON results** (*_results.json) | `archive/test_outputs/session_outputs/` |
| **Handoff documents** (*HANDOFF*.md) | `archive/historical_docs/handoffs/` |
| **Session summaries** (SESSION_*.md) | `archive/historical_docs/sessions/` |
| **Old strategy docs** (OPTIONS_*.md, FOMC_*, etc.) | `archive/historical_docs/old_strategies/` |
| **Status files** (STATE.md, BACKLOG.md) | `archive/historical_docs/status/` |
| **Failed strategies** (regime_sentiment, magellan_prime) | `archive/failed_strategies/` |
| **Research experiments** (HFT, backtests, ORB dev) | `archive/research_archive/` |

---

## Archive Structure

```
archive/
│
├── failed_strategies/
│   ├── regime_sentiment/          # Failed daily RSI strategy (5 configs)
│   └── magellan_prime/             # Early alpha scaffolding prototype (17 files)
│
├── research_archive/
│   ├── high_frequency/             # HFT experiments (40 files) - FAILED
│   ├── backtests/                  # Old backtest code (39 files)
│   ├── new_strategy_builds/        # ORB development (47 strategies + tests)
│   ├── websocket_poc/              # WebSocket research (integrated into src/)
│   ├── alternative_data/           # Alt data experiments
│   ├── congressional_trades/       # Congress trading data experiments
│   ├── insider_clustering/         # Insider trading experiments
│   ├── earnings_momentum/          # Earnings experiments
│   ├── fmp_data_audit/             # FMP API research (completed)
│   ├── capabilities_research/      # System capabilities audit
│   ├── event_straddles_full/       # Old straddles (superseded by Perturbations)
│   └── ML/                         # Machine learning experiments
│
├── test_outputs/
│   ├── root_test_files/            # All test_*.py, analyze_*.py, debug_*.py
│   │                               # Also: diagnose, inspect, verify scripts
│   ├── session_outputs/            # All CSV, JSON, TXT test results
│   │                               # equity_curves, stress_tests, *_results.json
│   └── results/                    # results/ directory contents
│
└── historical_docs/
    ├── handoffs/                   # All *HANDOFF*.md files
    ├── sessions/                   # All SESSION_*.md files
    ├── status/                     # STATE.md, BACKLOG.md, old validation reports
    └── old_strategies/             # Old strategy documentation
                                    # OPTIONS_*.md, FOMC_*, SCALPING_*, etc.
```

---

## What Stayed (Production Code)

### Root Directory (8 files)
- `main.py` - System entry point
- `.env` - API credentials (not in git)
- `.env.template` - Credential template
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `README.md` - Main documentation
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md` - Strategy reference
- `livetradelog.txt` - Recent live trading log

### Directories
- **src/** (21 .py files + options/) - Core infrastructure
- **config/** (20 JSON files) - Deployment configurations
- **scripts/** (8 .py files) - Operational utilities
- **data/cache/** - Market data cache
- **docs/operations/** - Validation history (audit trail)
- **research/Perturbations/** - 6 validated strategies
- **research/codebase_cleanup/** - This cleanup documentation

---

## Specific File Locations

### CSV Files (All in archive/test_outputs/session_outputs/)
- comprehensive_ic_scan.csv
- hysteresis_optimization_results.csv
- ic_analysis_results.csv
- index_etf_profitability_results.csv
- NVDA_2025_daily_pnl.csv
- NVDA_2025_hourly_pnl.csv
- SPY_2025_daily_pnl.csv
- TSLA_2025_daily_pnl.csv
- TSLA_2025_hourly_pnl.csv
- variant_f_equity_curve.csv
- All equity_curve*.csv files
- All stress_test*.csv files

### Markdown Files (Archived)
**In archive/historical_docs/status/:**
- FINAL_VALIDATION_REPORT.md
- NEXT_AGENT_PROMPT.md
- SPY_EVALUATION_SUMMARY.md
- VALIDATED_SYSTEMS.md (superseded by COMPLETE_REFERENCE)
- STATE.md
- BACKLOG.md
- STRATEGY_TESTING_HANDOFF.md

**In archive/historical_docs/old_strategies/:**
- All OPTIONS_*.md files
- FOMC_EVENT_STRADDLES_GUIDE.md
- SCALPING_STRATEGY_RESULTS.md
- REALITY_CHECK_FAILURE.md
- INDICES_HOURLY_FAILURE.md
- HOURLY_OPTIMIZATION_RESULTS.md
- And many more...

### Python Test Scripts (All in archive/test_outputs/root_test_files/)
- All test_*.py files (test_orb_v4.py through v12, etc.)
- All analyze_*.py files
- All debug_*.py files
- All check_*.py files
- All batch_*.py files
- diagnose_orb_v10.py
- inspect_cache.py, inspect_ic.py
- verify_temporal_leak_patch.py, verify_v1.py
- ascii_scan.py, ascii_scan_extended.py

### JSON/Data Files (All in archive/test_outputs/session_outputs/)
- All *_results.json files
- congressional_trades_filtered.json
- house_trading_raw.json
- senate_trading_raw.json
- earnings_calendar_2024.json
- economic_calendar_2024_raw.json
- economic_events_2024.json
- event_straddle_backtest_results_full.json
- .coverage (coverage tool output)

---

## How to Find Something

### 1. By File Type
```powershell
# Find all CSVs in archive
Get-ChildItem -Recurse -Filter *.csv archive\

# Find all test scripts
Get-ChildItem -Recurse -Filter test_*.py archive\

# Find all markdown docs
Get-ChildItem -Recurse -Filter *.md archive\
```

### 2. By Name
```powershell
# Search for specific file
Get-ChildItem -Recurse -Filter "*filename*" archive\

# Example: Find all ORB-related files
Get-ChildItem -Recurse -Filter "*orb*" archive\
```

### 3. By Content
```powershell
# Search file contents
Get-ChildItem -Recurse archive\ | Select-String "search term"
```

---

## Archive Statistics

### Files Moved
- **Python files:** ~280 (.py files)
- **CSV files:** ~50+ (test results)
- **JSON files:** ~30+ (results, data)
- **Markdown files:** ~40+ (docs, handoffs, summaries)
- **Directories:** 12 research folders + 2 failed strategies
- **Total:** ~300+ files

### Space Saved in Root
- **Before:** ~100 files in root directory
- **After:** 8 files in root directory
- **Clarity:** 100% improvement

---

## Restoring a File

If you need to restore something from archive:

```powershell
# Copy file back to root (doesn't remove from archive)
Copy-Item archive\path\to\file.py .

# Or move it back (removes from archive)
Move-Item archive\path\to\file.py .
```

---

## Production Code Inventory

### Python Files (~45 total)
- **1** main.py
- **21** src/*.py files
- **4** src/options/*.py files
- **8** scripts/*.py files
- **6** strategy .py files in Perturbations/
- **6** test_*.py files in Perturbations/ (validated tests)

### Configuration Files
- **20** JSON configs in config/
- **6** parameters_*.md files in Perturbations/
- **1** .env template
- **1** requirements.txt
- **1** .gitignore

### Documentation
- **1** README.md
- **1** DEPLOYMENT_GUIDE.md
- **1** VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md
- **Multiple** validation reports in docs/operations/

---

## Validated Strategies (Production)

All in `research/Perturbations/`:

1. **daily_trend_hysteresis/** - RSI daily trend (11 assets)
   - parameters_daily_trend_hysteresis.md

2. **hourly_swing/** - RSI hourly swing (2 assets)
   - parameters_hourly_swing.md

3. **fomc_straddles/** - FOMC event straddles (8 events/year)
   - parameters_fomc_straddles.md

4. **earnings_straddles/** - Earnings volatility (7 tickers)
   - parameters_earnings_straddles.md

5. **bear_trap/** - Small-cap reversals (9 symbols)
   - parameters_bear_trap.md

6. **GSB/** - Gas & Sugar breakout (NG, SB futures)
   - parameters_gsb.md

---

## Notes

- **Nothing was deleted** - Everything is in archive/
- **Git history preserved** - All changes are tracked
- **Safe to delete archive** after 6-12 months if not needed
- **This file** (ARCHIVE_INDEX.md) stays in root for reference

---

**Last Updated:** 2026-01-18  
**Cleanup Documentation:** research/codebase_cleanup/CLEANUP_COMPLETE.md
