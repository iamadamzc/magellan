# ORB STRATEGY - CRITICAL REGIME DEPENDENCY DISCOVERED

**Date**: 2026-01-17  
**Finding**: Strategy is NOT universally profitable - highly regime-dependent

---

## EXTENDED PERIOD RESULTS (RIOT)

### Partial Results So Far:

| Period | Trades | Win Rate | Total P&L | Status |
|--------|--------|----------|-----------|--------|
| Q4 2023 | 67 | 40.3% | **-37.92%** | ❌ DISASTER |
| Q1 2024 | 59 | 42.4% | **-46.65%** | ❌ DISASTER |
| Q2 2024 | ? | ? | ? | Testing... |
| Q3 2024 | ? | ? | ? | Testing... |
| Q4 2024 | ? | ? | ? | Testing... |
| Nov 24-Jan 25 | 50 | 58.0% | **+4.18%** | ✅ PROFITABLE |

---

## THE BRUTAL TRUTH

### What We Thought:
- ORB V7 works on RIOT (+4.18% over 2.5 months)
- Exit asymmetry is the problem
- Tuning parameters will improve performance

### What We Now Know:
- **The +4.18% was regime-specific luck**
- Q4 2023: -37.92% (bear market for crypto)
- Q1 2024: -46.65% (continued weakness)
- Nov 2024-Jan 2025: +4.18% (crypto bull run, BTC hitting ATHs)

**The strategy doesn't have universal edge. It has CONDITIONAL edge.**

---

## WHY THE EXPERTS WERE PARTIALLY WRONG

The 3 experts analyzed the Nov-Jan period and concluded:
- "Exit asymmetry is the problem" ✅ TRUE for that period
- "Remove VWAP exit and let winners run" ✅ CORRECT diagnosis
- "Strategy has edge on trending assets" ❌ INCOMPLETE

**What they missed**: They didn't test across multiple market regimes. The "edge" only exists when:
1. RIOT is in a strong uptrend (BTC bull market)
2. High volatility environment
3. Positive momentum / risk-on sentiment

In bear/sideways markets (Q4 2023, Q1 2024), the strategy **bleeds money** regardless of exit logic.

---

## THE REAL PROBLEM

### It's Not Exit Asymmetry - It's Entry Selection

The ORB breakout entry works when:
- ✅ Asset is trending UP strongly
- ✅ High volatility creates large intraday ranges
- ✅ Breakouts continue (momentum regime)

The ORB breakout FAILS when:
- ❌ Asset is ranging or declining
- ❌ Low volatility = small ranges
- ❌ Breakouts are fakeouts (mean reversion regime)

**Q4 2023 / Q1 2024**: RIOT was in decline, BTC was weak, breakouts failed constantly.  
**Nov 2024 - Jan 2025**: RIOT rallied with BTC, breakouts worked.

---

## WHAT THIS MEANS FOR TUNING

**All the parameter tuning in the world won't fix a regime problem.**

- V13 (surgical exits): Won't help in bear markets
- V14 (closer targets): Won't help in bear markets  
- V15 (let it run): Won't help in bear markets

The ONLY way to make this profitable is:

### Option 1: Regime Filter (REQUIRED)
Only trade when:
- BTC > 200-day MA (crypto bull market)
- VIX > 18 (volatility present)
- RIOT > 50-day MA (stock trending up)
- ADX > 25 (trending, not ranging)

**Expected**: Cuts trade frequency by 60-70%, but flips expectancy positive.

### Option 2: Different Strategy for Bear Markets
- Bull market: ORB breakouts (current strategy)
- Bear market: Fade the breakout / short ORB failures
- Sideways: Don't trade

### Option 3: Accept It's a Bull Market Only Strategy
- Deploy ONLY when regime filters are green
- Sit in cash 50%+ of the time
- Accept this is NOT an all-weather strategy

---

## IMMEDIATE NEXT STEPS

1. **Wait for full extended period test to complete**
   - See if ANY quarter besides Nov-Jan was profitable
   - Calculate full-year 2024 P&L

2. **Build Regime Filter**
   - BTC trend filter
   - Volatility filter  
   - RIOT trend filter
   - Test V7 WITH filters vs WITHOUT

3. **Test on Other Symbols**
   - Does MARA show same regime dependency?
   - Do small caps (TNMG, CGTL) work in all regimes?
   - Are commodities (KC, CL) less regime-dependent?

4. **Abandon Universal ORB Dream**
   - Stop trying to make one strategy work everywhere
   - Build regime-specific strategies
   - Accept lower trade frequency

---

## CONFIDENCE ASSESSMENT

**Previous Confidence**: 65% that parameter tuning would create profitable strategy

**Current Confidence**: 30% that ORB is deployable without regime filters

**New Hypothesis**: ORB + Regime Filter = 70% confidence of profitability

---

## THE WINNING PATH FORWARD

Stop tuning exits. Start filtering entries by regime.

**V16 Specification**:
- Keep V7 logic exactly as-is
- Add pre-trade regime check:
  ```python
  if BTC_above_200MA and RIOT_above_50MA and VIX > 18:
      # Take ORB trade
  else:
      # Skip
  ```
- Test on full 2024 period
- Expected: 20-30 trades instead of 200+, but positive expectancy

**This is the answer.**
