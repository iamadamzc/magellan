# ML Feature Engineering - Chad's Recommendations

**Date:** 2026-01-19  
**Source:** Chad G. Petey (Quant Advisor)  
**Status:** Implementing

---

## 🎯 **The Core Insight**

> **"Bear Trap is mean reversion first, momentum second. Scaling should often be delayed, not immediate."**

This means:
- ADD_ALLOWED being rare is CORRECT, not a failure
- Most trades shouldn't scale early
- ML should identify the few environments where scaling works

---

## 📊 **Tier 1 Features (Must-Have)**

### **1. Time of Day** ⭐⭐⭐⭐⭐

**Why it matters:**
- First 30-60 min: Different behavior (opening volatility)
- Midday: Different behavior (low volume, chop)
- Power hour: Different behavior (late-day reversals)

**How to implement:**
```python
entry_hour = df['entry_date'].dt.hour
entry_minute = df['entry_date'].dt.minute

# Create buckets
time_bucket = np.select([
    entry_hour < 10,           # First 30-60 min (9:30-10:00)
    entry_hour < 15,           # Midday (10:00-15:00)
    entry_hour >= 15           # Power hour (15:00-16:00)
], ['early', 'midday', 'late'])
```

**Expected pattern:**
- Early: High volatility, fast moves
- Midday: Chop, false signals
- Late: Stronger follow-through

---

### **2. Speed of Reclaim** ⭐⭐⭐⭐⭐

**Why it matters:**
- Fast snapback = strong buyers
- Slow crawl = weak recovery

**How to implement:**
```python
# Already in data!
bars_to_reclaim = entry_idx - session_low_break_idx
price_distance = (entry_price - session_low) / session_low

reclaim_speed = price_distance / bars_to_reclaim  # % per bar
```

**Expected pattern:**
- Fast reclaim (>1%/bar) = momentum continuation
- Slow reclaim (<0.5%/bar) = weak structure

---

### **3. Distance to VWAP at Entry** ⭐⭐⭐⭐⭐

**Why it matters:**
- Far below VWAP → snapback risk (revert to mean)
- Near VWAP → continuation potential (trend aligned)

**How to implement:**
```python
# Calculate VWAP at entry time
session_data = df_minute[df_minute['date'] == entry_date]
vwap = (session_data['close'] * session_data['volume']).cumsum() / session_data['volume'].cumsum()
vwap_at_entry = vwap.iloc[entry_idx]

distance_to_vwap = (entry_price - vwap_at_entry) / vwap_at_entry * 100
```

**Expected pattern:**
- Below -5% from VWAP: Snapback only, don't scale
- Within ±2% of VWAP: Continuation likely, can scale

---

## 🌍 **Tier 2 Features (External Context)**

### **4. Market Regime (SPY/IWM/VIX)**

```python
# Fetch SPY data for entry date
spy_day = spy_df[spy_df['date'] == entry_date]
spy_trend = (spy_day['close'] - spy_day['open']) / spy_day['open'] * 100

# VIX level
vix_level = vix_df[vix_df['date'] == entry_date]['close'].iloc[0]

# IWM (small cap proxy)
iwm_trend = (iwm_day['close'] - iwm_day['open']) / iwm_day['open'] * 100
```

**Expected pattern:**
- SPY/IWM down, VIX high: More volatile, higher risk
- SPY/IWM up, VIX low: Calmer, safer to scale

---

### **5. Symbol Recent Behavior**

```python
# How many Bear Traps in last 5 days?
recent_traps = trades_df[
    (trades_df['symbol'] == symbol) &
    (trades_df['entry_date'] > entry_date - timedelta(days=5)) &
    (trades_df['entry_date'] < entry_date)
]

trap_frequency = len(recent_traps)
recent_success_rate = (recent_traps['r_multiple'] > 0).mean()
```

**Expected pattern:**
- Too many recent traps: Symbol exhausted, don't scale
- High recent success: Symbol is "hot", can scale

---

## 📅 **Tier 3 Features (Calendar Effects)**

### **6. Day of Week**

```python
day_of_week = df['entry_date'].dt.dayofweek  # 0=Monday, 4=Friday

# Or categorize
is_monday = (day_of_week == 0)
is_friday = (day_of_week == 4)
```

**Expected pattern (small caps):**
- Monday: Follow-through from weekend
- Friday: Position squaring, different behavior

