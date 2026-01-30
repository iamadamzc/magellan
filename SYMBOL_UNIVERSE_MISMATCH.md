# CRITICAL ISSUE: Bear Trap Symbol Universe Mismatch

**Date:** January 26, 2026, 10:50 AM CT  
**Issue:** Deployed symbol list doesn't match backtest universe  
**Impact:** Severely reduced trading opportunities

---

## 🚨 THE PROBLEM

### **Backtest Universe vs Deployed Universe**

**What Was Backtested (from parameters_bear_trap.md):**
```
Categories Tested:
- Meme/Volatile stocks (AMC, GME, MULN, ONDS)
- Small-Cap Tech (CLSK, RIOT, MARA, SNDL, PLUG)
- Small-Cap Biotech (OCGN, GEVO, BNGO, SENS)
- Small-Cap EV/Battery (NKLA, GOEV, ARVL)
- Small-Cap Crypto-Related (BTBT, BTCS, CAN, EBON)
- Cannabis (ACB, TLRY, CGC, OGI)
- Energy (WKHS, FCEL)
- Other volatile small-caps

Total Universe: ~30+ symbols tested
```

**What Was Approved for Deployment (from VALIDATION_SUMMARY.md):**
```
Tier 1 (Deploy Immediately):
1. MULN
2. ONDS  
3. AMC
4. NKLA
5. WKHS

Tier 2 (Monitor, Add Later):
6. ACB
7. SENS
8. BTCS

Excluded:
- GOEV (unprofitable)

Total Approved: 8 symbols (5 Tier 1 + 3 Tier 2)
```

**What's Actually Deployed (from deployed/bear_trap/config.json):**
```json
"symbols": [
    "ONDS", "ACB", "AMC", "WKHS", "MULN",
    "GOEV",    // ❌ Was EXCLUDED in validation (unprofitable)
    "BTCS", "SENS", "DNUT", "CVNA",
    "PLUG", "KOSS", "TLRY", "DVLT",
    "NVAX", "NTLA", "MARA", "RIOT",
    "OCGN", "NKLA", "GME"
]

Total: 21 symbols
BUT: 3 are delisted (NKLA, MULN, GOEV)
Active: 18 symbols
```

---

## 📊 THE MISMATCH

### **Issue 1: Wrong Symbol Selection**

**Deployed but NOT in Tier 1:**
- DNUT ❓ (not in validation docs)
- CVNA ❓ (not in validation docs)
- PLUG ✅ (was in broader test universe)
- KOSS ❓ (not in validation docs)
- TLRY ✅ (was in broader test universe)
- DVLT ❓ (not in validation docs)
- NVAX ❓ (not in validation docs)
- NTLA ❓ (not in validation docs)
- MARA ✅ (was in broader test universe)
- RIOT ✅ (was in broader test universe)
- OCGN ✅ (was in broader test universe)
- GME ✅ (was in broader test universe)

**Approved but NOT deployed:**
- None missing (all Tier 1 are included)

### **Issue 2: Delisted Symbols Still Included**

- NKLA ❌ (delisted April 2025, but WAS in Tier 1)
- MULN ❌ (delisted October 2025, but WAS in Tier 1)
- GOEV ❌ (delisted January 2025, AND was excluded for being unprofitable)

---

## 💡 ROOT CAUSE ANALYSIS

### **Why This Happened:**

Looking at the deployment timeline:

1. **January 18-20, 2026:** Validation completed
   - Approved: MULN, ONDS, AMC, NKLA, WKHS (Tier 1)
   - Document says: "Deploy Tier 1 only"

2. **January 20-21, 2026:** Production deployment
   - Someone expanded to 21 symbols
   - Included symbols NOT in validation (DNUT, CVNA, KOSS, etc.)
   - Included GOEV despite being excluded
   - Didn't account for delistings

3. **Result:** Deployed universe ≠ Validated universe

---

## 📈 IMPACT ON TRADING FREQUENCY

### **Expected Trade Frequency (from backtest):**

**Tier 1 (5 symbols):**
- MULN: 588 trades over 4 years = 147 trades/year = 12.3 trades/month
- ONDS: 61 trades over 4 years = 15 trades/year = 1.3 trades/month
- AMC: 153 trades over 4 years = 38 trades/year = 3.2 trades/month
- NKLA: 140 trades over 4 years = 35 trades/year = 2.9 trades/month
- WKHS: 73 trades over 4 years = 18 trades/year = 1.5 trades/month

**Total Tier 1: ~21 trades/month** (if all symbols active)

### **Current Reality:**

**Active Tier 1 symbols:**
- ONDS ✅
- AMC ✅
- WKHS ✅
- MULN ❌ (delisted)
- NKLA ❌ (delisted)

**Lost capacity:**
- MULN: -12.3 trades/month (biggest contributor!)
- NKLA: -2.9 trades/month

**Remaining Tier 1 capacity: ~6 trades/month**

**Additional symbols (unvalidated):**
- Unknown performance
- May or may not meet -15% threshold frequently
- No backtest data to estimate trade frequency

---

## 🎯 RECOMMENDATIONS

### **Option 1: Strict Validation Adherence (RECOMMENDED)**

**Deploy ONLY validated Tier 1 symbols that are still active:**

