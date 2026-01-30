# MIDAS Protocol: Decision Tree Rule Extraction

## Executive Summary

**Objective:** Find sub-conditions within the Golden Window that push Win Rate above 60%.

**Base Win Rate (02:00-06:00 UTC):** 39.97%

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Golden Window | 02:00 - 06:00 UTC |
| Reward Target | +40 points |
| Risk Limit | 12 points |
| Forward Window | 30 minutes |
| Decision Tree Depth | 4 |
| Training Samples | 309,877 |

---

## Features Used (Physics)

| Feature | Description |
|---------|-------------|
| **Dist_EMA200** | Close - EMA(200). Rubber band stretch from trend |
| **Wick_Ratio** | (Close - Low) / (High - Low). Buyer absorption (1.0 = Hammer) |
| **Velocity_5m** | Close - Close(5 bars ago). Momentum speed |
| **Consecutive_Reds** | Count of consecutive red candles |
| **ATR_Ratio** | ATR / Avg_ATR(50). Volatility regime |

---

## Decision Tree Structure

```
|--- Velocity_5m <= 10.88
|   |--- Dist_EMA200 <= 220.88
|   |   |--- ATR_Ratio <= 0.50
|   |   |   |--- ATR_Ratio <= 0.06
|   |   |   |   |--- class: 0 (26.8% win rate)
|   |   |   |--- ATR_Ratio > 0.06
|   |   |   |   |--- class: 1 (57.7% win rate) ***
|   |   |--- ATR_Ratio > 0.50
|   |   |   |--- Velocity_5m <= -67.38
|   |   |   |   |--- class: 1 (60.4% win rate) ***
|   |   |   |--- Velocity_5m > -67.38
|   |   |   |   |--- class: 0 (43.2% win rate)
...
```

---

## High-Probability Setups Discovered

### ⭐ SETUP #1: Win Rate = 60.4% (+20.4% improvement)

| Metric | Value |
|--------|-------|
| **Win Rate** | **60.4%** |
| Samples | 23,763 |
| Wins | 14,362 |
| **Improvement** | +20.4% over baseline |

**Rules (If/Then Logic):**
1. `Velocity_5m <= 10.88` (not rallying fast)
2. `Dist_EMA200 <= 220.88` (not too far above trend)
3. `ATR_Ratio > 0.50` (moderate volatility)
4. `Velocity_5m <= -67.38` (crashing fast)

**Plain English:**
> "When price is CRASHING FAST (velocity < -67 pts in 5 mins), close to or below EMA200, with moderate volatility — **Win Rate = 60.4%**"

**Bot Logic:**
```python
def setup_1_crash_reversal(bar):
    return (
        bar['Velocity_5m'] <= -67.38 and      # Crashing fast
        bar['Dist_EMA200'] <= 220.88 and      # Near/below trend
        bar['ATR_Ratio'] > 0.50               # Moderate volatility
    )
```

---

### ⭐ SETUP #2: Win Rate = 57.7% (+17.7% improvement)

| Metric | Value |
|--------|-------|
| **Win Rate** | **57.7%** |
| Samples | 54,051 |
| Wins | 31,178 |
| **Improvement** | +17.7% over baseline |

**Rules (If/Then Logic):**
1. `Velocity_5m <= 10.88` (not rallying)
2. `Dist_EMA200 <= 220.88` (near/below trend)
3. `ATR_Ratio <= 0.50` (LOW volatility)
4. `ATR_Ratio > 0.06` (not dead quiet)

**Plain English:**
> "When price is stable or drifting down, close to EMA200, in a QUIET environment (low ATR but not dead) — **Win Rate = 57.7%**"

**Bot Logic:**
```python
def setup_2_quiet_mean_reversion(bar):
    return (
        bar['Velocity_5m'] <= 10.88 and       # Not rallying
        bar['Dist_EMA200'] <= 220.88 and      # Near/below trend
        0.06 < bar['ATR_Ratio'] <= 0.50       # Quiet but not dead
    )
```

---

