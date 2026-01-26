# MARGINAL STRATEGIES - TUNING OPPORTUNITIES

**Date**: 2026-01-16  
**Purpose**: Document strategies that showed promise but require additional tuning before deployment  
**Status**: Research & Development Roadmap

---

## EXECUTIVE SUMMARY

During comprehensive robustness testing, several strategies showed **marginal performance** (Sharpe 0.3-0.7) that could potentially be improved to deployment-ready levels (Sharpe > 1.0) with targeted tuning.

This document outlines:
1. **Current Performance**: Baseline metrics from testing
2. **Identified Weaknesses**: Specific failure modes
3. **Tuning Recommendations**: Evidence-based improvements
4. **Expected Outcomes**: Projected performance after tuning

---

## STRATEGY 1: DAILY TREND HYSTERESIS (CRYPTO)

### Current Performance

| Asset | Sharpe | Return | Buy & Hold | Alpha | Max DD | Status |
|-------|--------|--------|------------|-------|--------|--------|
| BTCUSD | 0.65 | +136.6% | +144.3% | -7.7% | -54.4% | ⚠️ Marginal |
| ETHUSD | 0.71 | +216.5% | +140.6% | +75.9% | -47.0% | ⚠️ Marginal |
| **Average** | **0.68** | **+176.6%** | **+142.4%** | **+34.1%** | **-50.7%** | ⚠️ **Marginal** |

**Test Period**: 2020-2025 (6 years)  
**Parameters**: RSI-14, Bands 55/45, Daily timeframe

### Identified Weaknesses

1. **Daily Timeframe Too Slow**:
   - Crypto moves 5-10% intraday
   - Daily signals miss intraday momentum
   - Overnight gaps cause whipsaws

2. **No Trend Filter**:
   - Takes counter-trend trades
   - Gets caught in range-bound periods
   - No regime awareness

3. **High Drawdowns**:
   - Max DD -50%+ (too high for crypto volatility)
   - No stop-loss protection
   - Holds through major crashes

4. **BTC Underperforms Buy & Hold**:
   - -7.7% alpha on BTC
   - Only ETH shows positive alpha (+75.9%)
   - Inconsistent across crypto assets

### Tuning Recommendations

#### **Option A: Convert to Hourly Timeframe** ⭐⭐⭐⭐⭐

**Hypothesis**: Hourly signals will capture crypto's intraday momentum better.

**Implementation**:
```python
# Change from Daily to Hourly
timeframe = '1Hour'  # instead of '1Day'
# Keep same RSI logic (14-period, 55/45 bands)
```

**Expected Improvement**:
- **Sharpe**: 0.68 → **1.2-1.8** (based on NVDA hourly results)
- **Max DD**: -50% → **-30%** (faster exits)
- **Alpha**: +34% → **+80-120%** (captures intraday moves)

**Effort**: 1 day (rerun WFA with hourly data)

---

#### **Option B: Add Weekly Trend Filter** ⭐⭐⭐⭐

**Hypothesis**: Only take daily signals when weekly trend agrees.

**Implementation**:
```python
# Calculate weekly RSI
weekly_rsi = calculate_rsi(weekly_bars, period=14)

# Only enter long if both agree
if daily_rsi > 55 and weekly_rsi > 50:
    enter_long()
```

**Expected Improvement**:
- **Sharpe**: 0.68 → **0.9-1.2** (filters counter-trend trades)
- **Win Rate**: ~50% → **60-65%** (higher quality signals)
- **Max DD**: -50% → **-35%** (avoids major reversals)

**Effort**: 2-3 days (fetch weekly data, modify logic, retest)

---

#### **Option C: Add 3% Hard Stop Loss** ⭐⭐⭐

**Hypothesis**: Stop losses will cap drawdowns without hurting Sharpe.

**Implementation**:
```python
# Exit if position down 3% from entry
if current_pnl_pct < -3.0:
    exit_position()
```

**Expected Improvement**:
- **Sharpe**: 0.68 → **0.75-0.85** (reduced tail risk)
- **Max DD**: -50% → **-15-20%** (capped losses)
- **Trade-off**: May reduce returns slightly

**Effort**: 1 day (add stop logic, retest)

---

#### **Option D: Regime-Adaptive Parameters** ⭐⭐⭐

**Hypothesis**: Adjust RSI parameters based on volatility regime.

