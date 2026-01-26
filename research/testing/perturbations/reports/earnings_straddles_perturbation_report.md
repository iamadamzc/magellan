# Earnings Straddles — Perturbation Testing Protocol

**Strategy ID**: Strategy 4  
**Asset Class**: Options (ATM Straddles on Tech Mega-Caps)  
**Validation Period**: 2020-2025 (6 Full Years - Most Comprehensive Testing)  
**Assets Under Test**: 7 Tickers (GOOGL, AAPL, AMD, NVDA, TSLA, MSFT, AMZN)  
**Capital Allocation**: $10,000 per event (start with GOOGL, scale to 4-7 tickers)  
**Report Date**: 2026-01-18

---

## Executive Summary

The Earnings Straddles strategy is the **most rigorously validated** strategy in the Magellan portfolio, having passed full Walk-Forward Analysis (WFA) across 6 years and 7 major tech tickers. Unlike the FOMC strategy (8 events, 1 asset), this strategy has been tested across **24+ earnings events per ticker**, providing strong statistical confidence.

**Core Thesis:**  
Tech mega-cap earnings create **predictable volatility expansion** that can be harvested via 3-day ATM straddle holds. The strategy exploits:
1. **Pre-earnings IV buildup** (T-2 entry captures rising IV)
2. **Earnings announcement volatility** (stock moves 4-10% overnight)
3. **Sustained post-earnings volatility** (T+1 exit before full IV crush)

**Key Validation Insight:**  
Performance **improved over time** as AI boom (2023-2024) increased tech earnings volatility. NVDA average earnings move grew from 4.9% (2020-2021) to 10.6% (2023).

**Primary Deployment Risks:**
1. **Ticker-specific robustness** - Some tickers (GOOGL Sharpe 4.80) >> others (AMZN Sharpe 1.12)
2. **Entry timing sensitivity** - T-2 vs T-1 vs T-0 entry could drastically change P&L
3. **IV crush dynamics** - Post-earnings IV collapse varies (30-60% drop per ticker/quarter)
4. **Regime dependency** - 2023-2024 AI boom inflated earnings moves; what if this normalizes?
5. **Sample size per ticker** - Only 4 events/year per ticker (limited statistical power per asset)

This protocol outlines **4 targeted perturbation tests** designed to validate the strategy's robustness across different market regimes and ticker characteristics.

---

## Strategy Characteristics

### Core Mechanism
```python
# Entry: T-2 days before earnings (2 trading days before announcement)
BUY CALL (ATM, 7-14 DTE)  # Match expiration to earnings week
BUY PUT (ATM, 7-14 DTE)
# Straddle cost: typically 4-8% of stock price

# Exit: T+1 day after earnings (fixed 3-day hold)
CLOSE both legs (no discretion)

# Hold Time: ~3 trading days (T-2 → T+1)
# Profit Driver: Earnings-driven volatility expansion > IV crush
```

### Validated Performance Metrics (2020-2025 WFA)
| Metric | Value |
|--------|-------|
| **Sample Size** | 24 events per ticker (NVDA); ~168 total events across 7 tickers |
| **Average OOS Sharpe** | 2.25 |
| **Win Rate** | 58.3% (aggregate across all tickers) |
| **Profit Factor** | 3.22 |
| **Annual Return** | 79.1% (portfolio-level) |
| **Frequency** | ~1.3 trades per quarter per ticker (4-5 events/year) |

### Performance by Ticker (Deployment Tiers)

#### 🟢 **Primary (High Confidence):**
| Ticker | Sharpe | Win Rate | Avg Move | Notes |
|--------|--------|----------|----------|-------|
| **GOOGL** | 4.80 | 62.5% | 6.2% | Highest Sharpe; most consistent; DEPLOY FIRST |

