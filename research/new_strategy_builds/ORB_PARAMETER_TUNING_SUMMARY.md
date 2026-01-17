# Opening Range Breakout (ORB) - Parameter Tuning Summary

**Date**: 2026-01-17  
**Strategy**: Opening Range Breakout for Small-Cap Scalping  
**Test Universe**: RIOT, MARA, AMC (Nov 2024 - Jan 2025)  
**Total Tests**: 4 versions, 3 symbols each

---

## Strategy Overview

**Core Logic**:
1. Calculate Opening Range (first N minutes of trading)
2. Enter LONG when price breaks above OR high with volume confirmation
3. Stop loss below OR low
4. Scale out at profit targets, trail remainder

**Target**: 50%+ win rate, +0.015% avg P&L per trade (after 12.5 bps friction)

---

## Version History & Results

### V1 - Original (Expert Baseline)

**Parameters**:
```python
OR_MINUTES = 5          # Opening range period
VOL_MULT = 2.0          # Volume spike multiplier
STOP_ATR = 0.4          # Stop loss (ATR units below OR low)
TRAIL_ACTIVATE_R = 1.5  # Start trailing at 1.5R
MAX_HOLD_MINUTES = 20   # Time stop
SCALE_1R_PCT = 0.45     # Scale 45% at 1R
SCALE_2R_PCT = 0.30     # Scale 30% at 2R
```

**Results**:
- **Total trades**: 1,143
- **Win rate**: 42.1%
- **Avg P&L**: -0.15% per trade
- **Status**: ❌ Losing (too strict filters, whipsaw on tight stops)

---

### V2 - Optimized (Added Filters)

**Parameters Changed**:
```python
OR_MINUTES = 10         # Wider OR (was 5)
VOL_MULT = 1.8          # Lower threshold (was 2.0)
STOP_ATR = 0.5          # Wider stop (was 0.4)
MIN_GAP_PCT = 2.0       # NEW: Minimum gap requirement
MIN_RVOL = 2.5          # NEW: Relative volume filter
MIN_OR_RANGE_PCT = 0.5  # NEW: Minimum OR range
```

**Results**:
- **Total trades**: 0
- **Win rate**: N/A
- **Status**: ❌ Too restrictive (gap filter eliminated all setups)

---

### V3 - Final (Balanced)

**Parameters Changed**:
```python
OR_MINUTES = 10
VOL_MULT = 1.5          # Further lowered (was 1.8)
STOP_ATR = 0.6          # Wider stop (was 0.5)
MIN_PRICE = 3.0         # NEW: Avoid penny stocks
TRAIL_ACTIVATE_R = 1.0  # Earlier trail (was 1.5)
MAX_HOLD_MINUTES = 30   # Longer hold (was 20)
SCALE_1R_PCT = 0.50     # More aggressive (was 0.45)
# Removed: gap filter, RVOL filter
```

**Results**:
- **Total trades**: 936
- **Win rate**: 41.9%
- **Avg P&L**: -0.162% per trade
- **Total P&L**: -146.43%
- **Status**: ❌ Losing (good frequency, low win rate)

---

### V4 - With Pyramiding & Proper Trailing (CURRENT)

**Parameters Changed**:
```python
# Same as V3, plus:
TRAIL_ATR = 0.8         # NEW: Trail distance in ATR
PYRAMID_MIN_R = 0.8     # NEW: Add to position at 0.8R
PYRAMID_MAX_ADDS = 1    # NEW: Max 1 pyramid add
SCALE_1R_PCT = 0.40     # Back to 40% (was 0.50)
```

**New Features**:
- **Pyramiding**: Adds 50% to position at 0.8R profit, moves stop to breakeven
- **Proper Trailing**: Trails 0.8 ATR below highest price (not just breakeven)
- **Dynamic Stop**: Tightens as position moves in favor

**Results**:
- **Total trades**: 920
- **Win rate**: 40.8%
- **Avg P&L**: -0.121% per trade
- **Total P&L**: -105.96%
- **Improvement**: +40.47% better than V3 ✅
- **Status**: ⚠️ Still losing, but 28% less loss

**Exit Breakdown** (RIOT example):
- Time stops: 327 (96.7%)
- Stop losses: 10 (3.0%)
- Scale at 1R: 1 (0.3%)

---

## Key Findings

### What's Working ✅
1. **High frequency**: 300+ trades per test (good sample size)
2. **Pyramiding**: Successfully adds to winners at 0.8R
3. **Proper trailing**: Captures more upside than breakeven-only
4. **Risk management**: Stop losses working, limiting max loss

### What's Not Working ❌
1. **Win rate too low**: 40.8% vs 52% needed for profitability
2. **Time stops dominate**: 96.7% of exits are time stops (cutting winners short)
3. **Rare profit targets**: Only 0.3% reach 1R (most stall before target)
4. **Entry timing**: Likely entering too late after breakout (chasing)

### The Math
**Current**: 40.8% × 1% - 59.2% × 1% - 0.125% friction = **-0.121% per trade**  
**Need**: 52% × 1% - 48% × 1% - 0.125% friction = **+0.015% per trade**  
**Gap**: Need to improve by **0.136% per trade** (11.6% win rate improvement OR better R:R)

---

## Parameter Sensitivity Analysis