**Implementation**:
```python
# Calculate 30-day volatility
volatility = returns.rolling(30).std()

if volatility > high_threshold:
    # High volatility: faster signals
    rsi_period = 7
    bands = (50, 50)
elif volatility < low_threshold:
    # Low volatility: slower signals
    rsi_period = 28
    bands = (60, 40)
else:
    # Normal: standard parameters
    rsi_period = 14
    bands = (55, 45)
```

**Expected Improvement**:
- **Sharpe**: 0.68 → **0.85-1.1** (adapts to market conditions)
- **Consistency**: More stable across different market regimes

**Effort**: 3-4 days (develop adaptive logic, backtest)

---

### Recommended Tuning Path

**Phase 1** (Week 1): Test Option A (Hourly Timeframe)
- **Why First**: Highest expected improvement (Sharpe 1.2-1.8)
- **Quick Win**: Reuse existing hourly infrastructure
- **Decision Point**: If Sharpe > 1.2, deploy. If not, proceed to Phase 2.

**Phase 2** (Week 2): Add Option B (Weekly Filter) to Hourly
- **Combine**: Hourly signals + Weekly trend confirmation
- **Expected**: Sharpe 1.5-2.0
- **Decision Point**: If Sharpe > 1.5, deploy. If not, proceed to Phase 3.

**Phase 3** (Week 3): Add Option C (Stop Loss) + Option D (Adaptive)
- **Full Enhancement**: All tuning applied
- **Expected**: Sharpe 1.8-2.2
- **Decision Point**: Deploy if Sharpe > 1.5, otherwise shelve.

---

## STRATEGY 2: DAILY TREND HYSTERESIS (MOMENTUM STOCKS)

### Current Performance

| Asset | Sharpe | Status | Asset Type |
|-------|--------|--------|------------|
| SPY | -0.02 | ❌ Failed | Mean-reverting index |
| QQQ | -0.03 | ❌ Failed | Mean-reverting index |
| NVDA | 0.01 | ⚠️ Marginal | High-momentum stock |
| TSLA | 0.01 | ⚠️ Marginal | High-momentum stock |

**Test Period**: 2020-2025 (Multi-asset WFA)  
**Parameters**: RSI-14, Bands 55/45, Daily timeframe

### Identified Weaknesses

1. **Wrong Asset Universe**:
   - Tested on mean-reverting indices (SPY, QQQ)
   - Should test on momentum stocks only

2. **No Momentum Screening**:
   - Trades all assets equally
   - Doesn't identify which assets are trending

3. **High Intraday Noise**:
   - NVDA/TSLA have 5-7% intraday volatility
   - Daily signals too slow to capture moves

### Tuning Recommendations

#### **Option A: Momentum Universe Screener** ⭐⭐⭐⭐⭐

**Hypothesis**: Only trade stocks in Top 20% Relative Strength.

**Implementation**:
```python
# Monthly universe selection
def select_momentum_universe():
    # Calculate 6-month returns vs SPY
    rs_scores = {}
    for symbol in all_stocks:
        stock_return = get_return(symbol, lookback=126)
        spy_return = get_return('SPY', lookback=126)
        rs_scores[symbol] = stock_return - spy_return
    
    # Top 20% RS
    threshold = np.percentile(list(rs_scores.values()), 80)
    momentum_stocks = [s for s, rs in rs_scores.items() if rs > threshold]
    return momentum_stocks

# Only trade stocks in momentum universe
if symbol in momentum_universe:
    apply_daily_trend_strategy()
```

**Expected Improvement**:
- **Sharpe**: 0.01 → **0.5-0.8** (avoids choppy assets)
- **Win Rate**: ~45% → **55-60%** (higher quality assets)
- **Consistency**: Works across market cycles

**Effort**: 1 week (build screener, test on historical data)

---

#### **Option B: Sector Rotation Filter** ⭐⭐⭐⭐

**Hypothesis**: Only trade sectors that are trending.

**Implementation**:
```python
# Identify trending sectors
sector_etfs = ['XLK', 'XLE', 'XLF', 'XLV', 'XLI']
trending_sectors = []

for sector in sector_etfs:
    # Check if sector > 50-day MA
    if sector_price > sector_ma_50:
        trending_sectors.append(sector)

# Only trade stocks in trending sectors
if stock_sector in trending_sectors:
    apply_daily_trend_strategy()
```

