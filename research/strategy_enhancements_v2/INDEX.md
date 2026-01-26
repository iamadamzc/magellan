# V2 Enhancement Testing - Quick Reference

**Location:** `research/strategy_enhancements_v2/`  
**Status:** Phase 1 Complete  
**Created:** 2026-01-19

---

## 📁 **What's Inside:**

```
strategy_enhancements_v2/
├── README.md                          # Framework documentation
├── daily_trend_hysteresis/
│   └── test_volume_filter.py         # Daily trend volume test
├── hourly_swing/
│   └── test_volume_filter.py         # Hourly swing RVOL test
└── results/
    ├── SUMMARY.md                     # ⭐ READ THIS FIRST
    ├── daily_trend_volume_test.csv    # Raw data
    └── hourly_swing_rvol_test.csv     # Raw data
```

---

## 🎯 **Quick Summary:**

### **Test 1: Daily Trend + Volume Filter**
- **Result:** No effect (volume always high on ETFs)
- **Status:** Inconclusive - need longer test period

### **Test 2: Hourly Swing + RVOL Filter** ⭐
- **Result:** 4x Sharpe improvement (0.13 → 0.54)
- **Status:** VERY PROMISING - extends testing recommended

---

## 🚀 **To Run Tests:**

```powershell
# Daily Trend test
python research\strategy_enhancements_v2\daily_trend_hysteresis\test_volume_filter.py

# Hourly Swing test
python research\strategy_enhancements_v2\hourly_swing\test_volume_filter.py
```

---

## 📊 **To View Results:**

1. **Quick view:** `research/strategy_enhancements_v2/results/SUMMARY.md`
2. **Raw data:** CSV files in `results/` folder

---

## 📝 **Next Steps:**

1. Read `results/SUMMARY.md` for detailed analysis
2. If interested, extend Hourly Swing test to 2020-2024
3. Consider deploying RVOL enhancement if multi-year test confirms

---

**Most Important Finding:**  
Hourly Swing + RVOL filter shows **4x Sharpe improvement** on limited testing. Worth investigating further!
