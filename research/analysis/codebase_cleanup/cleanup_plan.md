# Codebase Cleanup Plan

**Date**: 2026-01-18  
**Branch**: `codebase-cleanup-analysis`  
**Objective**: Clean repository to deployment-ready state

---

## Overview

Transform the Magellan repository from a research environment with 316+ experimental files into a clean, deployment-ready codebase containing only the 6 validated strategies.

### Cleanup Statistics

| Category | Current Files | After Cleanup | Action |
|----------|--------------|---------------|---------|
| **Core Infrastructure** (`src/`) | 22 files | 22 files | ✅ KEEP ALL |
| **Validated Strategies** | 49 files | 49 files | ✅ KEEP |
| **Experimental Research** | 200+ files | 0 files | 🗑️ ARCHIVE |
| **Root Test Scripts** | 27 files | 0 files | 🗑️ ARCHIVE |
| **Documentation** | 50+ files | ~15 files | ⚠️ CONSOLIDATE |

---

## Phase 1: Core Infrastructure ✅ NO CHANGES

**Decision**: Keep ALL `src/` code unchanged

```
src/
├── __init__.py
├── data_cache.py           # Used by all strategies (27% coverage)
├── data_handler.py         # Used by options strategies (7% coverage)
├── logger.py               # Used by all strategies (40% coverage)
├── broker/                 # Live trading (needed for deployment)
├── options/                # Options strategies (partially tested)
├── order_manager.py        # Live trading (not tested, but critical)
├── portfolio.py            # Position tracking (needed for deployment)
├── risk_manager.py         # Risk controls (critical for live trading)
└── websocket/              # Real-time data (needed for deployment)
```

**Rationale**: Low coverage reflects that these are **live trading** modules that won't appear in backtests. All are needed for production deployment.

---

## Phase 2: Consolidate Validated Strategies ✅ KEEP

**Location**: `research/Perturbations/` (Already clean and organized)

```
research/Perturbations/
├── DEPLOYMENT_INDEX.md                 # Master deployment reference
├── README.md                            # Framework documentation
│
├── daily_trend_hysteresis/              # Strategy 1
│   ├── README.md
│   ├── PERTURBATION_TEST_REPORT.md
│   ├── test_friction_sensitivity.py
│   └── configs/
│
├── hourly_swing/                        # Strategy 2  
│   ├── README.md
│   ├── PERTURBATION_TEST_REPORT.md
│   └── test_gap_reversal.py
│
├── fomc_straddles/                      # Strategy 3
│   ├── README.md
│   ├── PERTURBATION_TEST_REPORT.md
│   └── test_bid_ask_spread.py
│
├── earnings_straddles/                  # Strategy 4
│   ├── README.md
│   ├── PERTURBATION_TEST_REPORT.md
│   └── test_regime_normalization.py
│
├── bear_trap/                           # Strategy 5 (12 files)
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── PARAMETERS.md
│   ├── PERTURBATION_TEST_REPORT.md
│   ├── bear_trap.py                    # Strategy implementation
│   ├── test_slippage_tolerance.py
│   ├── test_bear_trap_wfa.py
│   └── configs/
│
├── gsb/                                 # Strategy 6 (8 files)
│   ├── README.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── RESEARCH_SUMMARY.md
│   ├── PERTURBATION_TEST_REPORT.md
│   └── gsb_strategy.py                 # Strategy implementation
│
└── reports/                             # Master reports
    ├── master_perturbation_summary.md
    ├── CRITICAL_TESTS_FINAL.md
    ├── BEAR_TRAP_GSB_FINAL.md
    └── test_results/                   # CSV outputs
```

**Action**: ✅ Keep as-is (already clean and deployment-ready)

---

## Phase 3: Archive Experimental Research 🗑️

### 3A: Failed/Superseded Strategies

```
archive/research_archive/
├── high_frequency/                      # 40 files - HFT experiments (failed)
├── earnings_momentum/                   # 1 file - Old earnings approach
├── alternative_data/                    # 2 files - Congressional/insider experiments
├── congressional_trades/                # 1 file
├── insider_clustering/                  # 1 file
└── websocket_poc/                       # 13 files - POC (completed, integrated into src/)
```

**Rationale**: 
- High-frequency trading documented as failed (see conversation `3285333d`)
- Alternative data experiments never validated
- WebSocket POC completed and integrated into `src/websocket/`

### 3B: Strategy Development Iterations

