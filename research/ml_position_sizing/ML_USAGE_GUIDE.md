# ML Position Sizing - Usage Guide

**Location:** `research/ml_position_sizing/`  
**Purpose:** ML-enhanced position sizing for Bear Trap strategy  
**Status:** Research complete, baseline identified, ML not yet effective

---

## 📁 **Directory Structure**

```
research/ml_position_sizing/
├── README.md                          # Overview and framework
├── SESSION_HANDOFF.md                 # Latest session summary
├── ML_USAGE_GUIDE.md                  # This file
│
├── data/                              # Training data
│   ├── bear_trap_trades_2020_2024.csv    # 2,025 clean trades (no lookahead)
│   └── labeled_regimes_v2.csv            # Trades with ML labels
│
├── models/                            # Trained models
│   ├── bear_trap_regime_classifier.pkl        # Model with outcome features (leaky)
│   ├── bear_trap_entry_only_classifier.pkl    # Model with entry-only features
│   └── feature_list.txt                       # Feature names
│
├── scripts/                           # All scripts
│   ├── extract_bear_trap_trades.py       # Extract trades from historical data
│   ├── add_tier1_features.py             # Add ML features and labels
│   ├── train_model.py                    # Train outcome-based model
│   ├── train_entry_only_model.py         # Train entry-only model
│   ├── simple_r_analysis.py              # Analyze R-multiples
│   ├── backtest_ml_scaling.py            # Backtest ML position sizing
│   ├── compare_lookahead.py              # Compare lookahead impact
│   ├── detailed_stats.py                 # Detailed statistics
│   ├── pnl_comparison.py                 # P&L comparison
│   ├── sharpe_analysis.py                # Sharpe ratio analysis
│   ├── skip_no_add_analysis.py           # Analyze skipping NO_ADD
│   └── compare_ml_live.py                # Compare ML to baseline
│
├── results/                           # Analysis results
│   ├── BACKTEST_ANALYSIS.md              # Detailed backtest findings
│   └── summary_comparison.csv            # Performance comparison
│
└── test_strategies/                   # Test implementations
    ├── bear_trap_ml_enhanced.py          # ML version (outcome features)
    ├── bear_trap_entry_only_ml.py        # ML version (entry-only)
    └── bear_trap_simple_filter.py        # Rule-based filter
```

---

## 🚀 **Quick Start**

### **1. Extract Historical Trades**

```bash
python research/ml_position_sizing/scripts/extract_bear_trap_trades.py
```

**Output:** `data/bear_trap_trades_2020_2024.csv` (2,025 trades)

---

### **2. Add ML Features and Labels**

```bash
python research/ml_position_sizing/scripts/add_tier1_features.py
```

**Output:** `data/labeled_regimes_v2.csv` (trades with ADD_ALLOWED/ADD_NEUTRAL/NO_ADD labels)

---

### **3. Train ML Model**

**Option A: Outcome-based (has data leakage)**
```bash
python research/ml_position_sizing/scripts/train_model.py
```

**Option B: Entry-only (no leakage, but not predictive)**
```bash
python research/ml_position_sizing/scripts/train_entry_only_model.py
```

**Output:** `models/bear_trap_*_classifier.pkl`

---

### **4. Test ML Strategy**

```bash
# Test with outcome-based model
python research/ml_position_sizing/test_strategies/bear_trap_ml_enhanced.py

# Test with entry-only model
python research/ml_position_sizing/test_strategies/bear_trap_entry_only_ml.py

# Test with simple rules
python research/ml_position_sizing/test_strategies/bear_trap_simple_filter.py
```

---

## 📊 **Analysis Scripts**

### **Compare Performance**
```bash
python research/ml_position_sizing/scripts/simple_r_analysis.py
```
Shows R-multiple comparison between baseline and ML.

### **Analyze Lookahead Impact**
```bash
python research/ml_position_sizing/scripts/compare_lookahead.py
```
Compares old (lookahead) vs new (fixed) data.

### **Detailed Statistics**
```bash
python research/ml_position_sizing/scripts/detailed_stats.py
```
Win rate, avg R, by regime breakdown.

### **Skip NO_ADD Analysis**
```bash
python research/ml_position_sizing/scripts/skip_no_add_analysis.py
```
Shows impact of filtering out NO_ADD trades.

---

## 🎯 **Current Status**

### **What Works:**
✅ Data extraction (2,025 clean trades)  
✅ Feature engineering (time, volume, momentum)  
✅ Model training (64% accuracy)  
✅ Lookahead bias fixed  

### **What Doesn't Work:**
❌ ML doesn't improve live performance  
❌ Entry-only features not predictive  
❌ Outcome features have data leakage  
❌ Simple rules too aggressive  

### **Baseline Performance (2024):**
- **543 trades**
- **43.5% win rate**
- **+0.15R average**
- **Profitable but weak**

---

## 🔬 **Key Findings**

### **1. Data Leakage Problem**
Models trained on `max_profit` and `bars_held` perform well in backtest but fail live because these features aren't known at entry.

### **2. Entry Features Not Predictive**
Features available at entry (time, volume, day_change) don't differentiate good from bad trades enough.

### **3. Lookahead Bias Impact**
Original Bear Trap had 30% optimistic results due to using full-day session_low at every bar.

### **4. Skip NO_ADD Paradox**
Backtests show skipping NO_ADD improves R by 44%, but live testing shows it makes things worse. This suggests the labels themselves are based on outcome data.

---

## 💡 **Next Steps**

### **To Make ML Work:**

1. **Better Entry Features**
   - Level 2 tape data
   - Order flow imbalance
   - Recent price action patterns
   - Relative volume at exact entry time

2. **Different Labeling Approach**
   - Label based on ENTRY characteristics of successful trades
   - Not based on OUTCOME
   - E.g., "trades that entered on high volume in late session"

3. **Simpler Approach**
   - Just filter by time (only 3pm-4pm)
   - Just filter by volume (only >3x average)
   - Test each filter independently

4. **Different Strategy**
   - Maybe Bear Trap just isn't ML-friendly
   - Try ML on Hourly Swing or Daily Trend instead

---

## 📝 **How to Use This Research**

### **For Backtesting:**
Use `data/labeled_regimes_v2.csv` to analyze historical performance by regime.

### **For Live Trading:**
**Don't use ML yet.** Stick with baseline Bear Trap (with lookahead fix).

### **For Further Research:**
1. Start with `scripts/extract_bear_trap_trades.py`
2. Modify feature engineering in `scripts/add_tier1_features.py`
3. Retrain with `scripts/train_entry_only_model.py`
4. Test with `test_strategies/bear_trap_entry_only_ml.py`

---

## ⚠️ **Important Notes**

- **All models saved in `models/` have issues** (either data leakage or not predictive)
- **Don't deploy any ML version yet**
- **Baseline (+0.15R) is the current best**
- **All lookahead bias has been fixed** in production files

---

## 🔗 **Related Documentation**

- `SESSION_HANDOFF.md` - Latest session summary
- `CHAD_RECOMMENDATIONS.md` - Expert insights on ML approach
- `LABELING_PROTOCOL.md` - How labels were created
- `results/BACKTEST_ANALYSIS.md` - Detailed backtest findings

---

**Last Updated:** 2026-01-19  
**Status:** Research phase complete, deployment not recommended yet
