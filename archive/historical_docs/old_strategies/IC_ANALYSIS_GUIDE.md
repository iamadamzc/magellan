# IC Analysis Execution Guide

**For Agent**: Gemini 3 Pro (or equivalent)  
**Task**: Execute IC analysis to diagnose NVDA validation failures  
**Complexity**: Medium (data analysis, numerical interpretation)  
**Estimated Time**: 5-10 minutes

---

## **Context**

User is trying to build a profitable automatic trading system. Current blocker:
```
[NVDA] VALIDATION FAILED - Hit rate <51%
```

This means the alpha signals are worse than random. We need to find out WHY.

---

## **Your Task**

Execute the IC (Information Coefficient) analysis script to identify which features actually predict returns.

### **Step 1: Run the Script**

```bash
cd a:\1\Magellan
python inspect_ic.py
```

**Expected Runtime**: 2-5 minutes (depends on API speed)

---

## **What the Script Does**

1. Fetches 1 year of NVDA 5Min bar data from Alpaca
2. Generates features (RSI, volume_zscore, sentiment, etc.)
3. Calculates IC for each feature (Spearman correlation with 15-bar forward returns)
4. Interprets results and provides recommendations
5. Saves to `ic_analysis_results.csv`

---

## **Interpreting Results**

**IC (Information Coefficient)** = Spearman rank correlation between feature and future returns

| IC Range | Interpretation | Action |
|----------|---------------|--------|
| **IC > 0.05** | ⭐ STRONG - Predictive | **KEEP** this feature, increase weight |
| **0.02 < IC ≤ 0.05** | ✓ WEAK - Somewhat useful | Maybe keep if combined with others |
| **IC ≤ 0.02** | ❌ NOISE - Not predictive | **DELETE** this feature |

**Statistical Significance**: 
- p-value < 0.01 = Highly significant
- p-value < 0.05 = Significant
- p-value > 0.05 = Not significant (could be random)

---

## **Possible Outcomes & Next Steps**

### **Scenario A: All IC < 0.02** (Worst Case)
**Meaning**: Current strategy doesn't work. Features have no predictive power.

**Recommendations**:
1. Try different features (MACD, Bollinger Bands, order flow)
2. Try different timeframes (1Hour instead of 5Min)
3. Consider machine learning (XGBoost with more features)
4. **Report back to user**: "Strategy needs redesign, current features don't predict returns"

---

### **Scenario B: RSI has IC > 0.05, others < 0.02** (Likely)
**Meaning**: RSI works, but volume/sentiment are noise.

**Recommendations**:
1. Update `config/nodes/master_config.json`:
   ```json
   "alpha_weights": {
       "rsi_14": 0.95,
       "volume_zscore": 0.05,
       "sentiment": 0.0
   }
   ```
2. Delete volume_zscore feature entirely
3. Re-run backtest to verify improvement
4. **Report back to user**: "RSI is only predictive feature, recommend focusing on it"

---

### **Scenario C: Multiple features have IC > 0.05** (Best Case)
**Meaning**: Strategy has potential, just needs better weight optimization.

**Recommendations**:
1. Use optimizer to find best weights for strong features
2. Run longer backtest (30 days) to validate
3. **Report back to user**: "Multiple features work, ready to optimize weights"

---

## **Common Errors & Fixes**

### **Error: "No module named 'src.data_handler'"**
**Fix**: 
```bash
cd a:\1\Magellan
python inspect_ic.py  # Make sure you're in root directory
```

### **Error: "API key not found"**
**Check**: `.env` file exists with:
```
APCA_API_KEY_ID=...
APCA_API_SECRET_KEY=...
```

### **Error: "Empty API response"**
**Likely Cause**: Weekend or market closed, Alpaca has no recent data  
**Fix**: Script uses 1 year of data, should have enough historical bars regardless

---

## **After Running**

### **Report Format**

Provide user with:

1. **Summary Table**:
   ```
   Feature          IC        Significance
   ---------------- --------- ------------
   rsi_14           +0.0623   ⭐ STRONG
   volume_zscore    +0.0012   ❌ NOISE
   sentiment        -0.0089   ❌ NOISE
   ```

2. **Key Finding**: 
   - "RSI is the only predictive feature (IC = 0.06)"
   - Or "All features are noise, strategy needs redesign"
   - Or "Multiple strong features found"

3. **Next Step Recommendation**:
   - Update config weights
   - Or redesign strategy
   - Or run optimizer with strong features only

---

## **Files to Reference**

- **STATE.md** - Full system context
- **AUDIT_UPDATE_2026-01-14.md** - Recent improvements
- **CLI_GUIDE.md** - How to run backtests

---

## **If Something Breaks**

1. Check `debug_vault.log` - all backend errors logged there
2. Run with `--verbose` for more output: (N/A for this script, but good to know)
3. Report error to user with full traceback

---

## **Token Conservation**

This is a **data analysis task** - you (Gemini 3 Pro) are well-suited for it.  
Expected token usage: ~5-10K for execution + reporting.

---

**Ready to Execute!**

Run: `python inspect_ic.py`

Then report findings to user with clear recommendations.