```
archive/strategy_development/
├── new_strategy_builds/
│   ├── strategies/                     # 47 strategy versions (keep only validated ones)
│   ├── small_cap_red_team/             # 20 files - Development artifacts
│   │
│   # Cleanup these test scripts (keep validated versions):
│   ├── test_v13b_quick.py through test_v23_vs_v22.py  # ~30 iteration test scripts
│   ├── test_orb_universe.py through test_walk_forward_universe.py
│   │
│   # Keep key documentation but consolidate:
│   ├── ORB_*.md                        # ~15 ORB development docs (consolidate to 2-3)
│   ├── OVERFITTING_ANALYSIS.md
│   └── WFA_*.md
│
└── backtests/                           # 39 files - Ad-hoc backtest results
```

**Rationale**: Iterations superseded by validated strategies in Perturbations folder

### 3C: Old Session Outputs

```
archive/session_outputs/
├── Root directory test scripts:
│   ├── test_orb_v4.py through test_orb_v12.py   # 27 files
│   ├── test_orb.py, test_orb_opt.py, test_orb_final.py
│   ├── test_vwap_v2.py
│   └── test_v10*.py, test_v11*.py, test_v12*.py
│
├── Old result files:
│   ├── equity_curve_*.csv               # Superseded by Perturbations results
│   ├── stress_test_*.csv
│   ├── *_results.json                   # Scattered optimization results
│  │   ├── advanced_scalping_results.json
│   │   ├── liquidity_grab_*.json
│   │   ├── mean_reversion_*.json
│   │   ├── orb_*.json
│   │   └── range_scalping_*.json
│   │
│   └── Old reports:
│       ├── optimization_report.txt
│       ├── output.txt, output_full.txt
│       └── various *.txt files
```

**Rationale**: These are outputs from old development sessions, superseded by Perturbations framework

---

## Phase 4: Consolidate Documentation 📄

### 4A: Root-Level Documentation (Simplify)

**Current State**: 40+ markdown files in root directory  
**Target State**: ~10 essential files

#### ✅ KEEP (Essential Documentation)

```
Root directory:
├── README.md                           # Main project readme
├── DEPLOYMENT_GUIDE.md                 # Master deployment guide  
├── CLI_GUIDE.md                        # System usage guide
├── START_HERE.md                       # Quick start
└── docs/                               # Detailed documentation folder
```

#### 🗑️ ARCHIVE (Superseded Session Docs)

```
archive/documentation/
├── Session handoffs (superseded by current state):
│   ├── AGENT_HANDOFF_COMPREHENSIVE.md
│   ├── STRATEGY_TESTING_HANDOFF.md
│   ├── STRATEGY_VALIDATION_HANDOFF.md
│   ├── WFA_COMPREHENSIVE_AUDIT_HANDOFF.md
│   ├── HANDOFF_PROMPT.md
│   └── NEXT_AGENT_PROMPT.md
│
├── Historical status (superseded):
│   ├── STATE.md
│   ├── BACKLOG.md
│   ├── SESSION_COMPLETE_WFA_PHASE.md
│   ├── SESSION_SUMMARY_2026_01_17.md
│   └── STRATEGY_CANONIZATION_SUMMARY.md
│
└── Old validation reports (superseded by Perturbations):
    ├── FINAL_VALIDATION_REPORT.md
    ├── VALIDATED_STRATEGIES_FINAL.md
    ├── VALIDATED_SYSTEMS.md
    ├── ADAPTIVE_HYSTERESIS_RESULTS.md
    ├── HOURLY_OPTIMIZATION_RESULTS.md
    └── SCALPING_STRATEGY_RESULTS.md
```

### 4B: Keep Master Reference Docs

```
research/
├── VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md   # Master strategy reference
└── Perturbations/                                # Deployment baseline
    ├── DEPLOYMENT_INDEX.md
    └── README.md
```

---

## Phase 5: Final Directory Structure 🎯

### After Cleanup

```
Magellan/
├── .env, .gitignore, requirements.txt
├── main.py                              # Main system entry point
├── README.md                            # Project overview
├── DEPLOYMENT_GUIDE.md                  # How to deploy
├── CLI_GUIDE.md                         # How to use
├── START_HERE.md                        # Quick start
│
├── src/                                 # Core infrastructure (22 files)
│   ├── data_cache.py
│   ├── data_handler.py
│   ├── logger.py
│   ├── broker/
│   ├── options/
│   └── ...
│
├── config/                              # System configuration (21 files)
│   └── (keep as-is)
│
├── data/                                # Cached market data (1303 files)
│   └── (keep as-is, add to .gitignore if needed)
│
├── research/
│   ├── VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md
│   ├── Perturbations/                  # 6 Validated strategies (49 files)
│   │   ├── DEPLOYMENT_INDEX.md
│   │   ├── daily_trend_hysteresis/
│   │   ├── hourly_swing/
│   │   ├── fomc_straddles/
│   │   ├── earnings_straddles/
│   │   ├── bear_trap/
│   │   ├── gsb/
│   │   └── reports/
│   │
│   └── codebase_cleanup/               # This cleanup initiative
│       ├── README.md
│       ├── coverage_analysis.md
│       ├── cleanup_plan.md             # This file
│       └── coverage_reports/
│
├── scripts/                             # Utility scripts (8 files, keep as-is)
│
├── docs/                                # Comprehensive documentation (170 files)
│   └── operations/
│       └── strategies/                  # Strategy-specific docs
│
└── archive/                             # Archived experimental code
    ├── research_archive/                # Experiments
    ├── strategy_development/            # Development iterations
    ├── session_outputs/                 # Old test outputs
    └── documentation/                   # Historical docs
```

