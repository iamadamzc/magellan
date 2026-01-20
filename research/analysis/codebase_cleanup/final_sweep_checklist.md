# Final Sweep - Comprehensive Checklist

**Date**: 2026-01-18  
**Pre-Cleanup Verification**

---

## ✅ CONFIRMED - Production Code

### Entry Point
- ✅ `main.py` - Production entry point

### Core Infrastructure (21 files)
- ✅ All `src/*.py` files - ALL confirmed needed
- ✅ All `src/options/*.py` files (4 files) - Used by FOMC/Earnings

### Configuration
- ✅ `config/` directory (20 JSON files) - All deployment configs
- ✅ `.env` - API credentials
- ✅ `.env.template` - Template for setup
- ✅ `.gitignore` - Git ignore rules
- ✅ `requirements.txt` - Python dependencies

### Utilities
- ✅ `scripts/` directory (8 files) - Operational utilities

### Validated Strategies
- ✅ `research/Perturbations/` - All 6 validated strategies
- ✅ All 6 `parameters_*.md` files created ✅

### Validation History
- ✅ `docs/operations/` - WFA/validation history (audit trail)

### Data
- ✅ `data/cache/` - Cached market data (keep)

---

## ⚠️ FOUND - Issues to Address

### 1. Duplicate Parameter Files

**Found:**
- `research/new_strategy_builds/BEAR_TRAP_PARAMETERS.md` (duplicate)
- `research/Perturbations/bear_trap/BEAR_TRAP_PARAMETERS.md` (old name)

**We created:**
- `research/Perturbations/bear_trap/parameters_bear_trap.md` (NEW standard)

**Action Required:**
✅ **DELETE** the 2 old files:
```powershell
rm research\new_strategy_builds\BEAR_TRAP_PARAMETERS.md
rm research\Perturbations\bear_trap\BEAR_TRAP_PARAMETERS.md
```

---

### 2. Root Directory - Many Historical Files

**Found 100+ files in root:**
- HANDOFF documents (AGENT_HANDOFF_COMPREHENSIVE.md, etc.)
- Session summaries (SESSION_*.md)
- Old validation reports
- Test results (equity_curve_*.csv, stress_test_*.csv)
- Old strategy documents

**Keep in root:**
- README.md
- DEPLOYMENT_GUIDE.md
- VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md (current reference)
- .env, .env.template, requirements.txt, .gitignore
- main.py

**Archive the rest** (~80+ files)

---

### 3. Additional Directories Investigated

**deployment_configs/**
- Contents: `regime_sentiment/` subfolder (5 files)
- Purpose: Deployment configs for regime sentiment strategy
- Action: ⚠️ **KEEP** - May be active

**magellan_prime/**
- Contents: `spy_node/` subfolder (17 files)
- Purpose: Unclear - possibly SPY-specific implementation
- Action: ⚠️ **KEEP FOR NOW** - Need user confirmation

**results/**
- Contents: Stress test reports, options results (27 files)
- Purpose: Historical test outputs
- Action: 🗑️ **ARCHIVE**

---

## ✅ FINAL ACTIONITEMS

### 1. Delete Duplicate Parameter Files (Ready to Execute)

```powershell
rm research\new_strategy_builds\BEAR_TRAP_PARAMETERS.md
rm research\Perturbations\bear_trap\BEAR_TRAP_PARAMETERS.md
```

### 2. Root Directory Cleanup Plan

**KEEP (10 essential files):**
1. README.md
2. DEPLOYMENT_GUIDE.md
3. VALIDATED_STRATEGIES_COMPLETE_REFERENCE.md
4. .env
5. .env.template
6. .gitignore
7. requirements.txt
8. main.py
9. (plus any user confirms)

**ARCHIVE (~80+ files):**
- All *HANDOFF*.md files
- All SESSION_*.md files
- All equity_curve_*.csv files
- All stress_test_*.csv/.txt files
- All *_results.json files
- Old strategy docs (VALIDATED_STRATEGIES_FINAL.md, etc.)
- Historical handoffs and summaries
- State/backlog files

---

## 📊 FINAL COUNTS

### Production (KEEP)
- **Core files:** 45 .py files (main + src + scripts)
- **Config:** 24 files (.env, requirements, 20 JSONs, .gitignore, template)
- **Parameters:** 6 files (all strategies documented)
- **Strategies:** research/Perturbations/ (6 folders)
- **Validation:** docs/operations/ (audit trail)
- **Total Python:** ~45 files

### Archive (~280-300 files)
- **Test scripts:** ~280 .py files
- **Root historical:** ~80 .md/.csv/.json files
- **Research folders:** new_strategy_builds, backtests, high_frequency, etc.
- **Results:** results/ directory
- **Total reduction:** ~85% of .py files

---

## 🔍 NEED USER CONFIRMATION

### Question 1: Are these production?
- **deployment_configs/regime_sentiment/** - Keep or archive?
- **magellan_prime/spy_node/** - Keep or archive?

### Question 2: Root directory
- Keep both root README.md and research/Perturbations/README.md?
- DEPLOYMENT_GUIDE.md stays in root or move to docs/?

---

## ✅ READY TO PROCEED

**What's Complete:**
✅ All 6 parameter files created with uniform format  
✅ All production code identified and verified  
✅ All src/ files confirmed needed (21/21)  
✅ Config files, scripts, data all accounted for  
✅ Duplicate parameter files identified for deletion  
✅ Root directory cleanup plan ready  

**Pending User Input:**
⏸️ Confirm status of deployment_configs and magellan_prime  
⏸️ Approve root directory cleanup list  

**Once confirmed:**
1. Delete 2 duplicate parameter files
2. Create archive/ structure
3. Move ~300 files to archive/
4. Clean production tree remains

---

**Status:** Ready for user confirmation before final cleanup execution