#### 🟡 **Secondary (Moderate Confidence):**
| Ticker | Sharpe | Win Rate | Avg Move | Notes |
|--------|--------|----------|----------|-------|
| **AAPL** | 2.90 | 54.2% | 4.8% | Stable; lower volatility than NVDA/TSLA |
| **AMD** | 2.52 | 58.3% | 7.1% | High beta; tech sector proxy |
| **NVDA** | 2.38 | 45.8% | 8.2% | High moves (AI boom) but lower win rate |
| **TSLA** | 2.00 | 50.0% | 9.4% | Extreme volatility; binary outcomes |

#### ⚪ **Marginal (Paper Trade First):**
| Ticker | Sharpe | Win Rate | Avg Move | Notes |
|--------|--------|----------|----------|-------|
| **MSFT** | 1.45 | 50.0% | 4.2% | Borderline; low moves (stable business) |
| **AMZN** | 1.12 | 30.0% | 5.8% | Lowest win rate; inconsistent |

### NVDA Performance by Year (6-Year Evolution)
| Year | Sharpe | Win Rate | Return | Avg Move | Market Regime |
|------|--------|----------|--------|----------|---------------|
| 2020 | 0.30 | 25% | +19.9% | 4.9% | Early COVID recovery |
| 2021 | 0.20 | 25% | +13.5% | 5.1% | Tech boom (pre-AI) |
| 2022 | -0.17 | 50% | -9.5% | 3.4% | ❌ Bear market; IV crush exceeded moves |
| 2023 | 1.59 | 75% | +230.6% | 10.6% | ✅ AI boom begins |
| 2024 | 2.63 | 100% | +157.1% | 8.2% | ✅ AI peak; outsized moves |
| 2025 | 0.83 | 75% | +63.4% | 5.7% | ✅ AI normalization |

**Key Observation**: Strategy performance tracks **earnings move magnitude**. 2022 bear market (low moves, high IV crush) = negative. 2023-2024 AI boom (high moves) = exceptional.

---

## Perturbation Test Suite

### Test 4.1: Ticker Robustness (Secondary Asset Validation)

#### Objective
Validate that the strategy is **genuinely diversified** and not over-reliant on GOOGL (Sharpe 4.80). If removing GOOGL collapses portfolio Sharpe, the strategy is effectively a "GOOGL-only" trade with false diversification.

**Critical Questions:**
1. Can the strategy remain profitable (Sharpe ≥1.5) without GOOGL?
2. Do secondary tickers (AAPL, AMD, NVDA, TSLA) add genuine diversification or just dilute returns?
3. Is there an "optimal portfolio" of 3-4 tickers that outperforms the full 7-ticker portfolio?

#### Methodology

**Portfolio Composition Stress Testing:**

1. **Individual Ticker Performance (Baselines):**
   - Run full 6-year WFA for each of the 7 tickers individually
   - Measure Sharpe, win rate, max drawdown, profit factor
   - Identify which tickers are standalone profitable (Sharpe ≥1.0)

2. **Tiered Portfolios:**
   - **GOOGL-Only**: 100% allocation to GOOGL (4 events/year)
   - **Top 3**: GOOGL + AAPL + AMD (12 events/year)
   - **Top 5**: GOOGL + AAPL + AMD + NVDA + TSLA (20 events/year)
   - **Full 7**: All tickers (28 events/year)

3. **GOOGL Removal Test:**
   - **No-GOOGL Portfolio**: AAPL + AMD + NVDA + TSLA + MSFT + AMZN (24 events/year)
   - Measure portfolio Sharpe without the top performer
   - Determine if remaining 6 tickers can maintain Sharpe ≥2.0

4. **Bottom-Tier Exclusion:**
   - Remove MSFT + AMZN (lowest Sharpe)
   - Portfolio: GOOGL + AAPL + AMD + NVDA + TSLA (20 events/year)
   - Measure if excluding marginal tickers improves risk-adjusted returns

**Total Test Matrix**: 7 individual baselines + 4 tiered portfolios + 2 exclusion tests = **13 analyses**

#### Pass Criteria

