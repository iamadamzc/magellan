# Strategy Decision Factors - What Actually Drives Each Strategy?

**Created:** 2026-01-19  
**Question:** Is RSI making all the trading decisions?  
**Answer:** NO - it varies by strategy!

---

## 📊 **Decision Factor Matrix**

| Strategy | Primary Factors | Decision Complexity |
|----------|----------------|---------------------|
| **1. Daily Trend** | RSI only | ⭐ Simple (1 factor) |
| **2. Hourly Swing** | RSI only | ⭐ Simple (1 factor) |
| **3. FOMC Straddles** | Time + Volatility + Options Pricing | ⭐⭐⭐ Complex (3+ factors) |
| **4. Earnings Straddles** | Earnings Date + IV + Options Pricing | ⭐⭐⭐ Complex (3+ factors) |
| **5. Bear Trap** | **7 factors combined** | ⭐⭐⭐⭐ Very Complex |
| **6. GSB** | **6 factors combined** | ⭐⭐⭐⭐ Very Complex |

---

## ⭐ **SIMPLE STRATEGIES (RSI Only)**

### **Strategy 1 & 2: Daily Trend + Hourly Swing**

**Decision Logic:**
```python
# ONLY RSI is checked
if RSI > upper_band:  # e.g., 60
    signal = BUY
elif RSI < lower_band:  # e.g., 40
    signal = SELL
```

**Why RSI-only?**
- **Intentionally simple** = more robust
- **Time-tested indicator** = 40+ years of use
- **Trend following** = RSI identifies overbought/oversold
- **Less overfitting risk** = fewer parameters to optimize

**What RSI Measures:**
- Momentum (price velocity)
- Overbought/oversold levels
- Trend exhaustion

---

## ⭐⭐⭐⭐ **COMPLEX STRATEGIES (Multi-Factor)**

### **Strategy 5: Bear Trap - 7 Decision Factors**

**Bear Trap entry requires ALL of these:**

```python
# 1. DAY CHANGE - Stock must be down big
if day_change >= -15%:
    ❌ Skip (need at least -15% drop)

# 2. SESSION LOW - Must break below session low first
if close <= session_low:
    ❌ Skip (need breakdown first)

# 3. RECLAIM - Must close ABOVE session low (the "trap")
if close > session_low:
    ✅ Potential setup

# 4. WICK RATIO - Candle must have long lower wick (rejection)
if lower_wick / candle_range >= 0.15:
    ✅ Shows buyers stepping in

# 5. BODY RATIO - Candle must have solid body (not doji)
if candle_body / candle_range >= 0.2:
    ✅ Shows conviction

# 6. VOLUME - Must have volume spike
if volume >= (avg_volume * 1.2):
    ✅ Confirmation

# 7. ATR STOP - Risk must be acceptable
if (price - stop_loss) / price <= 2%:
    ✅ Risk is contained
    
✅ ALL 7 CONDITIONS MET → ENTER TRADE
```

**From the actual code:**
```python
# Lines 139-176 in bear_trap_strategy.py
is_reclaim = (
    df.iloc[i]['close'] > session_low and                    # 1. Reclaim
    df.iloc[i]['wick_ratio'] >= params['RECLAIM_WICK_RATIO_MIN'] and  # 2. Wick
    df.iloc[i]['body_ratio'] >= params['RECLAIM_BODY_RATIO_MIN'] and  # 3. Body
    df.iloc[i]['volume_ratio'] >= (1 + params['RECLAIM_VOL_MULT'])    # 4. Volume
)

if is_reclaim and day_change <= -params['MIN_DAY_CHANGE_PCT']:  # 5. Down big
    # Calculate stop loss from ATR                              # 6. ATR stop
    stop_distance = session_low - (params['STOP_ATR_MULTIPLIER'] * current_atr)
    # Position sizing based on risk                             # 7. Risk calc
    if risk_per_share > 0:
        ✅ ENTER TRADE
```

