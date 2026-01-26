# Strategy Enhancements V2 - Testing Framework

**Created:** 2026-01-19  
**Purpose:** Test volume and other enhancements to validated strategies  
**Status:** Active Testing

---

## 📁 Directory Structure

```
research/strategy_enhancements_v2/
├── README.md                          # This file
├── daily_trend_hysteresis/           # Daily Trend enhancement tests
│   ├── test_volume_filter.py         # Volume filter backtest
│   ├── configs_baseline.json         # Original config (reference)
│   ├── configs_enhanced.json         # Enhanced config with volume
│   └── RESULTS.md                     # Test results
├── hourly_swing/                      # Hourly Swing enhancement tests
│   ├── test_volume_filter.py         # RVOL filter backtest
│   ├── configs_baseline.json         # Original config
│   ├── configs_enhanced.json         # Enhanced config with RVOL
│   └── RESULTS.md                     # Test results
└── results/                           # Aggregated results
    ├── comparison_report.csv          # All tests comparison
    └── SUMMARY.md                     # Executive summary
```

---

## 🎯 Naming Convention

### **Folders:**
- `{strategy_name}/` - One folder per strategy being tested
- `results/` - Aggregated test outputs

### **Files:**
- `test_{enhancement_name}.py` - Test script (e.g., test_volume_filter.py)
- `configs_baseline.json` - Original validated config (for reference)
- `configs_enhanced.json` - New config with enhancements
- `RESULTS.md` - Test results and analysis
- `comparison_report.csv` - Machine-readable results

---

## 🧪 Testing Protocol

### **Phase 1: Baseline Validation**
1. Run original strategy on test period
2. Record: Return %, # Trades, Win Rate, Sharpe

### **Phase 2: Enhanced Version**
1. Add enhancement (e.g., volume filter)
2. Run on SAME period
3. Record same metrics

### **Phase 3: Comparison**
1. Compare baseline vs enhanced
2. Determine if enhancement improves risk-adjusted returns
3. Document findings

### **Phase 4: Multi-Period Validation** (if Phase 3 is positive)
1. Test across 2020-2024
2. Check consistency
3. Make deployment decision

---

## 📊 Test Periods

**Initial Test:** December 2024 (1 month)  
**Extended Test:** 2020-2024 (5 years)  
**Why December 2024?** Recent data, quick feedback

---

## ✅ Success Criteria

An enhancement is considered successful if:
1. ✅ Win rate improves OR stays equal
2. ✅ Sharpe ratio improves
3. ✅ Max drawdown decreases OR stays equal
4. ✅ Works across multiple symbols (not just overfitted to one)

**Note:** Fewer trades is OK if quality improves!

---

## 🚫 What NOT to Do

- ❌ Don't modify files in `research/Perturbations/` (validated strategies)
- ❌ Don't test enhancements on live account
- ❌ Don't optimize parameters to one specific month
- ❌ Don't add multiple enhancements at once (test one at a time)

---

## 📝 Current Tests

### **Test 1: Daily Trend + Volume Filter**
- **Status:** In Progress
- **Enhancement:** Require volume > avg_volume * 1.2 for BUY signals
- **Hypothesis:** Filters out weak RSI breakouts
- **Symbols:** SPY, QQQ, IWM, GLD

### **Test 2: Hourly Swing + RVOL Filter**
- **Status:** In Progress
- **Enhancement:** Require RVOL > 1.5 for BUY signals
- **Hypothesis:** Confirms momentum with volume
- **Symbols:** TSLA, NVDA

---

**Last Updated:** 2026-01-19
