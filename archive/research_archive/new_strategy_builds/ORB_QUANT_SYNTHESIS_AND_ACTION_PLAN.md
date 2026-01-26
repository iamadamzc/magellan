# ORB STRATEGY - QUANT EXPERT SYNTHESIS & ACTION PLAN

**Author**: Quantitative Trading Expert  
**Date**: 2026-01-17  
**Mission**: Transform ORB from 60% win rate / negative P&L to profitable deployment through targeted parameter tuning and universe specialization.

---

## EXECUTIVE SUMMARY

After reviewing the handoff document and three expert consultations (Chad G, Dee S, Gem Ni), I have identified the path to profitability. The strategy **has edge** but suffers from **exit asymmetry + friction drag**. The solution is surgical: fix exits, specialize universe, reduce trade frequency.

**Expected Outcome**: 1.5-3.0% monthly return on specialized universe (RIOT, small caps, volatile commodities) with 40-50% win rate and 2:1+ R:R ratio.

---

## PART 1: EXPERT CONSENSUS ANALYSIS

### 100% AGREEMENT (All 3 Experts)

These are non-negotiable truths about the current ORB implementation:

#### 1. **The "Paradox" is Exit Asymmetry, Not Entry Failure**
- **Chad G**: "You've built a system that's great at not being wrong for long but terrible at getting paid when right."
- **Dee S**: "VWAP loss exit + tight trailing stops are systematically truncating winners while letting losers run to full stop."
- **Gem Ni**: "Eating like a bird and pooping like an elephant—taking small, frequent profits while absorbing full-size losses."

**Diagnosis**: Average winner (~0.5R) is 50% smaller than required breakeven (0.69R at 59% win rate + friction).

#### 2. **Breakeven @ 0.5R is a Right-Tail Killer**
- **Chad G**: "BE is a right-tail killer because normal noise tags it."
- **Dee S**: "Remove breakeven trigger at 0.5R. Keep initial stop until trade reaches 1R."
- **Gem Ni**: "Moving to breakeven at 0.5R turns potential 2R winners into scratch trades."

**Verdict**: The 0.5R BE trigger must be eliminated or moved to 1.0R+.

#### 3. **VWAP Loss Exit Must Be Removed**
- **Chad G**: "Remove VWAP-loss exit after breakeven."
- **Dee S**: "Remove all discretionary exits (VWAP loss)."
- **Gem Ni**: "VWAP Loss Exit: Exits if price violates VWAP after being profitable" [kills runners].

**Verdict**: VWAP loss exit is destroying expectancy by cutting winners before they can run.

#### 4. **Strategy is Asset-Specific, Not Universal**
- **Chad G**: "ORB is not one strategy. It's two: trend continuation ORB vs liquidity sweep/fade ORB."
- **Dee S**: "Accept: This is a trending asset strategy, not universal ORB."
- **Gem Ni**: "ORB is a Volatility Expansion strategy. Large Cap Tech spends 80% of the day mean-reverting."

**Verdict**: Stop forcing continuation ORB on mean-reverting megacaps (NVDA, PLTR). Specialize on high-beta trending assets.

#### 5. **Friction @ 0.125% is Destroying Edge on High-Frequency Implementation**
- **Chad G**: "50–60 trades × 0.125% is brutal drag."
- **Dee S**: "0.125% × 50 trades = 6.25% drag destroys edge."
- **Gem Ni**: "If your average winner is 0.5%, a 0.25% round-trip cost eats 50% of your gross profit."

**Verdict**: Must reduce trade frequency or increase avg profit/trade. Current implementation is suicidal.

---

### STRONG CORRELATION (2/3 Experts Agree)

#### 1. **Time Stop is Critical**
- **Chad G**: "Pick one: if trade hasn't reached +0.25R within N minutes, exit."
- **Dee S**: "Consider time-based stop: If trade hasn't become profitable after 30 minutes, exit."

**Application**: Add time-based stop at 20-30 minutes if not +0.25R or if price < ORH.

#### 2. **Wider Trailing Stop Once Trade Proves Itself**
- **Chad G**: "Do not trail until price reaches at least 1.0R. Trail using structure, not ATR."
- **Dee S**: "Only after trade has reached 1R, trail with 1 ATR."

