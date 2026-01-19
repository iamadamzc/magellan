# Configuration Files & Scripts Inventory

**Date**: 2026-01-18

---

## Configuration Files - Complete Inventory

### ✅ Root /config Directory (20 JSON files)

**Main config:**
- `config/index_etf_configs.json`

**Node configurations (10 files):**
- `config/nodes/master_config.json` ← **MAIN CONFIG**
- `config/nodes/SPY.json`
- `config/nodes/QQQ.json`
- `config/nodes/IWM.json`
- `config/nodes/VSS.json`
- `config/nodes/VTV.json`
- `config/nodes/daily_trend.json`
- `config/nodes/nvda_daily_hysteresis.json`
- `config/nodes/challenger_reversion.json`
- `config/nodes/regime_scan.json`

**MAG7 Daily Hysteresis configs (7 files):**
- `config/mag7_daily_hysteresis/AAPL.json`
- `config/mag7_daily_hysteresis/AMZN.json`
- `config/mag7_daily_hysteresis/GOOGL.json`
- `config/mag7_daily_hysteresis/META.json`
- `config/mag7_daily_hysteresis/MSFT.json`
- `config/mag7_daily_hysteresis/NVDA.json`
- `config/mag7_daily_hysteresis/TSLA.json`

**Hourly Swing configs (2 files):**
- `config/hourly_swing/NVDA.json`
- `config/hourly_swing/TSLA.json`

**Total: 20 JSON config files in /config**

---

### ✅ Perturbations Strategy Data Files

**FOMC economic events:**
- `research/Perturbations/fomc_straddles/economic_events_2024.json`

**Bear Trap results/deployment data (CSV):**
- `research/Perturbations/bear_trap/BEAR_TRAP_DEPLOY.csv`
- `research/Perturbations/bear_trap/BEAR_TRAP_VALIDATED_4YEAR.csv`
- `research/Perturbations/bear_trap/BEAR_TRAP_WFA.csv`
- `research/Perturbations/bear_trap/BEAR_TRAP_WINNERS.csv`

**Note:** These are **data files**, not configuration. The strategies have parameters embedded in their .py files and deployment guides.

---

## Strategy Configuration Approach

### Configuration is Stored In Multiple Places:

**1. Centralized Node Configs** (`/config/nodes/`)
- Used by main.py
- Per-ticker configurations
- RSI lookback, weights, intervals, etc.

**2. Strategy Parameter Documentation** (in Perturbations folders)
- `PARAMETERS.md` files document all strategy parameters
- Parameters are **hardcoded in the .py strategy files**
- Examples:
  - `research/Perturbations/bear_trap/PARAMETERS.md` - Full parameter spec
  - `research/Perturbations/bear_trap/bear_trap.py` - Has params dict in code

**3. Economic Event Data**
- `fomc_straddles/economic_events_2024.json` - FOMC event dates

**4. Results/Deployment Data** (CSV files)
- Bear Trap validation results
- Not configuration, but deployment artifacts

---

## /scripts Directory Analysis

**8 utility scripts:**

| File | Purpose | Keep? |
|------|---------|-------|
| `generate_configs.py` | Config file generator | ✅ KEEP - Utility |
| `generate_daily_signals.py` | Daily signal generation | ✅ KEEP - Operational |
| `prefetch_all_data.py` | Bulk data prefetch | ✅ KEEP - Utility |
| `prefetch_data.py` | Data prefetch script | ✅ KEEP - Utility |
| `prefetch_smallcap_1min.py` | Small-cap data prefetch | ✅ KEEP - Utility |
| `prefetch_smallcap_expanded.py` | Expanded small-cap prefetch | ✅ KEEP - Utility |
| `simulation_testing.py` | Simulation framework | ✅ KEEP - Testing utility |
| `update_master_config.py` | Config updater | ✅ KEEP - Utility |

**Verdict**: ✅ **KEEP all /scripts** - These are operational utilities

---

## Summary

### ✅ ALL Config Files Accounted For

**Primary configurations:**
- `/config/` - 20 JSON files (main system configs)
- `/config/__init__.py` - Config loader
- Perturbations data files - Economic events, deployment results

**Strategy parameters:**
- Documented in `PARAMETERS.md` files
- Hardcoded in strategy `.py` files  
- Example: bear_trap.py has params = {...} dict

**No config files will be lost** - everything is in:
1. `/config/` directory (KEEP)
2. `/research/Perturbations/` (KEEP)

### ✅ Scripts Directory

All 8 files are operational utilities:
- Data prefetching
- Config generation/updating
- Signal generation
- Simulation testing

**Keep entire /scripts directory**

---

## Action Items

✅ **KEEP**:
- Entire `/config/` directory
- Entire `/scripts/` directory  
- All Perturbations strategy folders (contain deployment data)

🗑️ **ARCHIVE**:
- None of the above - all are production

---

## Config Files: SAFE ✅

No configuration will be lost. Everything is accounted for and in the KEEP category.
