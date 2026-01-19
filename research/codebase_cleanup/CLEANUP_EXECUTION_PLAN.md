# Codebase Cleanup - Final Execution Plan

**Date**: 2026-01-18  
**Status**: Ready for Execution

---

## Executive Summary

**Goal:** Isolate production-ready "true state" of the Magellan trading system

**Method:** Move all non-production code to `archive/` directory structure

**Impact:**
- **Before:** 326 Python files, unclear structure
- **After:** ~45 Python files, clean deployment baseline
- **Reduction:** ~85% of Python files

---

## Phase 1: Delete Duplicate Parameter Files

### Files to Delete (2)
```powershell
rm research\new_strategy_builds\BEAR_TRAP_PARAMETERS.md
rm research\Perturbations\bear_trap\BEAR_TRAP_PARAMETERS.md
```

**Reason:** Duplicates of `research/Perturbations/bear_trap/parameters_bear_trap.md` (new standard)

---

## Phase 2: Create Archive Structure

### Directory Structure
```
archive/
├── failed_strategies/
│   ├── regime_sentiment/
│   └── magellan_prime/
├── research_archive/
│   ├── high_frequency/
│   ├── backtests/
│   ├── new_strategy_builds/
│   ├── websocket_poc/
│   ├── alternative_data/
│   ├── congressional_trades/
│   ├── insider_clustering/
│   ├── earnings_momentum/
│   ├── fmp_data_audit/
│   ├── capabilities_research/
│   ├── event_straddles_full/
│   └── ML/
├── test_outputs/
│   ├── root_test_files/
│   ├── results/
│   └── session_outputs/
└── historical_docs/
    ├── handoffs/
    ├── sessions/
    └── status/
```

---

## Phase 3: Archive Failed Strategies

### Move Experimental Strategies
```powershell
# Regime Sentiment Filter (failed daily strategy)
mv deployment_configs\regime_sentiment archive\failed_strategies\regime_sentiment

# Magellan Prime (early alpha scaffolding)
mv magellan_prime archive\failed_strategies\magellan_prime

# Clean up empty deployment_configs
rmdir deployment_configs
```

---

## Phase 4: Archive Research Folders

### Move Development/Research Folders
```powershell
# Failed HFT experiments (40 files)
mv research\high_frequency archive\research_archive\high_frequency

# Old backtest experiments (39 files)
mv research\backtests archive\research_archive\backtests

# ORB development iterations (47 strategy files + tests)
mv research\new_strategy_builds archive\research_archive\new_strategy_builds

# WebSocket POC (completed, integrated into src/)
mv research\websocket_poc archive\research_archive\websocket_poc

# Alternative data experiments
mv research\alternative_data archive\research_archive\alternative_data
mv research\congressional_trades archive\research_archive\congressional_trades
mv research\insider_clustering archive\research_archive\insider_clustering
mv research\earnings_momentum archive\research_archive\earnings_momentum

# FMP data audit (completed)
mv research\fmp_data_audit archive\research_archive\fmp_data_audit

# Capabilities research (completed)
mv research\capabilities_research archive\research_archive\capabilities_research

# Event straddles full (superseded by Perturbations)
mv research\event_straddles_full archive\research_archive\event_straddles_full

# ML experiments
mv research\ML archive\research_archive\ML
```

---

## Phase 5: Archive Test Outputs

### Move Results and Test Files
```powershell
# Results directory
mv results archive\test_outputs\results

# Root test scripts (27 test_orb_v*.py files)
mkdir archive\test_outputs\root_test_files
mv test_*.py archive\test_outputs\root_test_files\

# Root analyze/debug/check scripts
mv analyze_*.py archive\test_outputs\root_test_files\
mv debug_*.py archive\test_outputs\root_test_files\
mv check_*.py archive\test_outputs\root_test_files\
```

---

## Phase 6: Archive Root Historical Files

### Move Historical Documentation
```powershell
# Create subdirectories
mkdir archive\historical_docs\handoffs
mkdir archive\historical_docs\sessions
mkdir archive\historical_docs\status

# Handoff documents
mv *HANDOFF*.md archive\historical_docs\handoffs\

# Session summaries
mv SESSION_*.md archive\historical_docs\sessions\

# Status/state files
mv STATE.md archive\historical_docs\status\
mv BACKLOG.md archive\historical_docs\status\
mv STRATEGY_TESTING_HANDOFF.md archive\historical_docs\status\
mv VALIDATED_STRATEGIES_FINAL.md archive\historical_docs\status\
```

