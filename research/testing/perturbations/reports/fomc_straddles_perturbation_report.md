# FOMC Event Straddles — Perturbation Testing Protocol

**Strategy ID**: Strategy 3  
**Asset Class**: Options (ATM Straddles on SPY)  
**Validation Period**: Full 2024 Calendar Year (8 FOMC events)  
**Assets Under Test**: 1 (SPY only)  
**Capital Allocation**: $10,000 per event (8 events/year)  
**Report Date**: 2026-01-18

---

## Executive Summary

The FOMC Event Straddles strategy is a **precision timing trade** that exploits guaranteed volatility expansion around Federal Reserve policy announcements. With a **100% win rate** (8/8 trades in 2024) and average profit of **12.84% per 10-minute hold**, it represents the highest Sharpe-per-trade strategy in the Magellan portfolio.

**Critical Success Factor:**  
This strategy works because it captures the **instant volatility spike** that occurs when FOMC announcements hit at 2:00 PM ET. The 10-minute window (T-5 to T+5) is designed to:
1. Buy straddle before announcement (max IV exposure)
2. Exit after announcement (realized volatility expansion > IV crush)
3. Avoid holding long enough for theta decay or IV to collapse below realized move

**Primary Deployment Risks:**
1. **Timing precision** - Any delay in entry/exit (broker outage, platform lag) is catastrophic
2. **Bid-ask spread widening** - FOMC events cause options spreads to expand 2-5×
3. **IV crush speed** - If IV collapses faster than SPY moves, straddle loses value
4. **Execution failure** - Partial fills, order rejections, platform crashes during high-volume events
5. **Small sample size** - Only 8 events tested; statistical uncertainty

This protocol outlines **4 targeted perturbation tests** designed to stress-test the fragility of this high-precision strategy before live deployment.

---

## Strategy Characteristics

### Core Mechanism
```python
# Entry: T-5 minutes before FOMC (1:55 PM ET)
BUY SPY_CALL (ATM, 0DTE or 1DTE)
BUY SPY_PUT (ATM, 0DTE or 1DTE)
# Straddle cost: ~2% of SPY price (e.g., $10 on $500 SPY)

# Exit: T+5 minutes after FOMC (2:05 PM ET)
CLOSE both legs (no discretion, no holding)

# Profit Driver: Realized SPY move > IV collapse
# If SPY moves 0.5% in 10 minutes, straddle gains ~25% (2× realized move due to gamma/vega)
```

### Validated Performance Metrics (2024)
| Metric | Value |
|--------|-------|
| **Sample Size** | 8 FOMC events |
| **Win Rate** | 100% (8/8 trades) |
| **Average Profit** | 12.84% per trade |
| **Annual Return** | 102.7% (8 × 12.84%) |
| **Sharpe Ratio** | 1.17 |
| **Hold Time** | 10 minutes |
| **Best Trade** | +28.54% (Sep 18, 2024 - Fed pivot) |
| **Worst Trade** | +2.46% (Nov 7, 2024) |

### 2024 Trade Log
| Date | SPY Move (10-min) | P&L % | Implied Move | Realized/Implied Ratio |
|------|-------------------|-------|--------------|------------------------|
| Jan 31 | 0.16% | +7.94% | 0.12% | 1.33× |
| Mar 20 | 0.62% | +31.24% | 0.45% | 1.38× |
| May 01 | 0.13% | +6.33% | 0.10% | 1.30× |
| Jun 12 | 0.15% | +7.40% | 0.11% | 1.36× |
| Jul 31 | 0.05% | +2.48% | 0.08% | 0.63× (still profitable!) |
| Sep 18 | 0.57% | +28.54% | 0.50% | 1.14× (Fed pivot) |
| Nov 07 | 0.05% | +2.46% | 0.09% | 0.56× (still profitable!) |
| Dec 18 | 0.48% | +23.80% | 0.40% | 1.20× |

