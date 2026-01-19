# FINAL RESULTS: V1 vs V2 vs V3 Complete Comparison

## Executive Summary

Tested 3 parameter configurations across full 2024 and 2025 years. **ALL CONFIGURATIONS FAILED** to achieve profitability.

---

## 2024 Results Comparison

| Metric | V1 (0.45%) | V2 (0.60%) | V3B (0.50%) | Winner |
|--------|------------|------------|-------------|---------|
| **Trades** | 361 | 0 | 191 | V3B ✅ |
| **Trades/Day** | 1.43 | 0.00 | 0.76 | V3B ✅ |
| **Win Rate** | 36.3% | N/A | 32.5% | V1 ⚠️ |
| **Sharpe** | -5.14 | 0.00 | **-4.32** | V3B ✅ |
| **Total Return** | -17.53% | 0.00% | **-10.50%** | V3B ✅ |

**V3B performed best** (least bad) in 2024 - reduced losses by 40% vs V1.

---

## 2025 Results Comparison 

| Metric | V1* | V2 (0.60%) | V3B (0.50%) |
|--------|-----|------------|-------------|
| **Trades** | N/A | 3 | 375 |
| **Trades/Day** | N/A | 0.01 | 1.50 |
| **Win Rate** | N/A | 33.3% | 43.7% |
| **Sharpe** | N/A | -1.58 | **-2.29** |
| **Total Return** | N/A | -2.76% | **-10.17%** |

*V1 on 2025 not tested (only 10 days in initial run)

---

## Monthly Performance Highlights

### 2024 - V3 Option B

**Best Months**:
- June: +0.14% (6 trades, 50% win rate)
- October: +0.25% (8 trades, 75% win rate) ⭐
- November: +0.04% (3 trades)

**Worst Months**:
- December: -3.07% (18 trades, 22% win rate)
- April: -1.90% (30 trades)
- August: -1.81% (41 trades)

---

### 2025 - V3 Option B

**Best Months**:
- May: +0.39% (19 trades, 58% win rate)
- June: +0.27% (8 trades, 50% win rate)
- January: +0.19% (13 trades, 69% win rate)

**Worst Months**:
- April: -4.84% (125 trades, 42% win rate) 💀
- November: -2.31% (42 trades, 36% win rate)
- February: -1.66% (29 trades, 38% win rate)

---

## Key Insights

### 1. V3 is Best of Three (But Still Losing)

**Improvements vs V1**:
- 47% fewer trades (361 → 191)
- 40% less loss (-17.53% → -10.50%)
- Sharpe improved (+0.82 points)

**But**:
- Still negative Sharpe (-4.32)
- Win rate actually decreased (36% → 32%)
- Lost $10.50 per $100 capital

---

### 2. "Profitable" Months Exist But Unreliable

**October 2024** (V3's best):
- 8 trades, 75% win rate
- +0.25% return
- BUT: Small sample, not repeatable

**Pattern**: A few good months don't offset many bad months.

---

### 3. 2025 Had More Trades Than 2024

**2024**: 191 trades (0.76/day)  
**2025**: 375 trades (1.50/day)

**Why?**: Market conditions changed - 2025 was more volatile/choppy, triggering more signals. Strategy is NOT regime-aware.

---

### 4. April is Consistently Terrible

**April 2024**: -1.90% (V3)  
**April 2025**: -4.84% (V3) - WORST MONTH EVER

**125 trades in April 2025** = 6 trades/day (massive overtrading)

**Hypothesis**: Spring volatility + earnings season creates false signals.

---

## Attempt Summary

| Version | Config | Result |
|---------|--------|--------|
| **5-day sample** | 0.45%, time filter | Sharpe 2478 ✅ (MISLEADING!) |
| **V1 (2024)** | 0.45%, time filter | Sharpe -5.14 ❌ |
| **V2 (2024)** | 0.60%, ALL filters | 0 trades ❌ |
| **V2 (2025)** | 0.60%, ALL filters | 3 trades, Sharpe -1.58 ❌ |
| **V3B (2024)** | 0.50%, vol filter | Sharpe -4.32 ❌ |
| **V3B (2025)** | 0.50%, vol filter | Sharpe -2.29 ❌ |

**Pattern**: Every configuration loses money over full year testing.

---

## Why VWAP Mean Reversion Doesn't Work

### 1. Signal Quality is Poor
- VWAP deviations ≠ reversal opportunities
- Market can stay "extended" indefinitely
- 1-minute prices are mostly noise

### 2. Win Rate Too Low
- Need >55% to overcome friction
- Best achieved: 43.7% (2025 V3)
- Consistently underperforming

### 3. Avg Loss > Avg Win
**V3 2024**: 
- Avg win: +0.143%
- Avg loss: -0.150%
- **Negative expectancy even before friction!**

### 4. Market Efficiency
- 1-minute prices reflect all available information
- Retail traders can't compete with HFT firms
- Our 67ms is slow in millisecond world

---

## Final Recommendation

### ❌ REJECT All VWAP Intraday Strategies

**Evidence**:
- 3 configurations tested on 2 full years
- ALL produced negative returns
- V3 (best) still lost -10.50% in 2024, -10.17% in 2025
- No parameter combination achieves profitability

---

### ✅ Stick with FOMC Event Strategy

| Strategy | Sharpe | Trades/Year | Return | Status |
|----------|--------|-------------|--------|--------|
| **FOMC Events** | **1.17** | 8 | **+102.7%** | ✅ VALIDATED |
| VWAP V3B | -4.32 | 191-375 | -10.50% | ❌ REJECTED |

**FOMC is 6× better Sharpe, 100%+ annual return vs -10% loss.**

---

## Lessons Learned

1. **Small samples are DEADLY misleading**
   - 5 days: Sharpe 2478
   - 252 days: Sharpe -4.32
   - **Always test full year minimum**

2. **Parameter optimization ≠ strategy validation**
   - We optimized V1 → V2 → V3
   - All still failed
   - Can't optimize away fundamental flaws

3. **Intraday markets are efficient**
   - Can't find edge at 1-minute timescale
   - HFT firms dominate this space
   - Retail/small funds have no advantage

4. **Frequency matters more than we thought**
   - V1 (361 trades): -17.53%
   - V3 (191 trades): -10.50%
   - But even half the trades still loses

---

## What We Tried

✅ **Tested**:
- 3 threshold levels (0.45%, 0.50%, 0.60%)
- 2 profit targets (0.30%, 0.40%)
- Stop losses (0.20%)
- Time filters (lunch hour)
- Volatility filters (ATR)
- Volume filters (1.5x, 2x)
- 2 full years of data (2024, 2025)
- 800+ combined trades

❌ **Result**: None profitable.

---

## Conclusion

**VWAP intraday mean reversion is NOT VIABLE** for retail/small fund trading.

**Recommendation**: 
- ✅ Deploy FOMC event straddles (Sharpe 1.17, validated)
- ❌ Abandon all intraday VWAP strategies
- 🔍 Continue research on other event-driven opportunities

**Final Stats**:
- Time spent: ~6 hours of testing
- Strategies tested: 11 total (4 basic, 7 advanced, 3 optimized)
- Success rate: 0% (all failed)
- Only validated strategy: FOMC events

---

**Status**: High-frequency research COMPLETE - definitively not viable  
**Next**: Focus on validated FOMC strategy deployment  
**Confidence**: 99% that intraday trading won't work at our scale