---

## Execution Steps

### Step 1: Create Archive Structure

```bash
mkdir -p archive/research_archive
mkdir -p archive/strategy_development
mkdir -p archive/session_outputs  
mkdir -p archive/documentation
```

### Step 2: Archive Experimental Research

```bash
# Failed experiments
mv research/high_frequency archive/research_archive/
mv research/earnings_momentum archive/research_archive/
mv research/alternative_data archive/research_archive/
mv research/congressional_trades archive/research_archive/
mv research/insider_clustering archive/research_archive/
mv research/websocket_poc archive/research_archive/
mv research/backtests archive/research_archive/
mv research/fmp_data_audit archive/research_archive/
mv research/capabilities_research archive/research_archive/
mv research/event_straddles_full archive/research_archive/
mv research/ML archive/research_archive/
```

### Step 3: Archive Development Iterations

```bash
# Strategy development artifacts
mkdir archive/strategy_development/new_strategy_builds
mv research/new_strategy_builds/small_cap_red_team archive/strategy_development/new_strategy_builds/
mv research/new_strategy_builds/strategies archive/strategy_development/new_strategy_builds/
mv research/new_strategy_builds/test_*.py archive/strategy_development/new_strategy_builds/
mv research/new_strategy_builds/analyze_*.py archive/strategy_development/new_strategy_builds/
mv research/new_strategy_builds/ORB_*.md archive/strategy_development/new_strategy_builds/
```

### Step 4: Archive Root Test Scripts

```bash
# Old test scripts from root
mv test_orb*.py archive/session_outputs/
mv test_v*.py archive/session_outputs/
mv test_vwap*.py archive/session_outputs/
```

### Step 5: Archive Old Results

```bash
# Old result files
mv equity_curve_*.csv archive/session_outputs/
mv stress_test_*.csv archive/session_outputs/
mv *_results.json archive/session_outputs/
mv *.txt archive/session_outputs/  # Various output files
```

### Step 6: Archive Superseded Documentation

```bash
# Session handoffs
mv *HANDOFF*.md archive/documentation/
mv STATE.md archive/documentation/
mv BACKLOG.md archive/documentation/
mv SESSION_*.md archive/documentation/
mv VALIDATED_STRATEGIES_FINAL.md archive/documentation/
mv *_RESULTS.md archive/documentation/
```

### Step 7: Update README Files

Create new simplified README.md pointing to:
- `research/Perturbations/DEPLOYMENT_INDEX.md` for deployment
- `DEPLOYMENT_GUIDE.md` for detailed deployment instructions
- `research/VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md` for strategy details

---

## Risk Mitigation

### Safety Measures

1. **All in Git**: Every move is tracked
2. **Archive, Don't Delete**: Nothing is permanently removed
3. **Test After Cleanup**: Run perturbation tests to verify nothing broke
4. **Branch-based**: Work stays in `codebase-cleanup-analysis` until approved

### Rollback Plan

If anything breaks:
```bash
git checkout main  # Return to pre-cleanup state
```

All archived files remain in git history and can be restored.

---

## Validation Checklist

After executing cleanup, verify:

- [ ] All 6 Perturbation tests still pass
- [ ] `src/` modules import correctly
- [ ] Main system (`main.py`) runs without errors
- [ ] Coverage re-run shows same results
- [ ] Documentation links are not broken
- [ ] No critical files were accidentally archived

---

## Benefits

### Before Cleanup
- 316+ items in research/
- 27 test scripts in root
- Unclear which code is active
- Multiple copies of same strategies
- Hard to onboard new developers

### After Cleanup
- 49 files in validated strategies
- Clean root directory
- Single source of truth per strategy
- Clear deployment path
- Professional, production-ready structure

---

## Next Steps

1. **Review this plan with user**
2. **Get approval for specific moves**
3. **Execute Phase 2-6 sequentially**
4. **Validate after each phase**
5. **Create final walkthrough**
6. **Merge to main when approved**

---

**Created**: 2026-01-18  
**Status**: ⏸️ Awaiting User Approval  
**Estimated Execution Time**: 1 hour  
**Risk Level**: LOW (everything is archived, not deleted)
