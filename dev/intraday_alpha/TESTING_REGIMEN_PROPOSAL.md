# 🎯 Institutional Testing Regimen for Intraday Alpha Strategy
## Comprehensive Validation Suite for Paper & Live Deployment Readiness

**Strategy**: Intraday Alpha V1.0 (Laminar DNA)  
**Universe**: SPY, QQQ, IWM (Index ETFs)  
**Timeframes**: 3-5 minute bars  
**Original Deployment**: January 10, 2026 (Replaced by MAG7 on Jan 11, 2026)  
**Prepared**: January 24, 2026

---

## 🔬 Executive Summary

This testing regimen applies **Magellan's Institutional Validation Standard (IVS)** to the archived Intraday Alpha strategy to determine if it should be reactivated for live deployment. The strategy is a **high-frequency intraday system** operating on 3-5 minute bars, making it critically sensitive to execution latency, regime shifts, and friction costs.

### Key Risk Factors Identified:
1. **Execution Latency Sensitivity**: 3-5 min hold periods = extreme vulnerability to slippage/latency
2. **Frequency-Friction Death Spiral**: High trade frequency compounds friction costs exponentially
3. **Regime Dependency**: Original deployment was 1 day before strategy pivot—potential recency bias
4. **Sentiment Data Dependency**: V1.0 relied on external sentiment data (currently placeholder = 0.0)
5. **Market Structure Evolution**: 2+ week gap since deployment—microstructure may have shifted

---

## 📋 Testing Framework: 5-Phase Validation Pipeline

This regimen follows the **institutional "trust-but-verify" philosophy**: independent validation, adversarial stress testing, and production simulation before capital deployment.

---

## PHASE 1: Forensic Historical Reconstruction (Baseline Truth)
**Objective**: Establish the "true historical performance" under realistic execution assumptions

### Test 1.1: Clean-Room Backtest (2024-2025 Full Period)
**Purpose**: Verify baseline profitability across recent bull market regime

**Parameters**:
- **Period**: January 1, 2024 → January 10, 2026 (deployment date)
- **Assets**: SPY, QQQ, IWM (as configured)
- **Execution Model**: 
  - Signal on bar close → Fill on next bar open (+1 bar lag)
  - Market orders with 5 bps slippage assumption per trade
  - No partial fills (conservative)
- **Warmup**: 100 bars (sufficient for RSI-14 + volume MA-20)
- **Capital**: $100,000 initial (25% allocation per position = $25k max, capped at $50k config)

**Success Criteria**:
- ✅ Sharpe Ratio > 1.0
- ✅ Win Rate > 45%
- ✅ Profit Factor > 1.3
- ✅ Max Drawdown < 20%
- ✅ Trade Count > 100 (statistical significance)

**Failure Indicators**:
- ❌ Negative total PnL
- ❌ Sharpe < 0.5 (no edge after friction)
- ❌ Trade count < 50 (insufficient data)

---

### Test 1.2: Multi-Regime Stress Test (2022-2025 Extended)
**Purpose**: Test resilience across Bear (2022), Recovery (2023), Bull (2024-25) regimes

**Parameters**:
- **Period**: January 1, 2022 → January 10, 2026 (4 full years)
- **Regime Segmentation**:
  - 2022: Bear Market (Fed tightening, SPY -18%)
  - 2023: Choppy Recovery (Mixed signals, SPY +24%)
  - 2024: Bull Market (Rate cut hopes, SPY +23%)
  - 2025: Continuation (Jan 1-10 only)
- **WFA-C Compliance**: Must meet the **3/4 Reliability Heuristic**

**Success Criteria**:
- ✅ Profitable in ≥3 of 4 years
- ✅ Positive total PnL across full 4-year period
- ✅ Sharpe > 0.8 composite (acknowledging volatility tolerance for intraday)

**Failure Indicators**:
- ❌ Profitable in <3 years (regime-dependent, not structural edge)
- ❌ 2024 carries >80% of total PnL (recency bias mirage)
- ❌ Max Drawdown exceeds -30% in any single year

---

### Test 1.3: Data Integrity Audit
**Purpose**: Verify no corporate action artifacts or data feed corruption

