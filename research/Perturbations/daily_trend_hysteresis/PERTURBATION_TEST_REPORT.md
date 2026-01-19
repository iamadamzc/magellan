# Daily Trend Hysteresis — Perturbation Testing Protocol

**Strategy ID**: Strategy 1  
**Asset Class**: Equities (Daily Bars)  
**Validation Period**: June 2024 - January 2026 (19 months)  
**Assets Under Test**: 11 (7 MAG7 + 4 Indices/ETFs)  
**Capital Allocation**: $110,000 (69% of total portfolio)  
**Report Date**: 2026-01-18

---

## Executive Summary

The Daily Trend Hysteresis strategy is the **cornerstone** of the Magellan portfolio, commanding the largest capital allocation and spanning the most diverse asset base. Its RSI hysteresis mechanism (Schmidt trigger logic) demonstrated robust performance across 200+ parameter configurations during validation.

**Primary Deployment Risks:**
1. **Parameter overfitting** - Each asset uses custom RSI period (21 vs 28) and band thresholds (55/45 to 65/35)
2. **Regime dependency** - 19-month validation period was predominantly bullish (2024-2025)
3. **Friction sensitivity** - High trade frequency (70-100 trades/year) amplifies execution cost impact
4. **Correlation concentration** - MAG7 stocks highly correlated; simultaneous drawdown risk

This protocol outlines **4 targeted perturbation tests** designed to stress-test these specific vulnerabilities before live deployment.

---

## Strategy Characteristics

### Core Mechanism
```python
# RSI Hysteresis (Schmidt Trigger)
if RSI > upper_band:  # e.g., 55, 58, 60, 65
    position = LONG
elif RSI < lower_band:  # e.g., 35, 40, 42, 45
    position = FLAT
else:
    position = HOLD  # Hysteresis zone prevents whipsaw
```

### Validated Performance Metrics
| Metric | Range | Best Asset |
|--------|-------|------------|
| **Annual Return** | +13% to +167% | TSLA: +167% |
| **Sharpe Ratio** | 1.2 - 2.41 | GLD: 2.41 |
| **Max Drawdown** | -15% to -20% | Portfolio-level |
| **Win Rate** | 86% | 6/7 MAG7 profitable in 2025 |
| **Trade Frequency** | 70-100/year | All 11 assets combined |

### Parameter Distribution
| Asset | RSI Period | Upper/Lower Bands | 2024-2026 Return |
|-------|------------|-------------------|------------------|
| AAPL | 28 | 65/35 | +31% |
| AMZN | 21 | 55/45 | +17% |
| GOOGL | 28 | 55/45 | +108% |
| META | 28 | 55/45 | +13% |
| MSFT | 21 | 58/42 | +14% |
| NVDA | 28 | 58/42 | +25% |
| TSLA | 28 | 58/42 | +167% |
| SPY | 21 | 58/42 | +25% |
| QQQ | 21 | 60/40 | +29% |
| IWM | 28 | 65/35 | +38% |
| GLD | 21 | 65/35 | +96% |

**Key Observation**: Mix of RSI-21 (5 assets) and RSI-28 (6 assets); band widths vary from tight (55/45) to wide (65/35).

---

## Perturbation Test Suite

### Test 1.1: Parameter Robustness (Neighboring Parameter Stability)

#### Objective
Verify that edge is **structurally robust** rather than overfitted to exact RSI period or band thresholds. If a strategy only works at RSI-28 but fails completely at RSI-27 or RSI-29, it's likely curve-fitted.

#### Methodology

**For each of 11 assets:**

1. **RSI Period Perturbation:**
   - If validated config uses RSI-21, test at RSI-20 and RSI-22
   - If validated config uses RSI-28, test at RSI-27 and RSI-29
   - Keep band thresholds fixed at validated values

2. **Upper Band Perturbation:**
   - Test at ±2 threshold (e.g., 55 → 53/57, 60 → 58/62, 65 → 63/67)
   - Keep RSI period and lower band fixed

3. **Lower Band Perturbation:**
   - Test at ±2 threshold (e.g., 45 → 43/47, 40 → 38/42, 35 → 33/37)
   - Keep RSI period and upper band fixed

**Total Test Matrix**: 11 assets × 6 perturbations = **66 test runs**

#### Pass Criteria

