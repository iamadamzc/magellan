# MNQ Inverse Analysis: The Statistical DNA of a Winning Trade

**Author:** Magellan Quant Research  
**Date:** 2026-01-30  
**Asset:** MNQ (Micro E-mini Nasdaq-100 Futures)

---

## Executive Summary

**Objective:** Perform an "Inverse Analysis" to discover what market conditions are present when "perfect" trades occur - revealing the statistical DNA of consistently profitable entries.

**Definition of "Golden Trade" (Sniper Entry):**
- **REWARD**: Price reaches **+40 points** within the next 20 minutes
- **RISK**: Max drawdown stays **under 12 points** (tight stop survives)

This analysis identifies the indicators that show the **biggest divergence** between Golden Trades and normal market noise.

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| **Total Rows Analyzed** | 1,768,970 |
| **Date Range** | 2021-01-29 to 2026-01-28 (5 years) |
| **Unique Trading Days** | 1,557 |
| **Golden Trades Found** | 517,382 |
| **Golden Trade Rate** | 29.25% |

---

## Daily Frequency Analysis

| Metric | Value |
|--------|-------|
| **Days with at least 1 Golden Trade** | 1,525 / 1,557 (97.9%) |
| **Days with ZERO Golden Trades** | 32 |
| **Average Golden Trades per day** | 332 |
| **Median per day** | 341 |
| **Maximum in single day** | 1,000 |
| **Minimum in single day** | 1 |

**Conclusion:** Golden Trades occur on nearly every trading day (97.9%) with an average of ~332 opportunities per day.

---

## Feature Importance Report

### Key Findings

When a "Golden Trade" occurs, here's how market conditions differ from normal:

---

#### 1. Distance from EMA200 (Trend)

> **"When Golden Trades happen, the average Trend_Distance is -543.90"**  
> *(vs Normal Market: +225.88)*  
> **Divergence: 340.8% LOWER**

**Interpretation:** Golden Trades occur when price is significantly BELOW the 200-period EMA - a contrarian, mean-reversion setup.

---

#### 2. Consecutive Candles

> **"When Golden Trades happen, the average Consecutive_Candles is -0.62"**  
> *(vs Normal Market: +0.28)*  
> **Divergence: 323.4% LOWER**

**Interpretation:** Golden Trades occur after sequences of RED candles, indicating a selling exhaustion point.

---

#### 3. Distance from VWAP (Stretch)

> **"When Golden Trades happen, the average Stretch_VWAP is -496.00"**  
> *(vs Normal Market: +345.06)*  
> **Divergence: 243.7% LOWER**

**Interpretation:** Golden Trades occur when price is stretched significantly BELOW VWAP - the "snap back" to fair value provides the +40pt reward.

---

#### 4. ATR (Volatility)

> **"When Golden Trades happen, the average ATR is 481.94"**  
> *(vs Normal Market: 849.24)*  
> **Divergence: 43.3% LOWER**

**Interpretation:** Golden Trades occur in LOWER volatility environments - calmer conditions allow for tighter risk management.

---

#### 5. Bar Range (High-Low)

> **Divergence: 28.5% HIGHER**

**Interpretation:** Despite lower ATR, the current bar shows a WIDER range - indicating a potential exhaustion/reversal bar.

---

#### 6. RSI (Momentum)

> **"When Golden Trades happen, the average RSI is 45.58"**  
> *(vs Normal Market: 52.06)*  
> **Divergence: 12.5% LOWER**

**Interpretation:** Golden Trades occur in slightly oversold conditions, but RSI is NOT a strong differentiator.

---

#### 7. Volume Ratio (Panic)

> **"When Golden Trades happen, the average Volume_Ratio is 0.97"**  
> *(vs Normal Market: 1.05)*  
> **Divergence: 7.8% LOWER**

**Interpretation:** Volume is NOT a significant factor - Golden Trades don't require unusual volume spikes.

---

## Feature Importance Ranking

**Ranked by divergence from normal market conditions:**

| Rank | Feature | Divergence | Direction |
|------|---------|------------|-----------|
| 1 | **Distance from EMA200 (Trend)** | **340.8%** | LOWER |
| 2 | **Consecutive Candles** | **323.4%** | LOWER |
| 3 | **Distance from VWAP (Stretch)** | **243.7%** | LOWER |
| 4 | ATR (Volatility) | 43.3% | LOWER |
| 5 | Bar Range (High-Low) | 28.5% | HIGHER |
| 6 | RSI (Momentum) | 12.5% | LOWER |
| 7 | Volume Ratio (Panic) | 7.8% | LOWER |

---

## Time of Day Analysis

**Best Hour for Golden Trades: 04:00 (45.4% rate)**

### Hourly Distribution

| Hour | Golden Rate | Tier |
|------|-------------|------|
| 04:00 | 45.43% | Best |
| 03:00 | 43.02% | Best |
| 02:00 | 42.81% | Best |
| 05:00 | 40.77% | Good |
| 01:00 | 38.72% | Good |
| 22:00 | 38.83% | Good |
| 00:00 | 37.20% | Good |
| 23:00 | 37.25% | Good |
| 06:00 | 36.16% | Average |
| 10:00 | 34.16% | Average |
| 09:00 | 33.55% | Average |
| 11:00 | 31.21% | Average |
| 07:00 | 30.69% | Average |
| 08:00 | 30.23% | Average |
| 21:00 | 29.17% | Average |
| 20:00 | 25.40% | Below Avg |
| 12:00 | 23.92% | Below Avg |
| 18:00 | 17.57% | Poor |
| 17:00 | 16.68% | Poor |
| 16:00 | 15.71% | Poor |
| 19:00 | 15.35% | Poor |
| 13:00 | 14.96% | Worst |
| 15:00 | 13.48% | Worst |
| 14:00 | 11.51% | Worst |

### Time Summary

- **Best Window:** 02:00-05:00 (Pre-market / Overnight) - 40-45% rate
- **Good Window:** 22:00-01:00 (Evening session) - 37-39% rate
- **Poor Window:** 13:00-16:00 (Afternoon) - 11-16% rate

---

## Strategic Implications

Based on this inverse analysis, the statistical "DNA" of a winning MNQ trade reveals:

### Entry Criteria (High-Probability Filter)

1. **Price BELOW EMA200** - The strongest signal; look for contrarian entries when price is below the long-term trend
2. **After consecutive RED candles** - Selling exhaustion creates the snap-back opportunity
3. **Price stretched BELOW VWAP** - Mean-reversion setup; price returns to fair value
4. **Lower volatility environment** - Enables tighter risk management
5. **Time filter: 02:00-05:00** - Highest probability window

### What DOESN'T Matter

- **RSI** - Only 12.5% divergence; not a strong differentiator
- **Volume** - Only 7.8% divergence; volume spikes are not required

### Recommended Trading Approach

1. **Primary Filter:** Price below EMA200 AND stretched below VWAP
2. **Confirmation:** After 2+ consecutive red candles
3. **Time Filter:** Prioritize overnight/pre-market (02:00-05:00)
4. **Avoid:** 13:00-16:00 window (lowest probability)
5. **Target:** +40 points
6. **Stop:** 12 points

---

## Files Generated

| File | Description |
|------|-------------|
| `inverse_analysis_golden_trades.py` | Analysis script |
| `INVERSE_ANALYSIS_GOLDEN_TRADES.md` | This report |
| `golden_trades_analysis.csv` | Full dataset with features and Target labels |

---

*Generated by Magellan Quant Research - Inverse Analysis Module*  
*Analysis Date: 2026-01-30*