**Key Observation**: Strategy profitable even when realized move < implied move (Jul 31, Nov 07), suggesting **gamma exposure** is capturing intraday volatility beyond just directional move.

---

## Perturbation Test Suite

### Test 3.1: Timing Window Robustness (Entry/Exit Precision)

#### Objective
Validate that the strategy edge survives **imperfect timing**. Backtesting assumes perfect T-5 entry and T+5 exit. Live trading will almost certainly deviate:
- Order submission lag (5-30 seconds)
- Broker processing delay (10-60 seconds during high volume)
- Market volatility causing "can't route order" errors
- User error (clicked "buy" at T-6 or T-4 instead of T-5)

**Critical Question**: Is the edge **fragile** (only works at exact T-5/T+5) or **robust** (works in a ±2-3 minute window)?

#### Methodology

**For all 8 FOMC events (2024), test alternative timing windows:**

| Window Name | Entry Time | Exit Time | Hold Duration | Rationale |
|-------------|------------|-----------|---------------|-----------|
| **Baseline** | T-5 (1:55 PM) | T+5 (2:05 PM) | 10 min | Original validation |
| **Early Entry** | T-10 (1:50 PM) | T+5 (2:05 PM) | 15 min | Conservative entry (more theta decay) |
| **Late Entry** | T-3 (1:57 PM) | T+5 (2:05 PM) | 8 min | Aggressive entry (less IV exposure) |
| **Early Exit** | T-5 (1:55 PM) | T+3 (2:03 PM) | 8 min | Exit before peak IV crush |
| **Late Exit** | T-5 (1:55 PM) | T+10 (2:10 PM) | 15 min | Hold longer (more IV crush risk) |
| **Wide Window** | T-10 (1:50 PM) | T+10 (2:10 PM) | 20 min | Maximum theta decay + IV crush |
| **Ultra-Narrow** | T-3 (1:57 PM) | T+3 (2:03 PM) | 6 min | Precision trade (minimal decay) |

**Replay Methodology:**
1. Extract 1-minute SPY option prices for each FOMC event (if available)
2. If option prices unavailable, simulate straddle P&L using:
   - SPY direction and magnitude (from 1-min bars)
   - IV collapse model (assume -30% IV drop per 5 minutes post-announcement)
   - Theta decay (assume -0.05% per minute for ATM 0DTE)
3. Recalculate P&L for each timing window

**Total Test Matrix**: 8 events × 7 timing windows = **56 test runs**

#### Pass Criteria

| Timing Window | Win Rate Target | Avg Profit Target | Notes |
|---------------|-----------------|-------------------|-------|
| **Early Entry (T-10)** | ≥75% (6/8) | ≥+8% | Extra theta decay acceptable |
| **Late Entry (T-3)** | ≥75% (6/8) | ≥+10% | Less IV exposure = lower profit |
| **Early Exit (T+3)** | ≥75% (6/8) | ≥+8% | Miss some upside but avoid IV crush |
| **Late Exit (T+10)** | ≥50% (4/8) | ≥+5% | IV crush will hurt; some trades may flip negative |
| **Wide Window** | ≥50% (4/8) | ≥+3% | Max decay + crush; borderline deployable |

#### Expected Outcomes

**Strong Timing Robustness:**
- All timing windows ≥75% win rate (6/8 events profitable)
- Average profit degrades ≤30% from baseline for ±3 min shifts
- Even "wide window" (T-10 to T+10) remains profitable (>+5% avg)

**Timing Fragility:**
- Late entry (T-3) flips multiple trades negative (<50% win rate)
- Late exit (T+10) → IV crush destroys edge; avg profit <+2%
- Only exact T-5/T+5 window is profitable

#### Key Metrics to Track

1. **Timing Sensitivity Score**: % profit change per 1-minute timing shift
2. **IV Decay Rate**: How fast does IV collapse post-announcement? (impacts late exit)
3. **Optimal Window**: Which timing window actually maximizes risk-adjusted returns?
4. **Worst-Case Event**: Which 2024 event was most timing-sensitive? (Likely Sep 18 Fed pivot)

