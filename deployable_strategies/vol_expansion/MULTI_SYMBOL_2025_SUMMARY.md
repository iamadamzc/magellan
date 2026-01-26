# MULTI-SYMBOL 2025 OUT-OF-SAMPLE VALIDATION RESULTS

**Test Period**: 2025 (full year)  
**Training Data**: Pre-2025 (2022-2024)  
**Symbols Tested**: SPY, QQQ, IWM, VOO  
**Date**: January 25, 2026

---

## 📊 **COMPLETE RESULTS TABLE**

| Symbol | **Sniper** | | | **Workhorse** | | | **Combined** | |
|--------|------------|---------|------------|---------------|---------|------------|--------------|----------|
| | Trades | Return | Expect | Trades | Return | Expect | Return | Total Trades |
| **SPY** | 26 | **+18.4%** | 0.346R | 3 | +0.9% | 0.321R | **+9.7%** | 29 |
| **QQQ** | 32 | **-13.8%** | -0.217R | 1 | -1.0% | -1.003R | **-7.4%** | 33 |
| **IWM** | 19 | **-5.9%** | -0.143R | 4 | +0.2% | 0.059R | **-2.8%** | 23 |
| **VOO** | 1 | **-0.6%** | -0.322R | 7 | +0.6% | 0.088R | **-0.0%** | 8 |

---

## 🎯 **KEY FINDINGS**

### 1. **SPY is the Clear Winner** ✅

**SPY Performance**:
- Sniper: 26 trades, +18.4% return, 0.346R expectancy
- Workhorse: 3 trades, +0.9% return, 0.321R expectancy
- Combined: **+9.7% return** on true OOS data

**SPY is the ONLY symbol with positive combined returns in 2025**

---

### 2. **QQQ Underperformed Significantly** ❌

**QQQ Performance**:
- Sniper: 32 trades, **-13.8% return**, negative expectancy
- Workhorse: Only 1 trade (insufficient)
- Combined: **-7.4% return**

**Why QQQ Failed**:
- 2025 may have been choppy for tech
- Sniper win rate dropped to 31.3% (vs 50% on SPY)
- Strategies trained on SPY may not transfer well to QQQ

---

### 3. **IWM Also Negative** ❌

**IWM Performance**:
- Sniper: 19 trades, **-5.9% return**
- Workhorse: 4 trades, +0.2% (barely positive)
- Combined: **-2.8% return**

**Small caps behaved differently in 2025**

---

### 4. **VOO Neutral** (Essentially Break-Even)

**VOO Performance**:
- Sniper: Only 1 trade (insufficient data)
- Workhorse: 7 trades, +0.6% return
- Combined: **-0.0%** (essentially flat)

**VOO tracks SPY closely but had fewer signals**

---

## 📈 **STRATEGY PERFORMANCE BY SYMBOL**

### Sniper Strategy

| Symbol | Trades | Win Rate | Expectancy | Return | Status |
|--------|--------|----------|------------|--------|--------|
| **SPY** | 26 | 50.0% | 0.346R | **+18.4%** | ✅ Excellent |
| QQQ | 32 | 31.3% | -0.217R | -13.8% | ❌ Failed |
| IWM | 19 | 31.6% | -0.143R | -5.9% | ❌ Failed |
| VOO | 1 | 0.0% | -0.322R | -0.6% | ⚠️ Insufficient |

**Sniper works ONLY on SPY in 2025**

---

### Workhorse Strategy

| Symbol | Trades | Win Rate | Expectancy | Return | Status |
|--------|--------|----------|------------|--------|--------|
| SPY | 3 | 33.3% | 0.321R | +0.9% | ⚠️ Low frequency |
| QQQ | 1 | 0.0% | -1.003R | -1.0% | ❌ Insufficient |
| IWM | 4 | 50.0% | 0.059R | +0.2% | ⚠️ Low frequency |
| **VOO** | 7 | 42.9% | 0.088R | **+0.6%** | ✅ Best Workhorse |

