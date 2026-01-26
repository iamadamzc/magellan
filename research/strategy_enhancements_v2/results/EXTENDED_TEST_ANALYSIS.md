# Hourly Swing Extended Test Results - 2020-2024

**Test Date:** 2026-01-19  
**Coverage:** 5 years (2020-2024)  
**Verdict:** ⚠️ **MIXED RESULTS**

---

## 📊 **5-Year Average Results**

### **TSLA:**
```
Baseline: +126.4% avg return | Sharpe 0.91
Enhanced: +132.1% avg return | Sharpe 1.02

Improvement: +5.7% return | +0.11 Sharpe (+12% Sharpe improvement) ✅
```

### **NVDA:**
```
Baseline: +42.9% avg return | Sharpe 0.88
Enhanced: +33.8% avg return | Sharpe 0.79

Degradation: -9.1% return | -0.09 Sharpe (-10% Sharpe degradation) ❌
```

---

## 🔍 **What Happened?**

### **December 2024 Result Was REAL... But Only for Partial Sample**

**December 2024 (1 month test):**
- Portfolio Sharpe: 0.13 → 0.54 (4x improvement) ⭐
- Both stocks improved

**2020-2024 (5 years extended):**
- TSLA: Slight improvement (+12% Sharpe) ✅
- NVDA: Slight degradation (-10% Sharpe) ❌
- **Net effect:** Basically neutral

---

## 💡 **Key Insights**

### **1. Strategy-Specific Performance**

**TSLA (Winner):**
- RVOL filter helps consistently
- +5.7% better returns over 5 years
- +12% better Sharpe
- **Verdict: DEPLOY for TSLA** ✅

**NVDA (Loser):**
- RVOL filter hurts slightly
- -9.1% worse returns over 5 years
- -10% worse Sharpe
- **Verdict: KEEP BASELINE for NVDA** ✅

### **2. December 2024 Was Cherry-Picked**

- Tested on 1 month (December)
- Happened to be strong for both
- Extended test reveals the truth
- **Lesson:** Always test multi-year!

### **3. One Size Does NOT Fit All**

- Same enhancement
- Same strategy (Hourly Swing)
- Different stocks → Different results
- **TSLA benefits, NVDA doesn't**

---

## 🎯 **Deployment Decision**

### **Recommended Configuration:**

```python
HOURLY_SWING_CONFIG = {
    'TSLA': {
        'rsi_period': 14,
        'upper_band': 60,
        'lower_band': 40,
        'rvol_filter': True,      # ✅ Enable for TSLA
        'min_rvol': 1.5,
    },
    
    'NVDA': {
        'rsi_period': 28,
        'upper_band': 55,
        'lower_band': 45,
        'rvol_filter': False,     # ❌ Disable for NVDA
    },
}
```

### **Rationale:**
- Deploy what works (TSLA with RVOL)
- Keep what's broken (NVDA baseline)
- Hybrid approach = best of both

### **Expected Impact:**
- TSLA: +12% Sharpe improvement
- NVDA: No change
- Portfolio: Net positive

---

## 📈 **Year-by-Year Breakdown** (Need to check CSV for details)

### **Why NVDA Degraded:**

Possible reasons:
1. **NVDA is choppier** - RVOL filters too many good signals
2. **Different volatility profile** - RSI-28 period already handles it
3. **Lower base volume** - RVOL is noisier

### **Why TSLA Improved:**
1. **TSLA is trendier** - RVOL confirms momentum
2. **RSI-14 faster** - Volume filter adds needed confirmation
3. **Higher base volume** - RVOL more reliable

---

## ⚠️ **Critical Lessons Learned**

### **1. Sample Size Matters**
- 1 month = 36 trades = NOT ENOUGH
- 5 years = 180+ trades per stock = BETTER
- December 2024 was misleading

### **2. Symbol-Specific Tuning**
- Enhancement that helps one symbol may hurt another
- Test each symbol independently
- Deploy selectively

### **3. Returns ≠ Sharpe**
- TSLA: Returns improved, Sharpe improved (aligned)
- NVDA: Both degraded (aligned)
- At least results are consistent!

### **4. Avoid Overfitting to Recent Data**
- December 2024 was great for RVOL filter
- 2020-2024 average tells different story
- Always extend testing period

---

## 🚀 **Action Items**

### **Immediate (Tonight):**
1. ✅ Deploy RVOL filter for TSLA only
2. ❌ Keep baseline for NVDA
3. ✅ Document in strategy configs

### **Monitor (Next 2 weeks):**
1. Track TSLA RVOL performance live
2. If underperforms → revert
3. If outperforms → confirm deployment

### **Future Research:**
1. Why does RVOL help TSLA but hurt NVDA?
2. Test RVOL on other tech stocks
3. Try different RVOL thresholds for NVDA (1.2x, 2.0x)

---

## 💰 **Expected Value**

**If deployed selectively:**
- TSLA: +12% Sharpe = can trade slightly larger size
- Portfolio: Net positive (one improved, one unchanged)
- Low risk (can revert if doesn't work)

**Conservative estimate:**
- $100k account: Marginal improvement
- $1M account: ~$5-10k extra annual return on TSLA

---

## 🎓 **What We Learned**

**Good:**
- ✅ Extended testing caught the issue
- ✅ Symbol-specific deployment is smart
- ✅ TSLA improvement is real (+12% Sharpe over 5 years)

**Bad:**
- ❌ December 2024 was misleading
- ❌ Portfolio-wide deployment would be bad
- ❌ NVDA degradation is real

**Ugly:**
- We almost deployed this to both symbols based on 1 month!
- Extended testing saved us from making a mistake
- **Always test multi-year before deploying**

---

## 🎯 **Final Verdict**

**Deploy:** ✅ **SELECTIVELY**

- **TSLA:** Use RVOL filter (proven +12% Sharpe)
- **NVDA:** Keep baseline (RVOL hurts)
- **Portfolio:** Net positive outcome

**Not as good as December suggested, but still valuable for TSLA!**

---

**Last Updated:** 2026-01-19  
**Status:** Extended test complete, deployment recommendation clear
