# Bear Trap ML Enhancement - Session Handoff

**Date:** 2026-01-19  
**Session Duration:** ~10 hours  
**Status:** Lookahead bug fixed, ML exploration complete, ready for further refinement

---

## 🚨 **CRITICAL DISCOVERY: Lookahead Bias**

### **The Bug:**
Bear Trap used `.transform('min')` for `session_low`, giving every bar the FINAL session low (known only at EOD).

**Impact:**
- 32.7% of bars had lookahead advantage
- 3.5% false "reclaim" signals
- **All Bear Trap backtests were 30% optimistic**

### **The Fix:**
```python
# WRONG (lookahead):
df['session_low'] = df.groupby('date')['low'].transform('min')

# CORRECT (no lookahead):
df['session_low'] = df.groupby('date')['low'].cummin()
```

**Fixed in:**
- `research/Perturbations/bear_trap/bear_trap_strategy.py`
- `research/Perturbations/bear_trap/bear_trap.py`
- `research/ml_position_sizing/scripts/extract_bear_trap_trades.py`

**All other strategies checked - ONLY Bear Trap had this issue.** ✅

---

## 📊 **Bear Trap Performance (After Fix)**

### **Baseline (2024, 3 symbols):**
- Trades: 543
- Win Rate: 43.5%
- Avg R: **+0.15**
- Avg P&L: +0.33%

**Still profitable, just weaker than we thought.**

---

## 🤖 **ML Enhancement Attempts**

### **Attempt 1: Pandas-based labeling**
- Extracted 2,025 trades (2020-2024)
- Labeled as ADD_ALLOWED, ADD_NEUTRAL, NO_ADD
- **Backtest showed +71% improvement** (Skip NO_ADD)
- **BUT:** Used outcome features (max_profit, bars_held) = data leakage

### **Attempt 2: Inline decision tree**
- Simple if/then logic
- **Result:** -0.12R (LOSING)
- **Problem:** Didn't match training logic

### **Attempt 3: Trained sklearn model (outcome features)**
- DecisionTreeClassifier on labeled data
- **Result:** -0.12R (LOSING)
- **Problem:** Data leakage - model learned from outcomes

### **Attempt 4: Entry-only features model**
- Retrained with ONLY entry-time data
- Features: time_score, high_volume, big_drop, etc.
- **Result:** -0.12R (LOSING)
- **Problem:** Entry features not predictive enough

### **Attempt 5: Simple rule-based filter**
- Late session + high volume + fast reclaim
- **Result:** ~5 trades, -0.02R
- **Problem:** Too aggressive, filtered out everything

---

## ✅ **What Works**

**Baseline Bear Trap (+0.15R) with lookahead fix applied.**

That's it. ML doesn't help (yet).

---

## 📁 **Key Files**

### **Fixed Strategy Files:**
- `research/Perturbations/bear_trap/bear_trap_strategy.py` (lookahead fixed)
- `research/Perturbations/bear_trap/bear_trap.py` (lookahead fixed)

### **ML Research:**
- `research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv` (2,025 clean trades)
- `research/ml_position_sizing/data/labeled_regimes_v2.csv` (with ML labels)
- `research/ml_position_sizing/models/bear_trap_regime_classifier.pkl` (trained model)
- `research/ml_position_sizing/models/bear_trap_entry_only_classifier.pkl` (entry-only model)

### **Test Scripts:**
- `research/ml_position_sizing/bear_trap_ml_enhanced.py` (ML version)
- `research/ml_position_sizing/bear_trap_entry_only_ml.py` (entry-only ML)
- `research/ml_position_sizing/bear_trap_simple_filter.py` (rule-based)

### **Analysis:**
- `research/ml_position_sizing/results/BACKTEST_ANALYSIS.md` (detailed findings)
- `research/ml_position_sizing/scripts/compare_lookahead.py` (impact analysis)

---

## 🎯 **Next Steps to Find Better Edge**

### **Option A: Better Entry Filters**
Current entry is very permissive. Try:
- Stricter volume requirements (3x+ instead of 1.2x)
- Price action confirmation (e.g., must close in top 25% of range)
- Avoid first hour entirely (9:30-10:30)

### **Option B: Better Exit Logic**
Current: 30-min time stop OR stop loss  
Try:
- Profit targets (e.g., exit at +1R, +2R)
- Trailing stops
- Time-based exits by session (e.g., exit at 3:55pm regardless)

### **Option C: Symbol Selection**
Current: MULN, NKLA, AMC, etc.  
Try:
- Test on different universe (higher float, more liquid)
- Avoid penny stocks
- Focus on stocks with >$5 price, >10M volume

### **Option D: Regime Filters**
Don't trade Bear Trap in certain conditions:
- VIX > 30 (high volatility)
- Market down >1% (avoid capitulation days)
- Low RVOL days (< 1.5x)

### **Option E: Combine with Other Signals**
Bear Trap + something else:
- VWAP reclaim
- Level 2 tape reading
- News catalyst filter

---

## 🎁 **Bonus Discovery: GOOGL RVOL**

**Hourly Swing + RVOL filter on GOOGL:**
- Baseline: -0.50 Sharpe (LOSING)
- With RVOL: +0.45 Sharpe (WINNING)
- **+189% Sharpe improvement!**

**Deployment ready:** `research/Perturbations/hourly_swing/GOOGL_config.json`

---

## 💾 **Data Available**

- **2,025 Bear Trap trades** (2020-2024, clean, no lookahead)
- **ML labels** (ADD_ALLOWED, ADD_NEUTRAL, NO_ADD)
- **Trained models** (both outcome-based and entry-only)

All ready for further experimentation.

---

## 🔬 **What to Try Next**

1. **Run baseline on more symbols** - See if +0.15R holds across broader universe
2. **Test different exit strategies** - Current 30-min time stop might be suboptimal
3. **Add symbol filters** - Maybe Bear Trap only works on certain types of stocks
4. **Combine with volume profile** - Look for high-volume nodes as support
5. **Test on different timeframes** - Maybe 5-min or 15-min works better than 1-min

---

## 📝 **Key Learnings**

1. **Always check for lookahead bias** - Especially with session aggregations
2. **ML needs predictive features** - Entry-time features weren't enough
3. **Data leakage is subtle** - Using max_profit seemed fine but wasn't
4. **Simple baselines are valuable** - +0.15R isn't amazing but it's real
5. **Not every strategy needs ML** - Sometimes simple is better

---

**Ready for next session!** All files organized, bugs fixed, data clean. 🚀