**Bear Trap is NOT using RSI at all!** It's using:
- Price action (session highs/lows)
- Candlestick patterns (wicks, bodies)
- Volume analysis
- ATR for volatility

---

### **Strategy 6: GSB - 6 Decision Factors**

**GSB entry requires:**

```python
# 1. OPENING RANGE - Calculate first 10 minutes
or_high = max(first_10_bars['high'])
or_low = min(first_10_bars['low'])

# 2. BREAKOUT - Price must break above OR high
if close > or_high:
    ✅ Breakout confirmed

# 3. VOLUME SPIKE - Must have 1.8x normal volume
if volume >= (avg_volume * 1.8):
    ✅ Volume confirmation

# 4. PULLBACK ZONE - Entry on pullback to OR high
pullback_zone = or_high ± (0.15 * ATR)
if price in pullback_zone:
    ✅ Good entry zone

# 5. VWAP - Must be above VWAP (trend filter)
if price > vwap:
    ✅ Trend aligned

# 6. ATR STOP - Risk management
stop_loss = or_low - (0.4 * ATR)
if stop_distance is reasonable:
    ✅ ENTER TRADE
```

**From the actual code:**
```python
# Lines 122-140 in gsb_strategy.py
if df.iloc[i]['breakout'] and not breakout_seen:  # 1. Breakout
    breakout_seen = True

if breakout_seen:
    pullback_zone_low = current_or_high - (params['PULLBACK_ATR'] * current_atr)
    pullback_zone_high = current_or_high + (params['PULLBACK_ATR'] * current_atr)
    in_pullback_zone = (current_low <= pullback_zone_high) and (current_high >= pullback_zone_low)  # 2. Pullback
    
    if (in_pullback_zone and                                   # 3. Zone
        current_price > current_or_high and                    # 4. Above OR
        current_price > current_vwap and                       # 5. Above VWAP
        df.iloc[i]['volume_spike'] >= params['VOL_MULT']):    # 6. Volume
        ✅ ENTER TRADE
```

**GSB is NOT using RSI either!** It's using:
- Opening range mechanics
- Breakout detection
- VWAP (volume-weighted average price)
- Volume analysis
- ATR for stops

---

## 📋 **Complete Factor Breakdown by Strategy**

### **Strategy 1: Daily Trend Hysteresis**
**Factors:** 1
- ✅ RSI (21 or 28 period)

**Decision:** 
- RSI > upper_band → Long
- RSI < lower_band → Flat

---

### **Strategy 2: Hourly Swing**
**Factors:** 1
- ✅ RSI (14 or 28 period)

**Decision:**
- RSI > upper_band → Long
- RSI < lower_band → Flat

---

### **Strategy 3: FOMC Straddles**
**Factors:** 4
- ✅ FOMC announcement time (2:00 PM ET)
- ✅ SPY price (for ATM strike selection)
- ✅ Implied Volatility (IV spike expected)
- ✅ Time to expiration (0DTE options)

**Decision:**
- Buy call + put at ATM strike, 30 min before FOMC
- Exit at close or +50% profit

---

### **Strategy 4: Earnings Straddles**
**Factors:** 4
- ✅ Earnings announcement date/time
- ✅ Stock price (for ATM strike)
- ✅ Historical earnings move (expected range)
- ✅ Implied Volatility

**Decision:**
- Buy call + put 1 day before earnings
- Exit next day or +30% profit

---

### **Strategy 5: Bear Trap**
**Factors:** 7
- ✅ Day change % (must be -15% or worse)
- ✅ Session low (support level)
- ✅ Reclaim above session low
- ✅ Lower wick ratio (>15% of candle)
- ✅ Body ratio (>20% of candle)
- ✅ Volume ratio (>120% of average)
- ✅ ATR (for stop-loss calculation)

**Decision:**
- All 7 conditions → Enter
- Hit stop OR 30 min → Exit

---

### **Strategy 6: GSB**
**Factors:** 6
- ✅ Opening range (first 10 min high/low)
- ✅ Breakout confirmation (close > OR high)
- ✅ Volume spike (>180% of average)
- ✅ Pullback to OR (entry trigger)
- ✅ VWAP position (must be above)
- ✅ ATR (for stops and targets)