**Application**: No trailing until 1.0R+, then use 0.8-1.0 ATR or structural method (swing lows).

#### 3. **Partial Scaling is Acceptable (But Stop Scaling Too Early)**
- **Chad G**: "Take partial (25–50%) at +1.0R or +1.2R."
- **Dee S**: "Take 50% off at 1.3R (or 2R) and trail the rest."

**Application**: If using partials, take at 1.2-1.5R (not 1.3R currently), leave 50% for runners.

#### 4. **Higher Timeframe Bars (2-5min) Will Reduce Friction**
- **Dee S**: "Consider using 2-minute or 3-minute bars as a compromise."
- **Gem Ni**: "Switch to 2-minute or 5-minute bars (Reduces noise and trade count)."

**Application**: Test 2min and 5min bars to cut trade count by 40-60%.

#### 5. **Universe Filter: Volatility + Trend Strength**
- **Chad G**: "OR size as % of ATR, gap/catalyst proxy, RVOL threshold."
- **Dee S**: "MIN_BETA = 1.8, MIN_ATR_PERCENT = 2.0%, AVOID correlation > 0.7 to SPY."

**Application**: Pre-filter for high ATR%, beta, RVOL. Avoid SPY-correlated names.

---

### UNIQUE INSIGHTS (Single Expert, High Value)

#### From Chad G:
1. **"Don't confirm with delay; confirm with context"**
   - Market regime filter: only longs if SPY/QQQ above VWAP and rising.
   - Range expansion confirmation: entry candle closes above ORH and is wide-range bar.

2. **MAE/MFE diagnostic framework**
   - MFE distribution split by exit type (identify if VWAP/trail hits before large moves).
   - Time-to-MFE analysis (winners hit MFE in first 5-20 min, time-stop the rest).

#### From Dee S:
1. **Staggered Entry (Partial + Pullback)**
   - 50% on initial breakout, 50% on pullback to capture more of initial move + confirm.

2. **Multi-timeframe confirmation**
   - Wait for 5-minute bar to close above OR high, then enter on 1-minute pullback.

3. **Statistical validation required**
   - Bootstrap analysis to verify edge isn't random.
   - Monte Carlo simulation (10,000 runs).

#### From Gem Ni:
1. **"Instant" Breakout with Volatility Filter**
   - Enter on break of OR High if Volume > 2.0x RVOL (no pullback needed).
   - Stop at OR midpoint (tighter risk = higher R for same move).

2. **Pre-Market Catalyst Filter**
   - Only trade stocks with Gap > 2% or < -2% (stocks that gap are more likely to trend).

3. **Fixed Target Alternative**
   - Single entry, single exit: either Stop or 2.5R Target. No scaling, no trailing until near target.

---

## PART 2: ROOT CAUSE MATHEMATICAL PROOF

Let's prove why the current strategy loses money despite 59% win rate.

### Current V7 Performance Profile
- **Win Rate**: 59%
- **Avg Winner**: 0.5R (due to BE @ 0.5R + VWAP loss + tight trail)
- **Avg Loser**: 1.0R (full stop)
- **Friction**: 0.125% per trade

### Expectancy Calculation (No Friction)
```
E[R] = (Win% × Avg Win) - (Loss% × Avg Loss)
     = (0.59 × 0.5R) - (0.41 × 1.0R)
     = 0.295R - 0.41R
     = -0.115R per trade
```

### With Friction (0.10R per trade @ 1.2% stop)
```
E[R] = 0.295R - 0.41R - 0.10R
     = -0.215R per trade
```

**Result**: Even before friction, strategy is losing. Friction makes it catastrophic.

### Required Average Winner for Breakeven
```
At 59% win rate, solving for breakeven:
0.59 × Avg_Win = 0.41 × 1.0 + 0.10 (friction)
Avg_Win = 0.51 / 0.59 = 0.86R
```

**Current Avg Win**: 0.5R  
**Required Avg Win**: 0.86R  
**Gap**: **72% shortfall**

---

## PART 3: THE WINNING FORMULA

Based on expert consensus and mathematical requirements, here is the precise configuration for ORB profitability:

### V13 "SURGICAL" - Recommended Baseline

