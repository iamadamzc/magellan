# STRATEGY A: SILVER HOURLY SWING - FINAL ANALYSIS

**Test Date**: 2026-01-17  
**Status**: ✅ COMPLETE  
**Researcher**: Independent Adversarial Quantitative Analyst

---

## FINAL VERDICT: ❌ **REJECT**

---

## TEST RESULTS SUMMARY

| Period | Friction | Return | Sharpe | Max DD | Trades | Win Rate | Profit Factor | Verdict |
|--------|----------|--------|--------|--------|--------|----------|---------------|---------|
| **2024-2025** | Baseline (10 bps) | **+0.01%** | 1.02 | -0.01% | 15 | 40.0% | 2.20 | ❌ **REJECT** |
| 2024-2025 | Degraded (20 bps) | +0.01% | 0.80 | -0.01% | 15 | 40.0% | 1.96 | ❌ **REJECT** |
| **2022-2023** | Baseline (10 bps) | **+0.00%** | 0.77 | -0.00% | 13 | 38.5% | 2.04 | ❌ **REJECT** |
| 2022-2023 | Degraded (20 bps) | +0.00% | 0.31 | -0.00% | 13 | 38.5% | 1.58 | ❌ **REJECT** |

---

## CRITICAL FAILURES IDENTIFIED

### 1. **NEAR-ZERO RETURNS (FATAL)**
- **2024-2025**: +0.01% return (essentially breakeven)
- **2022-2023**: +0.00% return (exactly breakeven)
- **Total 4-year return**: +0.01% (meaningless)

**Conclusion**: Strategy has no edge after friction.

### 2. **LOW WIN RATE**
- **2024-2025**: 40.0% win rate (below breakeven)
- **2022-2023**: 38.5% win rate (below breakeven)
- **Consistent underperformance**: Win rate never exceeds 40%

**Conclusion**: Strategy loses more often than it wins.

### 3. **INSUFFICIENT TRADE COUNT**
- **2024-2025**: 15 trades (7.5 per year)
- **2022-2023**: 13 trades (6.5 per year)
- **Total**: 28 trades over 4 years

**Conclusion**: Sample size too small for statistical significance.

### 4. **PROFIT FACTOR DEGRADATION**
- **Baseline friction**: 2.04-2.20 (marginal)
- **Degraded friction**: 1.58-1.96 (poor)
- **Friction sensitivity**: High

**Conclusion**: Edge is fragile and friction-dependent.

### 5. **ASYMMETRIC WIN/LOSS**
- **Average win**: +3.34% to +7.69%
- **Average loss**: -0.75% to -1.94%
- **Win rate**: 38.5% to 40.0%

**Analysis**: Strategy has good win/loss ratio (3:1 to 4:1) but low win rate. This creates a breakeven situation where occasional large wins offset frequent small losses.

---

## ROBUSTNESS ASSESSMENT

| Test | Result | Verdict |
|------|--------|---------|
| **Sub-Period Performance** | Both periods: ~0% return | ❌ NO EDGE |
| **Friction Sensitivity** | Sharpe degrades 1.02 → 0.31 | ❌ FRAGILE |
| **Regime Analysis** | Consistent across periods | ✅ REGIME-AGNOSTIC (but still fails) |
| **Drawdown Control** | Minimal (-0.01%) | ✅ LOW RISK (but no reward) |
| **Trade Frequency** | 6.5-7.5 trades/year | ❌ TOO INFREQUENT |

---

## SUB-PERIOD ANALYSIS

### 2024-2025 (Recent Period)
- **Return**: +0.01% (essentially zero)
- **Sharpe**: 1.02 (baseline) / 0.80 (degraded)
- **Win Rate**: 40.0%
- **Trades**: 15 (7.5 per year)
- **Avg Win**: +7.69%
- **Avg Loss**: -1.94%
- **Avg Hold**: 89.1 hours (~3.7 days)

**Pattern**: Occasional large wins (+7.69% avg) offset by frequent small losses (-1.94% avg), resulting in breakeven.

### 2022-2023 (Historical Period)
- **Return**: +0.00% (exactly zero)
- **Sharpe**: 0.77 (baseline) / 0.31 (degraded)
- **Win Rate**: 38.5%
- **Trades**: 13 (6.5 per year)
- **Avg Win**: +3.34%
- **Avg Loss**: -0.75%
- **Avg Hold**: 91.4 hours (~3.8 days)

**Pattern**: Smaller wins (+3.34% avg) but also smaller losses (-0.75% avg), still resulting in breakeven.

---

## FAILURE ANALYSIS

### How the Strategy Fails

1. **Low Win Rate**:
   - Only wins 38.5-40.0% of the time
   - Loses 60-61.5% of the time
   - Needs large wins to compensate

2. **Insufficient Trade Frequency**:
   - Only 6.5-7.5 trades per year
   - RSI(28) with 60/40 bands too conservative
   - Misses most price movements

3. **Friction Erosion**:
   - 10 bps friction acceptable (Sharpe 0.77-1.02)
   - 20 bps friction destroys edge (Sharpe 0.31-0.80)
   - Edge is marginal at best

4. **No Directional Bias**:
   - Strategy is purely technical (RSI crossover)
   - No fundamental or trend filter
   - Trades both good and bad setups equally

### Hostile Market Conditions