| Rigor Level | Requirement |
|-------------|-------------|
| **Minimum** | ≥60% of neighboring configs remain profitable (return > 0%) |
| **Target** | ≥70% of neighboring configs remain profitable |
| **Ideal** | ≥80% of neighboring configs remain profitable; Sharpe degradation ≤30% |

#### Expected Outcomes

**Strong Edge Signals:**
- Small parameter changes (±1 RSI period, ±2 band threshold) cause ≤20% return degradation
- Sharpe ratio remains >1.0 even at suboptimal parameters
- Trade count changes by ≤30% (hysteresis remains functional)

**Overfitting Warning Signals:**
- Return flips negative with ±1 RSI period change
- Sharpe drops below 0.5 at neighboring parameters
- Win rate collapses by >20 percentage points

#### Implementation Notes

**Data Source**: Same validation data (Jun 2024 - Jan 2026)  
**Script**: `research/Perturbations/daily_trend_hysteresis/test_parameter_robustness.py`  
**Runtime**: ~10 minutes (66 backtests on cached daily data)

**Output Format:**
```csv
Asset,Validated_RSI,Validated_Bands,Perturbed_Config,Return,Sharpe,Max_DD,Trade_Count,Pass_Status
AAPL,28,65/35,RSI-27_65/35,+28.3%,1.25,-18%,82,PASS
AAPL,28,65/35,RSI-29_65/35,+29.1%,1.31,-16%,78,PASS
AAPL,28,65/35,RSI-28_63/35,+27.5%,1.18,-19%,88,PASS
...
```

---

### Test 1.2: Friction Sensitivity (Execution Cost Stress)

#### Objective
Quantify **exact friction tolerance** before strategy edge is destroyed. High trade frequency (70-100 trades/year) means slippage and commissions compound rapidly.

During validation, **2 bps per round-trip** was assumed (approximately $0.01/share on $100-$500 stocks). This is optimistic for retail execution and may not account for:
- Wider spreads during volatile market opens/closes
- Partial fills at worse prices
- Market impact on large orders

#### Methodology

**For each of 11 assets**, rerun full 19-month backtest with escalating friction costs:

| Friction Level | Round-Trip Cost | Scenario |
|----------------|-----------------|----------|
| **Baseline** | 2 bps | Original validation assumption |
| **Conservative** | 5 bps | Institutional-grade execution |
| **Realistic** | 10 bps | Retail broker with smart routing |
| **Stressed** | 15 bps | Adverse fills, wide spreads |
| **Extreme** | 20 bps | Worst-case scenario (market orders in illiquid moments) |

**Total Test Matrix**: 11 assets × 5 friction levels = **55 test runs**

#### Pass Criteria

| Friction Level | Requirement |
|----------------|-------------|
| **5 bps** | All 11 assets remain profitable; portfolio Sharpe ≥1.2 |
| **10 bps** | ≥9/11 assets profitable; portfolio Sharpe ≥1.0 |
| **15 bps** | ≥8/11 assets profitable; at least 2 MAG7 stocks + 1 index profitable |
| **20 bps** | ≥5/11 assets profitable; GOOGL/TSLA/GLD core trio remains positive |

#### Expected Outcomes

**Strong Friction Tolerance:**
- Strategy profitable at 10-15 bps for most assets
- High-alpha assets (GOOGL +108%, TSLA +167%) remain profitable even at 20 bps
- Portfolio-level return degrades linearly (not catastrophically) with friction

**Friction Vulnerability:**
- Multiple assets flip negative at 10 bps
- Portfolio Sharpe drops below 0.8 at 15 bps
- Only 1-2 assets survive 20 bps test

#### Key Metrics to Track

1. **Friction Breakeven Point**: Exact bps where each asset return crosses 0%
2. **Sharpe Degradation Rate**: Change in Sharpe per 1 bps friction increase
3. **Trade Count Sensitivity**: Does friction cause fewer trades (wider stops)? Or same trades (pure profit erosion)?

#### Implementation Notes

**Data Source**: Same validation data (Jun 2024 - Jan 2026)  
**Script**: `research/Perturbations/daily_trend_hysteresis/test_friction_sensitivity.py`  
**Runtime**: ~15 minutes (55 backtests with layered friction simulation)

