# ML Position Sizing - REVISED Quick Start

**Location:** `research/ml_position_sizing/`  
**Status:** Framework Ready (Corrected Labeling)  
**Created:** 2026-01-19

---

## ⚠️ **CRITICAL FIX: No Look-Ahead Bias Labeling**

**Original Approach (WRONG):**
- Label based on outcomes ("This trade won 2R, so call it ADD_ALLOWED")
- ❌ Conceptual look-ahead bias
- ❌ Teaches model to predict outcomes, not recognize regimes

**Corrected Approach (RIGHT):**
- Label based on ENTRY-TIME structure only
- ✅ No look-ahead bias
- ✅ Teaches model to recognize environments

**See:** `LABELING_PROTOCOL.md` for full explanation

---

## 🚀 **Quick Start (3 Steps)**

### **Step 1: Extract Historical Trades**
```powershell
cd a:\1\Magellan
python research\ml_position_sizing\scripts\extract_bear_trap_trades.py
```
**Time:** ~10 minutes  
**Output:** `data/bear_trap_trades_2020_2024.csv`  
**What it does:** Runs Bear Trap on 2020-2024, extracts all trades with entry-time features

---

### **Step 2: Label Trades (AUTOMATED - No Manual Work!)**
```powershell
python research\ml_position_sizing\scripts\label_regime_structural.py
```
**Time:** ~1 minute  
**Output:** `data/labeled_regimes.csv`  
**What it does:** 
- Calculates 5-component structural score (0-15 points)
- Maps to regime label (ADD_ALLOWED, ADD_NEUTRAL, NO_ADD)
- Validates correlation with outcomes
- Provides sanity checks

**5 Structural Components (All Entry-Time):**
1. **Trend Strength** - Higher highs count before entry
2. **Volatility Regime** - ATR percentile
3. **Volume Confirmation** - Volume vs 20-bar average
4. **Drop Severity** - How big was the drop (Bear Trap specific)
5. **Recent Performance** - Last 5 trades win rate (meta-level)

**Scoring:**
- 11-15 points → ADD_ALLOWED (strong setup)
- 7-10 points → ADD_NEUTRAL (mixed)
- 0-6 points → NO_ADD (weak setup)

---

### **Step 3: Validate Labels**
```powershell
# Review the output from Step 2
cat research\ml_position_sizing\data\validation_report.txt
```

**Check for:**
- ✅ ADD_ALLOWED avg R-multiple > NO_ADD avg R-multiple
- ✅ Quality score > 0
- ✅ Label distribution makes sense (~30% each)

**If validation FAILS:**
- ❌ Don't relabel based on outcomes!
- ✅ Revise structural features in `label_regime_structural.py`
- ✅ Re-run and validate again

---

## 📊 **Expected Validation Results**

**Good labeling looks like:**
```
ADD_ALLOWED:
  Avg R-multiple: +1.2
  Win rate: 65%

ADD_NEUTRAL:
  Avg R-multiple: +0.5
  Win rate: 55%

NO_ADD:
  Avg R-multiple: -0.2
  Win rate: 45%

Quality Score: +1.4 R ✅
```

**Bad labeling looks like:**
```
ADD_ALLOWED:
  Avg R-multiple: -0.5
  Win rate: 40%

NO_ADD:
  Avg R-multiple: +1.0
  Win rate: 60%

Quality Score: -1.5 R ⚠️ (features are backwards!)
```

---

## 🧠 **After Validation Passes:**

### **Step 4: Train ML Model** (Next session)
```powershell
python research\ml_position_sizing\scripts\train_regime_model.py
```
**What it does:**
- Trains decision tree on structural features
- Uses labeled data from Step 2
- Validates on holdout set

### **Step 5: Backtest** (Next session)
```powershell
python research\ml_position_sizing\scripts\backtest_ml_bear_trap.py
```
**What it does:**
- Runs Bear Trap with ML regime selection 
- Compares vs baseline
- Generates performance report

---

## 🎯 **Key Principle**

> **Labels describe the ENVIRONMENT at entry, not the RESULT after entry.**

**Analogy:**
- ✅ GOOD: "Storm clouds present" (observable now)
- ❌ BAD: "Will rain in 2 hours" (prediction)

**In Trading:**
- ✅ GOOD: "Strong trend + high volume + quick reclaim" (observable at entry)
- ❌ BAD: "This trade will win 2R" (outcome-based)

---

## ⚠️ **Common Pitfalls**

### **Pitfall 1: Relabeling Based on Outcomes**
```python
# ❌ WRONG
if trade_won_big:
    regime = 'ADD_ALLOWED'  # This is look-ahead bias!

# ✅ RIGHT
if structural_score >= 11:
    regime = 'ADD_ALLOWED'  # Based on entry conditions
```

### **Pitfall 2: Using Future Information**
```python
# ❌ WRONG - These are AFTER entry
if max_favorable_excursion > 5%:
    label = 'ADD_ALLOWED'

# ✅ RIGHT - These are AT/BEFORE entry
if volume_at_entry > avg_volume * 1.5:
    score += 2
```

### **Pitfall 3: Forcing Labels to Match Outcomes**
```python
# If validation fails:
# ❌ WRONG: Change labels to match outcomes
# ✅ RIGHT: Change structural features to better predict regime
```

---

## 📂 **File Structure**

```
ml_position_sizing/
├── README.md                          # Full framework
├── QUICK_START.md                     # This file
├── LABELING_PROTOCOL.md               # Critical fix explanation
├── data/
│   ├── bear_trap_trades_2020_2024.csv # ← Step 1 output
│   ├── labeled_regimes.csv            # ← Step 2 output
│   └── validation_report.txt          # ← Step 2 validation
└── scripts/
    ├── extract_bear_trap_trades.py    # ← Step 1
    ├── label_regime_structural.py     # ← Step 2 (CORRECTED)
    ├── train_regime_model.py          # ← Step 4 (to create)
    └── backtest_ml_bear_trap.py       # ← Step 5 (to create)
```

---

## 🔥 **What's Different from Original Plan?**

### **Original (Flawed):**
```
Step 2: Manual labeling based on outcomes
  ↓
"Trade won 2R → ADD_ALLOWED"
  ↓
Conceptual look-ahead bias
```

### **Corrected:**
```
Step 2: Automated structural scoring
  ↓
"Strong trend + high volume + quick reclaim → ADD_ALLOWED"
  ↓
No look-ahead bias
```

**Result:** 
- ✅ Faster (automated)
- ✅ More objective (scoring system)
- ✅ No bias (entry-time only)
- ✅ Reproducible (no subjective judgment)

---

## 📈 **Next Session (30-60 min)**

1. Run Step 1 (extract trades) - 10 min
2. Run Step 2 (label structurally) - 1 min
3. Review validation - 5 min
4. If validation passes → proceed to ML training
5. If validation fails → revise features and retry

---

**This corrected approach is bulletproof against look-ahead bias!** 🎯