---

## 🎯 **Redefining Labels (CRITICAL FIX)**

### **OLD Definition (Wrong):**
```python
ADD_ALLOWED = "big winner"
NO_ADD = "bad trade"
```
**Problem:** This is outcome-based thinking!

### **NEW Definition (Correct):**

```python
ADD_ALLOWED = "Environment historically tolerates additional exposure"
  Criteria:
  - Time alignment (not midday chop)
  - Liquidity alignment (near VWAP)
  - Structure alignment (fast reclaim)
  
ADD_NEUTRAL = "Base case, trade is fine but don't press"
  Criteria:
  - Mixed signals
  - Standard conditions
  
NO_ADD = "Environment punishes additional risk even if trade wins"
  Criteria:
  - Far from VWAP (snapback only)
  - Slow reclaim (weak)
  - Midday (choppy)
```

**Key distinction:**
- Labels describe ENVIRONMENT
- NOT predicted outcome
- Validation checks if environment-based labels improve risk metrics

---

## 🧪 **Testing Strategy (Chad's Approach)**

### **Don't test returns first. Test risk reduction.**

**Hypothesis:**
> "Suppressing adds during NO_ADD reduces tail losses"

**Metrics to check:**
```python
# Compare baseline vs ML-enhanced

# 1. Worst trades
baseline_worst_10 = baseline_trades.nsmallest(10, 'r_multiple')
enhanced_worst_10 = enhanced_trades.nsmallest(10, 'r_multiple')

print(f"Baseline worst 10 avg: {baseline_worst_10['r_multiple'].mean()}")
print(f"Enhanced worst 10 avg: {enhanced_worst_10['r_multiple'].mean()}")

# 2. Worst days (sum of all trades that day)
baseline_daily = baseline_trades.groupby('date')['r_multiple'].sum()
enhanced_daily = enhanced_trades.groupby('date')['r_multiple'].sum()

# 3. Variance of R
print(f"Baseline R std: {baseline_trades['r_multiple'].std()}")
print(f"Enhanced R std: {enhanced_trades['r_multiple'].std()}")
```

**Success = Lower variance and fewer catastrophic losses**

---

## ✅ **Implementation Checklist**

### **Phase 1: Feature Engineering**
- [ ] Add time of day buckets
- [ ] Calculate reclaim speed
- [ ] Calculate distance to VWAP at entry
- [ ] Add market regime (SPY/VIX)
- [ ] Add symbol recent behavior
- [ ] Add day of week

### **Phase 2: Relabel with New Framework**
- [ ] Define labels as risk posture (not outcome)
- [ ] Use Tier 1 features for scoring
- [ ] Accept that ADD_ALLOWED may be rare (~10-20% of trades)
- [ ] Validate that NO_ADD correlates with higher variance

### **Phase 3: Test Risk Reduction**
- [ ] Compare worst trades (baseline vs enhanced)
- [ ] Compare worst days
- [ ] Compare R variance
- [ ] Ignore mean return initially

### **Phase 4: If Risk Improves**
- [ ] Then check if mean return also improved
- [ ] If yes: Deploy
- [ ] If no but risk reduced: Still valuable (Sharpe improvement)

---

## 💡 **Key Takeaways**

### **1. This was a successful validation checkpoint**
✅ Proved strategy logic is already strong  
✅ Proved ML discipline prevented garbage modeling  
✅ Now know exactly where ML must live

### **2. ADD_ALLOWED being rare is CORRECT**
Bear Trap is mean reversion. Most trades shouldn't scale.  
ML should identify the 10-20% of trades where scaling is safe.

### **3. Focus on risk reduction first**
Not "will this make more money?"  
But "will this reduce catastrophic losses?"

### **4. Labels = Risk Posture, Not Outcome**
Environment that tolerates risk vs environment that punishes it.

---

## 🔥 **Why This Works**

Bear Trap's edge is mean reversion snapbacks.  
Scaling into mean reversion is dangerous (you're fighting the revert).  
ML should say: "Only scale when it's ALSO momentum continuation"

**The few trades that are:**
- Fast reclaim (momentum confirmed)
- Near VWAP (not oversold anymore)
- Good time of day (not chop) 
- Good market regime (tailwind)

**Those can scale. Everything else: take the snapback and exit.**

---

**Next:** Implement Tier 1 features and retest labeling.