**Output Format:**
```csv
Asset,Friction_BPS,Net_Return,Sharpe,Trades,Avg_Friction_Per_Trade,Breakeven_Friction
AAPL,2,+31.0%,1.42,85,$17.20,N/A
AAPL,5,+27.8%,1.28,85,$43.00,N/A
AAPL,10,+22.3%,1.09,85,$86.00,N/A
AAPL,15,+16.8%,0.87,85,$129.00,22.4
AAPL,20,+11.3%,0.64,85,$172.00,22.4
...
```

---

### Test 1.3: Regime Shift Stress (Bear Market Simulation)

#### Objective
Validate strategy performance during **prolonged drawdown periods**. The 19-month validation window (Jun 2024 - Jan 2026) was predominantly bullish:
- S&P 500: +15% (Jun 2024 - Jan 2026)
- Nasdaq: +22% (driven by AI boom)
- No sustained >20% correction

**Critical Question**: Does hysteresis prevent catastrophic whipsaw during high-volatility bear markets, or does it simply "buy the dip" repeatedly into a falling knife?

#### Methodology

**Synthetic Bear Market Overlay**

Since true out-of-sample bear market data isn't available post-validation, we'll apply a **synthetic regime shift** to historical data:

1. **Identify Bull Market Segment (Baseline):**
   - Use Jun 2024 - Jan 2026 as baseline (actual validation data)

2. **Create Synthetic Bear Market:**
   - Take 2022 bear market data (Jan 2022 - Oct 2022: SPY -25% drawdown)
   - Scale to match -30% portfolio drawdown scenario
   - Apply to all 11 assets with realistic correlation structure

3. **Test Scenarios:**
   - **Slow Grind Down**: -30% over 6 months (mimics 2022)
   - **Flash Crash + Recovery**: -30% in 1 month, +15% recovery over 2 months (mimics 2020 COVID)
   - **V-Shaped Bottom**: -30% in 3 months, full recovery in 3 months

4. **Measure:**
   - Max drawdown duration
   - Number of consecutive losses (whipsaw indicator)
   - Recovery time after "market bottom"
   - Final return (does strategy profit from the bounce?)

**Total Test Matrix**: 11 assets × 3 bear market scenarios = **33 test runs**

#### Pass Criteria

| Metric | Minimum | Target | Ideal |
|--------|---------|--------|-------|
| **Max Drawdown** | ≤40% | ≤35% | ≤30% |
| **Consecutive Losses** | ≤8 | ≤6 | ≤4 |
| **Recovery Time** | ≤6 months | ≤4 months | ≤3 months |
| **Post-Bottom Return** | ≥0% | ≥+10% | ≥+20% |

#### Expected Outcomes

**Hysteresis Advantage:**
- Strategy reduces trade frequency during high volatility (wider RSI swings = fewer crosses)
- Lower band (40-45) acts as floor; strategy exits early in decline
- Recovers faster than buy-and-hold due to hysteresis lag effect

**Hysteresis Failure:**
- Strategy whipsaws violently (8+ consecutive small losses)
- Max drawdown exceeds -40% (worse than buy-and-hold SPY -30%)
- Recovery takes >6 months (missed the bounce)

#### Implementation Notes

**Data Source**: 2022 bear market (Jan-Oct 2022) scaled to -30% for all assets  
**Script**: `research/Perturbations/daily_trend_hysteresis/test_regime_shift.py`  
**Runtime**: ~20 minutes (33 synthetic backtests + correlation modeling)

**Output Format:**
```csv
Asset,Scenario,Max_DD,Consecutive_Losses,Recovery_Months,Final_Return,Pass_Status
AAPL,Slow_Grind,-32%,5,3.5,+8.2%,PASS
AAPL,Flash_Crash,-38%,3,2.1,+12.5%,MARGINAL
AAPL,V_Shaped,-29%,4,2.8,+15.3%,PASS
...
```

---

### Test 1.4: Correlation Breakdown (Diversification Stress)

#### Objective
Assess **concentration risk** in the MAG7 portfolio. These 7 stocks are highly correlated (often >0.7 pairwise correlation), meaning they tend to move together. If all 7 simultaneously enter drawdown, portfolio-level risk could be underestimated.

**Critical Questions:**
1. Is any single asset critically load-bearing (>40% of returns)?
2. Does removing 3 random MAG7 assets collapse portfolio Sharpe?
3. What is the minimum number of assets required to maintain Sharpe >1.0?

#### Methodology

**Monte Carlo Asset Removal Simulation**

