# High-Frequency Trading Research - Final Summary

**Date**: 2026-01-16  
**Objective**: Systematically test HFT strategies to find profitable 1-minute trading opportunities  
**Friction**: 1.0 bps (0.01%) per round-trip trade (realistic)  
**Validation Standard**: Full year testing (252+ days) required

---

## Executive Summary

**CRITICAL FINDING**: All HFT strategies tested showed **severe sample bias**. Strategies that appeared profitable on 30-day samples (Q1 2024) consistently **failed when tested on full years** (2024 + 2025).

**Conclusion**: **NO HFT STRATEGY IS VIABLE** with realistic friction costs and residential latency.

---

## Testing Methodology

### Phase 1: Multi-Asset Screening (Q1 2024, ~30 days)
- Test strategy on 7 asset classes: SPY, QQQ, IWM, NVDA, TSLA, ES, NQ
- Identify best-performing asset
- **Problem**: 30-day samples showed false positives

### Phase 2: Full-Year Validation (2024 + 2025, 504 days)
- Test best asset on full 2024 (252 days)
- Test best asset on full 2025 (252 days)
- Calculate average Sharpe ratio
- **Result**: All strategies failed

### Key Learning
**Sample size matters critically**:
- 30 days: High variance, false positives
- 252 days: True performance revealed
- **Minimum 100+ days required** for any confidence

---

## Strategy Results

### 1. Liquidity Grab / Stop Run ❌

**Concept**: Fade breakouts, trade liquidity grabs and stop runs

**Q1 2024 Multi-Asset Results**:
- Best asset: **QQQ** (Sharpe 0.84)
- SPY: Sharpe -2.57
- ES: Sharpe -2.69
- Others: All negative

**Full Year Validation (QQQ)**:
- Q1 2024: Sharpe 0.84 ✅
- Full 2024: Sharpe **-2.45** ❌
- Full 2025: Sharpe **-1.38** ❌
- **Average: Sharpe -1.91** (FAILED)

**Why it failed**:
- Win rate collapsed from 58.8% (Q1) to 38.5% (full year)
- August 2024: 88 trades, -6.92% (catastrophic)
- Avg loss (-0.192%) exceeded avg win (0.218%)

---

### 2. Range Scalping (Bollinger Bands + RSI) ❌

**Concept**: Buy at lower BB, sell at upper BB, with RSI confirmation

**Q1 2024 Multi-Asset Results**:
- Best asset: **ES** (S&P 500 Futures, Sharpe 1.29)
- TSLA: Sharpe 0.06
- All others: Negative

**Full Year Validation (ES)**:
- Q1 2024: Sharpe 1.29 ✅
- Full 2024: Sharpe **-0.74** ❌
- Full 2025: Sharpe **0.32** ⚠️
- **Average: Sharpe -0.21** (FAILED)

**Why it failed**:
- July 2024: -5.38% (worst month)
- Win rate 48.5% insufficient to overcome friction
- 6.5 trades/day compounded friction costs

---

### 3. Opening Range Breakout ❌

**Concept**: Trade breakouts from first 10-15 minutes, 2-hour window

**Q1 2024 Multi-Asset Results** (V1 - all day trading):
- Massive overtrading: 33-40 trades/day
- All assets negative

**Q1 2024 Multi-Asset Results** (V2 - 2-hour window fix):
- Best asset: **QQQ** (Sharpe -0.26, almost breakeven)
- IWM: Sharpe -1.16

**QQQ Optimization**:
- Best config: 10-minute range
- Q1 2024: Sharpe **0.99** ✅ (looked profitable!)

**Full Year Validation (QQQ, optimized)**:
- Q1 2024: Sharpe 0.99 ✅
- Full 2024: Sharpe **-1.72** ❌
- Full 2025: Sharpe **-1.55** ❌
- **Average: Sharpe -1.64** (FAILED)

**Also tested IWM**:
- Full 2024: Sharpe -1.87 ❌
- Full 2025: Sharpe -0.88 ❌

**Why it failed**:
- Win rate only 26.9% (too low)
- 5.8 trades/day
- False breakouts dominated

---

### 4. Mean Reversion (Z-score + RSI) ❌

**Concept**: Trade when price deviates >2 std devs from mean

**Q1 2024 Multi-Asset Results**:
- Best asset: **NVDA** (Sharpe **2.04** - highest of all strategies!)
- ES: Sharpe 0.04 (barely positive)
- All others: Negative

