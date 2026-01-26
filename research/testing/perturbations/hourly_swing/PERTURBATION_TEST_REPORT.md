# Hourly Swing Trading — Perturbation Testing Protocol

**Strategy ID**: Strategy 2  
**Asset Class**: Equities (1-Hour Bars)  
**Validation Period**: Full 2025 Calendar Year (Jan 1 - Dec 31, 2025)  
**Assets Under Test**: 2 (TSLA, NVDA)  
**Capital Allocation**: $20,000 (12% of total portfolio)  
**Report Date**: 2026-01-18

---

## Executive Summary

The Hourly Swing Trading strategy is a **high-frequency complement** to the Daily Trend strategy, operating on 1-hour bars with mandatory overnight holds. Despite validating on only 2 high-beta tech stocks, it delivered strong risk-adjusted returns (TSLA +41.5%, NVDA +16.2%) with Sharpe ratios ~1.0-1.2.

**Critical Structural Dependency:**  
This strategy **requires overnight holds** (Swing Mode). Testing proved that forcing intraday exits (Day Mode) destroys returns:
- NVDA Swing Mode: +21.4% → Day Mode: +0.4%
- Reason: Gap profits + avoiding double commissions from intraday round-trips

**Primary Deployment Risks:**
1. **Overnight gap reversal** - Strategy profits from gaps but assumes they hold
2. **Execution timing precision** - 1-hour signals require fast fills; 30-min delay could erode edge
3. **Extreme friction sensitivity** - 105-240 trades/year = 2-4x Daily Trend frequency
4. **Concentration risk** - Only 2 assets; no diversification buffer

This protocol outlines **4 targeted perturbation tests** designed to validate robustness of these high-frequency mechanics before live deployment.

---

## Strategy Characteristics

### Core Mechanism
```python
# RSI Hysteresis on 1-Hour Bars (same logic as Daily, different timeframe)
if RSI_1H > upper_band:
    position = LONG
elif RSI_1H < lower_band:
    position = FLAT
else:
    position = HOLD  # Hysteresis zone

# CRITICAL: Do NOT force exit at market close
# Exit only when next RSI signal triggers (could be hours or days later)
```

### Validated Performance Metrics
| Asset | RSI/Bands | Annual Return | Sharpe | Win Rate | Trades/Year | Annual Friction (5bps) |
|-------|-----------|---------------|--------|----------|-------------|------------------------|
| **TSLA** | 14, 60/40 | +41.5% | ~1.2 | 47.5% | 105 | 0.525% |
| **NVDA** | 28, 55/45 | +16.2% | ~0.8 | 48.3% | 240 | 1.200% |

**Key Observations:**
- TSLA: Faster RSI-14, wider 60/40 bands → fewer trades, higher return
- NVDA: Slower RSI-28, tighter 55/45 bands → more trades, lower return but higher win rate
- Combined portfolio: ~345 trades/year (vs 70-100 for Daily Trend)

### Overnight Hold Dependency

**Critical Validation Finding:**
| Mode | NVDA Return | TSLA Return | Logic |
|------|-------------|-------------|-------|
| **Swing Mode** (Overnight Holds) | +21.4% | +41.5% | Exit only on next RSI signal |
| **Day Mode** (Force 3:55 PM Exit) | +0.4% | Not tested | Force flat every day |

**Why Day Mode Fails:**
1. **Double Commissions**: Intraday round-trip = 2× friction per day
2. **Missed Gap Profits**: Tech stocks gap frequently (earnings, news); forced exit misses these
3. **Whipsaw Magnification**: Hourly signals flip more than daily; intraday exit = more losing trades

**Deployment Implication**: This strategy **cannot be run intraday-only**. It requires the ability to hold positions overnight and through weekends.

---

## Perturbation Test Suite

### Test 2.1: Gap Reversal Stress (Adverse Overnight Moves)

#### Objective
Quantify **gap risk exposure**. The strategy's profitability depends heavily on overnight gaps holding their direction. But what if gaps fade (mean reversion) instead of extending?

**Scenario**: Stock gaps up 2% pre-market → opens +2% → fades to +0.5% by 10 AM.

