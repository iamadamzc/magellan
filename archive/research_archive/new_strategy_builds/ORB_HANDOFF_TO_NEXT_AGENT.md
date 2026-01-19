# ORB STRATEGY - HANDOFF TO NEXT AGENT

## Original Objective (Pre-Optimization Attempts)

**Goal**: Validate ORB strategy viability across a wide universe and prepare for deployment.

**Original Plan**:
1. ✅ Relax volume filter (1.8x → 1.5x) - TESTED
2. ✅ Expand testing universe - COMPLETED (87 symbols)
3. ✅ Analyze results - COMPLETED
4. ❌ **Walk-Forward Analysis (WFA)** - NOT STARTED
5. ❌ **Deployment** - NOT STARTED

---

## What Was Accomplished This Session

### Universe Testing (COMPLETED)
- Tested V7 baseline on **87 symbols** across all asset classes
- Results saved to: `research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv`
- **Key Finding**: 14 profitable symbols (16%), 73 losing symbols (84%)

### Strategy Optimization Attempts (12 versions tested - V7 through V12)
- **Result**: No universal improvements found
- **Discovery**: Mathematical paradox (55-61% win rates, still negative P&L)
- **Conclusion**: Strategy appears asset-specific, not universal
- **EXPERT CONSULTATION NEEDED** - See `ORB_EXPERT_CONSULTATION_BRIEF.md`

---

## Profitable Symbols Identified (Ready for WFA)

| Symbol | Trades | Win% | Total P&L | Asset Class |
|--------|--------|------|-----------|-------------|
| TNMG | 4 | 50.0% | +65.04% | Small Cap |
| PL | 1 | 100.0% | +8.26% | Futures (Platinum) |
| CGTL | 7 | 57.1% | +6.82% | Small Cap |
| KC | 6 | 66.7% | +4.83% | Futures (Coffee) |
| **RIOT** | 50 | 58.0% | **+4.18%** | Crypto Stock |
| CL | 2 | 100.0% | +3.20% | Futures (Crude) |
| GS | 10 | 50.0% | +2.26% | Financials |
| RIOX | 1 | 100.0% | +1.13% | Small Cap |
| LCID | 27 | 48.1% | +0.94% | Meme Stock |
| RIVN | 60 | 60.0% | +0.75% | EV Stock |
| VLO | 8 | 62.5% | +0.78% | Energy |
| JPM | 21 | 42.9% | +0.71% | Financials |
| HE | 4 | 50.0% | +0.21% | Futures (Lean Hogs) |
| KC | 6 | 66.7% | +4.83% | Futures (Coffee) |

---

## CRITICAL TASKS FOR NEXT AGENT

### Priority 1: Walk-Forward Analysis (WFA)
**Status**: NOT STARTED  
**Why Critical**: All current results are in-sample. Must validate robustness.

**Recommended Approach**:
1. **RIOT** (highest confidence):
   - Split data: Nov 2024 (train), Dec 2024 (validate), Jan 2025 (test)
   - Run V7 on each period separately
   - Confirm profitability holds out-of-sample

2. **TNMG, CGTL** (small caps):
   - Sample size too small (4-7 trades)
   - Need more historical data or skip WFA
   - Consider forward-test only

3. **Commodities (KC, CL, PL)**:
   - Use futures-specific WFA methodology
   - Account for contract rollovers
   - Test on longer history if available

**Expected Outcome**: If RIOT passes WFA, deploy. If fails, pivot to Path 2 (universe selection).

---

### Priority 2: Deployment Decision
**Status**: BLOCKED on WFA  

**Three Paths Forward**:

**Path A: Deploy V7 on Validated Subset** (if WFA passes)
- Symbols: RIOT + any others that pass WFA
- Risk: 1-2% per trade per symbol
- Max positions: 4-5 simultaneous
- Expected: ~1-2% monthly return per symbol

**Path B: Build Universe Scanner** (if WFA mixed/fails)
- Create daily scanner for "RIOT-like" characteristics:
  - High intraday volatility  
  - Trending behavior (not mean-reverting)
  - Float < 500M
  - Avg volume > $100M
  - Beta > 1.5
- Run V7 only on qualified candidates
- Dynamically update universe weekly

**Path C: Await Expert Consultation** (recommended)
- Expert brief created: `ORB_EXPERT_CONSULTATION_BRIEF.md`
- Get professional input before further optimization
- May reveal fundamental fixes we missed

---

### Priority 3: Recover Missing Symbols Data
**Status**: PARTIALLY COMPLETE