**Decision:**
- All 6 conditions → Enter
- Hit stop OR 2R target → Exit

---

## 💡 **Key Insights:**

### **1. Strategy Complexity Varies Dramatically**

**Simple (RSI only):**
- Daily Trend
- Hourly Swing
- ✅ Easier to understand
- ✅ Less overfitting risk
- ❌ May miss nuances

**Complex (Multi-factor):**
- Bear Trap (7 factors)
- GSB (6 factors)
- Options (4+ factors)
- ✅ Captures market structure better
- ✅ More precise entry/exit
- ❌ More parameters to tune

---

### **2. Why Different Approaches?**

**RSI works for:**
- ✅ Trending markets (ETFs, large-caps)
- ✅ Longer timeframes (daily, hourly)
- ✅ Mean reversion plays

**Multi-factor works for:**
- ✅ Event-driven trades (earnings, FOMC)
- ✅ Short-term reversals (Bear Trap)
- ✅ Intraday breakouts (GSB)
- ✅ High-volatility small-caps

---

### **3. The `features.py` File - Future Use**

Remember `features.py` from the architecture guide? It has:
- Multi-factor alpha generation
- Sentiment analysis
- News integration
- Volume z-scores
- Wavelet decomposition

**Currently:** ❌ NOT used by any of your 6 strategies  
**Future:** ✅ For advanced ML-based strategies

---

## 🎯 **Summary Table**

| Strategy | RSI? | Other Factors | Total Factors | Complexity |
|----------|------|---------------|---------------|------------|
| Daily Trend | ✅ Yes | None | 1 | Simple |
| Hourly Swing | ✅ Yes | None | 1 | Simple |
| FOMC | ❌ No | Time, IV, Options | 4 | Complex |
| Earnings | ❌ No | Date, IV, Options | 4 | Complex |
| Bear Trap | ❌ No | Price action, Volume, ATR | 7 | Very Complex |
| GSB | ❌ No | OR, VWAP, Volume, ATR | 6 | Very Complex |

---

## ✅ **Direct Answer to Your Question:**

**"Is RSI making the decision alone?"**

**For 2 out of 6 strategies: YES (Daily Trend, Hourly Swing)**
- These are intentionally simple
- RSI-only = proven, robust
- Less overfitting risk

**For 4 out of 6 strategies: NO**
- Bear Trap: 7 factors (NO RSI)
- GSB: 6 factors (NO RSI)
- FOMC: 4 factors (NO RSI)
- Earnings: 4 factors (NO RSI)

---

## 🔬 **Why Keep It Simple for Some Strategies?**

**Occam's Razor Principle:**
> "The simplest explanation is usually the best"

**For Daily/Hourly Trend:**
1. **Proven track record** - RSI has worked for 40+ years
2. **Less overfitting** - Fewer parameters = harder to overfit
3. **Robustness** - Simple strategies often survive regime changes better
4. **Transparency** - Easy to understand, debug, and trust

**But for intraday small-caps (Bear Trap):**
- Need more precision
- Market structure matters
- Volume patterns critical
- Single indicator insufficient

---

## 📝 **Example: Why Bear Trap Can't Use RSI Alone**

**Scenario:** Stock drops -20% in first hour

**RSI alone would say:**
- RSI = 15 (oversold)
- ✅ BUY?

**But Bear Trap checks:**
1. ❌ Did it break session low? (NO - just steady decline)
2. ❌ Did it RECLAIM above session low? (NO - still falling)
3. ❌ Is there a volume spike? (NO - quiet selling)
4. ❌ Is there a reversal candle? (NO - red candle)

**Result:** ❌ DON'T BUY - It's a falling knife, not a trap!

RSI alone would have lost money. Bear Trap's 7 factors avoid the trap (ironically!).

---

**Last Updated:** 2026-01-19  
**Status:** Complete multi-factor analysis