If the strategy entered long on a bullish RSI signal at 3 PM the previous day and held overnight, it captures the +2% gap at open. But if the gap immediately fades, the strategy gives back profits before the next hourly RSI signal can trigger an exit.

#### Methodology

**For each asset (TSLA, NVDA):**

1. **Identify All Overnight Holds:**
   - Parse 2025 backtest trade log
   - Flag all trades that held through market close (4:00 PM) and reopened next day
   - Extract gap size (% change from previous close to next open)

2. **Classify Gap Direction:**
   - **Bullish Gap**: Open > Previous Close (strategy held long)
   - **Bearish Gap**: Open < Previous Close (strategy held flat or would have avoided)

3. **Simulate Gap Fade Scenarios:**
   - **Baseline (No Fade)**: Gap holds all day (actual historical data)
   - **50% Fade**: Gap direction reverses by 50% within first 2 hours
     - Example: +2% gap → fades to +1% by 11 AM
   - **100% Fade (Full Reversal)**: Gap completely mean-reverts within first 2 hours
     - Example: +2% gap → fades to 0% by 11 AM
   - **Overshoot Reversal**: Gap not only fades but overshoots in opposite direction
     - Example: +2% gap → fades to -0.5% by 11 AM

4. **Recalculate P&L:**
   - For each overnight hold, adjust entry price based on fade scenario
   - Exit remains at next hourly RSI signal (unchanged)

**Total Test Matrix**: 2 assets × 3 fade scenarios = **6 test runs** + baseline

#### Pass Criteria

| Fade Scenario | TSLA Minimum | NVDA Minimum | Portfolio Target |
|---------------|--------------|--------------|------------------|
| **50% Fade** | Return ≥+25% | Return ≥+10% | Combined Sharpe ≥0.8 |
| **100% Fade** | Return ≥+10% | Return ≥0% | Combined Return ≥+10% |
| **Overshoot** | Return ≥0% | Return ≥-5% | Max Loss ≤20% of original returns |

#### Expected Outcomes

**Strong Gap Resilience:**
- Even with 50% gap fading, strategy remains highly profitable (TSLA >+25%)
- 100% gap fade scenario → strategy still positive (gap profits fully retained at open)
- Overshoot reversal → strategy enters stop-loss or RSI exit quickly (limited damage)

**Gap Dependency Risk:**
- 50% gap fade → returns collapse by >50%
- 100% gap fade → strategy flips negative
- Overshoot reversal → drawdowns exceed -30%

#### Key Metrics to Track

1. **Gap Contribution %**: What % of total 2025 return came from overnight gaps?
2. **Average Gap Size**: Mean % gap on overnight holds (bullish vs bearish)
3. **Gap Persistence**: What % of gaps held direction for ≥2 hours? ≥1 day?
4. **Worst-Case Gap Loss**: Largest single gap reversal loss in simulation

#### Implementation Notes

**Data Source**: 2025 1-hour bars (full year) + pre-market/open prices  
**Script**: `research/Perturbations/hourly_swing/test_gap_reversal.py`  
**Runtime**: ~5 minutes (2 assets, 3 scenarios, ~300-400 overnight holds total)

**Output Format:**
```csv
Asset,Fade_Scenario,Original_Return,Adjusted_Return,Gap_Contribution,Avg_Gap_Size,Pass_Status
TSLA,No_Fade,+41.5%,+41.5%,18.2%,1.8%,BASELINE
TSLA,50%_Fade,+41.5%,+32.1%,9.1%,0.9%,PASS
TSLA,100%_Fade,+41.5%,+23.3%,0.0%,0.0%,PASS
TSLA,Overshoot,+41.5%,+15.7%,-7.5%,-0.4%,MARGINAL
...
```

---

### Test 2.2: Execution Timing Sensitivity (Signal-to-Fill Lag)

#### Objective
Validate that the strategy edge survives **realistic execution delays**. 

In backtesting, we assume perfect fills at the 1-hour bar close price (e.g., signal at 2:00 PM, fill at 2:00:00 PM exactly). In live trading:
- Order submission takes 1-5 seconds
- Market orders get filled within seconds, but at potentially worse prices
- Limit orders might not fill immediately (partial fills, queue priority)
- Platform latency during volatile markets (TSLA/NVDA can move 0.5% in 60 seconds)

