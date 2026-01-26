# ✅ Intraday Alpha Testing Checklist

**Strategy**: Intraday Alpha V1.0 (Laminar DNA)  
**Testing Start Date**: _________________  
**Lead Analyst**: _________________

---

## 📋 PHASE 1: FORENSIC HISTORICAL RECONSTRUCTION

### Test 1.1: Clean-Room Backtest (2024-2025)
- [ ] Script developed: `run_phase1_baseline_backtest.py`
- [ ] Data cached: SPY/QQQ/IWM 1-min bars (Jan 2024 - Jan 2026)
- [ ] Backtest executed with +1 bar lag, 5 bps slippage
- [ ] Results logged to: `results/phase1_baseline_2024-2025.csv`

**Results**:
- Sharpe Ratio: _______ (Target: >1.0) ✅/❌
- Win Rate: _______% (Target: >45%) ✅/❌
- Profit Factor: _______ (Target: >1.3) ✅/❌
- Max Drawdown: _______% (Target: <20%) ✅/❌
- Trade Count: _______ (Target: >100) ✅/❌
- Total PnL: $_______ (Target: >$0) ✅/❌

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 1.2: Multi-Regime Stress (2022-2025)
- [ ] Script developed: `run_phase1_regime_stress.py` 
- [ ] Data cached: Full 4-year period (2022-2025)
- [ ] Backtest executed for each year separately
- [ ] Results aggregated and analyzed

**Year-by-Year Results**:

| Year | PnL | Sharpe | Win Rate | Max DD | Trades | Status |
|------|-----|--------|----------|--------|--------|--------|
| 2022 | $____ | ____ | ____% | ____% | ____ | ✅/❌ |
| 2023 | $____ | ____ | ____% | ____% | ____ | ✅/❌ |
| 2024 | $____ | ____ | ____% | ____% | ____ | ✅/❌ |
| 2025 | $____ | ____ | ____% | ____% | ____ | ✅/❌ |

**WFA-C Compliance** (3/4 years profitable): _______ years profitable ✅/❌

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 1.3: Data Integrity Audit
- [ ] Split verification: SPY/QQQ/IWM checked for stock splits (2022-2026)
- [ ] Dividend adjustments: Verified total return data
- [ ] Volume anomalies: Flagged >10x spikes, investigated root cause
- [ ] Bar continuity: Checked for gaps >30 min during market hours
- [ ] Secondary source validation: Spot-checked 10 trades against FMP data

**Issues Found**: _______________________________________________________

**Status**: ⬜ CLEAN / ⬜ MINOR ISSUES (documented) / ⬜ CRITICAL ERROR

---

## 🔥 PHASE 2: ADVERSARIAL PERTURBATION TESTING

### Test 2.1: Friction Escalation Ladder
- [ ] Script developed: `run_phase2_friction_ladder.py`
- [ ] Backtests run at 5, 10, 15, 20 bps slippage (2024 period)
- [ ] Breakeven friction calculated

**Results**:

| Friction (bps) | PnL | Sharpe | Win Rate | Status |
|---------------|-----|--------|----------|---------|
| 5 (baseline) | $____ | ____ | ____% | ✅/❌ |
| 10 (2x stress) | $____ | ____ | ____% | ✅/❌ |
| 15 | $____ | ____ | ____% | ✅/❌ |
| 20 (worst-case) | $____ | ____ | ____% | ✅/❌ |

**Breakeven Friction**: _______ bps (PnL crosses $0 at this level)

**10 bps Gate** (IVS requirement): ⬜ PASS / ⬜ FAIL

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 2.2: Parameter Stability Audit
- [ ] Script developed: `run_phase2_parameter_sweep.py`
- [ ] RSI lookback tested: 12, 13, 14, 15, 16
- [ ] Alpha threshold tested: 0.4, 0.45, 0.5, 0.55, 0.6
- [ ] Sentry gate tested: -0.1, 0.0, 0.1 (SPY/QQQ)

**Neighbor Profitability**:
- RSI neighbors profitable: _____/5 (Target: ≥4/5)
- Threshold neighbors profitable: _____/5 (Target: ≥4/5)
- Gate neighbors profitable: _____/3 (Target: ≥3/3)
- **Total**: _____/13 neighbors profitable (Target: ≥70% = 9/13)

