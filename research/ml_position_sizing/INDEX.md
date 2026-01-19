# ML Position Sizing - Quick Reference Index

**Quick navigation for all ML position sizing files**

---

## 📖 **Documentation**

| File | Purpose |
|------|---------|
| `README.md` | Framework overview and methodology |
| `ML_USAGE_GUIDE.md` | **START HERE** - How to use everything |
| `SESSION_HANDOFF.md` | Latest session summary and next steps |
| `CHAD_RECOMMENDATIONS.md` | Expert insights on ML approach |
| `LABELING_PROTOCOL.md` | How regime labels were created |

---

## 💾 **Data**

| File | Description | Records |
|------|-------------|---------|
| `data/bear_trap_trades_2020_2024.csv` | Clean historical trades (no lookahead) | 2,025 |
| `data/labeled_regimes_v2.csv` | Trades with ML regime labels | 2,025 |

---

## 🤖 **Models**

| File | Type | Status |
|------|------|--------|
| `models/bear_trap_regime_classifier.pkl` | Outcome-based | ⚠️ Data leakage |
| `models/bear_trap_entry_only_classifier.pkl` | Entry-only | ⚠️ Not predictive |
| `models/feature_list.txt` | Feature names | Reference |

**⚠️ Don't deploy these models - they don't work in live trading**

---

## 🔧 **Scripts** (in `scripts/`)

### **Data Preparation:**
- `extract_bear_trap_trades.py` - Extract trades from historical data
- `add_tier1_features.py` - Add ML features and labels

### **Model Training:**
- `train_model.py` - Train outcome-based model (has leakage)
- `train_entry_only_model.py` - Train entry-only model

### **Analysis:**
- `simple_r_analysis.py` - R-multiple comparison
- `compare_lookahead.py` - Lookahead bias impact
- `detailed_stats.py` - Win rate, R by regime
- `pnl_comparison.py` - P&L analysis
- `sharpe_analysis.py` - Sharpe ratio calculation
- `skip_no_add_analysis.py` - Skip NO_ADD impact
- `backtest_ml_scaling.py` - Full backtest simulation
- `compare_ml_live.py` - ML vs baseline comparison

---

## 🧪 **Test Strategies** (in `test_strategies/`)

| File | Approach | Result |
|------|----------|--------|
| `bear_trap_ml_enhanced.py` | ML with outcome features | -0.12R ❌ |
| `bear_trap_entry_only_ml.py` | ML with entry-only features | -0.12R ❌ |
| `bear_trap_simple_filter.py` | Rule-based filter | ~-0.02R ❌ |

**Baseline (no ML): +0.15R** ✅

---

## 📊 **Results** (in `results/`)

- `BACKTEST_ANALYSIS.md` - Detailed backtest findings
- `summary_comparison.csv` - Performance metrics
- `baseline_backtest.csv` - Baseline results
- `ml_enhanced_backtest.csv` - ML results

---

## 🚀 **Quick Commands**

```bash
# Extract trades
python research/ml_position_sizing/scripts/extract_bear_trap_trades.py

# Add labels
python research/ml_position_sizing/scripts/add_tier1_features.py

# Train model
python research/ml_position_sizing/scripts/train_entry_only_model.py

# Test strategy
python research/ml_position_sizing/test_strategies/bear_trap_entry_only_ml.py

# Analyze results
python research/ml_position_sizing/scripts/simple_r_analysis.py
```

---

## 🎯 **Current Status**

**Baseline Bear Trap: +0.15R (use this)**  
**ML versions: -0.12R (don't use)**

**Next:** Try better entry filters or different labeling approach

---

**Last Updated:** 2026-01-19