**Checks**:
1. **Split Verification**: Confirm SPY/QQQ/IWM had no splits in test period
2. **Dividend Adjustments**: Verify total return data includes reinvestment (if applicable)
3. **Volume Spikes**: Flag and investigate any >10x volume anomalies (potential bad ticks)
4. **Bar Continuity**: Log any gaps >30 minutes during market hours (data source issues)

**Action**: Manual review of flagged events; re-run tests with secondary data source (FMP vs Alpaca) for spot-check validation

---

## PHASE 2: Adversarial Perturbation Testing (Breaking Point Analysis)
**Objective**: Identify the boundaries where the strategy's edge collapses

### Test 2.1: Friction Escalation Ladder
**Purpose**: Determine exact BPS threshold where strategy becomes unprofitable

**Protocol**:
- Run 2024 backtest at escalating friction levels:
  - Baseline: 5 bps (realistic for liquid ETFs with Alpaca)
  - Stress 1: 10 bps (2x friction)
  - Stress 2: 15 bps (market impact during volatile periods)
  - Stress 3: 20 bps (adversarial worst-case)
- **Friction Floor Protocol (IVS)**: Strategy must remain profitable at 10 bps to pass

**Success Criteria**:
- ✅ Positive PnL at 10 bps friction
- ✅ Sharpe >0.5 at 10 bps

**Critical Insight**: Document the **"Breakeven Friction"** (exact BPS where PnL = $0)

---

### Test 2.2: Parameter Stability Audit
**Purpose**: Verify edge is not a "parameter island" (narrow optimum = overfitting)

**Tests**:
1. **RSI Lookback**: Test RSI periods 12, 13, 14, 15, 16 (±2 from baseline 14)
2. **Alpha Threshold**: Test entry thresholds at 0.4, 0.45, 0.5, 0.55, 0.6 (±0.1 from baseline 0.5)
3. **Sentry Gate**: Test gates at -0.1, 0.0, 0.1 for SPY/QQQ (currently 0.0)

**Success Criteria**:
- ✅ ≥70% of parameter neighbors remain profitable (Neighboring Stability Standard)
- ✅ Performance delta <30% between worst and best neighbor

**Failure Indicator**:
- ❌ Only baseline (14, 0.5, 0.0) is profitable → overfitting signal

---

### Test 2.3: Timing Shift Stress Test
**Purpose**: Measure sensitivity to execution timing precision (critical for intraday systems)

**Protocol**:
- **Entry Lag Tests**:
  - Baseline: Fill on next bar open (standard +1 bar)
  - Stress 1: Fill delayed by +1 additional bar (+2 bars total)
  - Stress 2: Fill delayed by +3 bars (worst-case latency scenario)
- **Exit Lag Tests**: Same progression for position exits

**Success Criteria**:
- ✅ Strategy remains profitable with +2 bar lag
- ✅ Sharpe degradation <40% under +2 bar lag

**Critical Insight**: If +2 bar lag destroys edge → strategy requires sub-minute execution precision (infrastructure risk)

---

### Test 2.4: Sentiment Oracle Test (Dependency Analysis)
**Purpose**: Quantify reliance on sentiment data (currently placeholder 0.0)

**Protocol**:
- **Test A**: Run backtest with sentiment forced to +0.5 (bullish)
- **Test B**: Run backtest with sentiment forced to -0.5 (bearish)
- **Test C**: Run backtest with random sentiment [-0.5, +0.5]
- **Compare**: Performance vs. baseline (neutral 0.0)

**Success Criteria**:
- ✅ Neutral (0.0) and Random sentiment produce similar results → low dependency
- ✅ Strategy maintains >50% of baseline Sharpe with random sentiment

**Failure Indicator**:
- ❌ Forced bullish sentiment produces 2x+ better results → strategy is actually "sentiment-betting" not "alpha-generating"

---

## PHASE 3: Statistical Robustness & Significance Testing
**Objective**: Prove the edge is not random luck

### Test 3.1: Monte Carlo Trade Shuffling
**Purpose**: Measure if PnL is attributable to timing skill or random distribution