1. **Full Portfolio Baseline:**
   - Run all 11 assets (7 MAG7 + 4 indices/ETFs) on validation data
   - Calculate portfolio-level Sharpe, return, max drawdown

2. **Random Removal (10,000 iterations):**
   - Randomly select 3 of 7 MAG7 assets to remove
   - Keep all 4 indices/ETFs (SPY, QQQ, IWM, GLD)
   - Recalculate portfolio metrics with remaining 8 assets (4 MAG7 + 4 indices)

3. **Sequential Removal (Best-to-Worst):**
   - Remove top performer (TSLA +167%) → measure impact
   - Remove top 2 (TSLA +167%, GOOGL +108%) → measure impact
   - Remove top 3 → measure impact
   - Repeat for worst performers (META +13%, MSFT +14%, AMZN +17%)

4. **Minimum Viable Portfolio:**
   - Identify smallest subset of assets that maintains Sharpe ≥1.0
   - Test if "Core 4" (GOOGL, TSLA, GLD, QQQ) outperforms full portfolio

**Total Test Matrix**: 10,000 Monte Carlo + 14 sequential removals = **10,014 simulations**

#### Pass Criteria

| Test | Minimum | Target | Ideal |
|------|---------|--------|-------|
| **Monte Carlo (3 removed)** | Sharpe ≥1.0 in ≥70% of runs | Sharpe ≥1.0 in ≥80% of runs | Sharpe ≥1.2 in ≥80% of runs |
| **Top Performer Removed** | Portfolio Sharpe remains ≥1.1 | Portfolio Sharpe remains ≥1.2 | Portfolio return drops ≤20% |
| **Single Asset Contribution** | No asset contributes >50% of returns | No asset contributes >40% | No asset contributes >30% |
| **Minimum Viable Portfolio** | 5 assets required for Sharpe ≥1.0 | 4 assets sufficient | 3 assets sufficient |

#### Expected Outcomes

**Healthy Diversification:**
- Removing any 3 MAG7 assets → Sharpe remains >1.0 in 90%+ of cases
- TSLA/GOOGL are strong contributors but not load-bearing (portfolio survives their removal)
- GLD (Sharpe 2.41) acts as portfolio stabilizer even with low correlation to tech

**Concentration Risk:**
- Removing TSLA or GOOGL → portfolio Sharpe drops below 1.0
- >50% of portfolio return comes from 2-3 assets
- Minimum viable portfolio requires 8+ assets (little diversification benefit)

#### Key Metrics to Track

1. **Asset Contribution**: % of total portfolio return attributable to each asset
2. **Sharpe Distribution**: Histogram of portfolio Sharpe across 10,000 removal simulations
3. **Worst-Case Scenario**: Removing which 3 assets causes maximum Sharpe degradation?
4. **Core vs Full**: Does "Core 4" (GOOGL, TSLA, GLD, QQQ) actually outperform the full 11-asset portfolio?

#### Implementation Notes

**Data Source**: Same validation data (Jun 2024 - Jan 2026)  
**Script**: `research/Perturbations/daily_trend_hysteresis/test_correlation_breakdown.py`  
**Runtime**: ~30 minutes (10,014 portfolio combinations)

**Output Format:**
```csv
Iteration,Removed_Assets,Remaining_MAG7,Portfolio_Sharpe,Portfolio_Return,Max_DD
1,"AAPL,MSFT,META","AMZN,GOOGL,NVDA,TSLA",1.28,+52.3%,-18%
2,"NVDA,AMZN,AAPL","GOOGL,META,MSFT,TSLA",1.15,+47.1%,-21%
...
```

**Sequential Removal Summary:**
```csv
Assets_Removed,Remaining_Count,Portfolio_Sharpe,Return,Top_Contributor
None,11,1.35,+65.0%,TSLA (25%)
TSLA,10,1.22,+48.5%,GOOGL (32%)
TSLA+GOOGL,9,1.08,+37.2%,GLD (28%)
...
```

---

## Risk Quantification & Mitigation

### Risk Matrix

| Risk Category | Likelihood | Impact | Mitigation Strategy |
|---------------|------------|--------|---------------------|
| **Parameter Overfitting** | Medium | High | Pass Test 1.1; reduce allocation to assets with narrow parameter optima |
| **Friction Erosion** | Medium | Medium | Pass Test 1.2; use limit orders, avoid market opens/closes |
| **Bear Market Whipsaw** | Low | High | Pass Test 1.3; implement volatility regime filter (pause trading if VIX >35) |
| **Correlation Concentration** | High | Medium | Pass Test 1.4; maintain minimum 8 assets; add non-correlated assets (GLD critical) |

