# Magellan Perturbation Testing — Master Summary

**Project**: Pre-Deployment Perturbation Testing for4 Validated Trading Strategies  
**Objective**: Stress-test each strategy's robustness against real-world deployment risks  
**Approach**: Strategy-specific targeted perturbations (no unnecessary over-testing)  
**Report Date**: 2026-01-18  
**Status**: 🟡 Testing Protocols Defined — Awaiting Execution

---

## Executive Summary

This document consolidates perturbation testing protocols for **4 production-ready trading strategies** that have completed initial validation but require final stress testing before live deployment. Each strategy has been analyzed for its unique structural vulnerabilities and assigned **focused, pragmatic perturbation tests** that target actual deployment risks rather than exhaustive theoretical scenarios.

**Total Testing Scope**: 16 perturbation tests across 4 strategies (4 tests per strategy)  
**Total Test Executions**: ~350 individual backtest runs  
**Estimated Timeline**: 5-7 business days from approval to deployment readiness

---

## Strategy Overview & Risk Profiles

| Strategy | Capital | Trades/Year | Validated Sharpe | Primary Risks | Tests Designed |
|----------|---------|-------------|------------------|---------------|----------------|
| **Daily Trend Hysteresis** | $110K (69%) | 70-100 | 1.2-1.4 | Parameter overfitting, friction, regime shifts, correlation | 4 |
| **Hourly Swing** | $20K (12%) | 105-240 | ~1.0 | Gap reversal, execution timing, friction, concentration | 4 |
| **FOMC Straddles** | $10K/event | 8 | 1.17 | Timing precision, slippage, IV crush, execution failure | 4 |
| **Earnings Straddles** | $10K/event | 4-28 | 2.25 | Ticker robustness, entry timing, IV crush, regime normalization | 4 |

**Combined Portfolio**: $160K allocation, 200-375 trades/year, 1.5-2.0 expected Sharpe, 50-80% expected annual return

---

## Testing Philosophy: Focused Perturbation

### Core Principle
**Perturb only what makes sense for each strategy's actual deployment context.**

Traditional perturbation testing applies the same stress tests to all strategies (e.g., "test all strategies in a bear market"). This approach:
- ✅ Ensures comprehensive coverage
- ❌ Wastes time testing irrelevant scenarios
- ❌ Creates false precision (testing FOMC 10-minute trades against multi-year regime shifts is meaningless)

### Our Approach
Each strategy receives **4 custom-designed tests** targeting its specific vulnerabilities:

#### Example 1: Daily Trend (19-month validation, 11 assets)
- ✅ **Parameter robustness** — Validate RSI-21 vs RSI-28 isn't overfitted
- ✅ **Friction sensitivity** — 70-100 trades/year means slippage matters
- ✅ **Regime shift stress** — 2024-2025 was bullish; test bear market resilience
- ✅ **Correlation risk** — MAG7 stocks highly correlated; test diversification
- ❌ **NOT testing**: Execution timing (daily bars = no precision required)
- ❌ **NOT testing**: IV dynamics (equity strategy, not options)

#### Example 2: FOMC Straddles (10-minute hold, 8 events)
- ✅ **Timing precision** — ±5 minutes could destroy edge
- ✅ **Bid-ask slippage** — Options spreads widen 2-5× during FOMC
- ✅ **IV crush speed** — If IV collapses faster than SPY moves, loses value
- ✅ **Execution failure** — Broker outages, partial fills during high-volume events
- ❌ **NOT testing**: Multi-year regime shifts (irrelevant for 10-minute trades)
- ❌ **NOT testing**: Parameter robustness (no parameter optimization; fixed T-5/T+5 window)

---

## Test Catalog by Strategy

### Strategy 1: Daily Trend Hysteresis

| Test ID | Test Name | Scenarios | Purpose | Pass Criteria |
|---------|-----------|-----------|---------|---------------|
| **1.1** | Parameter Robustness | 66 runs | Validate RSI/bands not overfitted | ≥70% neighboring configs profitable |
| **1.2** | Friction Sensitivity | 55 runs | Determine slippage tolerance | All assets profitable at 10 bps |
| **1.3** | Regime Shift Stress | 33 runs | Test bear market resilience | Max DD ≤35% in synthetic stress |
| **1.4** | Correlation Breakdown | 10,014 runs | Assess diversification risk | No asset contributes >40% of returns |

**Total**: 10,168 test executions  
**Critical**: Friction test — strategy MUST survive 15 bps slippage to be deployable

