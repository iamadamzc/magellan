# V1 vs V2 Results - Full Analysis

## Configuration Comparison

| Parameter | V1 (Original) | V2 (Strict) |
|-----------|---------------|-------------|
| VWAP Threshold | 0.45% | 0.60% |
| Profit Target |  0.30% | 0.40% |
| Stop Loss | None | 0.20% |
| Hold Time | 15 min | 20 min |
| Time Filter | 12-2 PM | 12-2 PM |
| Volatility Filter | None | ATR > 0.5% |
| Volume Filter | None | >2x avg |

---

##2024 Results

| Metric | V1 | V2 | Change |
|--------|----|----|--------|
| **Trades** | 361 | **0** | -361 ❌ |
| Trades/Day | 1.43 | 0.00 | -1.43 |
| **Win Rate** | 36.3% | N/A | N/A |
| **Sharpe** | -5.14 | 0.00 | +5.14 |
| **Total Return** | -17.53% | 0.00% | +17.53% |

**V2 Result**: NO TRADES in entire 2024 year! Too restrictive.

---

## 2025 Results

| Metric | V2 |
|--------|-----|
| **Trades** | 3 (all in April) |
| Trades/Day | 0.01 |
| **Win Rate** | 33.3% |
| **Sharpe** | -1.58 |
| **Total Return** | -2.76% |

**V2 Result**: Only 3 trades in full year, still lost money.

---

## Key Findings

### 1. V1 Was Too Loose
- 361 trades/year (1.43/day) = overtrading
- Win rate only 36.3% (need >55%)
- Sharpe -5.14 (losing)
- Annual friction: 14.8%

### 2. V2 Was Too Strict
- 0 trades in 2024, 3 trades in 2025
- Filters eliminate ALL opportunities
- Still lost money on the 3 trades that triggered

### 3. The "Goldilocks Problem"

```
V1: Too hot (361 trades, lose from friction)
V2: Too cold (0-3 trades, no opportunities)
V3: Need to find "just right"
```

---

## Why V2 Failed

**Triple-Filter Compounding**:
1. VWAP > 0.60% (already rare)
2. AND ATR > 0.5% (eliminates low volatility)
3. AND Volume > 2x (eliminates steady periods)
4. AND Time 10AM-12PM or 2PM-4PM (eliminates lunch + reduces hours)

**Result**: Filters are multiplicative, not additive!
- Each filter alone might be reasonable
- Combined = almost impossible to trigger

---

## Proposed V3 Configuration

**Philosophy**: Use filters SELECTIVELY, not ALL AT ONCE

### Option A: Threshold-Only Approach
```
VWAP Threshold: 0.52% (between 0.45% and 0.60%)
Profit Target: 0.35% (between 0.30% and 0.40%)
Stop Loss: 0.25%
Time Filter: 12-2 PM (keep)
Volatility Filter: NONE
Volume Filter: NONE
```
**Expected**: ~150-200 trades/year, win rate 40-45%

### Option B: Cherry-Pick Best Filter
```
VWAP Threshold: 0.50%
Profit Target: 0.30%
Stop Loss: 0.20%
Time Filter: 12-2 PM (keep)
Volume Filter: >1.5x (RELAXED from 2x)
Volatility Filter: NONE
```
**Expected**: ~100-150 trades/year, win rate 45-50%

### Option C: Adaptive Threshold
```
VWAP Threshold: DYNAMIC based on ATR
  - If ATR > 0.5%: Use 0.55% threshold
  - If ATR < 0.5%: Use 0.48% threshold
Profit Target: 0.35%
Stop Loss: 0.20%
Time Filter: 12-2 PM (keep)
```
**Expected**: ~120-180 trades/year, better signal quality

---

## My Recommendation: Option B

**Rationale**:
1. **0.50% threshold**: Sweet spot (not too loose, not too tight)
2. **Volume filter 1.5x**: Ensures some conviction without being too strict
3. **No ATR filter**: Let trades happen in all volatility regimes
4. **Stop loss 0.20%**: Protect against worst -0.805% losses

**Expected Results**:
- ~130 trades/year (0.5/day)
- Win rate: 48-52%
- Sharpe: 0.5-2.0 (marginally positive to good)
- Annual friction: 5.3% (manageable)

---

## Next Steps

Would you like me to:
1. ✅ **Test V3 Option B** on full 2024+2025?
2. Test all 3 V3 options and compare?
3. Give up on intraday VWAP and stick with FOMC events only?

---

## Reality Check

**Attempts so far**:
- V1 (0.45%): Sharpe -5.14 (failed)
- V2 (0.60% + filters): 0 trades (too strict)
- Small sample: Sharpe 2478 (curve-fit bias)

**Pattern**: Every time we optimize on the same data, we're curve-fitting. The "profitable" 5-day sample was pure luck.

**Honest Assessment**: 
- Intraday VWAP mean reversion may not be viable at ANY parameter setting
- Market is too efficient at 1-minute timescales
- FOMC events (Sharpe 1.17,validated) remains the only proven strategy

**Your call**: Test V3 or move on?