| Test | Minimum | Target | Ideal |
|------|---------|--------|-------|
| **GOOGL-Only Sharpe** | ≥3.0 | ≥4.0 | ≥4.80 (validated) |
| **Top 3 Sharpe** | ≥2.5 | ≥3.0 | ≥3.5 |
| **Top 5 Sharpe** | ≥2.0 | ≥2.5 | ≥3.0 |
| **Full 7 Sharpe** | ≥1.8 | ≥2.25 (validated) | ≥2.5 |
| **No-GOOGL Sharpe** | ≥1.5 | ≥2.0 | ≥2.5 |
| **No-Marginal (Top 5) Sharpe** | ≥2.5 | ≥2.8 | ≥3.0 (better than Full 7?) |

#### Expected Outcomes

**Strong Ticker Diversification:**
- No-GOOGL portfolio maintains Sharpe ≥2.0 (strategy works across multiple tickers)
- Top 3 (GOOGL, AAPL, AMD) delivers Sharpe ≥3.0 (meaningful diversification)
- Full 7 Sharpe comparable to Top 5 (marginal tickers don't dilute returns)

**GOOGL Dependency:**
- No-GOOGL portfolio Sharpe <1.5 (strategy collapses without GOOGL)
- GOOGL-only outperforms all tiered portfolios (false diversification)
- Removing MSFT/AMZN improves Sharpe by >0.5 (they're actively harmful)

#### Key Metrics to Track

1. **Ticker Contribution**: % of total portfolio return attributable to each ticker
2. **Sharpe Distribution**: Sharpe across different portfolio compositions
3. **Optimal Allocation**: Should it be equal-weight or weight by Sharpe/volatility?
4. **Correlation Matrix**: Pairwise correlation of earnings returns (do they diversify?)

#### Implementation Notes

**Data Source**: 6-year WFA results (2020-2025) for all 7 tickers  
**Script**: `research/Perturbations/earnings_straddles/test_ticker_robustness.py`  
**Runtime**: ~5 minutes (13 portfolio combinations from pre-computed WFA data)

**Output Format:**
```csv
Portfolio,Tickers,Sharpe,Win_Rate,Annual_Return,Max_DD,Events_Per_Year
GOOGL_Only,GOOGL,4.80,62.5%,+85.2%,-12%,4
Top_3,GOOGL+AAPL+AMD,3.42,58.3%,+92.1%,-14%,12
Top_5,GOOGL+AAPL+AMD+NVDA+TSLA,2.87,56.0%,+88.5%,-18%,20
Full_7,All,2.25,58.3%,+79.1%,-20%,28
No_GOOGL,AAPL+AMD+NVDA+TSLA+MSFT+AMZN,1.82,55.0%,+68.3%,-22%,24
No_Marginal,GOOGL+AAPL+AMD+NVDA+TSLA,3.12,57.5%,+94.7%,-16%,20
```

---

### Test 4.2: Entry Timing Sensitivity (T-2 vs T-1 vs T-0)

#### Objective
Validate that **T-2 entry** (2 days before earnings) is optimal, or if the strategy is robust across different entry timings. Entry timing affects:
1. **IV exposure**: Earlier entry = more IV buildup captured (but also more theta decay)
2. **Theta decay**: Longer hold = more time decay
3. **Event risk**: T-0 entry avoids "pre-announcement leak" risk (stock moving before earnings)

**Critical Question**: Is the edge fragile (only works at exact T-2) or robust (works at T-3, T-1, T-0)?

#### Methodology

**For NVDA (24 events, 2020-2025), test alternative entry timings:**

| Entry Timing | Entry Day | Exit Day | Hold Duration | Rationale |
|--------------|-----------|----------|---------------|-----------|
| **Baseline** | T-2 | T+1 | 3 days | Original validation |
| **Early (T-3)** | T-3 | T+1 | 4 days | Capture more IV buildup (more theta decay) |
| **Late (T-1)** | T-1 | T+1 | 2 days | Reduce theta decay; still capture earnings move |
| **Same-Day (T-0)** | T+0 (morning) | T+1 | 1.5 days | Minimal theta; pure directional bet on earnings |
| **Late Exit (T+2)** | T-2 | T+2 | 4 days | Hold longer; more IV crush risk |

**For each timing variant:**
1. Recalculate straddle cost (ATM strike at new entry time)
2. Recalculate exit value (T+1 or T+2 close)
3. Measure P&L, Sharpe, win rate

**Expand to all 7 tickers:**
- After validating on NVDA, run same analysis on:
  - GOOGL (highest Sharpe — should be robust)
  - AMZN (lowest Sharpe — likely more timing-sensitive)
  - 1-2 mid-tier tickers (AAPL, AMD)

**Total Test Matrix**: 1 ticker (NVDA) × 5 timing variants + 3 tickers (GOOGL, AMZN, AAPL) × 2 key variants (T-1, T-0) = **5 + 6 = 11 test runs**

#### Pass Criteria

| Entry Timing | NVDA Sharpe Target | GOOGL Sharpe Target | AMZN Sharpe Target | Notes |
|--------------|--------------------|--------------------|-------------------|-------|
| **T-2 (Baseline)** | 2.38 | 4.80 | 1.12 | Validated performance |
| **T-3 (Early)** | ≥1.8 | ≥3.5 | ≥0.8 | Acceptable with theta decay |
| **T-1 (Late)** | ≥2.0 | ≥4.0 | ≥1.0 | Should improve theta efficiency |
| **T-0 (Same-Day)** | ≥1.5 | ≥3.0 | ≥0.5 | Pure earnings bet; expect lower Sharpe |
| **T+2 Exit** | ≥1.5 | ≥3.0 | ≥0.5 | IV crush will hurt; lower expected Sharpe |

#### Expected Outcomes

**Timing Robustness (Good):**
- T-1 entry performs comparably to T-2 (Sharpe degradation <20%)
- T-0 entry still profitable (Sharpe ≥1.5 for NVDA, ≥3.0 for GOOGL)
- T-3 entry acceptable (theta decay doesn't destroy edge)

**Timing Sensitivity (Bad):**
- T-1 entry flips multiple tickers negative (edge only exists at T-2)
- T-0 entry destroys Sharpe (strategy requires pre-earnings IV buildup)
- T+2 exit catastrophic (IV crush exceeds earnings move capture)

#### Key Metrics to Track

1. **Optimal Entry Day**: Which entry timing maximizes Sharpe for each ticker?
2. **Theta Decay Impact**: How much does each extra day of hold cost in theta?
3. **IV Buildup Value**: How much pre-earnings IV expansion occurs from T-3 to T-2 to T-1?
4. **Ticker-Specific Patterns**: Do high-IV tickers (NVDA, TSLA) benefit from earlier entry?

#### Implementation Notes

**Data Source**: 6-year daily options data (if available) or synthetic IV/theta model  
**Script**: `research/Perturbations/earnings_straddles/test_entry_timing.py`  
**Runtime**: ~10 minutes (11 backtests with options pricing calculations)

**Output Format:**
```csv
Ticker,Entry_Timing,Entry_Day,Exit_Day,Hold_Days,Sharpe,Win_Rate,Avg_Return,Theta_Cost
NVDA,Baseline,T-2,T+1,3,2.38,45.8%,+19.2%,2.1%
NVDA,Early,T-3,T+1,4,1.92,41.7%,+15.7%,3.2%
NVDA,Late,T-1,T+1,2,2.51,50.0%,+20.8%,1.1%
NVDA,Same_Day,T-0,T+1,1.5,1.73,45.8%,+12.5%,0.6%
NVDA,Late_Exit,T-2,T+2,4,1.55,37.5%,+11.2%,2.8%
GOOGL,Late,T-1,T+1,2,4.92,66.7%,+22.3%,0.9%
GOOGL,Same_Day,T-0,T+1,1.5,3.28,62.5%,+16.1%,0.5%
AMZN,Late,T-1,T+1,2,0.98,25.0%,+4.2%,1.3%
AMZN,Same_Day,T-0,T+1,1.5,0.52,20.0%,-1.8%,0.7%
...
```

---

### Test 4.3: IV Crush Severity (Post-Earnings Collapse)

#### Objective
Quantify **IV crush risk** and validate that the strategy profits from **realized earnings moves**, not just IV expansion. Post-earnings, IV typically collapses by 30-60% within 24 hours. If the underlying stock doesn't move enough to offset this IV crush, the straddle loses value.

**Critical Question**: How severe can IV crush be before the strategy flips negative?

#### Methodology

**For each ticker (focus on NVDA, GOOGL, AMZN):**

1. **Historical IV Analysis:**
   - Extract pre-earnings IV (T-2 close)
   - Extract post-earnings IV (T+1 close)
   - Calculate IV crush %: (Post-IV - Pre-IV) / Pre-IV
   - Classify events into:
     - **Mild Crush**: <40% IV drop
     - **Normal Crush**: 40-50% IV drop
     - **Severe Crush**: >50% IV drop

2. **Profitability by Crush Cohort:**
   - Group all 24 NVDA events by crush severity
   - Measure win rate, Sharpe, avg profit for each cohort
   - Identify if strategy only works with mild IV crush

3. **Synthetic Stress Test (+20% Worse IV Crush):**
   - For each historical event, simulate IV crushing 20% more than actual
   - Example: If historical crush = -40%, simulate -48% (-40% × 1.20)
   - Recalculate straddle exit value
   - Measure adjusted Sharpe and win rate

4. **Breakeven IV Crush:**
   - For each event, calculate the IV crush % that would cause P&L = 0%
   - Example: If stock moved +8% but IV crushed -70%, what crush % causes breakeven?
   - Identify minimum stock move required for profitability at different crush levels

**Total Test Matrix**: 3 tickers × 3 crush cohorts + 3 tickers × stress test = **12 analyses**

#### Pass Criteria

| IV Crush Scenario | NVDA Win Rate | GOOGL Win Rate | AMZN Win Rate | Portfolio Target |
|-------------------|---------------|----------------|---------------|------------------|
| **Mild Crush (<40%)** | ≥75% | ≥85% | ≥50% | Sharpe ≥3.0 |
| **Normal Crush (40-50%)** | ≥50% | ≥60% | ≥30% | Sharpe ≥2.0 |
| **Severe Crush (>50%)** | ≥30% | ≥50% | ≥20% | Sharpe ≥1.0 |
| **Stress (+20% Worse)** | ≥40% | ≥55% | ≥25% | Sharpe ≥1.5 |

#### Expected Outcomes

**IV Resilience (Good):**
- Strategy profitable in all crush cohorts (even severe >50% crush)
- Stress test (+20% worse) → Sharpe degrades <30%
- Edge comes primarily from **realized stock move** (gamma), not IV expansion (vega)

**IV Dependency (Bad):**
- Strategy only profitable in mild crush cohort (<40% IV drop)
- Severe crush → win rate <30%; Sharpe <0.5
- Stress test → multiple tickers flip negative

#### Key Metrics to Track

1. **Average IV Crush by Ticker**: NVDA vs GOOGL vs AMZN (does NVDA crush more?)
2. **Realized Move vs IV Crush**: Scatter plot (X = stock move %, Y = IV crush %)
3. **Breakeven Stock Move**: For each ticker, what stock move % is required to offset a 50% IV crush?
4. **Ticker-Specific IV Patterns**: Do mega-caps (GOOGL, AAPL) have lower IV crush than high-beta (NVDA, TSLA)?

#### Implementation Notes

**Data Source**: Historical IV data (VIX-style calculation) or options chain data  
**Script**: `research/Perturbations/earnings_straddles/test_iv_crush_severity.py`  
**Runtime**: ~8 minutes (12 cohort analyses + stress simulations)

**Output Format:**
```csv
Ticker,Event_Date,Stock_Move,Pre_IV,Post_IV,IV_Crush_Pct,Cohort,P&L,Win_Status
NVDA,2023-01-15,+12.3%,0.85,0.42,-50.6%,Severe,+28.5%,WIN
NVDA,2023-04-20,+5.8%,0.78,0.52,-33.3%,Mild,+15.2%,WIN
NVDA,2022-08-10,+2.1%,0.92,0.38,-58.7%,Severe,-4.3%,LOSS
GOOGL,2024-10-05,+6.5%,0.62,0.35,-43.5%,Normal,+18.7%,WIN
AMZN,2023-07-18,+4.2%,0.88,0.42,-52.3%,Severe,+2.1%,MARGINAL
...
```

**Cohort Summary:**
```csv
Ticker,IV_Crush_Cohort,Event_Count,Win_Rate,Avg_Return,Sharpe
NVDA,Mild_(<40%),8,75.0%,+24.3%,3.12
NVDA,Normal_(40-50%),10,50.0%,+16.8%,2.05
NVDA,Severe_(>50%),6,33.3%,+8.2%,0.87
GOOGL,Mild,9,88.9%,+28.1%,5.23
GOOGL,Normal,11,63.6%,+21.5%,4.18
GOOGL,Severe,4,50.0%,+14.7%,2.92
...
```

---

### Test 4.4: Regime Normalization (AI Boom Reversal)

#### Objective
Stress-test the strategy against **earnings move normalization**. The 2023-2024 AI boom created outsized tech earnings moves:
- NVDA average move: 4.9% (2020-2021) → 10.6% (2023) → 8.2% (2024)
- AMD, TSLA also saw inflated earnings volatility

**Critical Question**: If AI hype fades and earnings moves revert to 2020-2021 levels (5% average instead of 8-10%), does the strategy remain profitable?

#### Methodology

**Synthetic Regime Shift Simulation:**

1. **Baseline (Historical):**
   - Use actual 6-year earnings moves (2020-2025) as baseline
   - Sharpe 2.25, return +79.1%

2. **Moderate Normalization (-30% Earnings Moves):**
   - Reduce all 2023-2024 earnings moves by 30%
   - Example: If NVDA moved +10% on 2023 Q3 earnings, simulate +7% move
   - Keep all 2020-2022 and 2025 moves unchanged (they're already "normal")
   - Recalculate straddle P&L with smaller realized moves

3. **Full Normalization (-50% Earnings Moves):**
   - Reduce all 2023-2024 earnings moves by 50%
   - Example: +10% move → +5% move (back to 2020-2021 average)
   - This simulates complete AI hype reversal

4. **Permanent Low-Volatility Regime:**
   - Reduce **all 6 years** of earnings moves by 30%
   - Simulates structural shift to lower volatility (e.g., regulations, market maturity)

**Test across all 7 tickers, but focus on:**
- **NVDA** (most inflated by AI boom)
- **GOOGL** (more stable; less AI-dependent)
- **MSFT** (already low volatility; baseline for comparison)

**Total Test Matrix**: 7 tickers × 3 normalization scenarios = **21 test runs**

#### Pass Criteria

| Normalization Scenario | NVDA Sharpe | GOOGL Sharpe | Full Portfolio Sharpe | Deployment Viability |
|------------------------|-------------|--------------|-----------------------|----------------------|
| **Baseline (Historical)** | 2.38 | 4.80 | 2.25 | Validated |
| **Moderate (-30% 2023-24)** | ≥1.5 | ≥3.5 | ≥1.8 | Deployable |
| **Full (-50% 2023-24)** | ≥1.0 | ≥2.5 | ≥1.5 | Marginal; reduce allocation |
| **Permanent Low-Vol (-30% All Years)** | ≥0.8 | ≥2.0 | ≥1.0 | Minimum viability |

#### Expected Outcomes

**Regime Resilience (Good):**
- Strategy remains profitable (Sharpe ≥1.0) even with -50% earnings move normalization
- GOOGL and AAPL (stable mega-caps) maintain Sharpe ≥2.5 regardless of regime
- Even in permanent low-vol regime, portfolio Sharpe ≥1.2

**Regime Dependency (Bad):**
- NVDA flips negative with -30% normalization (strategy only worked during AI boom)
- Portfolio Sharpe <1.0 with -50% normalization (unsustainable edge)
- Only 2-3 tickers remain profitable in permanent low-vol regime

#### Key Metrics to Track

1. **AI Boom Contribution**: What % of 6-year returns came from 2023-2024 AI boom?
2. **Ticker-Specific Regime Sensitivity**: Which tickers most dependent on inflated moves?
3. **Stable Alpha**: Which tickers (GOOGL, AAPL?) profitable across all regimes?
4. **Deployment Strategy**: Should we over-weight stable tickers (GOOGL, AAPL) and under-weight AI-dependent (NVDA, AMD)?

#### Implementation Notes

**Data Source**: 6-year WFA results with synthetic regime overlays  
**Script**: `research/Perturbations/earnings_straddles/test_regime_normalization.py`  
**Runtime**: ~7 minutes (21 backtests with synthetic move adjustments)

**Output Format:**
```csv
Ticker,Scenario,Sharpe,Win_Rate,Avg_Return,2023_24_Contribution_Pct
NVDA,Baseline,2.38,45.8%,+19.2%,68.5%
NVDA,Moderate_Norm_-30%,1.72,37.5%,+12.8%,42.1%
NVDA,Full_Norm_-50%,1.14,33.3%,+7.5%,18.3%
NVDA,Permanent_Low_Vol,0.95,37.5%,+6.2%,N/A
GOOGL,Baseline,4.80,62.5%,+24.7%,35.2%
GOOGL,Moderate_Norm_-30%,4.12,58.3%,+21.3%,22.8%
GOOGL,Full_Norm_-50%,3.28,54.2%,+17.9%,12.5%
GOOGL,Permanent_Low_Vol,2.85,54.2%,+15.8%,N/A
...
```

**Portfolio Summary:**
```csv
Scenario,Portfolio_Sharpe,Deployable_Tickers,Annual_Return,Max_DD
Baseline,2.25,7,+79.1%,-20%
Moderate_Norm,1.92,6,+62.3%,-22%
Full_Norm,1.58,5,+48.7%,-25%
Permanent_Low_Vol,1.35,4,+38.2%,-28%
```

---

## Risk Quantification & Mitigation

### Risk Matrix

| Risk Category | Likelihood | Impact | Mitigation Strategy |
|---------------|------------|--------|---------------------|
| **Ticker Concentration (GOOGL)** | Medium | Medium | Pass Test 4.1; deploy Top 3-5 tickers; avoid over-relying on single asset |
| **Entry Timing Precision** | Low | Medium | Pass Test 4.2; T-1 entry acceptable as backup if T-2 missed |
| **IV Crush Severity** | High | High | Pass Test 4.3; MANDATORY profitable in severe crush (>50% IV drop) |
| **AI Boom Normalization** | High | Very High | Pass Test 4.4; focus on stable tickers (GOOGL, AAPL); reduce NVDA allocation if moves normalize |

### Deployment Recommendations (Post-Testing)

#### Scenario 1: All Tests Pass
- **Action**: Deploy phased rollout
  - **Phase 1 (Months 1-3)**: GOOGL only ($10K per event, 4 events/year)
  - **Phase 2 (Months 4-6)**: Add AAPL + AMD ($30K total, 12 events/year)
  - **Phase 3 (Months 7-12)**: Add NVDA + TSLA ($50K total, 20 events/year)
  - **Phase 4 (Year 2+)**: Consider MSFT + AMZN if paper trading successful

#### Scenario 2: Ticker Robustness Fails (No-GOOGL Sharpe <1.5)
- **Action**: **GOOGL-only deployment**
  - Deploy $20K to GOOGL (4 events/year)
  - Paper trade other tickers for 6-12 months
  - Re-evaluate diversification after collecting more live performance data

#### Scenario 3: Regime Normalization Fails (Sharpe <1.0 at -50% normalization)
- **Action**: **Reduce allocation; over-weight stable tickers**
  - GOOGL: 50% allocation (most regime-resilient)
  - AAPL: 30% allocation (stable mega-cap)
  - AMD/NVDA: 20% combined (high-beta exposure only during favorable regimes)
- **Dynamic Allocation**: Increase high-beta tickers (NVDA, TSLA) when recent earnings moves >8%; reduce when <5%

#### Scenario 4: IV Crush Fails (Win rate <30% in severe crush cohort)
- **Action**: Implement **IV Crush Filter**
  - Before entering trade, check historical IV crush for this ticker
  - If ticker has >60% crush history (e.g., NVDA 2022), reduce position size by 50%
  - Alternatively, exit at T+0 (day of earnings) instead of T+1 to avoid full IV crush

---

## Success Metrics

### Testing Phase (Pre-Deployment)
| Metric | Target |
|--------|--------|
| **Ticker Diversification** | No-GOOGL Sharpe ≥1.5; Top 3 Sharpe ≥2.5 |
| **Entry Timing Robustness** | T-1 entry Sharpe degradation ≤20% |
| **IV Crush Resilience** | Win rate ≥40% even in severe crush (>50% IV drop) |
| **Regime Resilience** | Sharpe ≥1.0 even with -50% earnings move normalization |

### Live Deployment Phase (First 12 Events)
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Portfolio Sharpe** | ≥2.0 | <1.5 for 6 events |
| **Win Rate** | ≥55% | <45% for 6 events |
| **Individual Ticker Performance** | Each ticker profitable over 4 events | Any ticker with 3+ consecutive losses (drop ticker) |
| **Earnings Move Tracking** | Average moves remain ≥6% | <5% for 3 consecutive quarters (regime shift warning) |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Test Development** | 2 days | 4 Python scripts ready |
| **Test Execution** | 2 days | All 57 test runs complete (13+11+12+21) |
| **Analysis & Reporting** | 2 days | Pass/fail determination; optimal ticker portfolio; regime contingency plan |
| **Phase 1 Deployment** | 3 months | GOOGL-only live trading (12 events minimum for statistical significance) |

**Total**: 6 days testing + 3 months Phase 1 validation before scaling to multi-ticker portfolio.

---

## Appendices

### A. Earnings Calendar (Q1 2025)
| Ticker | Next Earnings (Est) | Deploy Phase |
|--------|---------------------|--------------|
| **GOOGL** | Late Jan / Early Feb | Phase 1 (immediate) |
| **AAPL** | Late Jan | Phase 2 (after GOOGL validation) |
| **AMD** | Late Jan | Phase 2 |
| **NVDA** | Mid-Feb | Phase 3 (after 3+ successful events) |
| **TSLA** | Late Jan | Phase 3 |
| **MSFT** | Late Jan | Phase 4 (paper trade only initially) |
| **AMZN** | Early Feb | Phase 4 (paper trade only initially) |

### B. Key Assumptions
1. **Earnings Schedule Stability**: Tech mega-caps maintain quarterly earnings (no schedule changes)
2. **Options Liquidity**: ATM 0DTE/1DTE options remain available with tight spreads
3. **IV Patterns**: Historical IV buildup/crush patterns remain representative (no structural market changes)
4. **Market Structure**: No major regulatory changes to options markets (e.g., pattern day trader rules, margin requirements)

### C. Out-of-Scope (Future Work)
- Expanding to non-tech sectors (financials, healthcare, energy)
- Dynamic position sizing based on historical IV crush patterns per ticker
- Hybrid strategy (straddle + directional bias based on pre-earnings sentiment)
- Rolling positions (taking partial profits at T+0, holding winners to T+2)

---

**Report Status**: DRAFT — Pending Test Execution  
**Next Action**: Execute Test 4.4 (Regime Normalization) — highest priority given AI boom concerns  
**Owner**: Quantitative Research Team  
**Last Updated**: 2026-01-18
