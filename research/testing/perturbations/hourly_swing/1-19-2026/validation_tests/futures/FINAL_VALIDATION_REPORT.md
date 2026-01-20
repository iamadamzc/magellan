# HOURLY SWING - FUTURES VALIDATION REPORT

**Date**: 2026-01-16  
**Test Period**: 2024-01-01 to 2025-12-31 (2 years)  
**Asset Class**: Index Futures (CME Micro Contracts)  
**Strategy**: Hourly RSI-28 Hysteresis, Bands 60/40, Long-Only

---

## EXECUTIVE SUMMARY

❌ **VALIDATION FAILED** - All 4 index futures contracts rejected for Hourly Swing strategy

The Hourly Swing strategy **did not translate successfully** from high-volatility equities (NVDA, TSLA, PLTR) to index futures. All tested contracts showed **negative Sharpe ratios** and losses.

### Key Findings

| Contract | Sharpe | Return | Max DD | Trades | Win% | Decision |
|----------|--------|--------|--------|--------|------|----------|
| MNQ | -0.05 | -3.6% | -18.5% | 91 | 40% | ❌ **REJECTED** |
| MYM | -0.06 | -2.5% | -13.3% | 86 | 40% | ❌ **REJECTED** |
| MES | -0.07 | -3.1% | -16.4% | 91 | 35% | ❌ **REJECTED** |
| M2K | -0.30 | -15.9% | -24.6% | 98 | 37% | ❌ **REJECTED** |

**Conclusion**: Index futures lack the intraday volatility required for Hourly Swing strategy.

---

## METHODOLOGY

### Data Source
- **Proxy Method**: Index ETFs (SPY, QQQ, DIA, IWM) on **HOURLY timeframe**
- **Provider**: Alpaca (SIP feed, resampled from minute data to hourly)
- **Bars**: ~8,000 hourly bars per contract (2 years)

### Strategy Parameters
- **RSI Period**: 28
- **Entry**: Hourly RSI > 60 (wider than daily 55)
- **Exit**: Hourly RSI < 40 (wider than daily 45)
- **Hysteresis**: 40-60 "dead zone"
- **Position**: Long-only
- **Friction**: 10 bps per round-turn (higher than daily due to frequency)

### Test Specifications
- **Capital**: $10,000 per contract
- **Timeframe**: Hourly closes (6.5 trading hours/day)
- **Sharpe Annualization**: sqrt(252 * 6.5) for hourly returns

---

## WHAT WENT WRONG

### 1. Insufficient Intraday Volatility

**Index ETFs** (SPY, QQQ, DIA, IWM) are **too stable on hourly timeframe**:
- Typical hourly move: 0.1-0.3%
- Strategy friction (10 bps) eats 30-100% of move
- **Result**: Death by a thousand cuts

**Comparison to Validated Hourly Assets**:
| Asset | Type | Hourly Volatility | Sharpe (Historical) |
|-------|------|-------------------|---------------------|
| NVDA | Equity | High (1-3%) | 1.2+ |
| TSLA | Equity | Extreme (2-5%) | 1.0+ |
| PLTR | Equity | High (1-2%) | 1.1+ |
| **SPY** | **Index ETF** | **Low (0.1-0.3%)** | **-0.07** ❌ |
| **QQQ** | **Index ETF** | **Low (0.2-0.4%)** | **-0.05** ❌ |

### 2. Too Many Trades

Hourly timeframe on stable assets = excessive trading:
- **91 trades** on MES over 2 years
- **~45 trades/year** = nearly weekly trading
- Each trade pays 10 bps friction
- **Total friction cost**: ~4.5% annually
- **Gross returns insufficient** to overcome friction

### 3. Low Win Rates with Small Wins

All contracts showed:
- Win rates: 35-40% (below 50%)
- Small average wins (insufficient to cover losses + friction)
- **Payoff ratio unfavorable** for this strategy/asset combination

---

## ROOT CAUSE ANALYSIS

### Why Hourly Swing Works on Equities but NOT Index Futures

**Hourly Swing thrives on**:
1. **High volatility** (multi-percent hourly moves)
2. **Momentum bursts** (earnings gaps, news catalysts)
3. **Directional conviction**  (strong trends lasting days)

**Index Futures exhibit**:
1. **Low intraday volatility** (0.1-0.3% hourly)
2. **Mean-reverting behavior** (equilibrium-seeking)
3. **Choppy price action** (lacks sustained hourly trends)

