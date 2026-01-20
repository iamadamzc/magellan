# Bear Trap-Specific Scaling Templates

**Updated:** 2026-01-19  
**Fix:** Strategy-specific templates instead of generic R-multiples

---

## 🎯 **Bear Trap Price Behavior**

**Typical winner pattern:**
```
Entry (reclaim) → Quick spike → Pullback → Continue or stop
        0R            +1-2R       +0.5R      +2R or out
         ↑              ↑            ↑           ↑
      Reclaim      Peak velocity  Dip test   Final move
```

**Key insight:** Adding at +0.5R = buying the spike top (bad price)

---

## 📋 **Corrected Templates**

### **Template 1: Conservative (NO_ADD Regime)**

```python
BEAR_TRAP_CONSERVATIVE = {
    'name': 'conservative',
    'regime': 'NO_ADD',
    
    # Position sizing
    'initial_size': 1.0,           # Full position at entry
    'scaling': None,               # No adds
    
    # Exit management
    'take_profit_1': {
        'r_multiple': 1.0,
        'percent_to_exit': 0.5,    # Take half at 1R
    },
    'take_profit_2': {
        'r_multiple': 2.0,
        'percent_to_exit': 1.0,    # Rest at 2R or time
    },
    
    # Time stop
    'max_bars': 30,                # 30-min time stop
    
    # Use case
    'when_to_use': 'Choppy markets, high volatility, weak setup'
}
```

---

### **Template 2: Normal (ADD_NEUTRAL Regime)**

```python
BEAR_TRAP_NORMAL = {
    'name': 'normal',
    'regime': 'ADD_NEUTRAL',
    
    # Position sizing
    'initial_size': 0.7,           # 70% at entry
    
    # Scaling rule: Add on pullback
    'scaling': {
        'type': 'pullback_to_support',
        'add_size': 0.3,           # Add 30% more
        
        # Pullback triggers
        'price_pulls_to': 'VWAP',  # or 'entry + 0.5*ATR'
        'holds_above_for_bars': 3,  # Must hold 3 bars
        'max_wait_bars': 15,       # Only add within 15 bars of entry
        
        # Safety: Don't add if...
        'cancel_if_below': 'entry_price',  # Below entry = abort
    },
    
    # Exit management
    'take_profit_1': {
        'r_multiple': 1.0,
        'percent_to_exit': 0.4,    # Lighter profit taking
    },
    'take_profit_2': {
        'r_multiple': 2.0,
        'percent_to_exit': 1.0,
    },
    
    # Time stop
    'max_bars': 30,
    
    # Use case
    'when_to_use': 'Mixed signals, normal volatility'
}
```

---

### **Template 3: Aggressive (ADD_ALLOWED Regime)**

```python
BEAR_TRAP_AGGRESSIVE = {
    'name': 'aggressive',
    'regime': 'ADD_ALLOWED',
    
    # Position sizing
    'initial_size': 0.6,           # 60% at entry
    
    # Scaling rule 1: Add on first pullback
    'add_1': {
        'type': 'pullback_to_support',
        'add_size': 0.2,           # Add 20% more
        
        'price_pulls_to': 'entry + 0.5*ATR',  # Shallow pullback
        'holds_above_for_bars': 2,
        'max_wait_bars': 15,
    },
    
    # Scaling rule 2: Add on TP1 confirmation
    'add_2': {
        'type': 'tp1_confirmation',
        'add_size': 0.2,           # Add final 20%
        
        # Only add if TP1 hit and price holds
        'requires_tp1_hit': True,
        'price_holds_above_tp1_for': 2,  # 2 bars above TP1
        'max_wait_bars': 10,       # Only within 10 bars of TP1
    },
    
    # Exit management
    'take_profit_1': {
        'r_multiple': 1.0,
        'percent_to_exit': 0.3,    # Take 30% at 1R
    },
    'take_profit_2': {
        'r_multiple': 1.5,
        'percent_to_exit': 0.3,    # Take 30% at 1.5R
    },
    'take_profit_3': {
        'r_multiple': 2.5,
        'percent_to_exit': 1.0,    # Rest at 2.5R or time
    },
    
    # Time stop (extended for aggressive)
    'max_bars': 35,
    
    # Use case
    'when_to_use': 'Strong trend, low volatility, excellent setup'
}
```

---

## 🔬 **Implementation Logic**

### **Pullback Detection:**
```python
def check_pullback_to_vwap(df, current_idx, entry_idx, vwap):
    """Check if price pulled back to VWAP and held"""
    
    # Need at least 3 bars after entry
    if current_idx - entry_idx < 3:
        return False
    
    # Check if price touched VWAP recently (within last 5 bars)
    recent_window = df.iloc[max(entry_idx, current_idx-5):current_idx+1]
    touched_vwap = (recent_window['low'] <= vwap * 1.01).any()
    
    if not touched_vwap:
        return False
    
    # Check if price held above VWAP for required bars
    hold_window = df.iloc[current_idx-2:current_idx+1]  # Last 3 bars
    held_above = (hold_window['close'] > vwap).all()
    
    return held_above
```

### **TP1 Confirmation:**
```python
def check_tp1_confirmation(df, current_idx, tp1_price, tp1_hit_idx):
    """Check if price hit TP1 and held above it"""
    
    # Has TP1 been hit?
    if tp1_hit_idx is None:
        return False
    
    # Has it been at least 2 bars since TP1 hit?
    if current_idx - tp1_hit_idx < 2:
        return False
    
    # Check if price held above TP1 for last 2 bars
    hold_window = df.iloc[current_idx-1:current_idx+1]
    held_above = (hold_window['close'] > tp1_price).all()
    
    return held_above
```

---

## 📊 **Key Differences from Original**

| Aspect | Original (WRONG) | Corrected (RIGHT) |
|--------|------------------|-------------------|
| Add trigger | Fixed R-multiple (+0.5R, +1.0R) | Price structure (pullback, confirmation) |
| Timing | Mechanical | Contextual |
| Bear Trap fit | Poor (buys spikes) | Good (buys dips) |
| Risk | Adds at worst price | Adds at better price |
| Complexity | Simple but wrong | Slightly more complex but aligned |

---

## ⚡ **Expected Impact**

**Conservative (No scaling):**
- Baseline performance
- Simplest implementation
- Good for weak setups

**Normal (Pullback add):**
- **Better average price** (add on dip)
- May improve returns by 5-10%
- Good risk/reward

**Aggressive (Pullback + Confirmation):**
- **Best on strong trends**
- May improve returns by 10-20%
- Requires both adds to trigger

---

## 🎯 **Testing Plan**

1. **Baseline:** No scaling (Conservative template ONLY)
2. **Test:** Pullback adds (Normal template)
3. **Compare:** Which performs better?
4. **If better:** Keep it
5. **If not:** Stick with Conservative

**ML will learn which template fits which market conditions.**

---

**Updated:** 2026-01-19  
**Status:** Bear Trap-specific, ready for testing