**Full Year Validation (NVDA)**:
- Q1 2024: Sharpe 2.04 ✅ (very promising!)
- Full 2024: Sharpe **0.49** ⚠️ (barely positive, +5.34%)
- Full 2025: Sharpe **-0.95** ❌ (losing, -10.37%)
- **Average: Sharpe -0.23** (FAILED)

**Why it failed**:
- 2024 was marginally profitable
- 2025 lost money (regime change)
- Win rate 57.4% insufficient
- Avg loss (-0.264%) > avg win (0.186%)

---

### 5. VWAP Scalping ❌
**Status**: Q1 testing only (SPY)
- Best Sharpe: -4.32
- Not worth full-year validation

### 6. Momentum Scalping ❌
**Status**: Q1 testing only (SPY)
- Best Sharpe: -3.64
- Not worth full-year validation

---

## Universal Findings

### 1. Sample Bias is Severe
| Strategy | Q1 Sharpe | Full Year Sharpe | Delta |
|----------|-----------|------------------|-------|
| Liquidity Grab (QQQ) | 0.84 | -1.91 | **-2.75** |
| Range Scalping (ES) | 1.29 | -0.21 | **-1.50** |
| Opening Range (QQQ) | 0.99 | -1.64 | **-2.63** |
| Mean Reversion (NVDA) | 2.04 | -0.23 | **-2.27** |

**Average collapse**: -2.29 Sharpe points

### 2. Why HFT Fails

**Friction compounds**:
- 1.0 bps × 5-7 trades/day = 5-7 bps/day
- Over 252 days = 12.6-17.6% annual friction
- Requires 60%+ win rate with good win/loss ratio

**Win rates insufficient**:
- Observed: 25-60%
- Required: 60%+ consistently
- Problem: Avg loss often exceeds avg win

**Market regimes change**:
- Q1 2024 had specific volatility patterns
- Rest of year different
- Strategies don't adapt

### 3. Asset Class Insights

**Best performers by strategy**:
- Liquidity Grab: QQQ (still failed)
- Range Scalping: ES futures (still failed)
- Opening Range: QQQ (still failed)
- Mean Reversion: NVDA (still failed)

**Pattern**: High volatility assets (QQQ, NVDA, ES) perform best but still lose money

---

## Recommendations

### 1. Abandon HFT Research ✅
**Rationale**:
- 4 major strategies tested exhaustively
- All failed full-year validation
- Sample bias is severe and consistent
- Friction barrier is insurmountable with residential latency

### 2. Focus on Validated Strategies ✅
**FOMC Event Straddles**:
- Sharpe: 1.17 (validated)
- Frequency: ~8 events/year
- Works because: Catalyst-driven, not technical

### 3. Minimum Testing Standards ✅
For any future strategy:
- **Minimum 100 days** for initial validation
- **Full year (252 days)** for deployment decision
- **Never trust 30-day samples**

### 4. Friction Reality ✅
With 1.0 bps friction and 5 trades/day:
- Need 60%+ win rate
- Need avg win > avg loss
- Need consistent performance across regimes
- **This is extremely difficult to achieve**

---

## Files Generated

### Multi-Asset Testing:
- `liquidity_grab_multi_asset.py` + results
- `range_scalping_multi_asset.py` + results
- `opening_range_breakout_multi_asset.py` + results
- `opening_range_breakout_v2_fixed.py` + results
- `mean_reversion_multi_asset.py` + results

### Full-Year Validation:
- `liquidity_grab_qqq_full_year.py` + results
- `range_scalping_es_full_year.py` + results
- `orb_full_year_qqq_iwm.py` + results
- `mean_reversion_nvda_full_year.py` + results

### Optimization:
- `liquidity_grab_qqq_optimization.py`
- `range_scalping_es_optimization.py`
- `orb_qqq_optimization.py`

### Analysis:
- `debug_q1_discrepancy.py` (sample bias investigation)
- `friction_reality_check.py`

---

## Conclusion

After exhaustive testing of 6 HFT strategies across 7 asset classes with full-year validation on the 4 most promising:

**NO HFT STRATEGY IS PROFITABLE** with:
- Realistic friction (1.0 bps)
- Residential latency (67ms)
- 1-minute bars
- Full-year validation

**The only validated profitable strategy remains**:
- **FOMC Event Straddles** (Sharpe 1.17)

**Recommendation**: Cease HFT research and focus on event-driven strategies.

---

**Research completed**: 2026-01-16  
**Total strategies tested**: 6  
**Full-year validations**: 4  
**Profitable strategies found**: 0  
**Verdict**: HFT NOT VIABLE
