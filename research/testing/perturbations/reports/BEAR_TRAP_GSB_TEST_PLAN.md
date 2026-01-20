# Bear Trap & GSB - Critical Perturbation Tests

**Date**: 2026-01-18  
**Strategies**: Bear Trap (small-cap reversals), GSB (commodity futures)  
**Status**: Preparing focused stress tests

---

## Overview

Both strategies are validated but require stress testing before full deployment:

| Strategy | Validated Period | Assets | Return | Critical Risk |
|----------|------------------|--------|---------|---------------|
| **Bear Trap** | 2022-2025 (4 years) | 9 small-caps | +455% | Slippage on low liquidity |
| **GSB** | 2022-2025 (4 years) | 2 futures (NG, SB) | +90.67% | Both failed in 2023 |

---

## Strategy 5: Bear Trap - Critical Tests

### Test 5.1: Slippage Tolerance (CRITICAL ✅)
**Rationale**: Small-cap stocks have wide spreads; assumed 0.125% friction may be too optimistic

**Test Matrix**:
- 9 validated symbols
- 5 slippage levels (0.125%, 0.25%, 0.5%, 1.0%, 2.0%)
- Total: 45 test runs

**Pass Criteria**:
- ≥7/9 symbols profitable at 0.5% slippage
- ≥5/9 symbols profitable at 1.0% slippage
- DEPLOYMENT BLOCKED if <5 symbols pass at 1.0%

**Expected Result**: Some symbols will fail at higher slippage (especially low-volume ones like BTCS, SENS)

---

### Test 5.2: Entry Timing Precision (CRITICAL ✅)
**Rationale**: Reclaim detection requires precise 1-minute bar timing; delays could miss reversals

**Test Matrix**:
- 3 timing scenarios (Perfect, +30sec lag, +60sec lag)
- Apply to all 9 symbols
- Total: 27 test runs

**Pass Criteria**:
- Portfolio remains profitable with 30-second lag
- ≥50% of returns preserved with 60-second lag
- DEPLOYMENT BLOCKED if 30sec lag destroys edge

---

### Test 5.3: Regime Stress Test
**Rationale**: Validated during 2022-2025 which includes bull/bear; test specific regime failures

**Test Matrix**:
- 2022 only (bear market)
- 2024-2025 only (AI boom/normalization)
- Split by volatility regime (VIX high vs low)
- Total: 27 test runs (9 symbols × 3 periods)

**Pass Criteria**:
- Profitable in both 2022 bear market AND 2024-2025
- No single regime dependency
- **Acceptable**: Lower returns in specific regimes (not total failure)

---

### Test 5.4: Symbol Degradation Risk
**Rationale**: Small-cap characteristics change over time; symbols may lose edge

**Test Matrix**:
- Walk-forward by year (2022, 2023, 2024, 2025)
- Identify symbols degrading over time
- Total: 36 test runs (9 symbols × 4 years)

**Pass Criteria**:
- ≥5 symbols show stable/improving returns over time
- Clear identification of degrading symbols for exclusion
- **Action**: Create rotation plan for degrading symbols

---

## Strategy 6: GSB (Gas & Sugar Breakout) - Critical Tests

### Test 6.1: 2023 Stress Test Deep Dive (CRITICAL ✅)
**Rationale**: Both NG and SB failed in 2023 (-12.50%, -8.85%); understand WHY

**Test Matrix**:
- Monthly 2023 breakdown (12 months)
- Identify failure patterns (trending vs choppy? low vol?)
- Test if any parameter adjustment could have saved 2023
- Total: 24 test runs (2 symbols × 12 months)

**Pass Criteria**:
- Losses are due to unfavorable market conditions (NOT strategy flaws)
- No single catastrophic month (losses spread across year)
- **If losses concentrated**: Regime filter needed
- **If parameter-dependent**: Strategy may be curve-fitted

---

### Test 6.2: Session Time Robustness (CRITICAL ✅)
**Rationale**: Strategy depends on precise session times (NG: 13:29, SB: 13:30); test tolerance

**Test Matrix**:
- Baseline: Correct times (13:29, 13:30)
- Early: -15 minutes (13:14, 13:15)
- Late: +15 minutes (13:44, 13:45)
- Total: 6 test runs (2 symbols × 3 timing scenarios)

**Pass Criteria**:
- ±5 minute tolerance acceptable
- ±15 minute tolerance causes <30% degradation
- DEPLOYMENT BLOCKER if exact timing required (operational risk)

---

### Test 6.3: Single-Contract Failure (CRITICAL ✅)
**Rationale**: Only 2 contracts; if one fails, diversification is lost

