# ML Labeling Protocol - CORRECTED APPROACH

**Created:** 2026-01-19  
**Critical Fix:** Label by ENTRY CONDITIONS, not outcomes  
**Principle:** No look-ahead bias, even conceptually

---

## ⚠️ **THE PROBLEM WITH NAIVE LABELING**

### **WRONG Approach (What I Originally Suggested):**
```python
# ❌ DANGER: This leaks future information
if max_r_multiple > 2.0 and smooth_path:
    label = 'ADD_ALLOWED'  # "This trade won, so call it aggressive"
elif stopped_out:
    label = 'NO_ADD'  # "This trade lost, so call it conservative"
```

**Why this fails:**
- You're teaching the model to predict the OUTCOME (future)
- Not teaching it to recognize the REGIME (present)
- **Subtle look-ahead bias** - conceptual, not numerical
- Model learns "when trades win" not "what conditions favor scaling"

---

## ✅ **CORRECT Approach: Label by Entry-Time Structure**

### **Philosophy:**
> **Labels must describe ENVIRONMENT at entry, not trajectory after entry.**

---

## 📊 **Structural Regime Scoring (Entry-Time Only)**

### **Score Component 1: Trend Strength (0-3 points)**

**Calculated at entry:**
```python
# Look at bars BEFORE entry (no look-ahead)
bars_before_entry = df.iloc[entry_idx-20:entry_idx]

# Count higher highs in last 20 bars
higher_highs = (bars_before_entry['high'] > bars_before_entry['high'].shift(1)).sum()
trend_score = higher_highs / 20  # Normalize to 0-1

# Convert to points
if trend_score > 0.7:
    trend_points = 3  # Strong trend
elif trend_score > 0.4:
    trend_points = 2  # Moderate trend
elif trend_score > 0.2:
    trend_points = 1  # Weak trend
else:
    trend_points = 0  # Choppy
```

---

### **Score Component 2: Volatility Regime (0-3 points)**

**Calculated at entry:**
```python
# ATR at entry vs historical
current_atr = df['atr'].iloc[entry_idx]
atr_20_bars_ago = df['atr'].iloc[max(0, entry_idx-20):entry_idx].mean()

# Is volatility expanding (good for scaling) or contracting (risky)?
if current_atr > atr_20_bars_ago * 1.2:
    vol_points = 0  # High volatility = risky
elif current_atr > atr_20_bars_ago * 0.8:
    vol_points = 2  # Normal volatility
else:
    vol_points = 3  # Low volatility = stable
```

---

### **Score Component 3: Reclaim Quality (0-3 points)**

**For Bear Trap specifically:**
```python
# Reclaim candle at entry (all known at entry time)
reclaim_candle = df.iloc[entry_idx]

# Wick ratio (long lower wick = strong rejection)
wick_ratio = reclaim_candle['wick_ratio']
if wick_ratio > 0.4:
    wick_points = 3  # Very strong rejection
elif wick_ratio > 0.25:
    wick_points = 2
elif wick_ratio > 0.15:
    wick_points = 1
else:
    wick_points = 0

# Body ratio (solid body = conviction)
body_ratio = reclaim_candle['body_ratio']
if body_ratio > 0.5:
    body_points = 3  # Very strong conviction
elif body_ratio > 0.3:
    body_points = 2
elif body_ratio > 0.2:
    body_points = 1
else:
    body_points = 0

reclaim_points = (wick_points + body_points) / 2  # Average
```

---

### **Score Component 4: Volume Confirmation (0-3 points)**

**Calculated at entry:**
```python
# Volume at entry vs recent average
volume_ratio = df['volume_ratio'].iloc[entry_idx]

if volume_ratio > 2.0:
    volume_points = 3  # Very strong volume
elif volume_ratio > 1.5:
    volume_points = 2
elif volume_ratio > 1.2:
    volume_points = 1
else:
    volume_points = 0  # Weak volume
```

---

### **Score Component 5: Speed of Reclaim (0-3 points)**

**Calculated at entry:**
```python
# How quickly did it reclaim after breaking session low?
session_bars = df[df['date'] == entry_date]
session_low_break_idx = session_bars[session_bars['low'] == session_low].index[0]
bars_since_low = entry_idx - session_low_break_idx

if bars_since_low <= 3:
    speed_points = 3  # Very fast (strong)
elif bars_since_low <= 10:
    speed_points = 2
elif bars_since_low <= 30:
    speed_points = 1
else:
    speed_points = 0  # Slow (weak)
```

---

## 🎯 **Combining Scores → Label**

```python
# Total structural score (0-15 points possible)
total_score = (
    trend_points +      # 0-3
    vol_points +        # 0-3
    reclaim_points +    # 0-3
    volume_points +     # 0-3
    speed_points        # 0-3
)

# Map score to regime label
if total_score >= 11:
    label = 'ADD_ALLOWED'     # Strong structural setup (73%+)
elif total_score >= 7:
    label = 'ADD_NEUTRAL'     # Mixed signals (47-73%)
else:
    label = 'NO_ADD'          # Weak structural setup (<47%)
```

---

## ✅ **Validation Step (Separate from Labeling)**

**After labeling ALL trades structurally, check correlation:**