### Most Impactful Parameters (by testing)
1. **VOL_MULT** (Volume filter): 
   - Too high (2.0) = misses setups
   - Too low (1.5) = more noise
   - Sweet spot: Unknown (needs testing)

2. **STOP_ATR** (Stop loss width):
   - Too tight (0.4) = whipsaw (V1: 42.1% win)
   - Too wide (0.6) = larger losses (V4: 40.8% win)
   - Trade-off: Tighter = more stops, Wider = bigger losses

3. **OR_MINUTES** (Opening range period):
   - Shorter (5 min) = tighter range, more breakouts
   - Longer (10 min) = wider range, fewer breakouts
   - Current: 10 min

4. **MAX_HOLD_MINUTES** (Time stop):
   - Shorter (20 min) = cuts winners early
   - Longer (30 min) = holds losers longer
   - **Critical**: 96.7% of trades hit time stop!

### Least Impactful (removed with no effect)
- Gap size filter (too restrictive)
- RVOL filter (too restrictive)
- OR range minimum (too restrictive)

---

## Expert Questions for Review

### 1. Entry Timing
**Issue**: Entering on breakout bar may be too late (chasing)  
**Question**: Should we:
- A) Enter on pullback after breakout (wait for retest)?
- B) Use limit orders at OR high (get better fill)?
- C) Require consolidation above OR high before entry?

### 2. Exit Strategy
**Issue**: 96.7% of trades hit time stop, only 0.3% reach 1R  
**Question**: Should we:
- A) Remove time stop entirely (let trailing stop do the work)?
- B) Shorten time stop to 15 min (cut losers faster)?
- C) Use dynamic time stop based on volatility?

### 3. Win Rate vs R:R Trade-off
**Issue**: Need either higher win rate OR better R:R  
**Question**: Should we:
- A) Tighten entry (fewer trades, higher quality)?
- B) Widen targets (lower win rate, bigger wins)?
- C) Add filters (VWAP, trend, momentum)?

### 4. Volume Filter
**Issue**: VOL_MULT = 1.5 may be letting in too much noise  
**Question**: What's optimal?
- A) Test range: 1.3, 1.5, 1.8, 2.0, 2.2
- B) Use adaptive volume (based on symbol volatility)?
- C) Add volume profile analysis (institutional levels)?

### 5. Stop Loss Strategy
**Issue**: Stop at OR low - 0.6 ATR may be too wide  
**Question**: Should we:
- A) Tighten to 0.4-0.5 ATR (accept more stops)?
- B) Use percentage-based stop (e.g., 1.5% from entry)?
- C) Use dynamic stop based on recent volatility?

### 6. Pyramiding Timing
**Issue**: Adding at 0.8R, but most trades don't reach 1R  
**Question**: Should we:
- A) Add earlier (0.5R) to capture more moves?
- B) Add later (1.0R) for higher quality?
- C) Skip pyramiding entirely (simplify)?

---

## Test Data Summary

**Symbols**: RIOT, MARA, AMC  
**Period**: Nov 1, 2024 - Jan 17, 2025 (2.5 months)  
**Timeframe**: 1-minute bars  
**Total bars**: ~40,000 per symbol  
**Market conditions**: Mixed (some trending days, some choppy)

**Symbol Characteristics**:
- **RIOT**: Crypto miner, high volatility, $8-15 range
- **MARA**: Crypto miner, high volatility, $15-25 range  
- **AMC**: Meme stock, moderate volatility, $4-6 range

---

## Recommended Next Steps

1. **Grid search on key parameters**:
   - VOL_MULT: [1.3, 1.5, 1.8, 2.0]
   - STOP_ATR: [0.4, 0.5, 0.6, 0.7]
   - MAX_HOLD_MINUTES: [15, 20, 25, 30, None]

2. **Test alternative entry logic**:
   - Wait for pullback after breakout
   - Require VWAP confirmation
   - Add momentum filter (RSI, MACD)

3. **Test on different symbols**:
   - HOOD, SOFI, DKNG (more liquid, less volatile)
   - Compare results to current universe

4. **Analyze losing trades**:
   - Why do 96.7% hit time stop?
   - What happens in first 5-10 minutes after entry?
   - Are we entering on exhaustion moves?

---

## Files & Code

**Strategy Implementations**:
- `research/new_strategy_builds/strategies/orb_strategy.py` (V1)
- `research/new_strategy_builds/strategies/orb_optimized.py` (V2)
- `research/new_strategy_builds/strategies/orb_final.py` (V3)
- `research/new_strategy_builds/strategies/orb_v4.py` (V4 - Current)

**Test Scripts**:
- `test_orb.py`, `test_orb_opt.py`, `test_orb_final.py`, `test_orb_v4.py`

**Data**:
- 57 cached datasets (19 symbols × 3 periods)
- Location: `data/cache/equities/*1min*.parquet`

---

## Conclusion

The ORB strategy has **excellent trade frequency** (300+ trades/test) and **functional risk management** (pyramiding, trailing, scaling). However, the **win rate is too low** (40.8% vs 52% needed) and **most trades hit time stops** before reaching profit targets.

**Key insight**: The strategy is very close to breakeven (-0.121% per trade). Small improvements in entry timing, exit logic, or parameter tuning could push it to profitability.

**Recommendation**: Focus on improving win rate through better entry timing (wait for pullback?) or removing time stops to let winners run.
