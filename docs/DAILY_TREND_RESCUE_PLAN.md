# DAILY TREND HYSTERESIS - RESCUE PLAN

**Current Status**: ❌ FAILED (Sharpe ~0.01 on SPY)  
**Goal**: Transform into a deployable strategy  
**Approach**: Evidence-based modifications using WFA insights

---

## WHY IT FAILED

### Root Cause Analysis (From WFA Data)

The strategy failed because it's designed for **trending momentum** but was tested on **mean-reverting indices**:

1. **SPY/QQQ/IWM**: Sharpe -0.02 to -0.04 (indices chop sideways at daily timeframe)
2. **NVDA/TSLA**: Sharpe ~0.01 (marginal - high intraday noise triggers false signals)
3. **Problem**: RSI > 55 = Buy works on **strong trends** but fails on **range-bound** or **choppy** markets

---

## RESCUE STRATEGIES (Ranked by Probability of Success)

### **Option 1: Universe Restriction (Highest Probability)** ⭐⭐⭐⭐⭐

**Hypothesis**: The logic is sound, but we're trading the wrong assets.

**Solution**: Only trade assets with **proven momentum characteristics**:

1. **Momentum Screener**:
   - Calculate 6-month Relative Strength (RS) vs SPY for all assets
   - Only trade assets in **Top 20% RS** (strong momentum)
   - Re-screen monthly

2. **Sector Rotation**:
   - Track which sectors are trending (e.g., Tech in 2023-2024, Energy in 2022)
   - Only trade daily trend on **trending sectors**
   - Example: XLE (Energy) in 2022 would have worked when SPY failed

3. **Volatility Filter**:
   - Only trade assets with **ATR > 2%** (sufficient daily movement)
   - Indices like SPY (ATR ~1%) don't move enough for daily RSI signals

**Expected Outcome**: Sharpe 0.5-1.0 (by avoiding choppy assets)

**Implementation**:
```python
# Monthly universe selection
def select_momentum_universe():
    # Calculate 6-month returns vs SPY
    rs_scores = calculate_relative_strength(all_assets, lookback=126)
    # Top 20% RS
    momentum_assets = rs_scores[rs_scores > rs_scores.quantile(0.8)]
    return list(momentum_assets.index)
```

---

### **Option 2: Dual-Timeframe Confirmation (High Probability)** ⭐⭐⭐⭐

**Hypothesis**: Daily signals are too noisy. Need higher timeframe confirmation.

**Solution**: Only take Daily RSI signals when **Weekly trend agrees**:

1. **Weekly Trend Filter**:
   - Calculate Weekly RSI (same 55/45 bands)
   - Only take Daily Long signals if Weekly RSI > 50 (weekly uptrend)
   - This filters out counter-trend daily signals

2. **Weekly MA Filter**:
   - Simpler alternative: Only Long if Price > Weekly 20-MA
   - This ensures you're trading **with** the weekly trend

**Expected Outcome**: Sharpe 0.3-0.7 (by filtering counter-trend trades)

**Implementation**:
```python
# Check weekly trend before daily entry
weekly_rsi = calculate_rsi(weekly_bars, period=14)
if daily_rsi > 55 and weekly_rsi > 50:
    enter_long()
```

---

### **Option 3: Regime-Adaptive Parameters (Moderate Probability)** ⭐⭐⭐

**Hypothesis**: Fixed parameters (RSI-14, 55/45 bands) don't adapt to changing volatility.

**Solution**: Adjust parameters based on **VIX regime**:

| VIX Regime | RSI Period | Bands | Rationale |
|------------|------------|-------|-----------|
| Low (VIX < 15) | RSI-28 | 60/40 | Slower signals in calm markets |
| Normal (VIX 15-25) | RSI-14 | 55/45 | Standard parameters |
| High (VIX > 25) | RSI-7 | 50/50 | Faster signals in volatile markets |

**Expected Outcome**: Sharpe 0.2-0.5 (by adapting to market conditions)

---

### **Option 4: Mean Reversion Flip (Low Probability)** ⭐⭐

**Hypothesis**: Maybe the logic should be **reversed** for indices.

**Solution**: Test **inverse signals** on SPY/QQQ:
- RSI > 70 = **Sell** (overbought)
- RSI < 30 = **Buy** (oversold)

**Why Low Probability**: This turns it into a mean reversion strategy, which is fundamentally different. Better to just use a dedicated mean reversion strategy.

---

### **Option 5: Combine with Earnings Straddles (Creative)** ⭐⭐⭐

**Hypothesis**: Use Daily Trend to **select which stocks** to trade Earnings Straddles on.

**Solution**:
- Run Daily Trend on all MAG7 stocks
- Only trade Earnings Straddles on stocks where Daily Trend is **currently Long**
- Rationale: Stocks in daily uptrends have higher earnings volatility

**Expected Outcome**: Improves Earnings Straddles win rate from 58% to 65%+

---

## RECOMMENDED IMPLEMENTATION PLAN

### **Phase 1: Universe Restriction (Week 1)**

1. **Test on Proven Momentum Assets**:
   - Crypto (BTC, ETH) - pure momentum
   - Sector ETFs during their trending periods (XLE 2022, XLK 2023-2024)
   - Individual stocks with RS > 80th percentile

2. **Expected Result**: If Sharpe > 0.5, proceed to Phase 2

### **Phase 2: Add Dual-Timeframe Filter (Week 2)**

1. **Combine Universe Restriction + Weekly Confirmation**
2. **Expected Result**: Sharpe 0.7-1.2

### **Phase 3: Regime Adaptation (Week 3)**

1. **Add VIX-based parameter adjustment**
2. **Expected Result**: Sharpe 1.0-1.5 (production ready)

---

## QUICK WIN: Test on Crypto

**Why Crypto**:
- **Pure momentum** (no mean reversion like indices)
- **High ATR** (5-10% daily moves)
- **24/7 trading** (no overnight gaps)
- **Proven RSI effectiveness** (crypto traders use RSI heavily)

**Test Assets**: BTC, ETH (via Alpaca crypto)

**Expected Sharpe**: 1.0-2.0 (if the logic is sound)

**Implementation**:
```python
# Test Daily Trend on BTC (2020-2025)
symbol = 'BTC/USD'
# Same RSI logic, but on crypto
# If this works, the strategy is validated
# If this fails, the logic itself is flawed
```

---

## DECISION TREE

```
Start: Daily Trend Failed on SPY
│
├─ Test on BTC/ETH (Crypto)
│  ├─ Sharpe > 1.0? → ✅ Strategy works! Deploy on crypto + momentum stocks
│  └─ Sharpe < 0.5? → ❌ Logic is fundamentally flawed, abandon
│
├─ Test on Momentum Universe (Top 20% RS)
│  ├─ Sharpe > 0.5? → ✅ Add Weekly Filter → Deploy
│  └─ Sharpe < 0.3? → Try Option 3 (Regime Adaptation)
│
└─ If all fail → Pivot to Hourly Swing (already validated)
```

---

## MY RECOMMENDATION

**Start with Crypto Test** (30 minutes):
1. Run Daily Trend WFA on BTC/ETH (2020-2025)
2. If Sharpe > 1.0: **Strategy validated** - just needed right assets
3. If Sharpe < 0.5: **Logic flawed** - abandon and focus on Hourly Swing

**Why This First**:
- **Fastest validation** (crypto is pure momentum)
- **Clear signal** (either works or doesn't)
- **Low effort** (reuse existing code, just change symbol)

Would you like me to run the **Crypto Test** right now? It will take ~5 minutes and definitively tell us if the Daily Trend logic is salvageable.
