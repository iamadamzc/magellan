# ORB Strategy - Expert Consultation Brief

## Executive Summary

We've developed and tested 12 versions of an Opening Range Breakout (ORB) strategy across 87 symbols over 2.5 months (Nov 2024 - Jan 2025). We've encountered a **mathematical paradox** that defies conventional strategy optimization:

**Multiple symbols achieve 55-61% win rates yet remain unprofitable.**

We need expert insight on the root cause and potential solutions.

---

## The Strategy (V7 - Best Performing)

### Core Logic
1. **Opening Range (OR)**: First 10 minutes (9:30-9:40 AM)
2. **Entry**: Breakout above OR high with:
   - 1.8x volume spike
   - Pullback to within 0.15 ATR of OR high
   - Price above VWAP
   - Reclaim of OR high
3. **Stop Loss**: OR low - 0.4 ATR (~1.0-1.5% typically)
4. **Exits**:
   - Breakeven trigger @ 0.5R
   - Scale 50% @ 1.3R (rarely hit)
   - Trail remaining 50% with 0.6 ATR
   - VWAP loss exit after breakeven
   - EOD (3:55 PM)

### Key Parameters
```python
OR_MINUTES = 10
VOL_MULT = 1.8
PULLBACK_ATR = 0.15
HARD_STOP_ATR = 0.4
BREAKEVEN_TRIGGER_R = 0.5
SCALE_13R_PCT = 0.50
TRAIL_ATR = 0.6
```

---

## Test Results - The Paradox

### Universe Test (87 Symbols)
- **Period**: Nov 1, 2024 - Jan 17, 2025
- **Timeframe**: 1-minute bars
- **Winners**: 14 symbols (16%)
- **Losers**: 73 symbols (84%)

### Top Winners
| Symbol | Trades | Win% | Total P&L | Asset Class |
|--------|--------|------|-----------|-------------|
| TNMG | 4 | 50.0% | **+65.04%** | Small Cap |
| PL | 1 | 100.0% | +8.26% | Futures (Platinum) |
| CGTL | 7 | 57.1% | +6.82% | Small Cap |
| KC | 6 | 66.7% | +4.83% | Futures (Coffee) |
| **RIOT** | 50 | 58.0% | **+4.18%** | Crypto Stock |

### The Paradox Symbols (High Win%, Negative P&L)

**V10 Results (0.7R target instead of 1.3R):**

| Symbol | Trades | Win Rate | Avg P&L | Total P&L | Status |
|--------|--------|----------|---------|-----------|--------|
| RIOT | 54 | **61.1%** | +0.064% | +3.44% | ✅ Profitable |
| PLTR | 62 | **61.3%** | -0.133% | -8.26% | ❌ Losing |
| NVDA | 44 | **59.1%** | -0.206% | -9.06% | ❌ Losing |
| COIN | 61 | **59.0%** | -0.190% | -11.56% | ❌ Losing |
| IREN | 66 | **57.6%** | -0.339% | -22.37% | ❌ Losing |
| SOFI | 67 | **56.7%** | -0.179% | -11.98% | ❌ Losing |
| HOOD | 66 | **56.1%** | -0.167% | -11.00% | ❌ Losing |
| MARA | 51 | **52.9%** | -0.267% | -13.62% | ❌ Losing |
| MSTR | 58 | **53.4%** | -0.493% | -28.59% | ❌ Losing |

**10 out of 16 symbols have 52%+ win rates but are LOSING money.**

---

## Optimization Journey

### Versions Tested

| Version | Change | RIOT Result | Paradox Rescue? |
|---------|--------|-------------|-----------------|
| **V7** | Baseline (1.3R target) | +4.18% (50 trades, 58% win) | N/A - Baseline |
| **V8** | No pullback entry | -14.50% (260 trades, 43% win) | ❌ Catastrophic |
| V9 | 2-bar confirmation | -13.17% (242 trades, 44% win) | ❌ No help |
| **V10** | 0.7R target (surgical) | +3.44% (54 trades, 61% win) | ❌ Paradox persists |
| V11 | Tight stop (OR low) | -5.30% (57 trades, 58% win) | ❌ Worse |
| V12 | No VWAP loss, wide trail | -0.26% (54 trades, 61% win) | ❌ Still negative |