### Move Test Results/Outputs
```powershell
# Create test outputs directory
mkdir archive\test_outputs\session_outputs

# Equity curves
mv equity_curve*.csv archive\test_outputs\session_outputs\

# Stress tests
mv stress_test*.csv archive\test_outputs\session_outputs\
mv stress_test*.txt archive\test_outputs\session_outputs\

# JSON results
mv *_results.json archive\test_outputs\session_outputs\
mv optimization_report.txt archive\test_outputs\session_outputs\
mv comprehensive_*.csv archive\test_outputs\session_outputs\

# Other test outputs
mv *.log archive\test_outputs\session_outputs\ (except live_trades.log if needed)
mv output*.txt archive\test_outputs\session_outputs\
mv simulation_output.txt archive\test_outputs\session_outputs\
```

### Move Old Strategy Docs
```powershell
mkdir archive\historical_docs\old_strategies

mv OPTIONS_*.md archive\historical_docs\old_strategies\
mv FOMC_EVENT_STRADDLES_GUIDE.md archive\historical_docs\old_strategies\
mv SCALPING_*.md archive\historical_docs\old_strategies\
mv REALITY_CHECK_FAILURE.md archive\historical_docs\old_strategies\
```

---

## What Stays in Root

### Essential Files Only (10-15 files)

**Core:**
- main.py
- .env
- .env.template
- .gitignore
- requirements.txt

**Documentation:**
- README.md
- DEPLOYMENT_GUIDE.md
- VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md

**Cleanup Documentation:**
- (research/codebase_cleanup/ folder stays for reference)

---

## What Stays in Production Tree

### Directories

```
Magellan/  (Clean Production Tree)
│
├── main.py
├── .env, .gitignore, requirements.txt
├── README.md, DEPLOYMENT_GUIDE.md
│
├── src/  (21 .py files)
│   └── options/  (4 .py files)
│
├── config/  (20 JSON files)
│   ├── nodes/
│   ├── mag7_daily_hysteresis/
│   └── hourly_swing/
│
├── scripts/  (8 utilities)
│
├── data/cache/  (market data)
│
├── docs/
│   └── operations/  (validation history)
│
├── research/
│   ├── Perturbations/  (6 strategies)
│   ├── VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md
│   └── codebase_cleanup/  (this cleanup documentation)
│
└── archive/  (everything else)
```

---

## Verification Checklist

### Before Execution
- [ ] All 6 parameter files confirmed created
- [ ] Bear Trap duplicates identified for deletion
- [ ] Failed strategies identified (regime_sentiment, magellan_prime)
- [ ] Production code inventory complete (main + src + config + scripts)

### After Execution
- [ ] Verify main.py runs
- [ ] Verify all 6 strategy parameter files exist
- [ ] Verify config/ directory intact
- [ ] Verify src/ directory intact (21 files)
- [ ] Verify Perturbations/ intact (6 strategies)
- [ ] Verify docs/operations/ intact
- [ ] Verify archive/ structure created correctly

---

## Estimated Impact

### Python Files
- **Before:** 326 .py files
- **After (production):** ~45 .py files
- **After (archive):** ~281 .py files
- **Reduction:** 86%

### Root Directory
- **Before:** ~100 files
- **After:** ~10-15 files
- **Reduction:** 85-90%

### Research Directory
- **Before:** 12 subdirectories
- **After:** 3 subdirectories (Perturbations, VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md, codebase_cleanup)
- **Archived:** 9 subdirectories

---

## Safety Measures

### Git Commit Before Archive
```powershell
git add -A
git commit -m "Pre-cleanup snapshot - all files before archive"
```

### Verification After Archive
```powershell
# Test main.py runs
python main.py --help

# Verify parameter files
ls research\Perturbations\*\parameters_*.md

# Verify config files
ls config\**\*.json
```

---

## Execution Commands

**Ready to execute?** This will:
1. Delete 2 duplicate parameter files
2. Create archive/ structure
3. Move ~300 files to archive/
4. Leave clean production tree

**Would you like me to:**
- A) Proceed with full execution now
- B) Execute in phases (you approve each phase)
- C) Make any modifications to the plan first

---

**Status:** Awaiting final approval to proceed