## Summary: The Two Winning Patterns

| Setup | Description | Win Rate | Samples | Key Condition |
|-------|-------------|----------|---------|---------------|
| **#1** | Crash Reversal | **60.4%** | 23,763 | Fast crash (Vel < -67) |
| **#2** | Quiet Drift | **57.7%** | 54,051 | Low volatility (ATR < 0.5) |

---

## Leaf Analysis (All Nodes)

| Leaf | Samples | Wins | Win Rate | Status |
|------|---------|------|----------|--------|
| **7** | 23,763 | 14,362 | **60.4%** | ⭐ BEST |
| **5** | 54,051 | 31,178 | **57.7%** | ⭐ GOOD |
| 8 | 160,381 | 69,218 | 43.2% | Base |
| 20 | 2,609 | 981 | 37.6% | Below avg |
| 11 | 9,229 | 3,426 | 37.1% | Below avg |
| 4 | 3,705 | 993 | 26.8% | Poor |
| 19 | 5,995 | 1,411 | 23.5% | Poor |
| 23 | 112 | 24 | 21.4% | Poor |
| 12 | 7,841 | 1,519 | 19.4% | Poor |
| 26 | 982 | 139 | 14.2% | Avoid |
| 29 | 384 | 37 | 9.6% | Avoid |
| 15 | 3,342 | 308 | 9.2% | Avoid |
| 22 | 690 | 49 | 7.1% | Avoid |
| 27 | 683 | 19 | 2.8% | Avoid |
| 14 | 4,500 | 63 | 1.4% | Avoid |
| **30** | 31,610 | 143 | **0.5%** | ❌ WORST |

---

## Combined Bot Entry Logic

```python
def check_midas_entry(bar):
    """
    MIDAS Protocol Entry Filter
    Only enter during 02:00-06:00 UTC when conditions match.
    """
    
    # Time filter (must be in Golden Window)
    if not (2 <= bar['hour'] < 6):
        return False
    
    # SETUP #1: Crash Reversal (60.4% win rate)
    if (bar['Velocity_5m'] <= -67.38 and
        bar['Dist_EMA200'] <= 220.88 and
        bar['ATR_Ratio'] > 0.50):
        return True
    
    # SETUP #2: Quiet Mean Reversion (57.7% win rate)
    if (bar['Velocity_5m'] <= 10.88 and
        bar['Dist_EMA200'] <= 220.88 and
        0.06 < bar['ATR_Ratio'] <= 0.50):
        return True
    
    return False
```

---

## What To AVOID (Anti-Patterns)

**Leaf #30: 0.5% Win Rate (31,610 samples)**

These conditions produce almost NO winners:
- `Velocity_5m > 18.38` (strong rally)
- `Wick_Ratio > 0.95` (doji/hammer at top)

**Plain English:**
> "When price is rallying fast and the bar closes near its high — 99.5% of trades LOSE. Do NOT enter longs here."

---

## Key Insights

1. **CRASH = OPPORTUNITY**: The best setup (#1, 60.4%) occurs when price is crashing fast (-67+ pts in 5 mins). The "snap back" is strong.

2. **QUIET = SAFE**: The second-best setup (#2, 57.7%) occurs in low-volatility environments. Less noise = cleaner signals.

3. **RALLIES = DANGER**: When price is already rallying (Velocity > 18), win rate drops to near zero.

4. **EMA200 is the anchor**: Both winning setups require price to be within 220 pts of EMA200. Don't chase extended moves.

---

## Implementation Checklist

- [ ] Add `Velocity_5m` calculation to live data feed
- [ ] Add `ATR_Ratio` (ATR / 50-period avg ATR)
- [ ] Add `Dist_EMA200` calculation
- [ ] Implement time filter (02:00-06:00 UTC only)
- [ ] Code the two entry conditions
- [ ] Backtest with out-of-sample data (2025-2026)
- [ ] Paper trade for validation

---

*Generated by Magellan Quant Research - Midas Protocol*  
*Analysis Date: 2026-01-30*
