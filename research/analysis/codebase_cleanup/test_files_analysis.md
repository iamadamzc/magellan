# Test File Analysis - Complete Inventory

**Date**: 2026-01-18  
**Total test_*.py files**: 78

---

## Summary by Location

| Location | Count | Status |
|----------|-------|--------|
| **Root directory** | 27 | 🗑️ ARCHIVE (ORB iterations v4-v12) |
| **research/new_strategy_builds/** | 25 | 🗑️ ARCHIVE (development tests) |
| **research/Perturbations/** | 9 | ✅ KEEP (validated tests) |
| **research/backtests/options/** | 9 | 🗑️ ARCHIVE (old options tests) |
| **research/high_frequency/** | 3 | 🗑️ ARCHIVE (failed HFT) |
| **research/websocket_poc/** | 2 | 🗑️ ARCHIVE (POC complete) |
| **research/alternative_data/** | 1 | 🗑️ ARCHIVE (experiment) |
| **Other research/** | 2 | 🗑️ ARCHIVE |

---

## Detailed Breakdown

### ✅ KEEP - Validated Strategy Tests (9 files)

**Location**: `research/Perturbations/`

These are the ONLY tests we need to keep - they validate deployment:

```
research/Perturbations/bear_trap/
├── test_slippage_tolerance.py          ✅ Critical test
├── test_bear_trap_4year.py             ✅ Validation 
├── test_bear_trap_50.py                ✅ Additional validation
├── test_bear_trap_missing.py           ✅ Edge case test
└── test_bear_trap_wfa.py               ✅ Walk-forward analysis

research/Perturbations/daily_trend_hysteresis/
└── test_friction_sensitivity.py        ✅ Critical test

research/Perturbations/hourly_swing/
└── test_gap_reversal.py                ✅ Critical test

research/Perturbations/fomc_straddles/
└── test_bid_ask_spread.py              ✅ Critical test

research/Perturbations/earnings_straddles/
└── test_regime_normalization.py        ✅ Critical test

research/Perturbations/
└── test_nvda_quick.py                  ⚠️ Diagnostic (probably archive)
```

**Action**: Keep the Perturbations tests, maybe archive test_nvda_quick.py

---

### 🗑️ ARCHIVE - Root Directory ORB Iterations (27 files)

**Location**: Root `/`

All ORB version iterations - development history, superseded:

```
test_orb.py
test_orb_opt.py  
test_orb_final.py
test_orb_v4.py
test_orb_v5.py
test_orb_v6.py
test_orb_v7.py
test_orb_v7_FULL_UNIVERSE.py
test_orb_v7_RECOVER.py
test_orb_v8.py
test_orb_v8_paradox.py
test_orb_v8_timeframes.py
test_orb_v9.py
test_orb_v9_quick.py
test_orb_v9_universe.py
test_orb_v10.py
test_orb_v10_quick.py
test_orb_v10b_batch.py
test_orb_v10c_batch.py
test_v10_surgical.py
test_v10d.py
test_v10e.py
test_v11_quick.py
test_v12_quick.py
test_v7_5min_fmp.py
test_v7_5min_quick.py
test_vwap_v2.py
```

**Action**: Archive all to `archive/session_outputs/root_test_scripts/`

---

### 🗑️ ARCHIVE - Strategy Development Tests (25 files)

**Location**: `research/new_strategy_builds/`

Development/iteration tests - superseded by Perturbations:

```
Bear Trap tests (duplicates of Perturbations):
├── test_bear_trap_4year.py
├── test_bear_trap_50.py
├── test_bear_trap_missing.py
└── test_bear_trap_wfa.py

ORB/GSB tests (iterations):
├── test_orb_universe.py
├── test_orb_v13_RIOT_ABLATION.py
├── test_v13b_quick.py
├── test_v14_quick.py
├── test_v15_quick.py
├── test_v16_regime.py
├── test_v17_full_validation.py
├── test_v17_multi_asset_hunt.py
├── test_v17_quick.py
├── test_v18_final.py
├── test_v19_all_commodities_final.py
├── test_v19_alpaca_futures_final.py
├── test_v19_futures.py
├── test_v19_futures_fixed.py
├── test_v19_quick.py
├── test_v21_all_final.py
├── test_v22_vs_v21.py
├── test_v23_extended_validation.py
└── test_v23_vs_v22.py

Other:
├── test_all_commodities_forex.py
├── test_extended_period.py
├── test_sequential_tweaks.py
├── test_vwap_incremental.py
├── test_walk_forward_simple.py
└── test_walk_forward_universe.py
```

**Action**: Archive all to `archive/strategy_development/new_strategy_builds/tests/`

---

### 🗑️ ARCHIVE - Options Backtest Tests (9 files)

**Location**: `research/backtests/options/`

Old options strategy tests - superseded by Perturbations:

```
test_earnings_simple.py
test_earnings_straddles.py

phase2_validation/
├── test_nvda_system4.py
├── test_premium_selling.py
├── test_premium_selling_simple.py
├── test_spy_baseline.py
├── test_system3_momentum.py
└── test_system4_fixed_duration.py
```

**Action**: Archive entire `research/backtests/` folder

---

### 🗑️ ARCHIVE - Failed Experiments (6 files)

Various failed experiments:

```
research/high_frequency/
├── test_qqq_simple.py
└── (2 more HFT test files)

research/websocket_poc/
├── test_fmp_1min_data.py
└── test_fmp_endpoints.py

research/alternative_data/
└── test_stable_endpoints.py
```

**Action**: Archive with their parent folders

---

## Cleanup Impact

### Before
- 78 test files scattered across repository
- Hard to find the "real" tests
- Unclear which tests are current

### After  
- 8-9 test files in `research/Perturbations/`
- All validated, deployment-critical
- Clear purpose and hierarchy
- 69 test files archived (88% reduction)

---

## Recommended Actions

### Immediate (Safe to Execute)

1. **Archive root test scripts** (27 files):
   ```bash
   mkdir -p archive/session_outputs/root_test_scripts
   mv test_*.py archive/session_outputs/root_test_scripts/
   ```

2. **Archive new_strategy_builds tests** (25 files):
   ```bash
   mkdir -p archive/strategy_development/new_strategy_builds/tests
   mv research/new_strategy_builds/test_*.py archive/strategy_development/new_strategy_builds/tests/
   ```

3. **Archive old backtests** (entire folder):
   ```bash
   mv research/backtests archive/research_archive/
   ```

4. **Archive experiments** (with parent folders):
   ```bash
   mv research/high_frequency archive/research_archive/
   mv research/websocket_poc archive/research_archive/
   mv research/alternative_data archive/research_archive/
   ```

### Result
- **Keep**: 8-9 tests in Perturbations
- **Archive**: 69 tests  
- **Reduction**: 88%

---

**Ready to execute or want to review more categories first?**
