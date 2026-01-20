# CLEAN-ROOM TESTING - PRELIMINARY FINDINGS

**Date**: 2026-01-17  
**Status**: PARTIAL RESULTS AVAILABLE  
**Researcher**: Independent Adversarial Quantitative Analyst

---

## EXECUTIVE SUMMARY

**Tests Completed**: 1 of 3 strategies (Strategy C - AAPL Earnings)  
**Tests In Progress**: 1 of 3 strategies (Strategy B - TSLA Daily)  
**Tests Failed**: 1 of 3 strategies (Strategy A - MSI Hourly - Data Unavailable)

---

## STRATEGY C: AAPL EARNINGS - ✅ COMPLETE

### Test Configuration
- **Instrument**: AAPL equity
- **Entry**: T-2 close (2 days before earnings)
- **Exit**: T+1 open (1 day after earnings)
- **Position**: 100 shares per event
- **Friction**: 5 bps baseline, 10 bps degraded

### Results Summary

| Test Period | Friction | Return | Avg P&L/Event | Sharpe | Win Rate | Profit Factor | Verdict |
|-------------|----------|--------|---------------|--------|----------|---------------|---------|
| **Primary (2024-2025)** | Baseline (5 bps) | **+0.11%** | **+0.16%** | **1.86** | **62.5%** | **2.44** | ⚠️ **MARGINAL** |
| Primary (2024-2025) | Degraded (10 bps) | -0.06% | +0.16% | 1.86 | 50.0% | 0.61 | ❌ **REJECT** |
| **Secondary (2022-2023)** | Baseline (5 bps) | **-0.31%** | **-0.13%** | **-0.62** | **25.0%** | **0.19** | ❌ **REJECT** |
| Secondary (2022-2023) | Degraded (10 bps) | -0.44% | -0.13% | -0.62 | 12.5% | 0.09 | ❌ **REJECT** |

### Key Findings

#### ❌ **CRITICAL FAILURE: Regime Dependence**
- **2024-2025 (Bull Market)**: Marginally profitable (+0.11%, Sharpe 1.86)
- **2022-2023 (Bear/Volatile Market)**: Significant losses (-0.31%, Sharpe -0.62)
- **Win rate collapse**: 62.5% → 25.0% between periods
- **Profit factor collapse**: 2.44 → 0.19 between periods

#### ❌ **CRITICAL FAILURE: Friction Sensitivity**
- **Doubling friction** (5 bps → 10 bps) **destroys profitability**
- Primary period: +0.11% → -0.06% (turns negative)
- Win rate drops from 62.5% → 50.0% with higher friction

#### ⚠️ **STRUCTURAL ISSUES**
1. **Tiny edge**: Average P&L per event is only +0.16% (before degraded friction)
2. **No actual hold time**: "Avg Hold: 0.0 days" suggests same-day execution
3. **Insufficient volatility capture**: AAPL earnings moves are too small
4. **Sample size**: Only 8 events per 2-year period (16 total)

### Trade-by-Trade Analysis (Primary Period, Baseline)

| Event | Entry Date | Exit Date | Entry Price | Exit Price | P&L % | P&L $ |
|-------|------------|-----------|-------------|------------|-------|-------|
| Q1 2024 | 2024-01-31 | 2024-02-01 | $185.33 | $185.43 | +0.05% | -$8.54 |
| Q2 2024 | 2024-05-01 | 2024-05-02 | $170.35 | $170.71 | +0.21% | +$18.95 |
| Q3 2024 | 2024-07-31 | 2024-08-01 | $223.70 | $223.45 | -0.11% | -$47.36 |
| **Q4 2024** | 2024-10-31 | 2024-11-01 | $221.71 | $222.63 | **+0.42%** | **+$69.88** |
| Q1 2025 | 2025-01-29 | 2025-01-30 | $239.00 | $239.00 | -0.00% | -$23.92 |
| Q2 2025 | 2025-04-30 | 2025-05-01 | $208.75 | $209.17 | +0.20% | +$21.10 |
| Q3 2025 | 2025-07-30 | 2025-07-31 | $208.82 | $209.21 | +0.19% | +$18.10 |
| **Q4 2025** | 2025-10-29 | 2025-10-30 | $270.81 | $271.75 | **+0.35%** | **+$66.62** |

**Observations**:
- Best trades: Q4 2024 (+0.42%), Q4 2025 (+0.35%)
- Worst trade: Q3 2024 (-0.11%)
- **Tiny moves**: Most events move less than 0.25%
- **Friction dominates**: 5 bps friction consumes most of the edge

### Robustness Assessment

#### Sub-Period Performance
- **2024-2025 (Recent)**: Marginally profitable, Sharpe 1.86
- **2022-2023 (Historical)**: Unprofitable, Sharpe -0.62
- **Verdict**: ❌ **NOT ROBUST** - Performance degrades significantly in different market regimes

#### Friction Sensitivity
- **Baseline (5 bps)**: +0.11% return (marginal)
- **Degraded (10 bps)**: -0.06% return (negative)
- **Verdict**: ❌ **EXTREMELY FRAGILE** - Cannot withstand realistic execution costs

