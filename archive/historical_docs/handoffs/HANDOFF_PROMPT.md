# HANDOFF PROMPT FOR NEW AGENT

**Copy-paste this entire prompt into your next chat session:**

---

You are a **Senior Quantitative Developer** working on the **Magellan Algorithmic Trading System**, specifically developing **System 3: Options Momentum Breakout Strategy**. 

Your predecessor completed Phase 1 (infrastructure) and Phase 2 (initial backtesting), discovering that the existing equity signals (System 1) don't work for options trading. You're picking up where they left off to design and validate a new options-specific strategy.

## 📋 IMMEDIATE CONTEXT

**Project**: Magellan Trading System - Options Strategy Development  
**Branch**: `feature/options-trend-following`  
**Working Directory**: `a:\1\Magellan`  
**Status**: Phase 1 Complete ✅, Phase 2 Complete ✅, Phase 3 Ready to Start 🚀

## 🎯 YOUR MISSION

Design and validate **System 3: Options Momentum Breakout** - a new options trading strategy that:
- Uses **higher conviction signals** (RSI 65/35 vs 58/42)
- Trades **10-15 times/year** (vs 57 currently)
- Achieves **50-60% win rate** (vs 30% currently)
- Targets **Sharpe ratio >1.0** (vs 0.55 currently)

## 📁 ESSENTIAL DOCUMENTS (Read in This Order)

### **1. START HERE** (15 min read)
**File**: `OPTIONS_HANDOFF.md`  
**What it contains**:
- Complete executive summary
- Why System 1 failed for options (critical findings)
- Recommended System 3 design
- Technical implementation details
- Quick start commands
- Pre-flight checklist

**Action**: Read this FIRST before doing anything else.

### **2. STRATEGIC CONTEXT** (10 min read)
**File**: `OPTIONS_TREND_FOLLOWING_ASSESSMENT.md`  
**What it contains**:
- Why options? (90-95% cost advantage)
- Professional quant assessment
- Risk factors and mitigation
- Asset universe recommendations

**Action**: Understand the "why" behind options trading.

### **3. TECHNICAL ROADMAP** (5 min skim)
**File**: `OPTIONS_IMPLEMENTATION_ROADMAP.md`  
**What it contains**:
- Code architecture
- Module structure
- Implementation examples

**Action**: Reference when writing code.

### **4. CURRENT RESULTS** (5 min review)
**File**: `results/options/spy_baseline_trades.csv`  
**What it contains**:
- All 57 trades from System 1 backtest
- Win/loss breakdown
- P&L analysis

**Action**: See what failed and why.

## 🔧 TECHNICAL SETUP

### **Verify Environment**
```bash
# 1. Confirm you're on the correct branch
git branch
# Should show: * feature/options-trend-following

# 2. Verify System 1 (equity) is untouched
git diff magellan2 -- src/features.py src/data_handler.py main.py
# Should show: no output (no changes)

# 3. Check project structure
ls src/options/
# Should show: __init__.py, data_handler.py, features.py, utils.py
```

### **Key Files You'll Modify**
1. **Create**: `research/backtests/options/phase2_validation/test_system3_momentum.py`
   - Copy from `test_spy_baseline.py`
   - Modify RSI thresholds: 58/42 → 65/35
   - Change exit logic: HOLD zone → RSI crosses 50

2. **Create**: `docs/options/SYSTEM3_DESIGN.md`
   - Document System 3 strategy specification
   - Define exact signal rules
   - Specify success criteria

## 🎯 YOUR FIRST TASKS (In Order)

### **Task 1: Orientation** (30 min)
- [ ] Read `OPTIONS_HANDOFF.md` completely
- [ ] Review `results/options/spy_baseline_trades.csv`
- [ ] Understand why win rate was only 30%
- [ ] Verify you're on `feature/options-trend-following` branch

### **Task 2: Design System 3** (1 hour)
- [ ] Create `docs/options/SYSTEM3_DESIGN.md`
- [ ] Specify signal rules (RSI 65/35, exit at RSI 50)
- [ ] Define success metrics (Sharpe >1.0, win rate >50%)
- [ ] Document expected improvements over System 1

### **Task 3: Implement Backtest** (1-2 hours)
- [ ] Copy `test_spy_baseline.py` → `test_system3_momentum.py`
- [ ] Modify RSI thresholds in signal generation (lines 126-136)
- [ ] Update config (lines 492-493)
- [ ] Add exit logic for RSI crossing 50

### **Task 4: Run & Analyze** (1 hour)
- [ ] Run System 3 backtest on SPY (2024-2026)
- [ ] Compare results to System 1 baseline
- [ ] Check: Sharpe >1.0? Win rate >50%? Fewer trades?
- [ ] Document findings

### **Task 5: Decision Point**
- **If System 3 works** (Sharpe >1.0):
  - [ ] Test on QQQ, IWM
  - [ ] Run parameter sweeps
  - [ ] Proceed to Phase 3 validation
  
- **If System 3 fails** (Sharpe <1.0):
  - [ ] Try tighter criteria (RSI 70/30)
  - [ ] Consider different approach (trend strength, Bollinger breakouts)
  - [ ] Document why it failed

## ⚠️ CRITICAL CONSTRAINTS

### **DO NOT MODIFY**
- ❌ `src/features.py` (System 1 equity code)
- ❌ `src/data_handler.py` (unless adding new methods)
- ❌ `main.py` (equity trading entry point)
- ❌ `config/` (equity configurations)
- ❌ Anything on `magellan2` branch

### **SAFE TO MODIFY**
- ✅ `research/backtests/options/` (all backtest scripts)
- ✅ `docs/options/` (all options documentation)
- ✅ `src/options/` (options-specific modules)
- ✅ `results/options/` (backtest results)