### Key Findings

1. **Pullback entry is CRITICAL** - Removing it increased trades 5x and destroyed performance
2. **Lower target helped** - 0.7R vs 1.3R increased win rate but didn't fix paradox
3. **Tighter stop failed** - Removed buffer, made RIOT unprofitable
4. **Removing exits failed** - No VWAP loss, wider trail → still negative

---

## The Mathematical Impossibility

### The Physics of Win Rate vs P&L

For a 59% win rate to be BREAKEVEN:
```
Avg Winner / Avg Loser = (1 - 0.59) / 0.59 = 0.695
```

**Paradox symbols have Avg Winner < 0.69 × Avg Loser**

This means **losers are 44% BIGGER than winners** despite 59% hit rate!

### Hypothesis on Cause

**Friction Costs:**
- Commission: 0.125% per trade
- 60 trades × 0.125% = **-7.5% drag**
- If gross P&L is +5%, net = -2.5%

**Asymmetric Exit Behavior:**
- Winners: Scale at 0.7R (~0.5%), VWAP loss cuts runners
- Losers: Run to full stop (~1.0-1.5%)
- Result: Small winners, full losers

### Exit Breakdown Analysis (V7)

**Across paradox symbols:**
- **Stops**: 60-70% of exits → Full loss
- **EOD**: 20-30% of exits → Mixed (mostly small winners)
- **Scales (1.3R)**: <5% of exits → Rare profit takes
- **VWAP loss**: 5-10% → Cuts runners prematurely

**Most profit comes from EOD on trending days, but most trades aren't trending.**

---

## Questions for Experts

### 1. Entry Timing
**Problem**: Pullback entry works (V7) but might be entering too late to capture full move.