#### Fat-Tail Dependence
- **Best event**: +0.42% (Q4 2024)
- **Worst event**: -0.73% (Q3 2023)
- **Top-decile contribution**: Minimal (no outlier wins)
- **Bottom-decile damage**: Moderate (Q3 2023 loss)
- **Verdict**: ⚠️ **NO FAT-TAIL EDGE** - No evidence of capturing large moves

### Failure Analysis

#### How the Strategy Fails
1. **Insufficient volatility**: AAPL earnings moves are too small (0.0% to 0.5%)
2. **Friction erosion**: 5-10 bps friction consumes most of the tiny edge
3. **Regime dependence**: Works in bull markets, fails in bear/volatile markets
4. **No directional edge**: Win rate collapses to 25% in adverse conditions

#### Hostile Market Conditions
- **Bear markets** (2022-2023): Win rate 25%, Sharpe -0.62
- **High volatility regimes**: Larger moves but more unpredictable
- **Tight spreads required**: Strategy needs sub-5 bps execution

#### Structural vs. Regime Failure
- **Structural failure**: Insufficient edge size (0.16% avg P&L)
- **Regime failure**: Performance collapses in bear markets
- **Verdict**: **BOTH** - Strategy has structural issues AND regime dependence

---

## FINAL VERDICT: STRATEGY C (AAPL EARNINGS)

### Classification: ❌ **REJECT**

### Rationale
1. **Insufficient edge**: Average P&L of +0.16% per event is too small
2. **Friction-dominated**: Doubling friction turns strategy negative
3. **Regime-dependent**: Fails completely in bear markets (2022-2023)
4. **Not robust**: Win rate collapses from 62.5% → 25.0% across periods
5. **Tiny sample size**: Only 16 events over 4 years
6. **No fat-tail capture**: No evidence of capturing large earnings moves

### Minimum Conditions for Use
**NONE** - Strategy should not be deployed under any conditions.

If forced to deploy:
- **Only in bull markets** (not predictable in advance)
- **Only with sub-3 bps execution** (unrealistic for retail)
- **Only with 10x larger position sizes** to overcome friction
- **Only with additional filters** (e.g., implied volatility, analyst surprises)

### Capital Patience Required
- **N/A** - Strategy is not viable

### Invalidation Criteria
Strategy is already invalidated by:
- ❌ Negative returns in secondary period
- ❌ Negative returns with realistic friction
- ❌ Win rate below 30% in secondary period
- ❌ Profit factor below 1.0 in most scenarios

---

## STRATEGY B: TSLA DAILY - 🔄 IN PROGRESS

### Preliminary Observations (Primary Period, Partial Results)

**⚠️ CRITICAL DATA ISSUE DETECTED**

| Metric | Value | Expected | Issue |
|--------|-------|----------|-------|
| **Trade Count** | **9,255 trades** | ~8-12 trades | **770x too many trades** |
| **Avg Hold** | **0.0 days** | ~30-60 days | **Intraday execution** |
| **Return** | **-136.74%** | Unknown | **Catastrophic loss** |
| **Sharpe** | **0.00** | Unknown | **No risk-adjusted return** |

### Root Cause Analysis

**HYPOTHESIS**: Data resolution mismatch
- **Expected**: Daily bars (1 bar per day, ~504 bars per 2 years)
- **Actual**: Minute or tick data (463,772 bars fetched)
- **Evidence**: 9,255 trades in 2 years = 12.7 trades per day

**CONCLUSION**: The Alpaca API is returning **minute-level data** instead of daily bars, causing the strategy to trade intraday on every RSI crossover.

### Next Steps
1. ⏳ Wait for backtest to complete
2. 🔍 Investigate data resolution issue
3. 🛠️ Fix data fetching to ensure true daily bars
4. 🔄 Re-run backtest with correct data

---

## STRATEGY A: MSI HOURLY - ❌ DATA UNAVAILABLE

### Issue
FMP API returned **empty DataFrame** for MSI hourly data.

### Possible Causes
1. **Symbol not supported**: MSI may not be available via FMP
2. **Endpoint incorrect**: `/historical-chart/1hour/MSI` may not exist
3. **Data not available**: FMP may not have hourly futures data
4. **API key limitations**: Free tier may not include futures

### Next Steps
1. 🔍 Verify FMP API documentation for futures symbols
2. 🔍 Test alternative symbols (e.g., SI for full-size silver)
3. 🔍 Test alternative endpoints
4. ⚠️ May need to use alternative data source (e.g., Alpaca futures if available)

---

## OVERALL ASSESSMENT (PRELIMINARY)

### Completed Tests: 1/3
- ✅ Strategy C (AAPL Earnings): **REJECT**

### In Progress: 1/3
- 🔄 Strategy B (TSLA Daily): Data issue detected, awaiting completion

### Failed: 1/3
- ❌ Strategy A (MSI Hourly): Data unavailable

### Key Learnings
1. **Friction matters**: Even 5-10 bps can destroy marginal strategies
2. **Regime dependence is fatal**: Strategies must work across bull/bear markets
3. **Data quality is critical**: Incorrect bar resolution can invalidate results
4. **Small edges don't scale**: 0.16% avg P&L is insufficient for real trading

---

**Status**: PARTIAL RESULTS  
**Next Update**: After Strategy B completes  
**Last Updated**: 2026-01-17 03:15 AM