**Performance Delta** (best vs. worst neighbor): _______% (Target: <30%)

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 2.3: Timing Shift Stress
- [ ] Entry lag tested: +1, +2, +3 bars
- [ ] Exit lag tested: +1, +2, +3 bars

**Results**:

| Lag (bars) | PnL | Sharpe | Degradation vs. Baseline |
|-----------|-----|--------|-------------------------|
| +1 (baseline) | $____ | ____ | 0% |
| +2 | $____ | ____ | ____% |
| +3 | $____ | ____ | ____% |

**+2 Bar Gate** (must remain profitable): ⬜ PASS / ⬜ FAIL

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 2.4: Sentiment Oracle Test
- [ ] Backtest run with sentiment = +0.5 (forced bullish)
- [ ] Backtest run with sentiment = -0.5 (forced bearish)
- [ ] Backtest run with sentiment = random [-0.5, +0.5]
- [ ] Results compared to baseline (sentiment = 0.0)

**Results**:

| Sentiment Mode | PnL | Sharpe | Alpha Contribution |
|----------------|-----|--------|-------------------|
| Neutral (0.0) | $____ | ____ | Baseline |
| Bullish (+0.5) | $____ | ____ | +____% |
| Bearish (-0.5) | $____ | ____ | ____% |
| Random | $____ | ____ | ____% |

**Dependency Assessment**:
- [ ] Low dependency (random ≥50% baseline Sharpe) ✅
- [ ] Moderate dependency (random 30-50% baseline)
- [ ] High dependency (random <30% baseline) ❌

**Status**: ⬜ LOW DEP / ⬜ MODERATE DEP / ⬜ HIGH DEP (risk)

---

## 📊 PHASE 3: STATISTICAL ROBUSTNESS

### Test 3.1: Monte Carlo Trade Shuffling
- [ ] Script developed: `run_phase3_monte_carlo.py`
- [ ] Extracted all trades from 2024 baseline backtest
- [ ] Shuffled trade sequence N=1,000 iterations
- [ ] Calculated PnL distribution, percentiles, CI

**Results**:
- Actual 2024 PnL: $_______
- Shuffled Mean PnL: $_______
- Shuffled Std Dev: $_______
- Actual Percentile Rank: _______% (Target: >75th)
- 95% CI: [$_______ to $_______]

**Luck Factor**: ⬜ SKILL (>75th) / ⬜ MIXED / ⬜ RANDOM (median)

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 3.2: Win Rate Significance
- [ ] Binomial test executed (H0: win rate = 50%)
- [ ] Sample size verified (need >100 trades)

**Results**:
- Win Rate: _______% 
- Trade Count: _______
- p-value: _______ (Target: <0.05)

**Statistical Significance**: ⬜ PASS (p<0.05 AND WR>50%) / ⬜ FAIL

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 3.3: Bootstrap Confidence Intervals
- [ ] Bootstrap sampling executed (N=1,000 iterations)
- [ ] 95% CI calculated for Sharpe, Total Return, Max DD

**Results**:

| Metric | Actual | 95% CI Lower | 95% CI Upper | Gate |
|--------|--------|--------------|--------------|------|
| Sharpe | ____ | ____ | ____ | Lower >0.5 ✅/❌ |
| Total Return | ____% | ____% | ____% | Lower >0% ✅/❌ |
| Max DD | ____% | ____% | ____% | Upper <25% ✅/❌ |

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

## ⚡ PHASE 4: INTRADAY-SPECIFIC VALIDATION

### Test 4.1: Frequency-Friction Audit
- [ ] Script developed: `run_phase4_frequency_audit.py`
- [ ] Calculated avg daily trades from 2024 backtest
- [ ] Computed annual friction burden

**Calculation**:
- Avg Daily Trades: _______ trades/day
- Annual Roundtrips: _______ × 252 = _______ roundtrips
- Friction per Roundtrip: _______ bps
- **Annual Friction**: (_______ × _______ bps) / $100,000 = _______% 

