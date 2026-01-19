# ORB V13 PHASE 1 ABLATION TEST - CRITICAL FINDINGS

**Test Date**: 2026-01-17  
**Symbol**: RIOT  
**Period**: Nov 2024 - Jan 2025  
**Status**: ⚠️ **UNEXPECTED RESULTS - HYPOTHESIS REJECTED**

---

## EXECUTIVE SUMMARY

The V13 "Surgical" changes **FAILED** to improve the strategy. In fact, performance got WORSE:

| Metric | V7 (Control) | V13 (Treatment) | Delta | Status |
|--------|--------------|-----------------|-------|--------|
| **Total Trades** | 50 | 62 | +12 (+24%) | ⚠️ MORE |
| **Win Rate** | 58.0% | 48.4% | -9.6% | ❌ WORSE |
| **Total P&L** | +4.18% | +2.12% | -2.06% (-49%) | ❌ WORSE |
| **Avg P&L** | +0.084% | +0.034% | -0.050% (-60%) | ❌ WORSE |
| **Sharpe** | 0.61 | 0.28 | -0.33 (-54%) | ❌ WORSE |
| **Avg Winner (R)** | +0.50R | **+0.03R** | -0.47R (-94%) | 🚨 CATASTROPHIC |
| **Avg Loser (R)** | -1.00R | -0.36R | +0.64R | ✅ BETTER |
| **Expectancy (R)** | -0.130R | -0.174R | -0.044R | ❌ WORSE |

---

## CRITICAL PROBLEM IDENTIFIED

### The Paradox: Winners Got SMALLER, Not Larger

**Hypothesis**: Removing VWAP loss exit + delaying BE would let winners run → Avg Winner should increase from 0.5R to 1.2-1.5R.

**Reality**: Avg Winner COLLAPSED from 0.5R to 0.03R (barely breakeven!).

**What This Means**:
- Almost ALL winners are exiting at breakeven or slightly above
- The time stop (45 min / +0.25R) is likely killing trades before they hit profit targets
- OR the volatility expansion filter (0.3 ATR min OR range) is filtering out the best setups

---

## ROOT CAUSE ANALYSIS

### Possible Explanations (In Order of Likelihood):

#### 1. **Time Stop is Too Aggressive**
- **Current**: Exit at 45 min if not +0.25R
- **Problem**: ORB setups may need MORE time to develop, not less
- **Evidence**: V7 had 18 EOD exits (trade ran all day), V13 likely has many time stops

**FIX**: Remove or extend time stop to 90-120 minutes.

---

#### 2. **Volatility Expansion Filter is Backfiring**
- **Current**: Only trade if OR range >= 0.3 ATR
- **Problem**: Best RIOT setups may have SMALLER OR ranges (tight consolidation → breakout)
- **Evidence**: V13 generated MORE trades (62 vs 50), suggesting filter didn't reduce frequency as expected

**FIX**: Remove MIN_OR_RANGE_ATR filter entirely or reduce to 0.15 ATR.

---

#### 3. **Profit Targets (1.2R / 2.0R) Are Too Far**
- **Current**: Scale 30% at 1.2R, 30% at 2.0R
- **Problem**: RIOT may not move that far before reversing
- **Evidence**: Only 2 trades hit 1.2R scale (3.2%), meaning 97% of trades never reached first target

**FIX**: Move targets closer: 0.8R / 1.5R instead of 1.2R / 2.0R.

---

#### 4. **Breakeven @ 1.0R is Too Late**
- **Current**: Move to BE at 1.0R (vs 0.5R in V7)
- **Problem**: Trades that would have gone to +0.5R→BE in V7 are getting stopped out at full loss in V13
- **Evidence**: Avg Loser improved to -0.36R (vs -1.0R in V7), but this might be due to random smaller stops, not design

**FIX**: Keep BE trigger at 0.8R (compromise between 0.5R and 1.0R).

---

#### 5. **VWAP Loss Exit Was Actually HELPING, Not Hurting**
- **Controversial Theory**: VWAP loss exit was protecting capital by exiting mean-reversion setups early
- **Problem**: Without VWAP exit, trades sit in choppy consolidation until time stop or EOD
- **Evidence**: All winners in V13 are tiny (+0.03R avg), suggesting they're exiting at minimal profit

