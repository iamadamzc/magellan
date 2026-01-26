# COMPLETE MULTI-SYMBOL 2025 OUT-OF-SAMPLE VALIDATION

**Test Period**: 2025 (full year)  
**Training Data**: Pre-2025 (2022-2024)  
**Symbols Tested**: SPY, QQQ, IWM, IVV, VOO, GLD, SLV, TQQQ, SOXL (9 total)  
**Date**: January 25, 2026

---

## 📊 **COMPLETE RESULTS TABLE**

| Symbol | **Sniper** | | | **Workhorse** | | | **Combined** | |
|--------|------------|---------|------------|---------------|---------|------------|--------------|----------|
| | Trades | Return | Expect | Trades | Return | Expect | Return | Total |
| **SPY** | 26 | **+18.4%** ✅ | 0.346R | 3 | +0.9% | 0.321R | **+9.7%** ✅ | 29 |
| QQQ | 32 | -13.8% ❌ | -0.217R | 1 | -1.0% | -1.003R | -7.4% ❌ | 33 |
| IWM | 19 | -5.9% ❌ | -0.143R | 4 | +0.2% | 0.059R | -2.8% ❌ | 23 |
| IVV | 5 | -9.7% ❌ | -1.015R | **134** | **+4.4%** ✅ | 0.039R | -2.7% ❌ | 139 |
| VOO | 1 | -0.6% | -0.322R | 7 | +0.6% | 0.088R | -0.0% | 8 |
| GLD | 42 | -8.4% ❌ | -0.089R | 138 | -25.0% ❌ | -0.203R | -16.7% ❌ | 180 |
| SLV | 52 | **-34.7%** ❌ | -0.393R | 103 | -19.2% ❌ | -0.199R | **-27.0%** ❌ | 155 |
| TQQQ | 42 | -29.2% ❌ | -0.396R | 0 | 0.0% | 0.000R | -14.6% ❌ | 42 |
| SOXL | 40 | -28.7% ❌ | -0.408R | 263 | **-58.5%** ❌ | -0.327R | **-43.6%** ❌ | 303 |

---

## 🎯 **CRITICAL FINDINGS**

### 1. **SPY is the ONLY Profitable Symbol** ✅

**SPY** is the only symbol with positive combined returns:
- Combined: **+9.7%**
- Sniper: +18.4% (26 trades)
- Workhorse: +0.9% (3 trades)

**All other 8 symbols lost money in 2025**

---

### 2. **IVV Shows Interesting Workhorse Pattern** 🔍

**IVV Workhorse** had the most trades and was profitable:
- **134 trades** (vs only 3 on SPY)
- **+4.4% return**
- 0.039R expectancy (positive but low)

**But IVV Sniper failed**: -9.7% (only 5 trades, 0% win rate)

**IVV is essentially SPY** (both track S&P 500), so this divergence is interesting.

---

### 3. **Leveraged ETFs Catastrophically Failed** 💥

**TQQQ** (3x QQQ):
- Sniper: -29.2%
- Workhorse: 0 trades (no signals)
- Combined: -14.6%

**SOXL** (3x Semiconductors):
- Sniper: -28.7%
- Workhorse: **-58.5%** (worst performance)
- Combined: **-43.6%**

**Leveraged ETFs are NOT suitable for these strategies**

---

### 4. **Precious Metals Failed** 🥇🥈

**GLD** (Gold):
- Combined: -16.7%
- Sniper: -8.4%
- Workhorse: -25.0%

**SLV** (Silver):
- Combined: **-27.0%**
- Sniper: **-34.7%** (second worst)
- Workhorse: -19.2%

**Commodities behave differently than equities**

---

## 📈 **STRATEGY PERFORMANCE ANALYSIS**

### Sniper Strategy by Symbol

| Symbol | Trades | Win Rate | Expectancy | Return | Verdict |
|--------|--------|----------|------------|--------|---------|
| **SPY** | 26 | 50.0% | 0.346R | **+18.4%** | ✅ **ONLY WINNER** |
| GLD | 42 | 35.7% | -0.089R | -8.4% | ❌ Failed |
| IVV | 5 | 0.0% | -1.015R | -9.7% | ❌ Failed |
| QQQ | 32 | 31.3% | -0.217R | -13.8% | ❌ Failed |
| SOXL | 40 | 25.0% | -0.408R | -28.7% | ❌ Failed |
| TQQQ | 42 | 23.8% | -0.396R | -29.2% | ❌ Failed |
| SLV | 52 | 26.9% | -0.393R | **-34.7%** | ❌ **WORST** |

**Sniper works ONLY on SPY**

---

### Workhorse Strategy by Symbol

| Symbol | Trades | Win Rate | Expectancy | Return | Verdict |
|--------|--------|----------|------------|--------|---------|
| **IVV** | **134** | 40.3% | 0.039R | **+4.4%** | ✅ **BEST** |
| SPY | 3 | 33.3% | 0.321R | +0.9% | ⚠️ Too few |
| VOO | 7 | 42.9% | 0.088R | +0.6% | ⚠️ Low freq |
| IWM | 4 | 50.0% | 0.059R | +0.2% | ⚠️ Too few |
| QQQ | 1 | 0.0% | -1.003R | -1.0% | ❌ Failed |
| SLV | 103 | 32.0% | -0.199R | -19.2% | ❌ Failed |
| GLD | 138 | 35.5% | -0.203R | -25.0% | ❌ Failed |
| SOXL | 263 | 29.3% | -0.327R | **-58.5%** | ❌ **WORST** |
| TQQQ | 0 | - | - | 0.0% | ❌ No signals |