**Critical Question**: If there's a 15-30 minute delay between signal generation and actual fill, does the edge disappear?

#### Methodology

**For each asset (TSLA, NVDA):**

1. **Baseline (Perfect Execution):**
   - Signal at hour close → fill at exact hour close price
   - This is the validated 2025 backtest result

2. **Simulate Execution Lag:**
   - **15-Minute Lag**: Signal at 2:00 PM → fill at 2:15 PM price
   - **30-Minute Lag**: Signal at 2:00 PM → fill at 2:30 PM price
   - **60-Minute Lag**: Signal at 2:00 PM → fill at 3:00 PM price (next hourly bar)

3. **Price Slippage Modeling:**
   - Calculate average price change between hour close and +15 min / +30 min / +60 min
   - Apply this as "execution slippage" on top of base friction (5 bps)
   - Measure both **favorable slippage** (price moved in our favor) and **adverse slippage**

4. **Worst-Case Scenario:**
   - Assume **100% adverse slippage** (price always moves against us during execution window)
   - Example: Signal says "buy at $200" → by the time we execute, stock jumped to $201 (we pay +0.5%)

**Total Test Matrix**: 2 assets × 3 lag scenarios × 2 slippage models (realistic vs worst-case) = **12 test runs**

#### Pass Criteria

| Lag Duration | Slippage Model | TSLA Minimum | NVDA Minimum | Portfolio Target |
|--------------|----------------|--------------|--------------|------------------|
| **15 min** | Realistic | Return ≥+35% | Return ≥+13% | Sharpe ≥1.0 |
| **30 min** | Realistic | Return ≥+25% | Return ≥+8% | Return ≥+15% |
| **60 min** | Realistic | Return ≥+15% | Return ≥0% | Return ≥+8% |
| **15 min** | Worst-Case | Return ≥+25% | Return ≥+8% | Return ≥+10% |

#### Expected Outcomes

**Low Timing Sensitivity (Good):**
- 15-min lag → <10% return degradation (edge is durable across hourly bar)
- 30-min lag → <25% return degradation (still profitable)
- Worst-case 15-min lag → remains profitable (>+20% combined return)

**High Timing Sensitivity (Bad):**
- 15-min lag → >30% return degradation (edge only exists at exact signal time)
- 30-min lag → strategy flips negative
- Worst-case 15-min lag → losses exceed -10%

#### Key Metrics to Track

1. **Average Execution Slippage**: Mean % price movement during 15/30/60 min window
2. **Favorable vs Adverse Ratio**: How often does lag help vs hurt?
3. **Hourly Volatility**: Which hours have highest slippage (avoid trading at market open/close?)
4. **Trade-Specific Impact**: Do long entries suffer more lag than exits?

#### Implementation Notes

**Data Source**: 2025 1-minute bars (for intra-hour price movements)  
**Script**: `research/Perturbations/hourly_swing/test_execution_timing.py`  
**Runtime**: ~10 minutes (requires 1-min data to calculate intra-hour slippage)

**Output Format:**
```csv
Asset,Lag_Minutes,Slippage_Model,Original_Return,Adjusted_Return,Avg_Slippage_BPS,Pass_Status
TSLA,0,Baseline,+41.5%,+41.5%,0,BASELINE
TSLA,15,Realistic,+41.5%,+38.2%,8.3,PASS
TSLA,30,Realistic,+41.5%,+32.7%,15.1,PASS
TSLA,60,Realistic,+41.5%,+24.1%,22.4,MARGINAL
TSLA,15,Worst_Case,+41.5%,+29.3%,18.7,PASS
...
```

---

### Test 2.3: Friction Extreme Stress (Intraday Slippage)

#### Objective
Determine **exact friction breakeven point** for both assets. With 105-240 trades/year (2-4× Daily Trend frequency), friction costs compound extremely fast.