---

### Strategy 2: Hourly Swing Trading

| Test ID | Test Name | Scenarios | Purpose | Pass Criteria |
|---------|-----------|-----------|---------|---------------|
| **2.1** | Gap Reversal Stress | 6 runs | Quantify overnight gap dependency | Profitable even with 50% gap fading |
| **2.2** | Execution Timing | 12 runs | Validate precision requirements | <15% degradation at 30-min lag |
| **2.3** | Friction Extreme Stress | 12 runs | Determine friction breakeven | Both assets profitable at 20 bps |
| **2.4** | Single-Asset Failure | 6 runs | Assess 2-asset concentration | Combined Sharpe ≥1.0 even if one fails |

**Total**: 36 test executions  
**Critical**: Gap reversal — if 100% fade causes losses, strategy may not be deployable

---

### Strategy 3: FOMC Event Straddles

| Test ID | Test Name | Scenarios | Purpose | Pass Criteria |
|---------|-----------|-----------|---------|---------------|
| **3.1** | Timing Window Robustness | 56 runs | Test entry/exit tolerance | ≥75% win rate with ±3 min window |
| **3.2** | Bid-Ask Spread Stress | 40 runs | Quantify true execution costs | ≥75% win rate at 1.0% slippage |
| **3.3** | IV Crush vs Realized Move | 32 runs | Validate edge isn't IV-dependent | ≥50% win rate with -60% IV crush |
| **3.4** | Execution Failure Contingency | Scenarios | Risk analysis (not backtest) | Expected loss <5% per event |

**Total**: 128 test executions + failure scenario analysis  
**Critical**: Slippage test — 1.0% round-trip tolerance is MANDATORY for deployment

---

### Strategy 4: Earnings Straddles

| Test ID | Test Name | Scenarios | Purpose | Pass Criteria |
|---------|-----------|-----------|---------|---------------|
| **4.1** | Ticker Robustness | 13 runs | Validate diversification works | No-GOOGL Sharpe ≥1.5 |
| **4.2** | Entry Timing Sensitivity | 11 runs | Test T-2 vs T-1 vs T-0 entry | T-1 entry degradation ≤20% |
| **4.3** | IV Crush Severity | 12 runs | Quantify IV collapse tolerance | Win rate ≥40% in severe crush |
| **4.4** | Regime Normalization | 21 runs | Stress AI boom reversal | Sharpe ≥1.0 with -50% move normalization |

**Total**: 57 test executions  
**Critical**: Regime normalization — if edge only exists during AI boom, not sustainable

---

## Risk-Adjusted Deployment Matrix

### Pre-Testing (Current State)
| Strategy | Validated | Deployment-Ready? | Blocker |
|----------|-----------|-------------------|---------|
| Daily Trend | ✅ 19 months | 🟡 Pending Tests | Friction/regime unknown |
| Hourly Swing | ✅ Full 2025 | 🟡 Pending Tests | Gap dependency unknown |
| FOMC Straddles | ✅ 8 events | 🟡 Pending Tests | Slippage tolerance unknown |
| Earnings Straddles | ✅ 6 years WFA | 🟡 Pending Tests | Regime dependency unknown |

### Post-Testing Scenarios

#### Scenario A: All Tests Pass (100% Pass Rate)
| Strategy | Capital | Deployment Plan |
|----------|---------|-----------------|
| Daily Trend | $110K | Deploy all 11 assets immediately |
| Hourly Swing | $20K | Deploy TSLA + NVDA (50/50 allocation) |
| FOMC Straddles | $10K/event | Deploy starting Jan 29, 2025 FOMC |
| Earnings Straddles | $10K/event | Phase 1: GOOGL only (Q1 2025) |

**Total Capital**: $160K  
**Expected Annual Return**: +60-80%  
**Expected Sharpe**: 1.6-2.0

#### Scenario B: Partial Pass (75% Pass Rate)
| Strategy | Test Failures | Adjusted Deployment |
|----------|---------------|---------------------|
| Daily Trend | Friction test marginal (12 bps tolerance) | Reduce to 8 best assets; use limit orders |
| Hourly Swing | Gap reversal severe (100% fade = losses) | TSLA-only; $10K allocation (drop NVDA) |
| FOMC Straddles | Timing fragile (T-5 exact required) | Paper trade 2 events before live |
| Earnings Straddles | GOOGL-dependent (no-GOOGL Sharpe <1.5) | GOOGL-only deployment; paper trade others |