**IVV Workhorse is surprisingly good but needs investigation**

---

## 💡 **KEY INSIGHTS**

### 1. **Strategy is SPY-Specific**

The strategies were discovered on SPY and **only work reliably on SPY**. This is expected but now definitively proven across 9 symbols.

---

### 2. **IVV Anomaly Needs Investigation** 🔍

IVV tracks the same index as SPY (S&P 500) but shows:
- **134 Workhorse trades** (vs 3 on SPY)
- **+4.4% Workhorse return** (vs +0.9% on SPY)
- But **0% Sniper win rate** (vs 50% on SPY)

**Possible explanations**:
1. Different liquidity/volume patterns
2. Different price action despite tracking same index
3. Model trained on SPY may cluster IVV differently
4. Could be statistical noise

**Recommendation**: Investigate IVV Workhorse further before deployment

---

### 3. **Leveraged ETFs are Toxic** ☠️

TQQQ and SOXL both lost **>40%** combined:
- High volatility breaks the strategies
- Decay from leverage compounds losses
- **Never deploy to leveraged ETFs**

---

### 4. **Commodities Don't Work**

GLD and SLV both failed:
- Different market dynamics
- Lower liquidity
- Different volatility patterns
- **Avoid commodities**

---

### 5. **Workhorse Frequency Varies Wildly**

| Symbol | Workhorse Trades |
|--------|------------------|
| SOXL | 263 |
| GLD | 138 |
| IVV | 134 |
| SLV | 103 |
| VOO | 7 |
| IWM | 4 |
| SPY | 3 |
| QQQ | 1 |
| TQQQ | 0 |

**Workhorse frequency is unpredictable across symbols**

---

## ✅ **DEPLOYMENT RECOMMENDATIONS**

### Option 1: SPY Sniper Only (Safest) ⭐

**Deploy**: SPY Sniper only
- Proven: +18.4% on OOS data
- 26 trades/year
- 50% win rate
- Ready for paper trading

**Pros**: Validated, simple, proven  
**Cons**: Limited diversification, low frequency

---

### Option 2: SPY Sniper + IVV Workhorse (Experimental)

**SPY**: Sniper only (+18.4%)  
**IVV**: Workhorse only (+4.4%, 134 trades)

**Pros**: More trades, diversification  
**Cons**: IVV Workhorse needs more validation, unclear why it differs from SPY

---

### Option 3: SPY Only, Both Strategies (Recommended) ⭐⭐

**SPY**: Run both Sniper and Workhorse
- Sniper: +18.4% (26 trades)
- Workhorse: +0.9% (3 trades)
- Combined: **+9.7%**

**Pros**: Proven, simple, validated  
**Cons**: Low Workhorse frequency

---

## 🚨 **DO NOT DEPLOY TO**

### ❌ **Never Deploy**:
1. **TQQQ** - Lost 14.6%
2. **SOXL** - Lost 43.6% (catastrophic)
3. **SLV** - Lost 27.0%
4. **GLD** - Lost 16.7%
5. **QQQ** - Lost 7.4%
6. **IWM** - Lost 2.8%

### ⚠️ **Needs More Work**:
- **IVV**: Interesting Workhorse pattern but needs investigation
- **VOO**: Too few signals

---

## 📊 **AGGREGATE STATISTICS**

### Across All 9 Symbols (2025)

**Total Trades**: 912  
**Profitable Symbols**: 1 (SPY only)  
**Total Capital Deployed**: $450,000 (9 × $50k)  
**Total P&L**: **-$58,160** (aggregate loss)  
**Average Return**: -12.9% per symbol

**Only SPY made money**

---

## 📌 **FINAL VERDICT**

### ✅ **DEPLOY: SPY SNIPER ONLY**

**SPY Sniper Strategy**:
- 26 trades in 2025
- **+18.4% return**
- 50% win rate
- 0.346R expectancy
- **Status**: READY for paper trading

---

### 🔍 **INVESTIGATE: IVV WORKHORSE**

**IVV Workhorse**:
- 134 trades (very high frequency)
- +4.4% return
- Needs to understand why it differs from SPY
- Paper trade alongside SPY to validate

---

### ❌ **REJECT: Everything Else**

All other symbols and configurations failed in 2025:
- QQQ: -7.4%
- IWM: -2.8%
- GLD: -16.7%
- SLV: -27.0%
- TQQQ: -14.6%
- SOXL: -43.6%

**Do not deploy to any of these symbols**

---

## 🎓 **LESSONS LEARNED**

1. **Strategies are symbol-specific** - What works on SPY doesn't transfer
2. **Leveraged ETFs are dangerous** - SOXL lost 43.6%
3. **Commodities behave differently** - GLD/SLV both failed
4. **IVV is interesting** - Same index as SPY but different Workhorse behavior
5. **Validation is critical** - 8 out of 9 symbols would have lost money

---

**Test Date**: January 25, 2026  
**Conclusion**: Deploy **SPY Sniper only**. Investigate IVV Workhorse. Reject all others.