**Question**: Is there a better entry trigger that:
- Maintains quality filtering (not V8's chaos)
- Captures more of the initial move
- Reduces trade count but increases R per trade?

**Ideas to evaluate:**
- Order flow confirmation (if data available)
- Multi-timeframe confirmation (5-min close above OR on 1-min data)
- Time-of-day filters (avoid first 30 min chop)
- Volatility regime filters (only trade high VIX days)

### 2. Exit Optimization
**Problem**: 61% win rate but negative P&L = winners too small, losers too big.

**Question**: How do we let winners run while cutting losers early?

**Current behavior:**
- Breakeven @ 0.5R protects capital ✓
- But then VWAP loss + tight trail cuts runners ✗
- Stops hit full size ✗

**Ideas to evaluate:**
- Remove breakeven trigger (stay at initial stop)?
- Use time-based stops (kill if not profitable after X minutes)?
- Only trail after hitting 1.0R, before that stay at BE?
- Profit target at 2.0R instead of scaling?

### 3. Universe Selection
**Problem**: Strategy works on 16% of symbols (high-volatility, trending stocks).

**Question**: Should we:
A. Keep optimizing for universal application
B. Accept asset-specificity and build better filters

**RIOT characteristics** (winner):
- Crypto mining stock (high beta)
- Float: ~200M shares
- Avg daily volume: $300M+
- Intraday trending behavior
- High correlation to BTC

**NVDA characteristics** (paradox loser):
- Large cap tech
- Highly liquid
- Mean-reverting intraday
- Algo-dominated (tight spreads)

**Ideas to evaluate:**
- Pre-filter universe by intraday trend strength?
- Only trade on high-news days?
- Volatility breakout filter (only if ATR > X)?

### 4. Timeframe
**Problem**: 1-min bars generate 50+ trades, friction eats profit.

**5-min test results:**
- RIOT: 3 trades, 66.7% win, -1.06% total
- Too few trades but cleaner signals

**Question**: 
- Is there an optimal bar size (2-min, 3-min)?
- Should we use 5-min for entry, 1-min for stops?
- Switch to daily/swing style instead of intraday?

### 5. The Friction Question
**Problem**: 0.125% × 50 trades = -6.25% drag on RIOT's +4.18%.

**Question**:
- Is the strategy fundamentally unprofitable after friction?
- Should we target 10-20 trades max per symbol?
- Can we reduce trade frequency while maintaining edge?

**Calculation:**
- RIOT gross (before friction): ~+10.43%
- After friction: +4.18%
- **60% of profit lost to friction**

---

## Data Available for Analysis

### Full Results CSVs
- `ORB_V7_FULL_UNIVERSE.csv` - 87 symbols, V7 baseline
- `v10_surgical_test.csv` - 16 symbols, V10 comparison
- `paradox_symbols.csv` - 11 high win%, negative P&L symbols

### Individual Trade Data
- Entry/exit times
- P&L per trade
- Exit type (stop, scale, VWAP loss, EOD)
- MAE/MFE per trade (available in some versions)

### Symbols Tested
- **Crypto stocks**: RIOT, MARA, CLSK, HUT, BITF, COIN, MSTR
- **Tech large caps**: NVDA, TSLA, AMD, AAPL, MSFT, GOOGL, META, AMZN
- **Meme stocks**: GME, AMC, PLTR, SOFI, LCID, RIVN
- **Small caps**: TNMG, CGTL, IBRX, RIOX, NEOV (mostly illiquid)
- **ETFs**: SPY, QQQ, IWM, sector ETFs
- **Futures**: ES, CL, GC, KC, HG, PL (limited data)

---

## Specific Expert Input Needed

### From Market Microstructure Experts:
1. Is the pullback entry optimal or should we trade initial breakout?
2. How do we detect and filter false breakouts on 1-min data?
3. Is VWAP the right intraday trend filter or should we use something else?

### From Risk Management Experts:
1. How do we size stops to match realistic profit targets?
2. Given 59% win rate, what Avg Winner/Avg Loser ratio do we need for 0.125% friction?
3. Should we use fixed R targets or adaptive trailing?

### From Statistical/Quant Experts:
1. Is this paradox (high win%, negative P&L) solvable or a sign of no edge?
2. What tests can we run to prove/disprove edge exists?
3. Is the sample size sufficient (2.5 months, 50-60 trades per symbol)?
4. Should we be using different performance metrics?

### From Execution Experts:
1. Is 0.125% realistic friction for these symbols?
2. Can we reduce friction with better routing/timing?
3. Should we use limit orders with different logic?

---

## Our Hypothesis

**The strategy has a genuine edge on trending, volatile stocks (RIOT, TNMG, commodities) but fails on mean-reverting, algo-dominated names.**

The paradox stems from:
1. **Entry timing**: Pullback catches end of move, not beginning
2. **Exit asymmetry**: Winners cut early (VWAP, trail), losers run full
3. **Friction costs**: 50+ trades per symbol = 6%+ drag
4. **Asset mismatch**: Applying trending strategy to choppy stocks

**We need expert guidance on whether to:**
- Fix the strategy (better entry/exits)
- Fix the universe (better symbol selection)
- Accept current performance and deploy on 4 winners only
- Abandon ORB entirely and try different approaches

---

## Files & Code Available

All strategy versions, test scripts, and results are in:
- `research/new_strategy_builds/strategies/` - All versions (V4-V12)
- `research/new_strategy_builds/results/` - All test results
- `test_orb_v*.py` - Test scripts for each version

**Ready to share code, data, and run any diagnostic tests suggested by experts.**

---

**Session Stats:**
- Versions tested: 12
- Symbols tested: 87  
- Total trades analyzed: 3,135
- Tokens used: 125k
- Hours invested: 4+

**We're at the edge of something but can't break through. Need fresh eyes from experts to find the missing piece.** 🎯