#### Entry Logic
- **Timeframe**: 5-minute bars (primary) with 1-minute execution precision
- **OR Definition**: First two 5-min bars (9:30-9:40)
- **Entry Trigger**: 
  - Price closes above ORH on 5-min bar
  - Volume > 1.8x avg (keep current)
  - RVOL > 2.0x at time of breakout
  - **NEW**: SPY/QQQ above VWAP (market regime filter)
  - **NEW**: OR range > 0.3 × ATR(14) (volatility expansion filter)

- **Entry Timing Window**: 9:40 AM - 10:15 AM (relaxed, avoids first 10-min chop)

- **Pullback Option**: 
  - **Path A (conservative)**: Wait for pullback within 0.15 ATR of ORH, then reclaim
  - **Path B (aggressive)**: Enter immediately on 5-min close above ORH if Volume > 2.5x

#### Stop Loss
- **Initial Stop**: OR Low - 0.3 ATR (slightly tighter than current 0.4 ATR)
- **Position Sizing**: Risk 1.0% of account (keep current)

#### Exit Logic - **THIS IS THE KEY**

**REMOVE ENTIRELY**:
- ❌ Breakeven @ 0.5R
- ❌ VWAP loss exit
- ❌ Scale @ 1.3R

**NEW EXIT SYSTEM** (Asymmetric Scaling):
1. **Stop moves to -0.05R** (small loss) once price hits **+1.0R** (not 0.5R)
2. **Partial Exit #1**: Take 30% at **+1.2R** (lock in profit)
3. **Partial Exit #2**: Take 30% at **+2.0R** (capture extended move)
4. **Trail Remaining 40%**: 
   - Use 0.8 ATR trail (wider than current 0.6 ATR)
   - OR use structural trail (below last two 5-min swing lows)
   - Only activate trail after +1.2R
5. **Time Stop**: Exit entire position at 45 minutes if not yet +0.25R

#### Trade Management Enhancements
- **PDH/PDL Context**: Avoid entries if breaking directly into Prior Day High (collision filter)
- **MAE/MFE Tracking**: Log on every trade for diagnostic refinement
- **Maximum Trades Per Day**: 2 (prevents overtrading, reduces friction)

---

### V14 "SPECIALIST" - Asset-Specific Universe

Same as V13, but with **strict universe filtering**:

#### Qualified Assets (Trade These)
- **Crypto Stocks**: RIOT, MARA (if passing individual testing)
- **Small Caps**: TNMG, CGTL, LCID (float < 500M, vol > $100M)
- **Volatile Commodities**: KC (Coffee), CL (Crude), PL (Platinum)
- **Financials with Volatility**: GS, JPM (only if ATR% > 2.0 on day)

#### Disqualified Assets (Never Trade)
- ❌ Large Cap Tech: NVDA, MSFT, AAPL, GOOGL, META
- ❌ Index ETFs: SPY, QQQ, IWM
- ❌ Mean-Reverting Stocks: Any with Correlation to SPY > 0.7 in first hour

#### Dynamic Daily Filter
Build a scanner that only activates ORB on symbols meeting:
- Gap > 2.0% or < -2.0% from prior close (catalyst present)
- Pre-market ATR(14) / Price > 2.5% (high relative volatility)
- Beta > 1.8
- Pre-market volume already > 30% of daily average by 9:25 AM

---

### V15 "HYBRID" - Multi-Timeframe Confirmation

For maximum edge with lowest trade frequency:

- **Signal Generation**: 5-minute bars
- **Entry Execution**: Wait for 1-minute pullback within 0.1 ATR of ORH
- **Stop Management**: 1-minute precision
- **Exit Management**: 5-minute bars (reduces whipsaw from noise)

**Effect**: Cuts trade count by ~60%, increases avg profit per trade, reduces friction to manageable levels.

---

## PART 4: TESTING & VALIDATION ROADMAP

### Phase 1: Exit Strategy Ablation (Week 1)
**Goal**: Prove that exit asymmetry is the root cause.

**Test Matrix**:
1. **Control**: V7 baseline (current losing config)
2. **Treatment A**: V7 entries + V13 exits (remove BE@0.5R, VWAP loss)
3. **Treatment B**: V7 entries + V13 exits + Time Stop @ 30min
4. **Treatment C**: V13 full (new entry + new exit)