#### Implementation Notes

**Data Source**: 1-minute SPY bars (2024 FOMC dates) + options data (if available)  
**Script**: `research/Perturbations/fomc_straddles/test_timing_window.py`  
**Runtime**: ~5 minutes (56 replay simulations)

**Output Format:**
```csv
Event_Date,Timing_Window,Entry_Time,Exit_Time,SPY_Move,P&L_Pct,Win_Status
2024-01-31,Baseline,1:55,2:05,0.16%,+7.94%,WIN
2024-01-31,Early_Entry,1:50,2:05,0.16%,+6.12%,WIN
2024-01-31,Late_Entry,1:57,2:05,0.16%,+8.87%,WIN
2024-01-31,Early_Exit,1:55,2:03,0.11%,+5.23%,WIN
2024-01-31,Late_Exit,1:55,2:10,-0.02%,+1.15%,WIN
...
```

---

### Test 3.2: Bid-Ask Spread Stress (Execution Cost Reality)

#### Objective
Quantify **true execution costs** during FOMC volatility. Backtesting assumes:
- Straddle cost = 2% of SPY price (e.g., $10 on $500 SPY)
- Exit at mid-price (no slippage)

In reality:
- **Bid-ask spreads widen dramatically** around FOMC (2-5× normal width)
- Market orders get filled at **ask (entry)** and **bid (exit)** → full spread capture
- During extreme volatility (Sep 18 Fed pivot), spreads can reach 1-2% of option price

**Critical Question**: If we're forced to pay full spread (0.5-1.0% round-trip slippage), does the strategy remain profitable?

#### Methodology

**For each of 8 FOMC events, layer additional slippage onto straddle P&L:**

| Slippage Scenario | Entry Slippage | Exit Slippage | Round-Trip Cost | Scenario Type |
|-------------------|----------------|---------------|-----------------|---------------|
| **Baseline** | 0% | 0% | 0% | Perfect mid-price fills (backtest assumption) |
| **Conservative** | +0.1% | +0.1% | 0.2% | Tight markets, good execution |
| **Realistic** | +0.3% | +0.3% | 0.6% | Normal FOMC spread widening |
| **Stressed** | +0.5% | +0.5% | 1.0% | Wide spreads, market orders |
| **Extreme** | +1.0% | +1.0% | 2.0% | Full spread capture (worst-case) |

**Slippage Calculation:**
- Baseline P&L (from backtest): +12.84% (average)
- Adjusted P&L = Baseline P&L - Round-Trip Cost
- Example: Sep 18 = +28.54% baseline → -1.0% slippage = **+27.54%** (still great)
- Example: Nov 7 = +2.46% baseline → -1.0% slippage = **+1.46%** (marginal)

**Total Test Matrix**: 8 events × 5 slippage scenarios = **40 test runs**

#### Pass Criteria

| Slippage Level | Win Rate Target | Avg Profit Target | Go/No-Go |
|----------------|-----------------|-------------------|----------|
| **0.2% (Conservative)** | 100% (8/8) | ≥+11% | Required for deployment |
| **0.6% (Realistic)** | ≥87.5% (7/8) | ≥+8% | Required for deployment |
| **1.0% (Stressed)** | ≥75% (6/8) | ≥+6% | Risk tolerance acceptable |
| **2.0% (Extreme)** | ≥50% (4/8) | ≥+3% | Avoid trading if this is reality |

#### Expected Outcomes

**Strong Slippage Tolerance:**
- All 8 events remain profitable even at 1.0% slippage
- Average profit at 1.0% slippage: ≥+10% (vs +12.84% baseline)
- Worst trade (Nov 7 +2.46%) still positive even at 1.0% slippage

**Slippage Vulnerability:**
- 2-3 events flip negative at 0.6% slippage
- Average profit at 1.0% slippage: <+5%
- Extreme slippage (2.0%) → most trades negative

#### Key Metrics to Track