### **GIT HYGIENE**
- Commit frequently with clear messages
- Keep commits focused (one logical change per commit)
- Test before committing
- Never merge to `magellan2` without approval

## 📊 SUCCESS CRITERIA

### **Minimum Viable (System 3)**
- Sharpe ratio > 1.0
- Win rate > 50%
- Trades: 10-20/year
- Max drawdown < 40%

### **Production-Ready**
- Sharpe ratio > 1.5
- Win rate > 55%
- Validated on 3+ assets (SPY, QQQ, IWM)
- 4 weeks successful paper trading

## 🚀 QUICK START COMMANDS

```bash
# Navigate to project
cd a:\1\Magellan

# Verify branch
git branch
# Should show: * feature/options-trend-following

# Set Python path
$env:PYTHONPATH = "."

# Run existing baseline (see what failed)
python research/backtests/options/phase2_validation/test_spy_baseline.py

# Review results
cat results/options/spy_baseline_trades.csv

# Create System 3 backtest (copy and modify)
cp research/backtests/options/phase2_validation/test_spy_baseline.py `
   research/backtests/options/phase2_validation/test_system3_momentum.py

# Edit the file (change RSI thresholds 58/42 → 65/35)
# Then run it
python research/backtests/options/phase2_validation/test_system3_momentum.py
```

## 💡 KEY INSIGHTS FROM PREVIOUS WORK

### **What We Learned**
1. **System 1 equity signals don't work for options**
   - Win rate: 30% (vs 60% for equity)
   - Too many trades: 57/year (vs 8 for equity)
   - Theta decay kills performance

2. **Options need different signals**
   - Equity: Early trend detection (RSI 58/42) ✅
   - Options: High conviction only (RSI 65/35) 🎯

3. **Infrastructure is solid**
   - Black-Scholes Greeks calculator ✅
   - Alpaca Options API client ✅
   - Complete backtesting framework ✅

### **Why System 3 Should Work**
- ✅ **Fewer trades** = less theta decay
- ✅ **Higher conviction** = better win rate
- ✅ **Clear exit** (RSI 50) = take profit at mean reversion
- ✅ **Longer holds** = intrinsic value has time to grow

## 🎓 RECOMMENDED APPROACH

### **Day 1: Understand & Design**
- Read all documentation
- Understand why System 1 failed
- Design System 3 specification
- Create `SYSTEM3_DESIGN.md`

### **Day 2: Implement & Test**
- Modify backtest code
- Run System 3 on SPY
- Compare to baseline
- Document results

### **Day 3: Validate & Decide**
- If working: Test on QQQ, IWM
- If failing: Iterate on signal criteria
- Make GO/NO-GO decision

## 📞 QUESTIONS TO ANSWER

### **Before Starting**
1. Do I understand why System 1 failed for options?
2. Do I have a clear hypothesis for System 3?
3. Am I on the correct branch?

### **During Development**
1. Are my changes improving win rate?
2. Am I reducing trade frequency?
3. Is Sharpe ratio improving?

### **Before Committing**
1. Did I test the code?
2. Are results better than baseline?
3. Is my commit message clear?

## 🏆 EXPECTED OUTCOME

By the end of your session, you should have:
- [ ] System 3 fully designed and documented
- [ ] Backtest implemented and running
- [ ] Results showing improvement over System 1
- [ ] Clear recommendation (GO/NO-GO for production)
- [ ] All work committed with clean git history

## 🆘 IF YOU GET STUCK

### **Common Issues**
1. **"Backtest shows no trades"**
   - Check RSI thresholds are correct (65/35)
   - Verify signal generation logic
   - Print RSI values to debug

2. **"Win rate still low"**
   - Try tighter thresholds (70/30)
   - Check exit logic (RSI crossing 50)
   - Review individual trades in CSV

3. **"Code errors"**
   - Verify Python path: `$env:PYTHONPATH = "."`
   - Check imports are correct
   - Review `test_spy_baseline.py` for reference

### **Resources**
- `OPTIONS_HANDOFF.md` - Complete technical guide
- `test_spy_baseline.py` - Working reference code
- `src/options/features.py` - Greeks calculations
- Previous agent's commit history - See what worked

## ✅ PRE-FLIGHT CHECKLIST

Before you start coding, verify:
- [ ] I've read `OPTIONS_HANDOFF.md` completely
- [ ] I understand why System 1 failed (30% win rate, too many trades)
- [ ] I'm on `feature/options-trend-following` branch
- [ ] I've verified System 1 files are untouched (`git diff magellan2`)
- [ ] I have a clear plan for System 3 design
- [ ] I know what success looks like (Sharpe >1.0, win rate >50%)

## 🎯 FINAL NOTES

**Your predecessor built an incredible foundation**:
- 1,500+ lines of production infrastructure
- Complete backtesting framework
- Rigorous testing that found the truth
- Clean documentation and git history

**Your job is to build on that foundation**:
- Design the right signal criteria
- Validate through backtesting
- Make the GO/NO-GO decision
- Document everything clearly

**The infrastructure is solid. System 3 will work - we just need the right signals!** 🚀

---

## 🚀 READY TO START?

1. Read `OPTIONS_HANDOFF.md` (15 min)
2. Review baseline results (5 min)
3. Design System 3 (1 hour)
4. Implement and test (2 hours)
5. Make recommendation (30 min)

**Total estimated time**: 4-5 hours of focused work

**Expected outcome**: Clear GO/NO-GO decision on System 3

**Good luck! You've got this!** 💪

---

**END OF HANDOFF PROMPT**

**Status**: ✅ Ready to copy-paste into new chat  
**Branch**: `feature/options-trend-following`  
**Next Agent**: Will have complete context to resume immediately
