Synthesis_Chad_G 

# Top 3 Small-Cap Momentum Scalping Strategies  
**Consensus Build-Out with Expert-Derived Parameter Ranges**

This document consolidates the **three most viable small-cap momentum strategies** based on overlap, robustness, and live-trading survivability across all expert inputs (system architect + agents Dee S., Gem Ni, Marina G).

The focus is **production-grade algorithmic deployment**, not theoretical elegance.

---

## Strategy 1: VWAP Reclaim / Washout Reversal  
**Tier:** Core / Highest Robustness  
**Type:** Mean Reversion → Momentum Shift  
**Market:** Small-cap equities ($1–$20), high RVOL, intraday movers

### Core Thesis
VWAP acts as a **liquidity magnet and regime separator**.  
Flushes below VWAP in strong names often represent **forced selling**, not trend failure.

### Core Logic
- Stock is **up ≥ 15–20% on the day**
- Price flushes below VWAP with speed
- Flush candle shows **absorption characteristics**
- Entry occurs on **reclaim and hold of VWAP**

### Entry Conditions
- Price deviation below VWAP ≥ `DEV_ATR * ATR`
- Flush candle:
  - Bottom wick ratio ≥ `WICK_RATIO_MIN`
  - Volume ≥ `FLUSH_VOL_MULT` × recent avg
- LONG on:
  - Close back above VWAP
  - OR reclaim + hold for `HOLD_BARS`

### Exit Rules
- **Stop Loss:** Below flush low − `STOP_ATR * ATR`
- **Take Profit Targets:**
  - TP1: VWAP → Mid-range
  - TP2: High of Day (HOD)
- **Time Stop:** Exit if VWAP fails again or stagnates

### Trailing Stop
- Primary: VWAP close violation
- Secondary (post-HOD):  
  `Highest_Close − TRAIL_ATR * ATR`

### Pyramiding
- Allowed only **after net risk reduction**
- Add on:
  - First higher low above VWAP
  - 20-SMA reclaim (optional)

### Scaling Out
- 30–40% into VWAP reaction
- 30–40% into HOD
- Runner trails

### Consensus Parameter Ranges
| Parameter | Suggested Range |
|--------|----------------|
| `DEV_ATR` | 0.7 – 1.2 |
| `WICK_RATIO_MIN` | 0.35 – 0.45 |
| `FLUSH_VOL_MULT` | 1.4 – 2.0 |
| `STOP_ATR` | 0.4 – 0.6 |
| `HOLD_BARS` | 1 – 3 (1-min) |
| `TRAIL_ATR` | 1.0 – 1.2 |
| `MAX_HOLD_MINUTES` | 20 – 40 |
| `MAX_ADDS` | 1 |

---

## Strategy 2: First Pullback After Breakout (FPB)  
**Tier:** Core / Best Risk-Adjusted Momentum Entry  
**Type:** Breakout → Structured Continuation  
**Market:** Small-cap equities ($1–$20), gappers, strong catalysts

### Core Thesis
Avoid chasing emotional breakouts.  
The **first orderly pullback** after a valid breakout provides the **cleanest R-multiple**.

### Core Logic
- Valid breakout above:
  - ORH, PMH, HOD, or flat-top resistance
- Pullback is **shallow, controlled, and low-volume**
- Entry on reclaim of pullback pivot

### Entry Conditions
- Breakout confirmed with:
  - Volume ≥ `BREAK_VOL_MULT`
  - Price above VWAP
- Pullback:
  - Depth ≤ `MAX_PB_ATR * ATR`
  - Retrace ≤ `MAX_RETRACE_RATIO`
- LONG on:
  - Break of pullback high
  - Volume expansion

### Exit Rules
- **Stop Loss:** Below pullback low or breakout level − cushion
- **Take Profit:**
  - TP1: 1R
  - TP2: 2R or measured move
- **Time Stop:** No continuation within window

### Trailing Stop
- Initial: Higher-low trail
- After `TRAIL_START_R`: ATR-based

### Pyramiding
- One add max
- Only after:
  - Entry reaches ≥ `ADD_MIN_R`
  - Stop on core position moved to reduce risk

### Scaling Out
- 35–40% at 1R
- 25–30% at 2R
- Runner trails

### Consensus Parameter Ranges
| Parameter | Suggested Range |
|--------|----------------|
| `BREAK_VOL_MULT` | 1.5 – 2.5 |
| `MAX_PB_ATR` | 0.8 – 1.2 |
| `MAX_RETRACE_RATIO` | 0.30 – 0.50 |
| `STOP_ATR` | 0.35 – 0.50 |
| `TRAIL_START_R` | 1.2 – 1.5 |
| `TRAIL_ATR` | 1.0 – 1.2 |
| `ADD_MIN_R` | 0.7 – 1.0 |
| `MAX_ADDS` | 1 |

---

## Strategy 3: Micro Pullback Continuation  
**Tier:** Core / High Frequency Momentum Scalp  
**Type:** Trend Continuation  
**Market:** Small-cap equities ($1–$20), sustained intraday trends

### Core Thesis
Strong trends reward **repeated shallow pullbacks**, not prediction.

### Core Logic
- Stock in confirmed intraday uptrend
- Price above VWAP and fast EMAs
- Shallow pullback into dynamic support
- Entry on momentum re-engagement

### Entry Conditions
- Trend filter:
  - Price > VWAP
  - EMA_fast > EMA_slow
- Pullback:
  - Depth ≤ `MAX_PULLBACK_ATR`
  - Volume contraction
- LONG on:
  - Break of reversal candle high
  - Volume ≥ `PB_REV_VOL_MULT`

### Exit Rules
- **Stop Loss:** Below pullback low or `STOP_ATR * ATR`
- **Take Profit:** 1R → 2R scalp
- **Time Stop:** Tight; exit stagnation

### Trailing Stop
- Primary: Last higher low
- Secondary: EMA_fast − `EMA_TRAIL_ATR * ATR`

### Pyramiding
- Allowed in strong trends
- Max 2 adds
- Only while volatility is **contracting**, not expanding

### Scaling Out
- 40–50% at 1R
- 25–30% at 2R
- Runner trails tightly

### Consensus Parameter Ranges
| Parameter | Suggested Range |
|--------|----------------|
| `EMA_FAST` | 8 – 9 |
| `EMA_SLOW` | 20 – 21 |
| `MAX_PULLBACK_ATR` | 0.6 – 0.9 |
| `PB_REV_VOL_MULT` | 1.2 – 1.5 |
| `STOP_ATR` | 0.4 – 0.5 |
| `EMA_TRAIL_ATR` | 0.6 – 0.8 |
| `MAX_HOLD_MINUTES` | 10 – 20 |
| `MAX_ADDS` | 2 |

---

## Global Notes (Critical)
- All parameters must be **ATR-normalized**
- Pyramiding only allowed when **net risk decreases**
- Regime filters (time-of-day, RVOL, spread) are mandatory
- Time stops are **non-negotiable**

These three strategies form a **complete, non-redundant core** capable of:
- Trend capture
- Mean-reversion exploitation
- Scalability across volatility regimes

Everything else is optional seasoning.