Validation assumed **5 bps round-trip** (0.05% = $50 on $100K position). This is optimistic for hourly trading:
- Intraday spreads are wider than daily close spreads
- TSLA/NVDA can have 0.10-0.30% spreads during volatile hours (9:30-10:30 AM, 3:00-4:00 PM)
- Market orders during fast moves can get filled 0.20-0.50% worse than limit price

**Critical Question**: At what friction level does high turnover destroy the edge completely?

#### Methodology

**For each asset (TSLA, NVDA), test escalating friction:**

| Friction Level | Round-Trip Cost | Scenario |
|----------------|-----------------|----------|
| **5 bps** | 0.05% | Validation baseline (institutional-grade fills) |
| **10 bps** | 0.10% | Realistic retail with smart routing |
| **20 bps** | 0.20% | Wide spreads during volatile hours |
| **30 bps** | 0.30% | Market orders in fast-moving conditions |
| **40 bps** | 0.40% | Worst-case (extreme volatility, poor execution) |
| **50 bps** | 0.50% | Catastrophic slippage (liquidity crisis) |

**Total Test Matrix**: 2 assets × 6 friction levels = **12 test runs**

#### Pass Criteria

| Friction Level | TSLA Requirement | NVDA Requirement | Portfolio Requirement |
|----------------|------------------|------------------|----------------------|
| **10 bps** | Return ≥+30% | Return ≥+10% | Both profitable |
| **20 bps** | Return ≥+15% | Return ≥0% | TSLA profitable |
| **30 bps** | Return ≥+5% | Return ≥-5% | Combined ≥0% |
| **40 bps** | Return ≥-10% | Return ≥-15% | Max loss <30% of capital |

#### Expected Outcomes

**Strong Friction Tolerance:**
- Both assets profitable at 20 bps
- TSLA (fewer trades, higher return) remains profitable even at 30-40 bps
- NVDA breakeven friction ≥25 bps

**Friction Vulnerability:**
- NVDA flips negative at 15-20 bps (240 trades/year × 15 bps = 3.6% friction drag)
- TSLA breakeven at <25 bps
- Both assets negative at 30 bps → strategy undeployable in retail conditions

#### Key Metrics to Track

1. **Friction Breakeven**: Exact bps where each asset return = 0%
2. **Friction Drag per Trade**: Total annual friction ÷ trade count
3. **Trade Count Sensitivity**: Does friction change number of trades? (Should not, unless it affects RSI calculation)
4. **Hourly Spread Analysis**: Which hours have highest average spreads? (Avoid those hours?)

#### Implementation Notes

**Data Source**: 2025 1-hour bars (same validation data)  
**Script**: `research/Perturbations/hourly_swing/test_friction_extreme.py`  
**Runtime**: ~3 minutes (12 backtests, simple friction overlay)

**Output Format:**
```csv
Asset,Friction_BPS,Net_Return,Sharpe,Trades,Total_Friction_Cost,Breakeven_Friction
TSLA,5,+41.5%,1.20,105,$525,N/A
TSLA,10,+36.2%,1.08,105,$1050,N/A
TSLA,20,+25.6%,0.82,105,$2100,N/A
TSLA,30,+15.0%,0.51,105,$3150,38.2
TSLA,40,+4.4%,0.15,105,$4200,38.2
TSLA,50,-6.2%,-0.22,105,$5250,38.2
...
```

---

### Test 2.4: Single-Asset Failure (Concentration Risk)

#### Objective
Assess **portfolio fragility** from only having 2 assets. Unlike Daily Trend (11 assets, diversification buffer), Hourly Swing has **zero diversification**.

**Critical Questions:**
1. If TSLA underperforms (or blows up) in live trading, what happens to the portfolio?
2. Is NVDA sufficient as a standalone strategy?
3. Does combining TSLA + NVDA actually improve risk-adjusted returns, or is TSLA just carrying NVDA?

#### Methodology

**Portfolio Composition Analysis:**

1. **Individual Asset Performance (Baseline):**
   - TSLA-only: +41.5% return, Sharpe ~1.2, 105 trades
   - NVDA-only: +16.2% return, Sharpe ~0.8, 240 trades

2. **Combined Portfolio (50/50 Allocation):**
   - $10K TSLA + $10K NVDA = $20K total
   - Weighted return: (0.5 × 41.5%) + (0.5 × 16.2%) = +28.85%
   - Calculate combined Sharpe (accounting for correlation)
   - Calculate combined max drawdown