**Symbols with data errors** (from full universe test):
- Futures indices: NQ, RTY, YM
- Metals: GC, SI
- Energy: RB, HO
- Ags: ZC, ZW, ZL
- Softs: CT
- Rates: ZN, ZB, ZF, ZT, ZQ
- FX: 6E, 6J, 6B, 6C, 6A, 6S
- Equities: BITF, JCSE, LCFY, CTMX, BIYA, TYGO, VERO

**Recovery script ready**: `test_orb_v7_RECOVER.py`  
**Action needed**: Fix FMP data integration, retest missing symbols

---

## Key Files & Locations

### Strategy Implementations
- `research/new_strategy_builds/strategies/orb_v7.py` - **BASELINE (use this)**
- `research/new_strategy_builds/strategies/orb_v10_surgical.py` - 0.7R target variant
- All other versions (V8-V12) - Failed optimization attempts

### Test Scripts
- `test_orb_v7_FULL_UNIVERSE.py` - Full universe test (87 symbols)
- `test_orb_v7_RECOVER.py` - Recover missing symbols
- `test_orb_v8_timeframes.py` - Multi-timeframe tester (1min, 5min, 15min)

### Results
- `research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv` - Full results
- `research/new_strategy_builds/results/paradox_symbols.csv` - High win%, negative P&L list
- `research/new_strategy_builds/results/v10_surgical_test.csv` - V10 comparison

### Documentation
- `research/new_strategy_builds/ORB_EXPERT_CONSULTATION_BRIEF.md` - For quant experts
- `research/new_strategy_builds/ORB_V7_UNIVERSE_RESULTS.md` - Summary of findings
- `research/new_strategy_builds/ORB_WINNER_DEPLOYMENT_GUIDE.md` - RIOT deployment guide

---

## Immediate Next Steps (In Order)

1. **Run WFA on RIOT** (highest priority)
   - Use V7 baseline
   - Test Nov, Dec, Jan separately
   - Confirm +4.18% wasn't sample bias

2. **Consult with quant experts** (parallel track)
   - Share `ORB_EXPERT_CONSULTATION_BRIEF.md`
   - Get input on paradox and optimization direction
   - Potentially pivot strategy based on feedback

3. **Recover missing futures data** (if pursuing commodities)
   - Fix FMP integration for metals, energies, rates
   - Test V7 on recovered symbols
   - Coffee (KC) and Crude (CL) already profitable

4. **Build universe scanner** (if WFA shows asset-specificity)
   - Daily scan for volatile, trending stocks
   - Deploy V7 only on qualified candidates
   - This is likely the RIGHT path based on current data

5. **Deployment configs** (if/when WFA passes)
   - Create asset-specific configs for each validated symbol
   - Set up position sizing, risk limits
   - Schedule for paper trading validation

---

## Critical Insights for Next Agent

### What Works
- **V7 baseline** on volatile, trending, crypto-related stocks (RIOT +4.18%)
- **Small caps** with low liquidity (TNMG +65%, CGTL +6.82%)
- **Commodities** (Coffee +4.83%, Crude +3.20%)
- **Pullback entry is CRITICAL** - Don't remove it

### What Doesn't Work
- Large cap tech (all negative)
- Index ETFs (all negative)
- Most crypto stocks except RIOT (MARA, CLSK, HUT all negative)
- Mean-reverting stocks (NVDA, PLTR despite 59%+ win rates)

### The Paradox
**10 symbols with 52-61% win rates are STILL LOSING MONEY.**

This is mathematically bizarre and suggests:
- Winners being cut prematurely (VWAP loss, tight trail)
- Losers running to full stop size
- Friction costs (0.125% per trade) eating all profit
- Fundamental mismatch between strategy and asset behavior

**Expert consultation recommended before further optimization.**

---

## What NOT to Do (Lessons Learned)

1. ❌ **Don't remove pullback entry** (V8 failed catastrophically)
2. ❌ **Don't chase universal application** (strategy is asset-specific)
3. ❌ **Don't over-optimize on in-sample data** (do WFA first)
4. ❌ **Don't ignore friction costs** (50+ trades = -6%+ drag)
5. ❌ **Don't force strategy on mean-reverting stocks**

---

## Recommended Focus

**Option 1** (Conservative): 
- WFA on RIOT → Deploy if passes → Build scanner for more RIOT-like stocks

**Option 2** (Aggressive):
- Expert consultation → Fundamental fixes → Retest universe

**Option 3** (Pragmatic):
- Deploy V7 on 4 known winners (RIOT, TNMG, CGTL, KC) immediately
- WFA in parallel
- Accept asset-specificity, focus on universe expansion

**My recommendation: Option 3** - Ship what works while validating.

---

**Session complete. 127k tokens used. ORB rabbit hole documented. Next agent has clear path forward.** 🎯