**Gates**:
- Annual Friction <15%: ⬜ PASS / ⬜ FAIL
- Gross Return / Friction Ratio: _______ (Target: >3.0x) ⬜ PASS / ⬜ FAIL

**Status**: ⬜ PASS / ⬜ FAIL (death spiral risk)

---

### Test 4.2: Session Performance Analysis
- [ ] Trades segmented by entry time (Open/Morning/Midday/Afternoon)
- [ ] Win rate and avg profit calculated per session

**Results**:

| Session | Time Window | Trades | Win Rate | Avg Profit | PnL Contribution |
|---------|------------|--------|----------|-----------|-----------------|
| Open | 9:30-10:00 | ____ | ____% | $____ | ____% |
| Morning | 10:00-11:30 | ____ | ____% | $____ | ____% |
| Midday | 11:30-14:00 | ____ | ____% | $____ | ____% |
| Afternoon | 14:00-16:00 | ____ | ____% | $____ | ____% |

**Concentration Risk**: Opening 30 min = _______% of total PnL (⚠️ if >70%)

**Status**: ⬜ DIVERSIFIED / ⬜ CONCENTRATED (risk)

---

### Test 4.3: Latency Simulation
- [ ] Baseline backtest latency overhead calculated (67ms residential)
- [ ] Re-run with +1 bps latency penalty added

**Results**:
- Baseline (no latency adjustment): Sharpe = _______
- With 67ms latency penalty: Sharpe = _______
- Degradation: _______% (acceptable if <20%)

**Latency Impact**: ⬜ MINIMAL (<10%) / ⬜ MODERATE (10-20%) / ⬜ SEVERE (>20%)

**Status**: ⬜ PASS / ⬜ WARNING / ⬜ FAIL

---

## 🎮 PHASE 5: PAPER TRADING LIVE (10 Days)

### Test 5.1: Forward Test Setup
- [ ] Script developed: `deploy_phase5_paper_trading.py`
- [ ] Deployed to Alpaca Paper Trading account
- [ ] Real-time logging enabled (signals, orders, fills, errors)
- [ ] Daily monitoring dashboard configured

**Test Period**: _____________ to _____________ (10 trading days)

**Daily Log**:

| Date | Trades | Fills | Avg Slippage (bps) | Daily PnL | Errors | Notes |
|------|--------|-------|-------------------|-----------|--------|-------|
| Day 1 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 2 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 3 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 4 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 5 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 6 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 7 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 8 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 9 | ____ | ____% | ____ | $____ | ____ | ____________ |
| Day 10 | ____ | ____% | ____ | $____ | ____ | ____________ |

**Summary Metrics**:
- Total Trades: _______
- Fill Rate: _______% (Target: >95%) ✅/❌
- Avg Slippage: _______ bps (Target: ≤5 bps) ✅/❌
- Total PnL: $_______
- Live Sharpe: _______ (compare to backtest)
- Critical Errors: _______ (Target: 0) ✅/❌

**Status**: ⬜ PASS / ⬜ CONDITIONAL / ⬜ FAIL

---

### Test 5.2: Regime Kill-Switch Test
- [ ] Simulated bearish sentiment event (or waited for VIX >25 day)
- [ ] Verified SPY/QQQ suppress signals (gate = 0.0)
- [ ] Verified IWM continues if sentiment > -0.2

**Test Results**:
- Date of test: _____________
- Sentiment level: _______
- SPY signals suppressed: ⬜ YES / ⬜ NO (should be YES)
- QQQ signals suppressed: ⬜ YES / ⬜ NO (should be YES)
- IWM behavior: ⬜ CORRECT / ⬜ INCORRECT

**Status**: ⬜ PASS / ⬜ FAIL

---

### Test 5.3: Circuit Breaker Testing
- [ ] Position Cap Test: Account boosted to $1M → verify $50k cap enforced
- [ ] PDT Test: Account reduced to $20k → verify trading halts
- [ ] Buying Power Test: Simulated margin call → verify no unfunded orders

**Results**:
- Position Cap Enforced: ⬜ YES / ⬜ NO
- PDT Protection Active: ⬜ YES / ⬜ NO
- Buying Power Check: ⬜ YES / ⬜ NO
- Graceful Degradation (no crashes): ⬜ YES / ⬜ NO

