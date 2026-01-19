# Magellan Codebase Cleanup Analysis

**Date**: 2026-01-18  
**Branch**: `codebase-cleanup-analysis`  
**Status**: 🔄 In Progress

---

## Objective

Clean up the Magellan codebase to preserve only actively used code for the 6 validated strategies ready for deployment:

1. **Daily Trend Hysteresis** (9/11 assets)
2. **Hourly Swing Trading**
3. **FOMC Event Straddles**
4. **Earnings Straddles**
5. **Bear Trap**
6. **GSB** (Gas & Sugar)

## Problem

Extensive iteration has resulted in:
- 316+ items in `research/` folder
- Multiple strategy versions (ORB v4-v12)
- Orphaned test scripts, optimization results
- Unclear which features/functions are actively used

## Solution

**Runtime Coverage Analysis** - Execute validated strategy tests with code coverage tracking to identify:
- ✅ **Active code** - Actually used by the 6 deployed strategies
- 🗑️ **Dead code** - Experimental iterations, failed strategies
- ⚠️ **Uncertain** - Infrastructure that may be needed

## Process

### Phase 1: Coverage Collection ✅
Run the Perturbations test suite with coverage tracking:
```bash
coverage run research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py
coverage run -a research/Perturbations/hourly_swing/test_gap_reversal.py
coverage run -a research/Perturbations/bear_trap/test_slippage_tolerance.py
coverage run -a research/Perturbations/bear_trap/test_bear_trap_4year.py
coverage run -a research/Perturbations/fomc_straddles/test_bid_ask_spread.py
coverage run -a research/Perturbations/earnings_straddles/test_regime_normalization.py
coverage run -a research/Perturbations/GSB/test_gsb.py  # If exists
```

### Phase 2: Analysis 🔄
- Generate HTML coverage reports
- Export detailed findings
- Map dependencies
- Create cleanup recommendations

### Phase 3: Planning 📋
- Document what to keep vs archive
- Create migration plan
- Get user approval

### Phase 4: Execution 🚀
- Move experimental code to `archive/`
- Consolidate validated strategies
- Clean root directory
- Verify deployment readiness

---

## Directory Structure

```
research/codebase_cleanup/
├── README.md                          # This file
├── coverage_analysis.md               # Coverage findings
├── dependency_map.md                  # Module dependencies
├── cleanup_plan.md                    # Proposed changes
├── coverage_reports/                  # Exported data
│   ├── coverage_summary.txt
│   └── coverage_detailed.json
└── archived_file_manifest.md          # Record of moved files
```

---

## Timeline

- **Coverage Collection**: 1-2 hours (depends on backtest runtime)
- **Analysis & Planning**: 1 hour
- **Review & Approval**: User decision
- **Execution**: 1 hour
- **Total**: ~3-5 hours

---

**Created**: 2026-01-18  
**Owner**: Codebase Cleanup Initiative  
**Next**: Run coverage on Perturbations test suite