**Test Universe**: RIOT only (highest sample size, known winner)

**Success Criteria**: Treatment A must show >50% improvement in Total P&L vs Control.

**Expected Outcome**: 
- Win rate may drop from 59% to 45-50%
- Avg Win will increase from 0.5R to 1.2-1.5R
- Expectancy flips positive

**Deliverable**: `ORB_V13_EXIT_ABLATION_RESULTS.md` with side-by-side comparison.

---

### Phase 2: Universe Specialization (Week 2)
**Goal**: Identify the 8-10 "RIOT-like" symbols that work with new exit logic.

**Test**: Run V13 on all 87 symbols with new exit system.

**Filters to Apply**:
- Minimum 20 trades per symbol (statistical threshold)
- Positive expectancy after friction
- Max Drawdown < 15%
- Sharpe Ratio > 0.8

**Expected Winners**:
- RIOT, MARA (crypto stocks)
- TNMG, CGTL (small cap volatility)
- KC, PL, CL (commodities)
- 2-3 surprise winners from testing

**Deliverable**: `ORB_V13_APPROVED_UNIVERSE.csv` with performance metrics per symbol.

---

### Phase 3: Timeframe Optimization (Week 3)
**Goal**: Reduce friction without sacrificing edge.

**Test Matrix**: Run V13 on approved universe (from Phase 2) using:
1. 1-minute bars (baseline)
2. 2-minute bars
3. 5-minute bars
4. Hybrid (5-min signal, 1-min execution)

**Success Metric**: Minimize (Friction Drag / Gross Profit) while maintaining Total Return.

**Expected Winner**: 5-minute bars or Hybrid approach.

**Deliverable**: `ORB_V13_TIMEFRAME_ANALYSIS.md`

---

### Phase 4: Walk-Forward Analysis (Week 4)
**Goal**: Validate V13 robustness out-of-sample.

**Test Design**:
- **Training**: Nov 2024 (optimize if needed)
- **Validation**: Dec 2024 (test without changes)
- **Walk-Forward**: Jan 2025 (final blind test)

**Test on**: Top 3 symbols from Phase 2 (likely RIOT + 2 others).

**Success Criteria**: 
- Positive P&L in all 3 periods
- Sharpe > 0.5 in validation + walk-forward
- Max DD < 20%

**Deliverable**: `ORB_V13_WFA_REPORT.md` with GO/NO-GO for deployment.

---

### Phase 5: Live Parameter Tuning (Week 5)
**Goal**: Fine-tune parameters on approved symbols only.

**Tunable Parameters** (constrained ranges to avoid overfitting):
- Time Stop: [20min, 30min, 45min]
- Partial Exit 1: [1.0R, 1.2R, 1.5R]
- Partial Exit 2: [1.8R, 2.0R, 2.5R]
- Trail ATR Multiple: [0.6, 0.8, 1.0]
- OR Range Minimum: [0.25 ATR, 0.30 ATR, 0.35 ATR]

**Method**: Grid search on training period, validate on walk-forward.

**Constraint**: Max 3 parameter changes from V13 baseline.

**Deliverable**: `ORB_FINAL_DEPLOYMENT_CONFIGS/` folder with per-symbol configs.

---

## PART 5: IMMEDIATE NEXT ACTIONS (Priority Order)

### Action 1: Implement V13 Strategy File
**File**: `research/new_strategy_builds/strategies/orb_v13_surgical.py`

**Changes from V7**:
```python
# EXIT CHANGES (CRITICAL)
MOVE_TO_BREAKEVEN_PROFIT = 1.0  # Was 0.5
BREAKEVEN_OFFSET = -0.05  # Was 0.0 (allows small loss vs scratch)
PROFIT_TARGET_1 = 1.2  # Take 30%
PROFIT_TARGET_2 = 2.0  # Take 30%
PROFIT_TARGET_1_SIZE = 0.30  # Was 0.50 @ 1.3R
TRAIL_ATR_MULTIPLE = 0.8  # Was 0.6
ENABLE_VWAP_LOSS = False  # **WAS TRUE - THIS IS THE KILL SWITCH**
TIME_STOP_MINUTES = 45  # NEW

# ENTRY CHANGES
ENTRY_WINDOW_START = "09:40"  # Was 09:30
ENTRY_WINDOW_END = "10:15"  # Was 10:00
MIN_OR_RANGE_ATR_MULTIPLE = 0.30  # NEW (volatility filter)
REQUIRE_SPY_ABOVE_VWAP = True  # NEW (regime filter)
```