**Total Capital**: $120K  
**Expected Annual Return**: +40-60%  
**Expected Sharpe**: 1.2-1.5

#### Scenario C: Critical Failures (50% Pass Rate)
| Strategy | Critical Failure | Action |
|----------|------------------|--------|
| Daily Trend | Friction <10 bps tolerance | ❌ **DO NOT DEPLOY** (undeployable with realistic slippage) |
| Hourly Swing | Gap reversal catastrophic | ❌ **DO NOT DEPLOY** (edge doesn't exist) |
| FOMC Straddles | Slippage destroys edge | 🟡 **Deploy only on "big FOMC" events** (expected SPY move >0.5%) |
| Earnings Straddles | AI boom only (fails normalization) | 🟡 **Reduced allocation** ($5K/event; GOOGL+AAPL only) |

**Total Capital**: $50K (Daily/Hourly dropped; options strategies reduced)  
**Expected Annual Return**: +30-50%  
**Expected Sharpe**: 1.0-1.3

---

## Implementation Roadmap

### Phase 1: Test Development (2 Days)
**Deliverables**:
- [ ] 4 Python scripts for Daily Trend (`research/Perturbations/daily_trend_hysteresis/`)
- [ ] 4 Python scripts for Hourly Swing (`research/Perturbations/hourly_swing/`)
- [ ] 4 Python scripts for FOMC Straddles (`research/Perturbations/fomc_straddles/`)
- [ ] 4 Python scripts for Earnings Straddles (`research/Perturbations/earnings_straddles/`)

**Owner**: Quantitative Research Team  
**Blocker**: None (all data already cached from previous validation)

### Phase 2: Test Execution (2 Days)
**Execution Plan**:
1. **Day 1 AM**: Run Daily Trend tests (10,168 runs — longest, start first)
2. **Day 1 PM**: Run Earnings Straddles tests (57 runs)
3. **Day 2 AM**: Run FOMC Straddles tests (128 runs)
4. **Day 2 PM**: Run Hourly Swing tests (36 runs)

**Total Compute Time**: ~6 hours (parallelizable; can run overnight)  
**Manual Time**: ~4 hours (reviewing outputs, flagging failures)

### Phase 3: Analysis & Reporting (2 Days)
**Deliverables**:
- [ ] Pass/fail determination for each test
- [ ] Risk quantification matrices
- [ ] Adjusted deployment recommendations
- [ ] Mitigation strategies for marginal failures
- [ ] Final Go/No-Go decision per strategy

**Owner**: Quantitative Research Team + Risk Review

### Phase 4: Deployment Decision (1 Day)
**Decision Framework**:
| Test Results | Decision | Next Action |
|--------------|----------|-------------|
| **100% Pass** | ✅ Full Deployment | Execute deployment plan immediately |
| **≥75% Pass** | 🟡 Conditional Deployment | Deploy with reduced allocation/stricter controls |
| **<75% Pass** | ⚠️ Selective Deployment | Deploy only strategies that passed; reject failures |
| **<50% Pass** | ❌ Pause Deployment | Return to validation; re-evaluate strategy logic |

---

## Success Metrics

### Testing Phase
| Metric | Target |
|--------|--------|
| **Script Development** | 16 scripts complete in 2 days |
| **Test Execution** | All 10,389 runs complete in 2 days |
| **Zero False Positives** | No tests fail due to implementation bugs |
| **Actionable Results** | Clear pass/fail for each test; deployment plan ready |

### Deployment Phase (First 3 Months Post-Deployment)
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Portfolio Sharpe** | ≥1.4 | <1.0 for 1 month |
| **Individual Strategy Sharpe** | Each ≥1.0 | Any strategy <0.5 for 1 month |
| **Actual vs Expected Friction** | Within ±3 bps | >5 bps difference (execution quality issue) |
| **Perturbation Predictions** | Actual live performance within ±20% of stressed scenarios | >30% deviation (model error) |

---

## Appendices

### A. Directory Structure
```
research/Perturbations/
├── daily_trend_hysteresis/
│   ├── test_parameter_robustness.py
│   ├── test_friction_sensitivity.py
│   ├── test_regime_shift.py
│   └── test_correlation_breakdown.py
├── hourly_swing/
│   ├── test_gap_reversal.py
│   ├── test_execution_timing.py
│   ├── test_friction_extreme.py
│   └── test_single_asset_failure.py
├── fomc_straddles/
│   ├── test_timing_window.py
│   ├── test_bid_ask_spread.py
│   ├── test_iv_crush.py
│   └── test_execution_failure.py
├── earnings_straddles/
│   ├── test_ticker_robustness.py
│   ├── test_entry_timing.py
│   ├── test_iv_crush_severity.py
│   └── test_regime_normalization.py
└── reports/
    ├── daily_trend_hysteresis_perturbation_report.md ✅
    ├── hourly_swing_perturbation_report.md ✅
    ├── fomc_straddles_perturbation_report.md ✅
    ├── earnings_straddles_perturbation_report.md ✅
    └── master_perturbation_summary.md ✅ (this document)
```

### B. Test Execution Commands
```bash
# Daily Trend Hysteresis (10,168 runs — run overnight)
python research/Perturbations/daily_trend_hysteresis/test_parameter_robustness.py
python research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py
python research/Perturbations/daily_trend_hysteresis/test_regime_shift.py
python research/Perturbations/daily_trend_hysteresis/test_correlation_breakdown.py

# Hourly Swing (36 runs — ~30 minutes)
python research/Perturbations/hourly_swing/test_gap_reversal.py
python research/Perturbations/hourly_swing/test_execution_timing.py
python research/Perturbations/hourly_swing/test_friction_extreme.py
python research/Perturbations/hourly_swing/test_single_asset_failure.py

# FOMC Straddles (128 runs — ~1 hour)
python research/Perturbations/fomc_straddles/test_timing_window.py
python research/Perturbations/fomc_straddles/test_bid_ask_spread.py
python research/Perturbations/fomc_straddles/test_iv_crush.py
python research/Perturbations/fomc_straddles/test_execution_failure.py

# Earnings Straddles (57 runs — ~30 minutes)
python research/Perturbations/earnings_straddles/test_ticker_robustness.py
python research/Perturbations/earnings_straddles/test_entry_timing.py
python research/Perturbations/earnings_straddles/test_iv_crush_severity.py
python research/Perturbations/earnings_straddles/test_regime_normalization.py
```

### C. Critical Tests (Must Pass for Deployment)

| Strategy | Critical Test | Rationale |
|----------|---------------|-----------|
| **Daily Trend** | Friction Sensitivity (Test 1.2) | High turnover = friction can destroy edge |
| **Hourly Swing** | Gap Reversal Stress (Test 2.1) | Strategy depends on gap profits |
| **FOMC Straddles** | Bid-Ask Spread Stress (Test 3.2) | Realistic slippage = 1.0% minimum tolerance |
| **Earnings Straddles** | Regime Normalization (Test 4.4) | AI boom may not be sustainable |

**Deployment Rule**: If any critical test fails, that strategy is **NOT deployable** until the issue is resolved (parameter tuning, reduced allocation, or strategy rejection).

---

## Questions for Review

Before proceeding with test execution, please confirm:

1. **Scope Approval**: Are these 16 tests (4 per strategy) the right balance of rigor vs efficiency?
2. **Pass Criteria**: Do the pass/fail thresholds align with your risk tolerance?
3. **Timeline**: Is 5-7 days acceptable, or is there urgency to deploy sooner?
4. **Critical Tests**: Do you agree with the "critical test" designations, or should others be added?
5. **Deployment Capital**: Is the $160K total allocation correct, or should it be adjusted?
6. **Next FOMC Event**: Jan 29, 2025 is in 4 business days. Should we fast-track FOMC testing to catch this trade?

---

**Report Status**: 🟢 **READY FOR REVIEW**  
**Next Action**: Await user approval → Begin Phase 1 (Test Development)  
**Owner**: Quantitative Research Team  
**Last Updated**: 2026-01-18

---

## Summary of Deliverables

### Completed:
✅ **Implementation Plan** — Strategy-specific perturbation design  
✅ **Daily Trend Report** — 4 tests, 10,168 runs, friction/regime/correlation focus  
✅ **Hourly Swing Report** — 4 tests, 36 runs, gap/timing/friction focus  
✅ **FOMC Straddles Report** — 4 tests, 128 runs, timing/slippage/IV crush focus  
✅ **Earnings Straddles Report** — 4 tests, 57 runs, ticker/regime/IV crush focus  
✅ **Master Summary** — Consolidated testing roadmap and deployment scenarios (this document)

### Pending User Approval:
- [ ] Proceed with Phase 1 (Test Development)?
- [ ] Any adjustments to test design or pass criteria?
- [ ] Priority order (e.g., fast-track FOMC for Jan 29 event)?