**Expected Improvement**:
- **Sharpe**: 0.01 → **0.4-0.7** (rides sector momentum)
- **Example**: Would have caught Tech 2023-2024, Energy 2022

**Effort**: 3-4 days (map stocks to sectors, implement filter)

---

#### **Option C: Convert to Hourly + Momentum Screen** ⭐⭐⭐⭐⭐

**Hypothesis**: Combine hourly timeframe with momentum screening.

**Implementation**:
```python
# 1. Screen for Top 20% RS stocks (monthly)
momentum_stocks = select_momentum_universe()

# 2. Apply Hourly Swing to momentum stocks
for symbol in momentum_stocks:
    run_hourly_swing(symbol)
```

**Expected Improvement**:
- **Sharpe**: 0.01 → **1.0-1.5** (best of both worlds)
- **Rationale**: Hourly works on NVDA (0.95), momentum screen finds more NVDAs

**Effort**: 1 week (combine existing components)

---

### Recommended Tuning Path

**Phase 1** (Week 1): Test Option A (Momentum Screener)
- **Quick Test**: Run Daily Trend on Top 20% RS stocks (2023-2024)
- **Decision Point**: If Sharpe > 0.5, proceed. If not, skip to Option C.

**Phase 2** (Week 2): Test Option C (Hourly + Momentum)
- **Hypothesis**: This will likely be the winner
- **Expected**: Sharpe 1.0-1.5
- **Decision Point**: If Sharpe > 1.0, deploy. Otherwise, shelve.

---

## STRATEGY 3: HOURLY SWING (MARGINAL ASSETS)

### Current Performance

| Asset | Sharpe | Status | Notes |
|-------|--------|--------|-------|
| **NVDA** | **0.95** | ✅ **Validated** | Primary alpha engine |
| **GLD** | **0.52** | ✅ **Validated** | Defensive hedge |
| **TSLA** | **0.60** | ✅ **Validated** | With 3% stop |
| **AMZN** | **0.36** | ⚠️ **Marginal** | Needs improvement |
| SPY | 0.15 | ⚠️ Marginal | Index, mean-reverting |
| QQQ | 0.18 | ⚠️ Marginal | Index, mean-reverting |
| AAPL | 0.15 | ⚠️ Marginal | Low volatility |
| MSFT | -0.08 | ❌ Failed | Low volatility |

**Test Period**: 2020-2025 (Multi-asset WFA)  
**Parameters**: RSI-21, Bands 60/40, 1-Hour timeframe

### Identified Weaknesses (AMZN, SPY, QQQ, AAPL)

1. **Insufficient Volatility** (AAPL, MSFT):
   - ATR < 2% (not enough hourly movement)
   - Signals trigger but moves are too small

2. **Mean Reversion** (SPY, QQQ):
   - Indices chop at hourly timeframe
   - Momentum signals get whipsawed

3. **Inconsistent Trends** (AMZN):
   - Works in some periods, fails in others
   - No clear regime pattern

### Tuning Recommendations

#### **Option A: Volatility Filter for AMZN** ⭐⭐⭐⭐

**Hypothesis**: Only trade AMZN when ATR > 2%.

**Implementation**:
```python
# Calculate 14-period ATR
atr = calculate_atr(data, period=14)
atr_pct = (atr / price) * 100

# Only trade if sufficient volatility
if atr_pct > 2.0:
    apply_hourly_swing()
```

**Expected Improvement**:
- **Sharpe**: 0.36 → **0.55-0.75** (trades only when volatile)
- **Win Rate**: ~50% → **60%** (higher quality setups)

**Effort**: 1 day (add ATR filter, retest)

---

#### **Option B: Abandon Indices, Focus on Stocks** ⭐⭐⭐⭐⭐

**Hypothesis**: Hourly Swing is designed for stocks, not indices.

**Implementation**:
```python
# Remove SPY, QQQ, IWM from universe
# Focus on individual momentum stocks
validated_assets = ['NVDA', 'GLD', 'TSLA', 'AMZN']
```

**Expected Improvement**:
- **Portfolio Sharpe**: 0.70 → **0.75-0.85** (removes drag)
- **Simplicity**: Cleaner strategy, easier to manage

**Effort**: 0 days (just remove indices from deployment)

---

#### **Option C: Add More Momentum Stocks** ⭐⭐⭐⭐

**Hypothesis**: Find more assets like NVDA (high volatility, strong trends).