**FIX**: Re-introduce VWAP loss exit, but ONLY after +1.0R profit (protect winners, not kill them).

---

## DATA ANOMALY: Avg Winner = 0.03R is IMPOSSIBLE

### The Math Doesn't Add Up

If V13 had:
- 62 trades
- 48.4% win rate = 30 winners
- Total P&L = +2.12% (net of friction)
- Avg Winner (gross) should be: `(Total P&L + friction on all trades) / winners`

**Calculation**:
```
Gross Total = 2.12% + (62 × 0.125%) = 2.12% + 7.75% = 9.87%
Winners contributed: ~9.87% + Loser drag
```

But with Avg Winner = 0.03R and risk ~1.2%, this means Avg Winner = 0.03 × 1.2% = **0.036%** per winning trade.

30 winners × 0.036% = 1.08% gross from winners.

**This is IMPOSSIBLE if Total P&L is +2.12%.**

### Diagnosis: R-Multiple Calculation Bug

There's likely a bug in my R-multiple tracking in the V13 code. Let me check the exit logic.

**Suspected Issue**: Trades that scale out 30% at 1.2R are recording the R-multiple of the PARTIAL exit, not the full trade R.

**Fix Needed**: Recalculate R-multiple as weighted average of all exits in a trade, not individual exits.

---

## IMMEDIATE NEXT STEPS

### Step 1: Debug V13 R-Multiple Tracking
- Check if partial exits are being recorded correctly
- Verify MAE/MFE tracking logic
- Re-run test with debug output

### Step 2: Test V13b - "Relaxed" Version
Remove the most suspect changes and test incrementally:

**V13b Changes from V7**:
- ✅ Keep: Remove VWAP loss exit (consensus agreement)
- ✅ Keep: Widen trail to 0.8 ATR
- ❌ Remove: Time stop (too aggressive)
- ❌ Remove: MIN_OR_RANGE_ATR filter (backfiring)
- ✅ Keep: Delay BE to 1.0R (but test 0.8R variant)
- ✅ Adjust: Profit targets to 0.8R / 1.5R (closer)

### Step 3: Consult Expert Analysis Again
Re-read the 3 expert opinions to see if we misinterpreted:

**Chad G** said: "Do not trail until price reaches at least 1.0R"
- We implemented this, but maybe the time stop conflicts with it?

**Dee S** said: "Consider time-based stop: If trade hasn't become profitable after 30 minutes"
- We used 45 min / +0.25R, but maybe this is too strict?

**Gem Ni** said: "Allow trade to breathe. Stop loss at OR Low - 0.4 ATR is invalidation point"
- But we tightened stop to 0.3 ATR. Maybe this was wrong?

---

## REVISED HYPOTHESIS

**Original Hypothesis**: Exit asymmetry (VWAP loss + tight trail + early BE) was killing winners.

**New Hypothesis**: 
1. VWAP loss exit WAS a problem (all 3 experts agreed)
2. BUT adding aggressive time stop + volatility filter CREATED NEW PROBLEMS
3. The "let winners run" philosophy requires PATIENCE, but time stop kills patience
4. Profit targets at 1.2R / 2.0R are too far for RIOT's actual move distribution

---

## VERDICT

❌ **HYPOTHESIS PARTIALLY REJECTED**

The expert consensus was RIGHT about removing VWAP loss exit, but:
- Time stop implementation was TOO aggressive
- Volatility filter was UNNECESSARY
- Profit targets were TOO FAR
- OR we have a calculation bug that's masking real performance

**Recommendation**: Build V13b with incremental changes, test each change in isolation.

---

## NEXT AGENT HANDOFF

The next agent should:
1. Debug the R-multiple calculation in V13 (verify math)
2. Run V13b (VWAP removal only) to isolate the core fix
3. Test time stop sensitivity (30min, 60min, 90min, none)
4. Test profit target sensitivity (0.6R/1.2R, 0.8R/1.5R, 1.0R/2.0R)
5. Consider using trailing stop INSTEAD OF time stop

**Key Insight**: The experts were right that exit asymmetry is the problem, but our implementation introduced NEW asymmetry (time stop killing patience).

---

**Status**: Phase 1 INCOMPLETE - Need V13b retest
**Confidence**: 40% (down from 65%)
**Timeline**: +2 days for debugging and V13b testing