3. **Stress Scenarios:**
   - **TSLA Fails**: Simulate TSLA returning -20% (complete strategy failure)
     - Portfolio becomes NVDA-only: +16.2% on half capital = +8.1% blended
   - **NVDA Fails**: Simulate NVDA returning -10%
     - Portfolio: (0.5 × 41.5%) + (0.5 × -10%) = +15.75% blended
   - **Both Underperform**: TSLA +10%, NVDA +5%
     - Portfolio: +7.5% blended (vs +28.85% expected)

4. **Correlation Analysis:**
   - Calculate TSLA-NVDA correlation on 2025 hourly returns
   - Measure diversification benefit (or lack thereof)
   - Compare to TSLA-only Sharpe vs combined TSLA+NVDA Sharpe

**Total Test Matrix**: 2 individual baselines + 1 combined + 3 stress scenarios = **6 analyses**

#### Pass Criteria

| Test | Minimum | Target | Ideal |
|------|---------|--------|-------|
| **TSLA-Only Sharpe** | ≥1.0 | ≥1.2 | ≥1.5 |
| **NVDA-Only Sharpe** | ≥0.6 | ≥0.8 | ≥1.0 |
| **Combined Sharpe** | ≥1.0 | ≥1.2 | ≥1.4 (diversification benefit) |
| **TSLA Failure Impact** | Portfolio ≥+5% | Portfolio ≥+8% | Portfolio ≥+10% |
| **Both Underperform** | Portfolio ≥+5% | Portfolio ≥+7% | Portfolio ≥+10% |

#### Expected Outcomes

**Healthy 2-Asset Portfolio:**
- Combined Sharpe > individual Sharpe (diversification benefit)
- TSLA-NVDA correlation <0.6 (meaningful diversification)
- TSLA failure → portfolio still positive (+8-10% from NVDA alone)

**Concentration Risk:**
- Combined Sharpe ≤ TSLA-only Sharpe (NVDA dilutes returns without improving risk)
- TSLA-NVDA correlation >0.8 (no diversification)
- TSLA failure → portfolio near-zero or negative

#### Key Metrics to Track

1. **Correlation**: TSLA-NVDA hourly returns correlation (2025)
2. **Sharpe Enhancement**: Combined Sharpe vs maximum individual Sharpe
3. **Downside Capture**: What % of TSLA's drawdowns does NVDA also experience?
4. **Optimal Allocation**: Should it be 50/50, or 70% TSLA / 30% NVDA? Or 100% TSLA?

#### Implementation Notes

**Data Source**: 2025 1-hour bars (same validation data)  
**Script**: `research/Perturbations/hourly_swing/test_single_asset_failure.py`  
**Runtime**: ~2 minutes (simple portfolio math + correlation calculation)

**Output Format:**
```csv
Scenario,TSLA_Return,NVDA_Return,Portfolio_Return,Portfolio_Sharpe,Correlation
Baseline,+41.5%,+16.2%,+28.85%,1.15,0.62
TSLA_Fails,-20%,+16.2%,+8.1%,0.35,0.62
NVDA_Fails,+41.5%,-10%,+15.75%,0.78,0.62
Both_Underperform,+10%,+5%,+7.5%,0.52,0.62
```

**Alternative Allocation Analysis:**
```csv
TSLA_Weight,NVDA_Weight,Portfolio_Return,Portfolio_Sharpe,Max_DD
100%,0%,+41.5%,1.20,-22%
70%,30%,+33.9%,1.18,-19%
50%,50%,+28.85%,1.15,-17%
30%,70%,+23.8%,1.08,-16%
0%,100%,+16.2%,0.80,-15%
```

---

## Risk Quantification & Mitigation

### Risk Matrix