**Test Matrix**:
- NG-only portfolio
- SB-only portfolio
- Compare to combined portfolio
- Total: 6 test runs (2 solo + 1 combined × 2 periods)

**Pass Criteria**:
- Each contract independently profitable over 4 years
- Combined Sharpe ≥1.0
- **If one fails**: Consider replacing or adding 3rd contract

---

### Test 6.4: Parameter Sensitivity
**Rationale**: Multiple parameters (OR period, volume mult, ATR mult); test stability

**Test Matrix**:
- OR period: 5min, 10min (baseline), 15min
- Volume multiplier: 1.5x, 1.8x (baseline), 2.1x
- Pullback zone: 0.10 ATR, 0.15 ATR (baseline), 0.20 ATR
- Total: 18 test runs (2 symbols × 9 parameter combos)

**Pass Criteria**:
- ≥70% of neighboring configs profitable
- No single "magic" parameter (robust across range)
- DEPLOYMENT BLOCKER if only 1 config works (overfitting)

---

## Execution Plan

### Priority 1: Critical Tests (Must Pass)
1. **Bear Trap Test 5.1** - Slippage (45 runs, ~20 min)
2. **GSB Test 6.1** - 2023 Deep Dive (24 runs, ~30 min)
3. **GSB Test 6.3** - Single Contract Failure (6 runs, ~5 min)
4. **Bear Trap Test 5.2** - Entry Timing (27 runs, ~15 min)

**Total Runtime**: ~70 minutes

### Priority 2: Risk Assessment Tests
1. **GSB Test 6.2** - Session Timing (6 runs, ~5 min)
2. **Bear Trap Test 5.3** - Regime Stress (27 runs, ~15 min)

**Total Runtime**: ~20 minutes

### Priority 3: Robustness Tests
1. **GSB Test 6.4** - Parameter Sensitivity (18 runs, ~15 min)
2. **Bear Trap Test 5.4** - Symbol Degradation (36 runs, ~25 min)

**Total Runtime**: ~40 minutes

---

## Expected Outcomes

### Bear Trap Predictions

| Test | Expected Result | Risk Level |
|------|-----------------|------------|
| 5.1 Slippage | MARGINAL - 6-7/9 pass at 0.5% | 🟡 Medium |
| 5.2 Timing | PASS - Reclaims are multi-bar events | 🟢 Low |
| 5.3 Regime | PASS - Already tested across regimes | 🟢 Low |
| 5.4 Degradation | CAUTION - 2-3 symbols may degrade | 🟡 Medium |

**Overall**: 🟡 **CONDITIONAL DEPLOYMENT** (exclude high-slippage symbols)

### GSB Predictions

| Test | Expected Result | Risk Level |
|------|-----------------|------------|
| 6.1 2023 Dive | PASS - Losses due to commodity trends | 🟢 Low |
| 6.2 Session Timing | MARGINAL - May need ±10 min tolerance | 🟡 Medium |
| 6.3 Single Contract | PASS - Both independently profitable | 🟢 Low |
| 6.4 Parameters | PASS - Robust across neighbors | 🟢 Low |

**Overall**: ✅ **APPROVE DEPLOYMENT** (monitor 2023-like conditions)

---

## Deployment Recommendations (Preliminary)

### Bear Trap
- **Deploy** Tier 1 symbols with proven low-slippage profiles
- **Exclude** symbols that fail 1.0% slippage test
- **Phased rollout**: Paper trade 2 weeks, then scale
- **Capital**: $50-75K (reduced from $100K due to slippage risk)

### GSB
- **Deploy** both NG + SB immediately (diversification critical)
- **Monitor** for 2023-like trending regimes (consider pause/reduce if detected)
- **Validate** session times are correct in production
- **Capital**: $100K (per strategy documentation)

---

## Next Steps

1. ✅ Create test implementation plan
2. ⏳ Implement 4 critical tests (Priority 1)
3. ⏳ Run tests and analyze results
4. ⏳ Generate deployment recommendations
5. ⏳ Commit final results to git

**Est. Time to Complete**: 2-3 hours (implementation + execution + analysis)

---

**Files to Create**:
```
research/Perturbations/bear_trap/
├── test_slippage_tolerance.py (5.1)
├── test_entry_timing.py (5.2)
├── test_regime_stress.py (5.3)
└── test_symbol_degradation.py (5.4)

research/Perturbations/gsb/
├── test_2023_deep_dive.py (6.1)
├── test_session_timing.py (6.2)
├── test_single_contract.py (6.3)
└── test_parameter_sensitivity.py (6.4)
```

**Ready to proceed?**