**Protocol**:
- Extract all trade returns from 2024 baseline backtest
- Shuffle trade sequence randomly (N=1,000 iterations)
- Calculate distribution of terminal PnL across shuffled paths
- **Luck Factor Analysis**: Compare actual PnL to shuffled distribution

**Success Criteria**:
- ✅ Actual PnL > 75th percentile of shuffled distribution (skill-based)
- ✅ 95% Confidence Interval includes positive returns

**Failure Indicator**:
- ❌ Actual PnL within median ±10% of shuffled → timing is random

---

### Test 3.2: Win Rate Significance Test
**Purpose**: Verify win rate is statistically different from coin-flip (50%)

**Protocol**:
- Binomial test: H0 = Win Rate = 50%, H1 = Win Rate ≠ 50%
- Significance level: p < 0.05
- Minimum sample: 100 trades (already required in baseline)

**Success Criteria**:
- ✅ p-value < 0.05 AND Win Rate > 50% (statistically significant edge)

---

### Test 3.3: Bootstrap Confidence Intervals
**Purpose**: Quantify uncertainty around performance metrics

**Protocol**:
- Sample trades with replacement (N=1,000 bootstrap iterations)
- Calculate 95% CI for: Sharpe Ratio, Total Return, Max Drawdown
- **Risk Quantification**: Document worst-case 5th percentile outcomes

**Success Criteria**:
- ✅ 95% CI lower bound for Sharpe > 0.5
- ✅ 95% CI lower bound for Total Return > 0%

---

## PHASE 4: Intraday-Specific Validation (Frequency & Microstructure)
**Objective**: Test vulnerabilities unique to high-frequency strategies

### Test 4.1: Frequency-Friction Audit
**Purpose**: Calculate annual friction burden as % of capital

**Calculation**:
```
Annual Friction = (Avg Daily Trades × 252 days × 2 sides × BPS) / Initial Capital
```

**Death Spiral Threshold (IVS Protocol)**: Annual friction >15% = fundamentally non-viable

**Example**:
- If strategy averages 5 trades/day on SPY (in+out = 10 roundtrips)
- At 5 bps: 10 × 252 × 5 bps = 12,600 bps = 126% annual friction
- **Result**: Strategy must generate >126% gross return just to break even

**Success Criteria**:
- ✅ Annual friction <15% of initial capital
- ✅ Gross Return / Friction Ratio > 3.0x

**Failure Indicator**:
- ❌ Friction >15% → strategy is "paying the casino more than it can win"

---

### Test 4.2: Session-Based Performance Analysis
**Purpose**: Identify if edge is concentrated in specific market hours

**Protocol**:
- Segment 2024 trades by entry time:
  - Open (9:30-10:00 AM ET)
  - Morning (10:00-11:30 AM ET)
  - Midday (11:30 AM-2:00 PM ET)
  - Afternoon (2:00-4:00 PM ET)
- Calculate win rate, avg profit, and trade count per segment

**Critical Insights**:
- If >70% of PnL from opening 30 min → strategy is "gap trading" not "intraday alpha"
- If midday trades are break-even → consider session filters

---

### Test 4.3: Tick-by-Tick Latency Simulation
**Purpose**: Model impact of residential vs. co-located execution infrastructure

**Parameters** (from Magellan POC Jan 2026):
- Residential Latency: 67ms average (established baseline)
- Co-located Latency: ~10ms (institutional baseline)
- **Delta Impact**: 57ms disadvantage per order

**Simulation**:
- Assume 3-minute bars = 180,000ms holding period
- Latency overhead = (67ms × 2 orders) / 180,000ms = 0.074% time penalty
- For strategies with <5 min avg hold, latency can cause **0.5-2% slippage increase**

**Adjustment**: Re-run baseline backtest with +1 bps latency penalty to model residential infrastructure

---

## PHASE 5: Production Simulation (Paper Trading Dress Rehearsal)
**Objective**: Test strategy in live market conditions without capital risk

### Test 5.1: Paper Trading Live Forward Test (2 Weeks)
**Purpose**: Validate strategy behavior in real-time market microstructure

**Protocol**:
- Deploy strategy to Alpaca Paper Trading account
- Run live for 10 trading days (Jan 27 - Feb 7, 2026)
- Log every signal, order, fill, and reject in real-time
- **No manual intervention** (pure algorithmic execution)