**Implementation**:
```python
# Test Hourly Swing on:
candidates = [
    'AMD',   # Chip momentum (like NVDA)
    'META',  # Tech momentum
    'COIN',  # Crypto proxy (high volatility)
    'PLTR',  # High beta tech
]

# Run WFA on each, deploy if Sharpe > 0.5
```

**Expected Improvement**:
- **Diversification**: More uncorrelated alpha sources
- **Expected**: 2-3 additional assets with Sharpe > 0.5

**Effort**: 1 week (test 10-15 candidates, validate top performers)

---

### Recommended Tuning Path

**Phase 1** (Immediate): Implement Option B
- **Action**: Remove SPY, QQQ from deployment
- **Effort**: 0 days
- **Impact**: Improves portfolio Sharpe immediately

**Phase 2** (Week 1): Test Option A (AMZN Volatility Filter)
- **Goal**: Improve AMZN from 0.36 to 0.55+
- **Decision Point**: If successful, keep AMZN. If not, remove.

**Phase 3** (Week 2): Test Option C (New Assets)
- **Screen**: Test 10-15 high-volatility stocks
- **Deploy**: Add any with Sharpe > 0.5

---

## STRATEGY 4: EARNINGS STRADDLES (BEAR MARKET FILTER)

### Current Performance

| Regime | Sharpe | Win Rate | Avg P&L | Status |
|--------|--------|----------|---------|--------|
| **Bull** (2023-2024) | **1.59-2.63** | **75-100%** | **+92-131%** | ✅ **Excellent** |
| **Bear** (2022) | **-0.17** | **50%** | **-5.4%** | ❌ **Failed** |
| **Overall** | **2.25** | **58.3%** | **+45.5%** | ✅ **Good** |

**Test Period**: 2020-2025 (24 NVDA earnings events)  
**Parameters**: Entry T-2, Exit T+1, ATM straddle

### Identified Weaknesses

1. **Bear Market Failure**:
   - 2022 (Fed tightening): Sharpe -0.17
   - Earnings moves were muted during risk-off

2. **No Regime Filter**:
   - Trades all earnings equally
   - Doesn't pause during bear markets

### Tuning Recommendations

#### **Option A: SPY 200-Day MA Filter** ⭐⭐⭐⭐⭐

**Hypothesis**: Pause strategy when SPY < 200-day MA.

**Implementation**:
```python
# Before each earnings trade
spy_price = get_current_price('SPY')
spy_ma_200 = get_ma(spy_price, period=200)

# Only trade if in bull market
if spy_price > spy_ma_200:
    enter_earnings_straddle()
else:
    print("Bear market detected - skipping trade")
```

**Expected Improvement**:
- **Sharpe**: 2.25 → **2.8-3.2** (avoids 2022 losses)
- **Win Rate**: 58.3% → **65-70%** (only trades in favorable regime)
- **Drawdown**: Eliminates 2022 -5.4% avg P&L

**Effort**: 1 day (add filter, retest historical data)

---

#### **Option B: VIX > 30 Circuit Breaker** ⭐⭐⭐⭐

**Hypothesis**: Pause when VIX > 30 for 5+ consecutive days (market panic).

**Implementation**:
```python
# Check VIX before trade
vix_5day_avg = get_vix_average(days=5)

# Pause if sustained high VIX
if vix_5day_avg > 30:
    skip_trade()
```

**Expected Improvement**:
- **Sharpe**: 2.25 → **2.6-3.0** (avoids panic periods)
- **Complements**: Works with Option A for dual protection

**Effort**: 2 days (fetch VIX data, implement logic)

---

#### **Option C: IV Rank < 50 Filter** ⭐⭐⭐

**Hypothesis**: Only trade when IV is not already elevated.

**Implementation**:
```python
# Calculate IV Rank (current IV vs 1-year range)
iv_rank = (current_iv - iv_min) / (iv_max - iv_min) * 100

# Only trade if IV not already high
if iv_rank < 50:
    enter_straddle()
```

**Expected Improvement**:
- **Sharpe**: 2.25 → **2.5-2.8** (avoids overpriced options)
- **Win Rate**: 58.3% → **62-65%** (better entry prices)

**Effort**: 3-4 days (calculate historical IV Rank, backtest)

---

### Recommended Tuning Path