| Risk Category | Likelihood | Impact | Mitigation Strategy |
|---------------|------------|--------|---------------------|
| **Gap Reversal** | Medium | High | Pass Test 2.1; implement pre-market gap fade filter (skip entry if gap >3% and fading) |
| **Execution Timing** | High | Medium | Pass Test 2.2; use limit orders within 0.10% of signal price; timeout after 15 min |
| **Friction Erosion** | High | Very High | Pass Test 2.3; MANDATORY profitable at ≥20 bps or strategy is undeployable |
| **Concentration** | Very High | Medium | Pass Test 2.4; add 1-2 more high-beta assets (e.g., AMD, COIN) to reduce single-asset dependency |

### Deployment Recommendations (Post-Testing)

#### Scenario 1: All Tests Pass
- **Action**: Deploy full $20K allocation (50/50 TSLA/NVDA)
- **Execution**: Use limit orders ±0.10% of hourly close; 15-minute timeout → retry next hour
- **Monitoring**: Daily friction tracking; pause if 3-day average slippage >15 bps

#### Scenario 2: Gap Reversal Test Fails (100% fade → negative returns)
- **Action**: Implement **Gap Fade Filter**
  - If pre-market gap >2%, check if gap is holding at 9:45 AM
  - If gap faded >50% by 9:45 AM → skip entry, wait for next signal
- **Rationale**: Avoid entering on gaps that are already reversing

#### Scenario 3: Friction Test Fails (<20 bps tolerance)
- **Action**: **DO NOT DEPLOY STRATEGY**
- **Rationale**: Hourly strategies REQUIRE <20 bps friction to be viable; if edge doesn't survive realistic slippage, it's not deployable
- **Alternative**: Convert to Daily Trend for these assets (TSLA/NVDA already validated on daily bars)

#### Scenario 4: Concentration Test Fails (Combined Sharpe ≤ TSLA-only)
- **Action**: Deploy **TSLA-only** with $20K allocation
- **Reasoning**: If NVDA dilutes returns without improving risk, drop it
- **Alternative**: Find 1-2 additional high-beta assets to create true 3-4 asset portfolio

---

## Success Metrics

### Testing Phase (Pre-Deployment)
| Metric | Target |
|--------|--------|
| **Gap Resilience** | Profitable even with 50% gap fading |
| **Execution Timing** | <15% return degradation at 30-min lag |
| **Friction Tolerance** | Both assets profitable at 20 bps |
| **Diversification** | Combined Sharpe ≥ individual Sharpe |

### Live Deployment Phase (First 3 Months)
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Portfolio Sharpe** | ≥1.0 | <0.8 for 2 weeks |
| **Average Execution Slippage** | ≤12 bps | >18 bps for 1 week |
| **Gap Fade %** | <30% of gaps fade >50% | >50% for 1 week (market regime shift) |
| **Individual Asset Performance** | Both assets profitable monthly | Either asset negative for 2 months (drop asset) |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Test Development** | 1 day | 4 Python scripts ready |
| **Test Execution** | 1 day | All 36 test runs complete (6+12+12+6) |
| **Analysis & Reporting** | 1 day | Pass/fail determination; friction breakeven analysis |
| **Deployment Decision** | 1 day | Go/No-Go with optimized allocation (50/50 vs TSLA-only) |

**Total**: 4 business days from approval to deployment readiness.

---

## Appendices

### A. Key Assumptions
1. **Overnight Gaps**: Historical 2025 gap distribution remains representative (no systemic regime shift to zero gaps)
2. **Execution Access**: Ability to hold positions overnight (not PDT-restricted account)
3. **Data Quality**: 1-hour bars and 1-minute bars (for slippage modeling) are accurate
4. **No Correlation Shift**: TSLA-NVDA correlation remains in 0.5-0.7 range (currently 0.62)

### B. Out-of-Scope (Future Work)
- Expanding universe to 5-10 high-beta assets (AMD, COIN, SQ, etc.)
- Hybrid Daily+Hourly strategy (run Daily Trend on same assets, Hourly as overlay)
- Options hedging for overnight gap risk (buy cheap OTM puts before close)
- Intraday volatility filter (skip trading during low-volume hours like 1-2 PM)

---

**Report Status**: DRAFT — Pending Test Execution  
**Next Action**: Execute Test 2.1 (Gap Reversal Stress) and update with results  
**Owner**: Quantitative Research Team  
**Last Updated**: 2026-01-18