**Monitoring Metrics**:
- Fill rate (% of orders filled within 30 seconds)
- Slippage (actual fill price vs. expected price at signal time)
- Signal stability (how many signals flip before execution)
- Position accuracy (does live position match expected state)

**Success Criteria**:
- ✅ Fill rate >95%
- ✅ Average slippage ≤5 bps
- ✅ No critical errors/exceptions
- ✅ Live Sharpe within 30% of backtest Sharpe (accounting for short sample)

**Failure Indicators**:
- ❌ Fill rate <85% (liquidity issues)
- ❌ Average slippage >10 bps (cost model broken)
- ❌ Strategy produces opposite sign PnL vs. backtest

---

### Test 5.2: Regime Detection & Kill-Switch Test
**Purpose**: Verify sentry gate operates correctly in live bear regime

**Protocol**:
- Manually simulate bearish sentiment event (if sentiment feed is integrated)
- OR wait for market selloff day (VIX >25)
- Verify strategy correctly:
  - Suppresses LONG signals when sentiment < gate
  - Exits positions if sentiment deteriorates
  - Resumes trading when sentiment recovers

**Success Criteria**:
- ✅ Zero trades during simulated bearish regime for SPY/QQQ (gate=0.0)
- ✅ IWM continues trading if sentiment > -0.2 (gate=-0.2)

---

### Test 5.3: Circuit Breaker & Risk Limit Testing
**Purpose**: Verify strategy respects position caps, PDT rules, and buying power

**Tests**:
1. **Position Cap Test**: Artificially boost paper account to $1M → verify orders respect $50k cap
2. **PDT Test**: Reduce paper account to $20k → verify strategy halts trading
3. **Buying Power Test**: Simulate margin call → verify strategy doesn't place unfunded orders

**Success Criteria**:
- ✅ All risk limits enforced programmatically
- ✅ Strategy degrades gracefully (no crashes) when limits hit

---

## PHASE 6: Live Capital Deployment Readiness Gate
**Objective**: Final GO/NO-GO decision before real capital deployment

### Deployment Approval Criteria (All Must Pass):

**Quantitative Gates**:
- [ ] Sharpe Ratio >1.0 (4-year backtest)
- [ ] Win Rate >45% AND p<0.05 significance
- [ ] Profitable at 10 bps friction (2x stress)
- [ ] Annual friction burden <15%
- [ ] 3/4 year profitability (WFA-C Standard)
- [ ] Max Drawdown <20% (any single year)
- [ ] Parameter stability: ≥70% neighbors profitable

**Qualitative Gates**:
- [ ] Paper trading 2-week test: No critical errors
- [ ] Paper trading: Fill rate >95%, slippage ≤5 bps
- [ ] Sentiment dependency analysis: Strategy viable without perfect sentiment
- [ ] Infrastructure audit: Latency <100ms, uptime >99.5%
- [ ] Code audit: No hardcoded values, production-grade error handling
- [ ] Operational runbook: Documented restart, recovery, and kill-switch procedures

**Final Recommendation Framework**:

| Status | Condition | Action |
|--------|-----------|--------|
| **APPROVED (Full Deployment)** | All gates passed, Sharpe >1.5 | Deploy with $100k capital (initial allocation) |
| **CONDITIONAL APPROVAL** | ≥80% gates passed, Sharpe 1.0-1.5 | Deploy with $50k capital (reduced risk) + 30-day review |
| **PAPER TRADING ONLY** | ≥60% gates passed, Sharpe 0.5-1.0 | Extended 60-day paper test, re-evaluate |
| **REJECTED** | <60% gates passed OR Sharpe <0.5 | Archive strategy, do not deploy |

---

## 📊 Testing Infrastructure & Tooling

### Required Scripts (To Be Developed):
1. **`run_phase1_baseline_backtest.py`**: Clean-room 2024-2025 backtest
2. **`run_phase1_regime_stress.py`**: 2022-2025 multi-regime test
3. **`run_phase2_friction_ladder.py`**: Escalating friction tests
4. **`run_phase2_parameter_sweep.py`**: Neighboring parameter stability
5. **`run_phase3_monte_carlo.py`**: Trade shuffling and bootstrap analysis
6. **`run_phase4_frequency_audit.py`**: Friction burden calculation
7. **`deploy_phase5_paper_trading.py`**: Live paper trading runner with monitoring