**Mismatch**: Strategy → Asset Class

---

## COMPARISON TO DAILY TREND (SAME ASSETS, DIFFERENT TIMEFRAME)

| Asset | Daily Sharpe | Hourly Sharpe | Difference |
|-------|--------------|---------------|------------|
| MES | **+1.06** ✅ | **-0.07** ❌ | -1.13 |
| MNQ | **+1.15** ✅ | **-0.05** ❌ | -1.20 |
| MYM | **+0.65** ⚠️ | **-0.06** ❌ | -0.71 |
| M2K | **+0.13** ❌ | **-0.30** ❌ | -0.43 |

**Key Insight**: Same RSI hysteresis logic works on **DAILY** timeframe but fails on **HOURLY** timeframe for index futures.

**Reason**: Daily captures **multi-day trends**. Hourly tries to capture **intraday swings** that don't exist in stable indices.

---

## RECOMMENDATION: PIVOT TO HIGH-VOLATILITY ASSETS

### DO NOT Test Other Index Futures on Hourly

All index futures (including commodities like MGC) will likely fail for the same reason:
- Low intraday volatility
- High friction relative to move size
- Mean-reverting hourly behavior

### DO Test High-Volatility Futures (If Data Available)

**Candidates for Hourly Swing** (not tested due to data limitations):
1. **Micro Bitcoin (MBT)** - Extreme 24-hour volatility via BTCUSD on FMP
2. **Micro Crude Oil (MCL)** - High energy news-driven moves via CLUSD
3. **Micro Natural Gas (MNG)** - Extreme volatility via NGUSD

**Expected Outcome** (if tested):
- **MBT**: Sharpe 1.0-1.5 (based on BTCUSD spot volatility)
- **MCL**: Sharpe 0.8-1.2 (energy market volatility)
- **MNG**: Sharpe 0.5-1.0 (but very choppy, may still fail)

**Data Blocker**: FMP commodity/crypto hourly data requires additional implementation (not in scope for this test).

---

## VERDICT

❌ **HOURLY SWING STRATEGY DOES NOT WORK ON INDEX FUTURES**

**Reasons**:
1. Insufficient intraday volatility
2. Excessive friction relative to move size
3. Mean-reverting hourly price action

**Action**: **REJECT** Hourly Swing for all index futures.

---

## ALTERNATE PATHS FORWARD

### Option 1: Skip Hourly Swing for Futures (RECOMMENDED)

- **Daily Trend** already works excellently on MES/MNQ
- Hourly adds complexity without benefit on stable assets
- **Focus** on what works: Daily Trend for indices

### Option 2: Test High-Volatility Assets Only

If pursuing Hourly Swing on futures:
1. Implement FMP hourly data fetcher for commodities/crypto
2. Test **only** MBT, MCL, MNG (high-volatility candidates)
3. Skip all index and currency futures (too stable)

**Estimated Success Rate**: 30-50% (1-2 contracts may pass)

### Option 3: Modify Strategy for Index Futures

Test **wider bands** to reduce trade frequency:
- Try 70/30 bands instead of 60/40
- **Expected**: Fewer trades, still likely negative due to low volatility

**Not recommended** - root issue is asset volatility, not parameters.

---

## CONCLUSION

The Hourly Swing strategy validation on index futures **definitively failed**. This is a **valid negative finding** that saves future wasted effort.

**Key Learnings**:
1. ✅ Daily Trend works on index futures
2. ❌ Hourly Swing does NOT work on index futures
3. ⚠️ Hourly Swing *might* work on high-volatility futures (untested)

**Recommendation**: **MOVE TO NEXT STRATEGY** (FOMC Event Straddles on Futures)

---

## FILES CREATED

- `tests/futures/run_futures_hourly.py` ✅ (executed successfully)
- `tests/futures/futures_hourly_results.csv` ✅ (negative results documented)
- `tests/futures/FINAL_VALIDATION_REPORT.md` ✅ (this file)

**Next Agent**: Proceed to FOMC Event Straddles futures testing (final strategy).

---

**Status**: Hourly Swing futures validation **COMPLETE** (Negative Finding - Strategy Rejected for Index Futures)  
**Date**: 2026-01-16  
**Verdict**: ❌ **DO NOT DEPLOY** Hourly Swing on index futures