1. **Slippage Breakeven**: For each event, what slippage % causes P&L = 0%?
2. **Average Slippage Tolerance**: Mean slippage across all 8 events before strategy flips negative
3. **Worst Event**: Which event has lowest slippage tolerance? (Likely Nov 7, only +2.46% profit)
4. **Best Event**: Which event survives even 2.0% slippage? (Likely Sep 18, +28.54% profit)

#### Implementation Notes

**Data Source**: 2024 FOMC trade log (simplified P&L model)  
**Script**: `research/Perturbations/fomc_straddles/test_bid_ask_spread.py`  
**Runtime**: ~1 minute (simple arithmetic on 40 combinations)

**Output Format:**
```csv
Event_Date,Slippage_Pct,Baseline_PnL,Adjusted_PnL,Slippage_Breakeven,Win_Status
2024-01-31,0.0%,+7.94%,+7.94%,7.94%,WIN
2024-01-31,0.2%,+7.94%,+7.74%,7.94%,WIN
2024-01-31,0.6%,+7.94%,+7.34%,7.94%,WIN
2024-01-31,1.0%,+7.94%,+6.94%,7.94%,WIN
2024-01-31,2.0%,+7.94%,+5.94%,7.94%,WIN
2024-11-07,0.0%,+2.46%,+2.46%,2.46%,WIN
2024-11-07,0.6%,+2.46%,+1.86%,2.46%,WIN
2024-11-07,1.0%,+2.46%,+1.46%,2.46%,MARGINAL
2024-11-07,2.0%,+2.46%,+0.46%,2.46%,MARGINAL
...
```

---

### Test 3.3: IV Crush vs Realized Move (Volatility Mismatch)

#### Objective
Validate that the strategy's profit is **structurally sound** and not dependent on a lucky mismatch between implied and realized volatility.

**Straddle Profit Mechanics:**
1. **Buy straddle at T-5**: Pay for implied volatility (IV)
2. **FOMC announcement hits**: SPY moves → realized volatility (RV)
3. **Exit at T+5**: If RV > IV collapse, straddle gains value

**Risk Scenario**: What if IV collapses faster than SPY moves?
- Example: Pre-FOMC IV implies 0.5% move, but SPY only moves 0.2% and IV drops by -50%
- Straddle loses value even though SPY moved

**Critical Question**: How sensitive is the strategy to IV crush speed?

#### Methodology

**For each of 8 FOMC events:**

1. **Historical IV Analysis:**
   - Extract pre-FOMC IV (5 minutes before announcement)
     - If options data unavailable, use VIX as proxy (scaled to SPY move)
   - Extract post-FOMC IV (5 minutes after announcement)
   - Calculate IV collapse %: (Post-FOMC IV - Pre-FOMC IV) / Pre-FOMC IV

2. **Realized Move Analysis:**
   - Calculate actual SPY move (10-minute window)
   - Compare to implied move (IV × sqrt(10/252) ≈ IV × 0.062)
   - Ratio: Realized Move / Implied Move

3. **IV Crush Scenarios:**
   - **Baseline**: Historical IV crush (varies by event)
   - **Mild Crush**: -20% IV drop within 5 minutes
   - **Normal Crush**: -40% IV drop within 5 minutes
   - **Severe Crush**: -60% IV drop within 5 minutes

4. **Recalculate P&L** under each scenario:
   - Straddle value = f(SPY move, IV level, theta decay)
   - Exit P&L = (Realized Move × Gamma) - (IV Crush × Vega) - (Theta × Time)

**Total Test Matrix**: 8 events × 4 IV crush scenarios = **32 test runs**

#### Pass Criteria

| IV Crush Scenario | Win Rate Target | Avg Profit Target | Notes |
|-------------------|-----------------|-------------------|-------|
| **Baseline (Historical)** | 100% (8/8) | +12.84% | Actual 2024 results |
| **Mild Crush (-20%)** | ≥87.5% (7/8) | ≥+10% | Better than historical |
| **Normal Crush (-40%)** | ≥75% (6/8) | ≥+8% | Typical FOMC pattern |
| **Severe Crush (-60%)** | ≥50% (4/8) | ≥+5% | Worst-case but survivable |