### Data Requirements:
- **Historical Data**: SPY/QQQ/IWM 1-minute bars (2022-2026) via Alpaca API
- **Cache Strategy**: Use `USE_ARCHIVED_DATA=true` for reproducible tests
- **Sentiment Data**: If available, integrate; otherwise document limitation

### Reporting Format:
Each test produces:
- **Summary Metrics**: Sharpe, Win Rate, PnL, Max DD, Trade Count
- **Trade Log**: CSV with entry/exit timestamps, prices, PnL per trade
- **Visualization**: Equity curve, drawdown profile, monthly returns heatmap
- **Pass/Fail Assessment**: Clear GREEN/YELLOW/RED status per test

---

## 🚨 Known Risks & Mitigation Strategies

### Risk 1: Sentiment Data Unavailable
**Impact**: Strategy relies on sentiment weights (10% for SPY/QQQ)  
**Mitigation**: Phase 2.4 tests quantify dependency; if high, integrate real sentiment API (Polygon, Benzinga) OR remove sentiment component and retest

### Risk 2: Excessive Friction Burden
**Impact**: Intraday strategies on 3-5 min bars are notoriously friction-sensitive  
**Mitigation**: Phase 4.1 calculates exact burden; if >15%, consider:
- Increase alpha threshold (0.5 → 0.6) to reduce trade frequency
- Add minimum holding period (e.g., 3 bars minimum)
- Switch to longer timeframes (15-min or 1-hour bars)

### Risk 3: Regime Dependency (Recency Bias)
**Impact**: Strategy deployed Jan 10, 2026 in bull market—may fail in bear markets  
**Mitigation**: Phase 1.2 tests 2022 bear market performance; if fails, add VIX-based regime filter

### Risk 4: Latency-Induced Slippage
**Impact**: 67ms residential latency may degrade fill quality on fast-moving 3-min bars  
**Mitigation**: Phase 5.1 paper trading measures actual slippage; if >10 bps, consider co-located VPS

### Risk 5: Data Leakage / Look-Ahead Bias
**Impact**: Backtests use full bar data at bar close; live trading sees partial bar data  
**Mitigation**: All backtests enforce +1 bar fill lag (signal on close of bar N → fill on open of bar N+1)

---

## 📅 Execution Timeline

**Week 1 (Jan 27-31, 2026)**:
- Complete Phase 1 (Baseline & Regime Tests)
- Complete Phase 2 (Adversarial Perturbations)
- Preliminary Report: Document any critical failures

**Week 2 (Feb 3-7, 2026)**:
- Complete Phase 3 (Statistical Robustness)
- Complete Phase 4 (Frequency/Microstructure Analysis)
- Comprehensive Report: GREEN/YELLOW/RED status per gate

**Week 3 (Feb 10-21, 2026)**:
- Deploy Phase 5 (Paper Trading - 10 days live)
- Daily monitoring and logging
- Real-time anomaly detection

**Week 4 (Feb 24-28, 2026)**:
- Phase 5 analysis and final report
- Executive decision meeting: GO/NO-GO for live capital
- If GO: Prepare production deployment (code audit, runbook, monitoring)

**Total Duration**: 4 weeks from kickoff to deployment decision

---

## 📚 References & Standards Alignment

This testing regimen is built on:

1. **Magellan Institutional Validation Standard (IVS)** (Jan 19, 2026)
   - 7-Pillar Certified Validation Suite principles
   - WFA-C 3/4 Reliability Heuristic
   - Friction Floor Protocol (2x stress standard)

2. **Adversarial Perturbation Standard (V-ADS-2026)** (Jan 19, 2026)
   - Clean-Room Independent Audit (V-CRA) methodology
   - Neighboring Stability testing (≥70% threshold)
   - Breaking Point analysis

3. **Frequency-Friction Bounds Protocol** (Jan 16, 2026)
   - 15% annual friction death spiral threshold
   - 3x alpha-to-friction margin requirement