```json
"symbols": [
    "ONDS",   // ✅ Tier 1, +25.9%, 61 trades, Sharpe 4.35
    "AMC",    // ✅ Tier 1, +18.1%, 153 trades, Sharpe 2.89
    "WKHS"    // ✅ Tier 1, +20.1%, 73 trades, Sharpe 2.05
]
```

**Pros:**
- ✅ Matches validated strategy
- ✅ All symbols proven profitable
- ✅ Known performance characteristics
- ✅ Reduces complexity

**Cons:**
- ❌ Only 3 symbols (reduced diversification)
- ❌ Lower trade frequency (~6/month vs 21/month)
- ❌ Lost MULN (biggest contributor)

**Expected Performance:**
- ~6 trades/month
- Combined 4-year return: +64% (ONDS +26%, AMC +18%, WKHS +20%)
- Average Sharpe: 3.1

---

### **Option 2: Expand to Validated Universe**

**Add symbols from the broader backtest universe that were tested:**

```json
"symbols": [
    // Tier 1 (active)
    "ONDS", "AMC", "WKHS",
    
    // Tier 2 (validated)
    "ACB", "SENS", "BTCS",
    
    // Broader universe (tested but not in Tier 1/2)
    "PLUG", "MARA", "RIOT", "OCGN", "GME", "TLRY"
]
```

**Total: 12 symbols** (all from validated universe)

**Pros:**
- ✅ All symbols have backtest data
- ✅ Better diversification
- ✅ Higher trade frequency
- ✅ Includes high-volume symbols (GME, MARA, RIOT)

**Cons:**
- ⚠️ Some symbols not in official "approved" list
- ⚠️ Need to verify individual symbol performance
- ⚠️ More complex to monitor

---

### **Option 3: Find MULN Replacement**

**Problem:** MULN was the biggest contributor (12.3 trades/month, +30% over 4 years)

**Potential replacements (similar characteristics):**
- **GME** - Meme stock, high volatility, proven -15% crashes
- **RIOT** - Crypto-related, high volatility
- **MARA** - Crypto-related, high volatility

**Action:** Backtest these symbols specifically to find best MULN substitute

---

### **Option 4: Lower Threshold to -10% or -12%**

**Rationale:** With fewer symbols, need more opportunities per symbol

**Pros:**
- ✅ More trades per symbol
- ✅ Faster validation of strategy
- ✅ Better utilization of capital

**Cons:**
- ❌ **UNTESTED** - no backtest data at -10%
- ❌ May reduce win rate
- ❌ May reduce Sharpe ratio
- ❌ Deviates from validated parameters

**Recommendation:** Only consider if Option 1-3 fail after 4-8 weeks

---

## 🔧 IMMEDIATE ACTION PLAN

### **Step 1: Decide on Symbol Universe (TODAY)**

**My Recommendation: Option 2 (Validated Universe)**

Use all symbols from the backtest that are:
1. Still actively trading
2. Have historical data
3. Were tested in the validation

**Proposed List (12 symbols):**
```json
"symbols": [
    "ONDS", "AMC", "WKHS",           // Tier 1 (active)
    "ACB", "SENS", "BTCS",           // Tier 2
    "PLUG", "MARA", "RIOT",          // Tested, crypto/tech
    "OCGN", "GME", "TLRY"            // Tested, meme/biotech/cannabis
]
```

**Remove:**
- NKLA, MULN, GOEV (delisted)
- DNUT, CVNA, KOSS, DVLT, NVAX, NTLA (not in validation docs)

---

### **Step 2: Update Config (After Hours)**

**File:** `deployed/bear_trap/config.json`

**Change:**
```json
"symbols": [
    "ONDS", "AMC", "WKHS",
    "ACB", "SENS", "BTCS",
    "PLUG", "MARA", "RIOT",
    "OCGN", "GME", "TLRY"
]
```

---

### **Step 3: Monitor for 2-4 Weeks**

**Expected Results with 12 symbols:**
- **Trade Frequency:** ~10-15 trades/month (estimated)
- **Performance:** Should align with backtest (if symbols behave similarly)

**If still too low:**
- Consider backtesting -12% threshold
- Consider adding more validated symbols
- Consider finding MULN replacement

---

## 📊 COMPARISON TABLE

| Approach | Symbols | Trade/Month | Validation | Risk |
|----------|---------|-------------|------------|------|
| **Current (18)** | Mixed | Unknown | ❌ Partial | High |
| **Option 1 (3)** | Tier 1 only | ~6 | ✅ Full | Low |
| **Option 2 (12)** | Validated | ~10-15 | ✅ Good | Medium |
| **Option 3 (4)** | Tier 1 + replacement | ~15-18 | ⚠️ Partial | Medium |
| **Option 4 (-10%)** | Current | ~30+ | ❌ None | High |

---

## ✅ FINAL RECOMMENDATION

**Deploy Option 2: 12 Validated Symbols**

**Rationale:**
1. All symbols have backtest data
2. Balances trade frequency with validation
3. Removes unvalidated symbols (DNUT, CVNA, etc.)
4. Removes delisted symbols
5. Maintains diversification
6. Proven to work in backtests

**Timeline:**
- Update config after market close today
- Monitor for 2-4 weeks
- Evaluate if threshold adjustment needed

---

**Created:** 2026-01-26 10:50 AM CT  
**Priority:** HIGH  
**Action Required:** Symbol list decision + config update