**Phase 1** (Week 1): Implement Option A (SPY 200-MA Filter)
- **Why First**: Simplest, highest impact
- **Expected**: Sharpe 2.25 → 2.8-3.2
- **Decision Point**: If successful, deploy immediately

**Phase 2** (Week 2): Add Option B (VIX Circuit Breaker)
- **Dual Protection**: SPY MA + VIX filter
- **Expected**: Sharpe 3.0-3.5
- **Decision Point**: Deploy if Sharpe > 3.0

**Phase 3** (Optional): Test Option C (IV Rank)
- **Only if**: Want to further optimize
- **Effort vs Reward**: Marginal improvement for added complexity

---

## SUMMARY: TUNING PRIORITY MATRIX

| Strategy | Current Sharpe | Tuning Option | Expected Sharpe | Effort | Priority | ROI |
|----------|----------------|---------------|-----------------|--------|----------|-----|
| **Earnings Straddles** | **2.25** | **SPY 200-MA Filter** | **2.8-3.2** | **1 day** | **🔥 HIGHEST** | **⭐⭐⭐⭐⭐** |
| Daily Trend (Crypto) | 0.68 | Convert to Hourly | 1.2-1.8 | 1 day | 🔥 High | ⭐⭐⭐⭐⭐ |
| Hourly Swing (AMZN) | 0.36 | ATR Volatility Filter | 0.55-0.75 | 1 day | 🔥 High | ⭐⭐⭐⭐ |
| Daily Trend (Stocks) | 0.01 | Hourly + Momentum Screen | 1.0-1.5 | 1 week | Medium | ⭐⭐⭐⭐ |
| Hourly Swing | 0.70 | Add More Assets | 0.75-0.85 | 1 week | Medium | ⭐⭐⭐ |
| Daily Trend (Crypto) | 0.68 | Weekly Trend Filter | 0.9-1.2 | 2-3 days | Low | ⭐⭐⭐ |

---

## RECOMMENDED TUNING ROADMAP

### **Week 1: Quick Wins** 🚀

1. **Earnings Straddles + SPY Filter** (1 day)
   - Expected: Sharpe 2.25 → 3.0
   - Deploy immediately if successful

2. **Daily Trend Crypto → Hourly** (1 day)
   - Expected: Sharpe 0.68 → 1.5
   - Deploy if Sharpe > 1.2

3. **Hourly Swing AMZN + ATR Filter** (1 day)
   - Expected: Sharpe 0.36 → 0.65
   - Keep if Sharpe > 0.5, otherwise remove

### **Week 2: Expansion** 📈

4. **Hourly Swing + New Assets** (1 week)
   - Test AMD, META, COIN, PLTR
   - Deploy any with Sharpe > 0.5

5. **Daily Trend + Momentum Screener** (1 week)
   - Test on Top 20% RS stocks
   - Deploy if Sharpe > 1.0

### **Week 3: Optimization** ⚙️

6. **Earnings Straddles + VIX Filter** (2 days)
   - Add to SPY filter for dual protection
   - Deploy if Sharpe > 3.0

7. **Daily Trend Crypto + Weekly Filter** (3 days)
   - Only if hourly conversion didn't work
   - Deploy if Sharpe > 1.0

---

## EXPECTED OUTCOMES

### **If All Tuning Successful**:

| Strategy | Current Sharpe | Tuned Sharpe | Improvement |
|----------|----------------|--------------|-------------|
| Earnings Straddles | 2.25 | **3.0-3.5** | +33-56% |
| Hourly Swing | 0.70 | **0.80-0.95** | +14-36% |
| Daily Trend (Crypto Hourly) | 0.68 | **1.2-1.8** | +76-165% |
| Daily Trend (Momentum Stocks) | 0.01 | **1.0-1.5** | +9900% |

### **Portfolio Impact**:

**Current Validated Portfolio**:
- Earnings Straddles (Sharpe 2.25) + Hourly Swing (Sharpe 0.70)
- **Blended Sharpe**: ~1.5

**After Tuning**:
- Earnings Straddles (Sharpe 3.0) + Hourly Swing (Sharpe 0.85) + Daily Trend Crypto (Sharpe 1.5)
- **Blended Sharpe**: ~2.0-2.5

**Improvement**: +33-67% in risk-adjusted returns

---

**Last Updated**: 2026-01-16  
**Status**: Research roadmap for marginal strategies  
**Next Action**: Prioritize Week 1 quick wins