- **All market conditions**: Strategy produces zero returns
- **High friction environments**: Sharpe drops to 0.31
- **Choppy markets**: Likely generates whipsaw losses (though net zero)

### Structural vs. Regime Failure

- **Structural failure**: ✅ YES - Strategy has no edge
- **Regime failure**: ❌ NO - Consistent across periods (but consistently zero)
- **Parameter failure**: ✅ YES - 60/40 bands too wide, generates too few trades

---

## COMPARISON TO OTHER STRATEGIES

| Metric | Strategy A (Silver) | Strategy B (TSLA) | Strategy C (AAPL) |
|--------|---------------------|-------------------|-------------------|
| **Return (Primary)** | +0.01% | -35.77% | +0.11% |
| **Return (Secondary)** | +0.00% | -69.33% | -0.31% |
| **Sharpe (Primary)** | 1.02 | 0.30 | 1.86 |
| **Win Rate (Primary)** | 40.0% | 50.0% | 62.5% |
| **Max DD (Primary)** | -0.01% | -44.14% | -0.11% |
| **Verdict** | ❌ REJECT | ❌ REJECT | ❌ REJECT |

**Ranking (Least Bad to Worst)**:
1. **Strategy C (AAPL)**: +0.11% return, Sharpe 1.86 (marginal edge)
2. **Strategy A (Silver)**: +0.01% return, Sharpe 1.02 (no edge)
3. **Strategy B (TSLA)**: -35.77% return, Sharpe 0.30 (catastrophic)

**Conclusion**: Strategy A is "less bad" than Strategy B but worse than Strategy C. However, **ALL THREE ARE REJECTED**.

---

## FRICTION SENSITIVITY

| Period | Baseline (10 bps) | Degraded (20 bps) | Sharpe Change |
|--------|-------------------|-------------------|---------------|
| 2024-2025 | Sharpe 1.02 | Sharpe 0.80 | -21.6% |
| 2022-2023 | Sharpe 0.77 | Sharpe 0.31 | -59.7% |

**Conclusion**: Doubling friction destroys Sharpe ratio, especially in the secondary period (-59.7%). This indicates the edge is extremely fragile.

---

## FINAL CLASSIFICATION: ❌ **REJECT**

### Rationale

1. ❌ **Near-zero returns** (+0.01% over 4 years)
2. ❌ **No statistical edge** (breakeven after friction)
3. ❌ **Low win rate** (38.5% to 40.0%)
4. ❌ **Insufficient trade count** (28 trades over 4 years)
5. ❌ **Friction-sensitive** (Sharpe degrades 59.7% with 2x friction)
6. ❌ **No practical value** (zero returns = wasted capital)

### Minimum Conditions for Use

**NONE** - Strategy should not be deployed under any conditions.

While the strategy doesn't lose money (unlike Strategy B), it also doesn't make money. There is no point in deploying a strategy that produces zero returns.

### Capital Patience Required

**N/A** - Strategy is not viable. Capital would be better deployed in:
- **Risk-free rate** (e.g., Treasury bills at 4-5%)
- **Buy-and-hold silver** (if bullish on silver)
- **Alternative strategies** with positive expected returns

### Invalidation Criteria

Strategy is invalidated by:
- ❌ Zero returns over 4 years
- ❌ Win rate below 50%
- ❌ Insufficient trade frequency (6.5-7.5 per year)
- ❌ No evidence of any edge after friction
- ❌ Better alternatives exist (risk-free rate, buy-and-hold)

---

## ROOT CAUSE ANALYSIS

### Why This Strategy Fails

1. **Wrong Parameters**:
   - RSI(28) with 60/40 bands too conservative
   - Generates only 6.5-7.5 trades per year
   - Misses most price movements

2. **No Trend Filter**:
   - Trades both trending and ranging markets
   - No regime detection
   - No volatility adjustment

3. **Low Win Rate**:
   - Only wins 38.5-40.0% of the time
   - Needs large wins to compensate
   - Friction erodes the edge

4. **Insufficient Frequency**:
   - 28 trades over 4 years is too few
   - Cannot achieve statistical significance
   - Cannot compound returns effectively

### What Would Be Needed to Fix

1. **Tighter bands**: Use 55/45 or 52/48 to increase trade frequency
2. **Shorter RSI period**: Use RSI(14) or RSI(21) for more responsiveness
3. **Trend filter**: Only trade in direction of longer-term trend
4. **Volatility filter**: Only trade when volatility is elevated
5. **Position sizing**: Scale position based on signal strength

**However**: Even with these fixes, the strategy may still not be viable. The fundamental approach (RSI crossover on hourly silver) may be incompatible with profitable trading.

---

## FINAL RECOMMENDATION

### DO NOT DEPLOY

This strategy should NOT be deployed because:
- **Zero returns** over 4 years
- **No edge** after friction
- **Low win rate** (38.5-40.0%)
- **Better alternatives exist** (risk-free rate, buy-and-hold)

### Alternative Approaches

If you want to trade silver on an hourly timeframe:
1. **Use buy-and-hold** (if bullish on silver fundamentals)
2. **Use momentum indicators** (not RSI)
3. **Use tighter parameters** (increase trade frequency)
4. **Use trend filters** (only trade with trend)
5. **Use different timeframe** (daily or 4-hour may be better)

---

**Status**: ✅ COMPLETE  
**Final Verdict**: ❌ **REJECT - NO EDGE**  
**Last Updated**: 2026-01-17 05:00 AM