### Deployment Recommendations (Post-Testing)

#### Scenario 1: All Tests Pass
- **Action**: Deploy full $110K allocation across all 11 assets
- **Monitoring**: Weekly Sharpe tracking; alert if any asset Sharpe <0.5 for 2 consecutive weeks

#### Scenario 2: Friction Test Fails (<8 assets profitable at 15 bps)
- **Action**: Reduce allocation to high-friction assets; prioritize low-turnover configs
- **Example**: Drop AAPL (RSI-28, 65/35 bands = tightest, most trades) if friction breakeven <12 bps

#### Scenario 3: Regime Test Fails (Max DD >40% in bear market simulation)
- **Action**: Implement **VIX Circuit Breaker**
  - Pause all Daily Trend trading when VIX >35 (extreme fear)
  - Resume when VIX <30 for 3 consecutive days
- **Rationale**: Hysteresis works in trending markets, fails in pure volatility

#### Scenario 4: Correlation Test Fails (>50% return from single asset)
- **Action**: Rebalance portfolio to equal-weight
- **Current**: ~$10K per asset
- **Alternative**: Weight by inverse volatility or inverse correlation to MAG7

---

## Success Metrics

### Testing Phase (Pre-Deployment)
| Metric | Target |
|--------|--------|
| **Parameter Robustness** | ≥70% neighboring configs profitable |
| **Friction Tolerance** | All assets profitable at 10 bps |
| **Bear Market Max DD** | ≤35% in synthetic stress test |
| **Diversification** | No asset contributes >40% of returns |

### Live Deployment Phase (First 3 Months)
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Portfolio Sharpe** | ≥1.2 | <1.0 for 2 weeks |
| **Max Drawdown** | ≤20% | -25% |
| **Trade Execution Quality** | Avg slippage ≤8 bps | >12 bps for 1 week |
| **Correlation** | MAG7 pairwise <0.75 | >0.85 for 1 week (add non-correlated asset) |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Test Development** | 2 days | 4 Python scripts ready to execute |
| **Test Execution** | 1 day | All 186 test runs complete (66+55+33+10,014) |
| **Analysis & Reporting** | 1 day | Pass/fail determination; risk mitigation plan |
| **Deployment Decision** | 1 day | Go/No-Go with adjusted capital allocation |

**Total**: 5 business days from approval to deployment readiness.

---

## Appendices

### A. Reference Code Structure
```python
# Pseudocode for Test 1.1 (Parameter Robustness)
for asset in [AAPL, AMZN, GOOGL, ...]:
    validated_config = load_config(asset)
    
    # RSI perturbations
    for rsi_delta in [-1, +1]:
        perturbed_config = validated_config.copy()
        perturbed_config['rsi_period'] += rsi_delta
        result = backtest(asset, perturbed_config, data='Jun2024-Jan2026')
        log_result(asset, perturbed_config, result)
    
    # Band perturbations
    for band in ['upper', 'lower']:
        for delta in [-2, +2]:
            perturbed_config = validated_config.copy()
            perturbed_config[f'{band}_band'] += delta
            result = backtest(asset, perturbed_config, data='Jun2024-Jan2026')
            log_result(asset, perturbed_config, result)
```

### B. Key Assumptions
1. **Data Quality**: FMP daily bars assumed accurate and complete (no missing days)
2. **Execution**: All trades assumed to execute at daily close price + friction
3. **No Slippage Variance**: Friction applied uniformly (reality: worse during volatile days)
4. **No Position Sizing**: All tests assume full $10K allocation per asset (no Kelly criterion or risk parity)

### C. Out-of-Scope (Future Work)
- Multi-asset portfolio optimization (Modern Portfolio Theory allocation)
- Dynamic position sizing based on volatility regime
- Options hedging overlay for downside protection
- Sector rotation (currently concentrated in tech)

---

**Report Status**: DRAFT — Pending Test Execution  
**Next Action**: Execute Test 1.1 (Parameter Robustness) and update with results  
**Owner**: Quantitative Research Team  
**Last Updated**: 2026-01-18