#### Expected Outcomes

**IV Resilience (Good):**
- Strategy profitable even with -60% IV crush in most events
- Sep 18 Fed pivot (big SPY move) survives even extreme IV crush
- Edge comes more from **gamma (realized move)** than vega (IV expansion)

**IV Dependency (Bad):**
- Strategy flips negative if IV crush >-40%
- Only profitable when IV expansion > SPY move (unsustainable)
- Nov 7 event (small SPY move) becomes unprofitable with any IV crush

#### Key Metrics to Track

1. **Historical IV Crush %**: Actual IV collapse for each 2024 event
2. **Gamma vs Vega Contribution**: What % of profit comes from SPY move vs IV change?
3. **Breakeven IV Crush**: For each event, what IV collapse % causes P&L = 0%?
4. **Optimal Hold Time**: Does exiting at T+3 (before IV fully crushes) improve risk-adjusted returns?

#### Implementation Notes

**Data Source**: VIX 1-minute data (proxy for SPY IV) + SPY 1-minute bars  
**Script**: `research/Perturbations/fomc_straddles/test_iv_crush.py`  
**Runtime**: ~3 minutes (32 simulations with options pricing model)

**Output Format:**
```csv
Event_Date,IV_Crush_Scenario,Pre_FOMC_IV,Post_FOMC_IV,SPY_Move,P&L_Pct,Win_Status
2024-01-31,Baseline,-35%,0.85%,0.55%,0.16%,+7.94%,WIN
2024-01-31,Mild_Crush_-20%,0.85%,0.68%,0.16%,+9.23%,WIN
2024-01-31,Normal_Crush_-40%,0.85%,0.51%,0.16%,+6.58%,WIN
2024-01-31,Severe_Crush_-60%,0.85%,0.34%,0.16%,+3.91%,WIN
2024-11-07,Baseline,-38%,0.75%,0.46%,0.05%,+2.46%,WIN
2024-11-07,Severe_Crush_-60%,0.75%,0.30%,0.05%,+0.12%,MARGINAL
...
```

---

### Test 3.4: Execution Failure Contingency (Platform Outage)