**Workhorse has very low frequency across all symbols**

---

## 💡 **CRITICAL INSIGHTS**

### 1. **SPY-Specific Strategy**

The strategies were discovered and trained on SPY data, and they **only work reliably on SPY**. This is not surprising but important to acknowledge.

**Implication**: Don't deploy to QQQ/IWM without retraining on those specific symbols.

---

### 2. **2025 Was Challenging for QQQ**

QQQ's -13.8% Sniper return suggests:
- Different market dynamics in 2025
- Tech sector may have been more volatile/choppy
- Trend filter may have kept QQQ below SMA(50) more often

---

### 3. **Workhorse Frequency Problem Persists**

Even across multiple symbols, Workhorse rarely triggers:
- SPY: 3 trades
- QQQ: 1 trade
- IWM: 4 trades
- VOO: 7 trades

**Total across 4 symbols**: Only 15 trades in all of 2025

---

### 4. **VOO Shows Promise for Workhorse**

VOO had the most Workhorse trades (7) and positive return (+0.6%). This suggests:
- VOO may be a better fit for Workhorse than SPY
- Consider using VOO for Workhorse deployment

---

## ✅ **DEPLOYMENT RECOMMENDATIONS**

### Option 1: SPY Only (Recommended)

**Deploy ONLY on SPY**:
- Sniper: Proven with +18.4% OOS return
- Workhorse: Accept low frequency (3 trades/year)
- Combined: +9.7% annual return

**Pros**: Validated, proven, simple  
**Cons**: Limited diversification

---

### Option 2: SPY + VOO Portfolio

**SPY**: Run Sniper only  
**VOO**: Run Workhorse only

**Rationale**:
- SPY Sniper: +18.4% (26 trades)
- VOO Workhorse: +0.6% (7 trades)
- Combined: More diversification, more signals

**Pros**: Better frequency, diversification  
**Cons**: More complex, VOO Workhorse needs more validation

---

### Option 3: Retrain for QQQ/IWM

**Before deploying to QQQ or IWM**:
1. Retrain Workhorse model on QQQ/IWM-specific data
2. Re-discover Sniper thresholds for those symbols
3. Validate on 2025 OOS data

**Pros**: Could unlock more opportunities  
**Cons**: Significant work, may not improve results

---

## 🚨 **WARNINGS**

1. **Do NOT deploy to QQQ with current parameters** - Lost 13.8% in 2025
2. **Do NOT deploy to IWM with current parameters** - Lost 5.9% in 2025
3. **Workhorse has insufficient signals** - Only 3-7 trades per symbol per year
4. **SPY is the only validated symbol** - Everything else needs more work

---

## 📌 **FINAL VERDICT**

### ✅ **READY FOR DEPLOYMENT**

**SPY Sniper Strategy**:
- 26 trades in 2025
- +18.4% return
- 50% win rate
- 0.346R expectancy
- **Status**: READY for paper trading

---

### ⚠️ **NEEDS MORE WORK**

**Workhorse Strategy (All Symbols)**:
- Too few signals (3-7 per year)
- Consider:
  - Loosening filters
  - Using VOO instead of SPY
  - Alternative cluster selection

**QQQ/IWM Strategies**:
- Both failed in 2025
- Need symbol-specific retraining
- Not recommended for deployment

---

## 📊 **SUMMARY STATISTICS**

### Across All Symbols (2025)

**Total Trades**: 93 (across 4 symbols)  
**Profitable Symbols**: 1 (SPY only)  
**Sniper Trades**: 78  
**Workhorse Trades**: 15

**Average Returns**:
- SPY: +9.7%
- QQQ: -7.4%
- IWM: -2.8%
- VOO: -0.0%

**Overall**: Only SPY is viable for deployment

---

**Test Date**: January 25, 2026  
**Conclusion**: Deploy **SPY Sniper only**. All other configurations need more work.