**Complexity**: 7/10 (core logic change, high impact)

---

### Action 2: Create V13 Test Script
**File**: `research/new_strategy_builds/test_orb_v13_RIOT_ABLATION.py`

**Purpose**: Test V13 vs V7 on RIOT only for rapid validation.

**Output**: Side-by-side comparison CSV showing:
- Total Trades
- Win Rate
- Avg Win (R-multiple)
- Avg Loss (R-multiple)
- Total P&L
- Max DD
- Expectancy per trade

**Run Command**:
```bash
python research/new_strategy_builds/test_orb_v13_RIOT_ABLATION.py
```

---

### Action 3: Run Phase 1 Testing
**Timeline**: Next 2-3 hours

**Steps**:
1. Run V7 baseline on RIOT (control)
2. Run V13 on RIOT (treatment)
3. Compare results
4. Generate `ORB_V13_EXIT_ABLATION_RESULTS.md`

**Decision Point**: 
- If V13 shows >30% P&L improvement → Proceed to Phase 2
- If V13 shows <30% improvement → Re-examine exit parameters, retest
- If V13 still negative → Consult on entry logic changes

---

### Action 4: Prepare Universe Scanner Enhancement
**File**: `research/new_strategy_builds/orb_universe_scanner.py`

**Purpose**: Daily pre-market scan to identify "RIOT-like" candidates.

**Filters**:
```python
MIN_GAP_PERCENT = 2.0  # Absolute value
MIN_PREMARKET_RVOL = 2.0
MIN_BETA = 1.8
MIN_ATR_PERCENT = 2.5  # ATR(14) / Price
MAX_SPY_CORRELATION_1H = 0.7  # Avoid mean-reverters
MIN_DOLLAR_VOLUME = 100_000_000
MAX_FLOAT_SHARES = 500_000_000
```

**Output**: List of 5-10 qualified symbols each morning by 9:25 AM.

---

### Action 5: Documentation Updates
Create comprehensive testing documentation:

1. **ORB_V13_SPECIFICATION.md** - Full strategy specification
2. **ORB_EXIT_ASYMMETRY_ANALYSIS.md** - Mathematical proof of why V7 failed
3. **ORB_EXPERT_CONSENSUS_SUMMARY.md** - This document (synthesizing 3 experts)

---

## PART 6: RISK MANAGEMENT & EXPECTATIONS

### Realistic Performance Targets (V13 on Specialized Universe)

**Conservative Estimates** (after friction):
- **Monthly Return**: 1.5-2.5% per symbol
- **Win Rate**: 40-50% (down from 59%, but acceptable)
- **Avg Win**: 1.2-1.8R (up from 0.5R)
- **Avg Loss**: 1.0R (unchanged)
- **Sharpe Ratio**: 0.8-1.2
- **Max Drawdown**: 12-18%
- **Trade Frequency**: 8-15 trades/month per symbol (down from 20+)

**Portfolio Construction**:
- Deploy on 4-6 symbols simultaneously
- Risk 1% per trade per symbol
- Max 2 positions per symbol
- Max 8 positions total
- Expected portfolio return: 6-12% monthly (before compounding)

### Failure Scenarios & Mitigation