4. **The 252-Day Mandate** (Jan 16, 2026)
   - Minimum 1-year test for short-interval strategies
   - Sharpe collapse detection (>2.0 point delta = rejection)

5. **Regime Stress Standards** (Jan 17-20, 2026)
   - Multi-cycle testing (Bear + Bull + Chop)
   - 4-year robustness standard (2022-2025)

---

## ✅ Deliverables

Upon completion of this testing regimen, the following artifacts will be produced:

1. **Comprehensive Test Report** (40-60 pages)
   - Executive summary with GO/NO-GO recommendation
   - Detailed results for all 19 tests across 6 phases
   - Equity curves, trade logs, and statistical analysis
   - Risk assessment and mitigation strategies

2. **Production Deployment Package** (if approved)
   - Validated strategy code (production-ready)
   - Configuration file (optimized parameters if tuning performed)
   - Operational runbook (start/stop/monitor/recover procedures)
   - Monitoring dashboard specification

3. **Knowledge Base Update**
   - Update Intraday Alpha Strategy Track KI with test results
   - Document lessons learned and edge characterization
   - Archive all test scripts and data for future audits

---

## 🎓 Strategic Recommendations (Preliminary)

Based on initial analysis of the strategy characteristics:

**Concerns**:
- ⚠️ **High Frequency Risk**: 3-5 min bars are vulnerable to friction death spiral
- ⚠️ **Single-Day Deployment History**: Only 1 day live before pivot—limited production validation
- ⚠️ **Sentiment Dependency**: Unclear if strategy works without live sentiment feed
- ⚠️ **Replaced for a Reason**: Team pivoted to MAG7 after 1 day—investigate why

**Strengths**:
- ✅ **Liquid Universe**: SPY/QQQ/IWM are ultra-liquid (minimal market impact)
- ✅ **Conservative Position Sizing**: $50k caps and 25% allocation limit risk
- ✅ **Multi-Factor Design**: Combining RSI/Volume/Sentiment is theoretically sound
- ✅ **Architectural Parity**: Core logic (sentry gates, hysteresis) preserved in current system

**Hypothesis to Test**:
- This strategy may have been abandoned due to **insufficient profit vs. operational complexity**, not fundamental unprofitability
- If friction burden is manageable (<10%), strategy could be viable for "set-and-forget" intraday allocation
- May perform better in **high volatility regimes** (2022, 2025) vs. smooth bull markets (2024)

**Alternative Deployment Scenarios**:
1. **Scenario A**: If tests pass → Deploy as "Index Intraday" separate account ($50k allocation)
2. **Scenario B**: If marginal pass → Extend to 15-min or 1-hour bars to reduce friction
3. **Scenario C**: If sentiment dependency high → Integrate Polygon sentiment or reject
4. **Scenario D**: If fails → Archive as "historical baseline" and document lessons learned

---

## 🤔 Questions for Strategy Owner

Before proceeding with testing execution, please confirm:

1. **Sentiment Data Availability**: Do we have access to historical sentiment data (2022-2026) for SPY/QQQ/IWM? If not, should we test without it or defer until integrated?

2. **Deployment Intent**: Is the goal to:
   - Reactivate this exact strategy as-is?
   - Use it as a baseline to develop improved intraday strategies?
   - Academic exercise to validate historical claims?

3. **Capital Allocation**: If approved, what initial capital allocation is acceptable?
   - Conservative: $25k-$50k
   - Standard: $100k (as originally deployed)
   - Aggressive: $200k+ (if tests are exceptional)

4. **Risk Tolerance**: Given this is intraday trading (multiple trades/day), what is acceptable:
   - Daily loss limit? (e.g., -2% of allocated capital)
   - Max position duration? (e.g., force exit by market close?)
   - Consecutive loss limit? (e.g., halt after 5 consecutive losing days)

5. **Timeline Flexibility**: Is the 4-week timeline acceptable, or is there urgency to deploy sooner?

---

**Prepared by**: Antigravity AI (Quantitative Testing Strategist)  
**Date**: January 24, 2026  
**Status**: AWAITING APPROVAL TO PROCEED WITH TESTING  
**Next Action**: User review → Authorize Phase 1 execution