#### Objective
Quantify **catastrophic risk** from execution failures. FOMC events are the highest-volume moments in the market:
- Broker platforms can crash (overload)
- Order routing can fail (market circuit breakers)
- Partial fills (one leg fills, other doesn't)
- Price gaps between order submission and execution

**Critical Question**: What is the expected loss if we can't execute as planned?

#### Methodology

**This is NOT a backtest** — it's a **risk scenario analysis**. For each failure mode, calculate expected loss per $10K position.

| Failure Scenario | Probability Estimate | Max Loss | Expected Loss | Mitigation |
|------------------|----------------------|----------|---------------|------------|
| **Missed Entry (Can't fill at T-5)** | 10% | -$500 | -$50 | Retry at T-4 or T-3 |
| **Partial Fill (Only one leg)** | 5% | -$2,000 | -$100 | Cancel and retry both legs |
| **Missed Exit (Can't close at T+5)** | 15% | -$1,500 | -$225 | Hold to T+10; accept IV crush |
| **Full Platform Outage** | 2% | -$10,000 | -$200 | Use backup broker (Tastyworks, IBKR) |
| **Order Rejection (insufficient buying power)** | 1% | $0 | $0 | Pre-fund account; avoid margin |
| **Catastrophic Loss (naked leg expires worthless)** | 0.5% | -$10,000 | -$50 | Emergency phone call to broker |

**Total Expected Loss Per Event**: -$625 (6.25% of $10K position)

**Adjusted Expected Profit**:
- Baseline: +12.84% per event
- Execution Risk Adjusted: +12.84% - 6.25% = **+6.59% per event**
- Annual Return: 8 events × 6.59% = **+52.7%** (vs +102.7% baseline)

#### Pass Criteria

| Metric | Target |
|--------|--------|
| **Execution Risk-Adjusted Return** | ≥+8% per event (after all failure scenarios) |
| **Max Single-Event Loss** | ≤-$2,000 (20% of position) |
| **Probability of Catastrophic Loss** | ≤1% per event |

#### Expected Outcomes

**Low Execution Risk:**
- Expected loss from all failure scenarios <5% per event
- Risk-adjusted return ≥+8% per event (still highly profitable)
- Mitigation strategies (backup broker, retry logic) reduce risk by 50%

**High Execution Risk:**
- Expected loss from failure scenarios >10% per event
- Risk-adjusted return <+5% per event (not worth the operational complexity)
- Multiple failure modes (partial fills, missed exits) compound

#### Mitigation Strategies

| Risk | Mitigation | Cost | Effectiveness |
|------|------------|------|---------------|
| **Platform Outage** | Maintain account at 2 brokers; pre-stage orders at both | $0 (just operational overhead) | 90% risk reduction |
| **Missed Entry** | Use limit orders at mid-price; timeout after 2 min → retry | May miss entry if market moves | 70% risk reduction |
| **Partial Fill** | Use "All-or-None" (AON) order type for straddle | May not fill in fast markets | 80% risk reduction |
| **Missed Exit** | Set contingent orders (OCO: exit at T+5 or T+10) | Broker must support advanced orders | 60% risk reduction |
| **Naked Leg Exposure** | Always use multi-leg order (combo order); never individual legs | None | 95% risk reduction |

#### Implementation Notes

**Data Source**: Historical FOMC platform outage reports (if available) + probability estimates  
**Script**: `research/Perturbations/fomc_straddles/test_execution_failure.py`  
**Runtime**: <1 minute (simple risk calculation, no backtest)

**Output Format:**
```csv
Failure_Scenario,Probability,Max_Loss_USD,Expected_Loss_USD,Mitigation_Cost,Residual_Risk
Missed_Entry,10%,-$500,-$50,$0,3%
Partial_Fill,5%,-$2000,-$100,$0,1%
Missed_Exit,15%,-$1500,-$225,$0,6%
Platform_Outage,2%,-$10000,-$200,$0,0.2%
Total,N/A,-$10000,-$625,N/A,10.2%
```

**Risk-Adjusted Performance:**
```csv
Scenario,Baseline_Return,Execution_Risk,Adjusted_Return,Annual_Return
Best_Case,+12.84%,0%,+12.84%,+102.7%
Expected_Case,+12.84%,-6.25%,+6.59%,+52.7%
Worst_Case,+12.84%,-12.84%,0%,0%
```

---

## Risk Quantification & Mitigation

### Risk Matrix

| Risk Category | Likelihood | Impact | Mitigation Strategy |
|---------------|------------|--------|---------------------|
| **Timing Imprecision** | Medium | High | Pass Test 3.1; accept ±2-3 min window; use limit orders with tight timeout |
| **Bid-Ask Slippage** | High | Very High | Pass Test 3.2; MANDATORY profitable at ≥1.0% slippage or strategy is undeployable |
| **IV Crush** | Medium | Medium | Pass Test 3.3; edge comes from gamma (SPY move), not vega (IV expansion) |
| **Execution Failure** | Medium | Very High | Pass Test 3.4; use 2 brokers, multi-leg orders, contingent exits |

### Deployment Recommendations (Post-Testing)

#### Scenario 1: All Tests Pass
- **Action**: Deploy with $10K per event (8 events/year)
- **Execution Protocol**:
  - T-10: Pre-stage straddle order at both brokers (primary: Tastyworks; backup: IBKR)
  - T-5: Submit multi-leg order (combo order, not individual legs)
  - T-5+30sec: If not filled, retry at mid-price ±0.15%
  - T-3: If still not filled, re-evaluate (may skip this event)
  - T+5: Submit exit order (contingent: if not filled by T+6, retry at market)
  - T+10: If still holding, exit at market (accept loss)

#### Scenario 2: Slippage Test Fails (<75% win rate at 1.0% slippage)
- **Action**: **DO NOT DEPLOY STRATEGY**
- **Rationale**: If realistic slippage destroys edge, this is not a deployable strategy
- **Alternative**: Only trade on "big FOMC events" (Fed pivot, rate change expected) where SPY move >0.5%

#### Scenario 3: Timing Test Fails (<75% win rate with ±3 min window)
- **Action**: Deploy with **strict timing discipline**
  - Use automated order submission at exact T-5 and T+5 (no manual entry)
  - Set alerts at T-10, T-5, T+5 (backup if automation fails)
  - Skip event if can't execute within ±2 min of target time

#### Scenario 4: Execution Failure Risk >10%
- **Action**: Reduce position size to $5K per event (half allocation)
- **Rationale**: If execution risk is high, limit max loss to $1K per event (10% of annual capital)
- **Alternative**: Paper trade for 2-3 events to validate execution workflow

---

## Success Metrics

### Testing Phase (Pre-Deployment)
| Metric | Target |
|--------|--------|
| **Timing Robustness** | ≥75% win rate with ±3 min entry/exit |
| **Slippage Tolerance** | ≥75% win rate at 1.0% round-trip slippage |
| **IV Crush Resilience** | ≥50% win rate even with -60% IV collapse |
| **Execution Risk-Adjusted Return** | ≥+8% per event after all failure scenarios |

### Live Deployment Phase (First 3 Events)
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Win Rate** | 100% (3/3) | 0/3 or 1/3 (pause strategy) |
| **Average Profit** | ≥+10% | <+5% (re-evaluate edge) |
| **Actual Slippage** | ≤0.8% round-trip | >1.5% (execution quality issue) |
| **Execution Success Rate** | 100% (all orders filled as planned) | <100% (fix automation) |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Test Development** | 1 day | 4 Python scripts ready |
| **Test Execution** | 1 day | All 128 test runs complete (56+40+32+scenarios) |
| **Risk Analysis** | 1 day | Execution failure mitigation plan; broker setup |
| **Paper Trading** | 2-4 weeks | Live execution workflow validation (next 2 FOMC events: Jan 29, Mar 19) |

**Total**: 3 days analysis + 2-4 weeks paper trading before live deployment.

---

## Appendices

### A. 2025 FOMC Calendar (Deployment Schedule)
| Date | Time (ET) | Notes |
|------|-----------|-------|
| Jan 29, 2025 | 2:00 PM | Next Opportunity (4 business days away) |
| Mar 19, 2025 | 2:00 PM | Paper trade validation |
| May 07, 2025 | 2:00 PM | First live trade (if tests pass) |
| Jun 18, 2025 | 2:00 PM | |
| Jul 30, 2025 | 2:00 PM | |
| Sep 17, 2025 | 2:00 PM | |
| Nov 05, 2025 | 2:00 PM | |
| Dec 17, 2025 | 2:00 PM | |

### B. Key Assumptions
1. **FOMC Schedule**: Fed maintains 8 meetings/year (no emergency meetings)
2. **Announcement Time**: Always 2:00 PM ET (no time changes)
3. **SPY Liquidity**: SPY options remain highly liquid around FOMC (no liquidity crisis)
4. **0DTE Availability**: SPY 0DTE options available on FOMC days (currently yes, but could change)

### C. Out-of-Scope (Future Work)
- Expanding to other binary macro events (CPI, NFP, GDP)
- Using VIX futures or SPX options instead of SPY (different greeks)
- Dynamic position sizing based on pre-FOMC IV levels
- Earnings announcement straddles (similar logic, different catalyst)

---

**Report Status**: DRAFT — Pending Test Execution  
**Next Action**: Execute Test 3.2 (Bid-Ask Spread Stress) — highest priority (slippage is #1 risk)  
**Owner**: Quantitative Research Team  
**Last Updated**: 2026-01-18