**Scenario A**: V13 still shows negative P&L on RIOT
- **Diagnosis**: Entry logic has no edge (unlikely given current 59% win rate)
- **Mitigation**: Test "Instant Breakout" version (Gem Ni's suggestion) with no pullback

**Scenario B**: V13 works on RIOT but fails on other symbols
- **Diagnosis**: RIOT is a statistical outlier
- **Mitigation**: Deploy on RIOT only, build scanner to find more RIOT-like names weekly

**Scenario C**: Win rate drops to 30-35% (too low)
- **Diagnosis**: Removed too many protective exits
- **Mitigation**: Reintroduce VWAP loss exit but ONLY after 1.5R profit, not before

**Scenario D**: Friction still too high even at lower frequency
- **Diagnosis**: Strategy is not scalable with current execution costs
- **Mitigation**: Switch to options ORB (buy ATM calls on ORB breakout, wider spreads acceptable)

---

## PART 7: CONFIDENCE ASSESSMENT

### Probability of Success by Phase

| Phase | Goal | Probability | Rationale |
|-------|------|-------------|-----------|
| Phase 1 | V13 beats V7 on RIOT | **85%** | All 3 experts agree exit change will work |
| Phase 2 | Find 5+ profitable symbols | **70%** | Universe specialization is proven concept |
| Phase 3 | 5-min bars reduce friction 40%+ | **80%** | Simple math, lower frequency = lower cost |
| Phase 4 | WFA validates robustness | **60%** | Small sample size is a risk |
| Phase 5 | Tuning adds 10-20% improvement | **50%** | Diminishing returns, overfitting risk |

**Overall Deployment Probability**: **60-65%**

**Reasoning**: 
- Exit fix alone should flip expectancy positive (80% confident)
- Universe specialization will work (70% confident)
- WFA validation is the wild card (60% confident due to small sample)

---

## PART 8: EXPERT SYNTHESIS - FINAL VERDICT

### What All 3 Experts Would Agree On

If I could get Chad G, Dee S, and Gem Ni in a room, here's what they would universally endorse:

**✅ DO THIS**:
1. Remove VWAP loss exit immediately
2. Remove or delay breakeven trigger to 1.0R+
3. Widen trailing stop to 0.8-1.0 ATR
4. Add time stop (30-45 minutes)
5. Filter out mean-reverting large caps
6. Test on 5-minute bars
7. Focus on RIOT + small caps + volatile commodities
8. Track MAE/MFE on every trade

**❌ DON'T DO THIS**:
1. Don't add more entry confirmations (delays entry, reduces R)
2. Don't try to make NVDA/PLTR work (wrong microstructure)
3. Don't scale out at 1.3R (too early)
4. Don't optimize on in-sample data before WFA
5. Don't ignore friction costs
6. Don't force universal application

### The One Thing They Might Disagree On

**Entry Method**:
- **Chad G**: Keep pullback entry, add regime/context filters
- **Dee S**: Staggered entry (50% breakout, 50% pullback)
- **Gem Ni**: Instant breakout with no pullback if Volume > 2x

**My Recommendation**: Test all three as V13a, V13b, V13c. Let the data decide. My hypothesis is **Dee S's staggered entry** will win (best of both worlds).

---

## PART 9: PERSONAL QUANT ASSESSMENT

As a quantitative algorithmic trading expert, here's my professional opinion:

### What Makes This Strategy Salvageable

1. **High Win Rate Proves Valid Pattern Recognition**: 59% on RIOT across 50 trades is not luck. The entry logic is finding real breakouts.

2. **Clear Mathematical Diagnosis**: This isn't a mysterious failure. It's a textbook case of negative skew + friction. We know exactly what to fix.

3. **Proven Winners Exist**: RIOT (+4.18%), TNMG (+65%), KC (+4.83%) demonstrate the strategy works on the right assets.

4. **Conservative Position Sizing**: 1% risk per trade means we have room to absorb drawdowns during tuning.

### What Concerns Me

1. **Sample Size**: 50 trades over 2.5 months is borderline for statistical significance. We need 100+ trades for confidence.

2. **Regime Dependency**: All testing was done in Nov 2024-Jan 2025. We don't know how this performs in low-volatility or bear regimes.

3. **Small Cap Illiquidity**: TNMG's +65% on 4 trades is exciting but not scalable. Slippage on entry/exit could eat the edge on larger size.

4. **Friction Assumption Accuracy**: If real friction is 0.20% instead of 0.125%, even V13 might fail. Need to validate with live execution.

### My Edge Hypothesis

The ORB strategy is capturing **volatility expansion reversal** on stocks that:
- Gap on news/catalyst
- Experience early selling pressure (creates OR)
- Reclaim OR high as shorts cover + momentum buyers enter
- Continue higher due to low float/high short interest

This is NOT a pure trend-following system. It's a **liquidity squeeze detector** on small caps and **regime shift detector** on commodities.

**Implication**: The strategy should work best on:
- Stocks with high short interest
- Low float
- Catalyst-driven (earnings, news, sector rotation)
- High RVOL at open

This explains why RIOT works (high retail interest, news-driven, volatile) and NVDA fails (deep liquidity, mean-reverting, institutionally arbitraged).

---

## PART 10: THE WINNING PATH FORWARD

### My Recommended Approach (Combining Best of All 3 Experts)

**Version**: ORB V13 "EXPERT HYBRID"

#### Entry (Dee S + Chad G hybrid)
- **Timeframe**: 5-minute bars
- **OR Definition**: 9:30-9:40 (first two 5-min bars)
- **Entry**: 
  - **50% position**: Immediate entry on 5-min close above ORH if:
    - Volume > 2.5x RVOL
    - SPY above VWAP (regime filter per Chad)
    - OR range > 0.3 ATR (volatility filter per Chad)
  - **50% position**: Add on pullback within 0.15 ATR of ORH + reclaim (Dee's staggered entry)
- **Entry Window**: 9:40-10:15 AM
- **PDH Filter**: No entry if ORH breakout is within 0.5% of Prior Day High (Chad's collision filter)

#### Stop Loss
- **Initial**: OR Low - 0.3 ATR (Gem's tighter stop for better R)
- **Move to -0.05R**: Once price hits +1.0R (Chad's "not BE" insight)

#### Exits (Consensus from all 3)
- **REMOVED**: VWAP loss exit, BE @ 0.5R, scale @ 1.3R
- **NEW**:
  1. **30% exit at +1.2R** (lock profit)
  2. **30% exit at +2.0R** (capture extension)
  3. **Trail 40%** with 0.8 ATR or structural method, only after +1.2R
  4. **Time Stop**: Exit all at 45 minutes if not +0.25R (Chad + Dee consensus)
  5. **Hard close**: Exit all at 3:50 PM (no overnight holds)

#### Universe Filter (Chad + Dee + Gem consensus)
**Daily Pre-Market Scan** (by 9:25 AM):
- Gap > 2.0% or < -2.0% (Gem's catalyst filter)
- Beta > 1.8 (Dee's spec)
- ATR(14) / Price > 2.5% (volatility requirement)
- Pre-market volume > 30% of daily avg (liquidity + interest)
- **EXCLUDE**: Any symbol with 1-hour SPY correlation > 0.7 (Dee's mean-reversion filter)

**Permanent Whitelist** (always trade if qualified):
- RIOT, MARA (if individually tested)
- TNMG, CGTL, LCID (small cap volatility)
- KC, CL, PL (commodities)

**Permanent Blacklist** (never trade):
- NVDA, MSFT, AAPL, META, GOOGL, AMZN (wrong microstructure)
- SPY, QQQ, IWM (ETFs are mean-reverting)

#### Risk Management
- Risk 1% per trade
- Max 2 positions per symbol
- Max 6 positions total across portfolio
- Daily loss limit: 3% of account (auto-shutdown)

#### Diagnostics (Chad's MAE/MFE framework)
Track on every trade:
- MAE (max adverse excursion)
- MFE (max favorable excursion)
- Time to MFE
- Exit type (stop, target, trail, time)
- Market regime at entry (SPY trend, VIX level)

---

## CONCLUSION

The ORB strategy **has structural edge** but was being **executed poorly**. The three experts unanimously diagnosed the problem: **exit asymmetry + friction**.

**The fix is surgical, not systemic**:
1. Remove VWAP loss exit
2. Delay/remove breakeven trigger
3. Widen trail
4. Add time stop
5. Specialize universe
6. Reduce frequency (5-min bars)

**Expected Result**: Transform from 59% win rate / -2% P&L to 45% win rate / +2-3% P&L monthly on specialized universe.

**Confidence**: 65% that V13 will pass WFA and deploy successfully.

**Timeline**: 4-5 weeks to full validation and deployment.

---

## NEXT IMMEDIATE STEP

**I am ready to implement V13 and run the Phase 1 ablation test on RIOT.**

Shall I:
1. Create `orb_v13_surgical.py` with the exact specification above?
2. Create `test_orb_v13_RIOT_ABLATION.py` to compare V13 vs V7?
3. Run the test and generate results within the next hour?

**Your call.** 🎯