```python
# Group by structural label
add_allowed_trades = df[df['regime_label'] == 'ADD_ALLOWED']
no_add_trades = df[df['regime_label'] == 'NO_ADD']

# Calculate outcome statistics
stats = {
    'ADD_ALLOWED': {
        'avg_r_multiple': add_allowed_trades['r_multiple'].mean(),
        'win_rate': (add_allowed_trades['r_multiple'] > 0).mean(),
        'avg_max_loss': add_allowed_trades['max_loss'].mean(),
    },
    'NO_ADD': {
        'avg_r_multiple': no_add_trades['r_multiple'].mean(),
        'win_rate': (no_add_trades['r_multiple'] > 0).mean(),
        'avg_max_loss': no_add_trades['max_loss'].mean(),
    }
}

# Check if labels make sense
print("ADD_ALLOWED trades:")
print(f"  Avg R-multiple: {stats['ADD_ALLOWED']['avg_r_multiple']:.2f}")
print(f"  Win rate: {stats['ADD_ALLOWED']['win_rate']:.1%}")

print("NO_ADD trades:")
print(f"  Avg R-multiple: {stats['NO_ADD']['avg_r_multiple']:.2f}")
print(f"  Win rate: {stats['NO_ADD']['win_rate']:.1%}")

# If ADD_ALLOWED has LOWER r-multiple than NO_ADD:
# → Your structural features are WRONG, not your labels
# → Fix the features, don't relabel based on outcomes
```

---

## 📋 **Revised Labeling Process**

### **Step 1: Extract Trades**
Run `extract_bear_trap_trades.py` (includes all entry-time features)

### **Step 2: Calculate Structural Scores**
```python
# For each trade, calculate 5 components (all entry-time data)
# Sum to get total score (0-15)
# Map to label (ADD_ALLOWED, ADD_NEUTRAL, NO_ADD)
```

### **Step 3: Validate Correlation**
```python
# Check if ADD_ALLOWED correlates with better outcomes
# If NO: Features are wrong, revise scoring
# If YES: Proceed to training
```

### **Step 4: Train ML**
```python
# Now train on structural features
# Model learns "what structural conditions match these labels"
# NOT "what outcomes led to these labels"
```

---

## 🔬 **Why This Works**

### **Traditional (Flawed) Approach:**
```
Outcome → Label → Features
  ↓
"This trade won 2R, so call it ADD_ALLOWED"
  ↓
Model learns: "Predict which trades will win"
  ↓
IMPOSSIBLE (this is price prediction in disguise)
```

### **Structural (Correct) Approach:**
```
Entry Conditions → Label → Validate
  ↓
"This had strong trend + low vol + fast reclaim = ADD_ALLOWED"
  ↓
Model learns: "Recognize structural environment"
  ↓
POSSIBLE (regime classification, not prediction)
```

---

## 🎯 **Specific Features for Bear Trap**

**All calculated at entry (no look-ahead):**

1. **Trend Strength**
   - Higher highs in last 20 bars
   - Slope of 20-bar MA
   - Distance from session high

2. **Volatility Regime**
   - ATR percentile (20-bar lookback)
   - ATR expansion/contraction
   - Bollinger Band width

3. **Reclaim Quality**
   - Wick ratio (lower wick / total range)
   - Body ratio (body / total range)
   - Close position in candle

4. **Volume Pattern**
   - Volume ratio vs 20-bar average
   - Volume vs session average
   - Volume trend (increasing/decreasing)

5. **Reclaim Speed**
   - Bars since session low break
   - Price distance from session low
   - Number of lower lows before reclaim

---

## ⚠️ **Red Flags (Signs of Look-Ahead Bias)**

### **NEVER label based on:**
- ❌ Final R-multiple
- ❌ Whether trade was profitable
- ❌ Max favorable excursion (MFE)
- ❌ How long position was held
- ❌ Exit reason
- ❌ Any information after entry

### **ALWAYS label based on:**
- ✅ Market structure at entry
- ✅ Pre-entry trend
- ✅ Entry candle characteristics
- ✅ Volume at entry
- ✅ Volatility at entry
- ✅ Recent price action

---

## 📊 **Example: Correct Labeling**

```python
# Trade #1
entry_features = {
    'trend_strength': 0.75,      # Strong uptrend before entry
    'atr_percentile': 0.40,      # Moderate volatility
    'wick_ratio': 0.35,          # Good rejection
    'volume_ratio': 1.8,         # Strong volume
    'reclaim_speed': 5,          # Fast reclaim (5 bars)
}

# Calculate structural score
score = 3 + 2 + 3 + 2 + 2 = 12 points

# Label
regime_label = 'ADD_ALLOWED'  # Based on structure

# Later validation (separate from labeling)
actual_outcome = {
    'r_multiple': 2.3,           # This confirms the label was good
    'max_loss': 1.2,            # But we DIDN'T use this to create label
}
```

---

## 🎯 **Implementation**

I'll create updated script: `label_regime_structural.py`

This will:
1. Calculate all 5 structural components
2. Score each trade (0-15 points)
3. Map to regime label
4. Validate correlation with outcomes
5. Flag any mismatches for review

---

## 🔥 **Key Takeaway**

> **Your labels must describe the PRESENT (market structure), not the FUTURE (trade outcome).**

**Think of it like weather:**
- ✅ GOOD: "Storm conditions present" (observable now)
- ❌ BAD: "Will rain later" (prediction)

You're labeling the **environment**, not the **result**.

---

**This is THE critical fix. Thank you for catching this!** 🎯

Want me to create the corrected labeling script?