**Status**: ⬜ PASS / ⬜ FAIL

---

## 🚦 PHASE 6: FINAL GO/NO-GO DECISION

### Quantitative Gates Summary (9 Required)

| Gate # | Metric | Target | Actual | Status |
|--------|--------|--------|--------|--------|
| 1 | 4-Year Composite Sharpe | >1.0 | ____ | ⬜ ✅ / ⬜ ❌ |
| 2 | Win Rate + Significance | >45% AND p<0.05 | ____%, p=____ | ⬜ ✅ / ⬜ ❌ |
| 3 | 3/4 Year Profitability | ≥3 years | ____ years | ⬜ ✅ / ⬜ ❌ |
| 4 | Profitable at 10 bps | PnL >$0 | $____ | ⬜ ✅ / ⬜ ❌ |
| 5 | Annual Friction | <15% | ____% | ⬜ ✅ / ⬜ ❌ |
| 6 | Max Drawdown | <20% | ____% | ⬜ ✅ / ⬜ ❌ |
| 7 | Parameter Stability | ≥70% neighbors | ____% | ⬜ ✅ / ⬜ ❌ |
| 8 | Trade Count | >100/year | ____ | ⬜ ✅ / ⬜ ❌ |
| 9 | Profit Factor | >1.3 | ____ | ⬜ ✅ / ⬜ ❌ |

**Quantitative Score**: _____/9 gates passed (_____%)

---

### Qualitative Gates Summary (5 Required)

| Gate # | Criteria | Status | Notes |
|--------|----------|--------|-------|
| 1 | Paper Trading Success (fill >95%, slip ≤5bps) | ⬜ ✅ / ⬜ ❌ | _____________ |
| 2 | Sentiment Independence (viable without perfect data) | ⬜ ✅ / ⬜ ❌ | _____________ |
| 3 | Infrastructure Ready (latency <100ms, uptime >99.5%) | ⬜ ✅ / ⬜ ❌ | _____________ |
| 4 | Code Audit (production-grade, no hardcoded values) | ⬜ ✅ / ⬜ ❌ | _____________ |
| 5 | Operational Runbook (documented procedures) | ⬜ ✅ / ⬜ ❌ | _____________ |

**Qualitative Score**: _____/5 gates passed (_____%)

---

### FINAL VERDICT

**Total Gates Passed**: _____/14 (_____%)

**Sharpe Ratio (4-Year)**: _______

**Deployment Recommendation**:

⬜ **APPROVED (Full Deployment)**
- Capital Allocation: $100,000
- Review Period: Monthly
- Conditions: _________________________________________________

⬜ **CONDITIONAL APPROVAL**
- Capital Allocation: $50,000 (reduced risk)
- Review Period: Weekly for 30 days
- Conditions: _________________________________________________

⬜ **PAPER-ONLY (Extended Testing)**
- Capital Allocation: $0 (paper trading only)
- Extended Test: 60 days
- Re-evaluation Date: _____________
- Conditions: _________________________________________________

⬜ **REJECTED**
- Reason: ____________________________________________________
- Archive Date: _____________
- Lessons Learned: ___________________________________________

---

**Decision Date**: _________________  
**Decision Maker**: _________________  
**Signature**: _________________

---

## 📝 Post-Decision Actions

### If APPROVED or CONDITIONAL:
- [ ] Production deployment package prepared
- [ ] Operational runbook finalized
- [ ] Monitoring dashboard configured
- [ ] Capital allocated to strategy account
- [ ] First review meeting scheduled for: _____________

### If PAPER-ONLY:
- [ ] Extended paper trading period configured (60 days)
- [ ] Enhanced monitoring added for specific risk areas
- [ ] Re-evaluation checklist prepared
- [ ] Next decision date: _____________

### If REJECTED:
- [ ] Strategy archived to: `archive/intraday_alpha_v1/`
- [ ] Lessons learned documented in KI
- [ ] Test results preserved for future reference
- [ ] Team debriefing scheduled for: _____________

---

**Checklist Complete**: _________________  
**Final Report Delivered**: _________________
