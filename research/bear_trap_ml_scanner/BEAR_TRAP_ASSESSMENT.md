# Current Bear Trap Assessment & Recommendations

> **For**: User / Next Agent
> **Context**: Current Bear Trap has not traded despite being deployed
> **Created**: January 22, 2026

---

## 🔴 Problem Statement

**Current Issue**: The deployed Bear Trap strategy on EC2 is looking for -15% moves on a static list of 21 symbols and **has not taken any trades**.

---

## 📊 Why It's Not Trading

### Root Cause Analysis

Based on our research:

| Factor | Current Setting | Reality |
|--------|-----------------|---------|
| **Threshold** | -15% intraday drop | Very rare (98 events in 5 years) |
| **Symbols** | 21 static list | Limited opportunity window |
| **Universe** | Pre-defined | Missing opportunities on other stocks |
| **Time Filter** | All day? | Best edge is time-specific |

### The Math Problem
```
Current Setup:
- -15% threshold: ~20 events/year/symbol (generous)
- 21 symbols: 420 potential events/year
- But: These don't align to when you're monitoring
- Reality: Maybe 1-2 visible per month during market hours

From our data:
- -15% threshold yielded only 495 events over 3 YEARS across 14 symbols
- That's ~12 events/month... but spread across random days/times
```

**Verdict**: The current settings are TOO RESTRICTIVE.

---

## 🔬 What Our Research Shows

### -10% Threshold Results
| Metric | -15% (Old) | -10% (New) | Difference |
|--------|------------|------------|------------|
| Events (3 years, 14 symbols) | 495 | 5,000+ | 10x more |
| Events (5 years, 250 symbols) | ~1,000 | 8,999 | 9x more |
| Midday Reversal Rate | Unknown | 59.8% | Validated |

### Optimal Configuration Discovered
```python
# Based on 8,999 event analysis:
RECOMMENDED_CONFIG = {
    'threshold_pct': -10.0,           # More opportunities
    'time_window': ('11:30', '14:00'), # Midday focus (60% win rate)
    'min_above_200sma': True,          # Optional but helpful
    'max_days_since_last': 5,          # Avoid clustering
    'spy_context': 'flat_or_up',       # Market tailwind
}
```

---

## 🎯 Recommendations

### Option A: Modify Current Bear Trap (Recommended)
**Change the existing deployed strategy**

```python
# In prod/bear_trap/config.json or strategy.py:

# FROM:
threshold_pct = -15.0
symbols = [list of 21]

# TO:
threshold_pct = -10.0
symbols = [expanded list of 100+]
time_filter = "midday"  # 11:30-14:00 only
```

**Pros**:
- Fastest to implement
- Uses existing infrastructure
- Maintains single strategy

**Cons**:
- May need to update EC2 deployment
- Testing overhead

### Option B: Create New "Midday Reversion" Strategy
**Keep Bear Trap at -15%, add new strategy at -10%**

```
prod/
├── bear_trap/              # Keep as-is (catches extreme moves)
├── midday_reversion/       # NEW: -10% threshold, midday focus
│   ├── strategy.py
│   ├── config.json
│   └── runner.py
```

**Pros**:
- No risk to current (even if it's not trading)
- Can run both in parallel
- Clear separation

**Cons**:
- More infrastructure
- More monitoring
- Potential overlap

### Option C: Hybrid Approach
**Keep -15% for "extreme" plays, -10% for "midday" plays**

```python
# Two alert tiers:
if drop_pct <= -15.0:
    priority = "EXTREME"
    position_size = 2.0x  # Larger position, rare
elif drop_pct <= -10.0 and time_bucket == "midday":
    priority = "STANDARD"
    position_size = 1.0x  # Normal position, frequent
```

**Pros**:
- Best of both worlds
- Dynamic response

**Cons**:
- More complex logic

---

## 📋 Immediate Actions Required

### 1. Check Current Bear Trap Configuration
```bash
# On EC2 or locally:
cat prod/bear_trap/config.json
```

Verify:
- Threshold setting
- Symbol list
- Entry/exit logic
- Time filters (if any)

### 2. Compare to Research Findings
Use `DATA_USAGE_GUIDE.md` to validate:
- Are current symbols in our dataset?
- What's their historical selloff frequency?
- At -15% vs -10%?

### 3. Decide on Path Forward
- **If want more trades**: Lower to -10%, expand symbols
- **If want quality**: Add midday time filter
- **If want both**: Implement Option C hybrid

---

## 📁 Files to Review/Modify

### Current Bear Trap Location
```
prod/bear_trap/
├── config.json         # Symbol list, threshold
├── strategy.py         # Core logic
├── runner.py           # Execution loop
└── README.md           # Documentation
```

### Research Data for Comparison
```
research/bear_trap_ml_scanner/
├── STRATEGY_CATALOG.md              # All strategies identified
├── HANDOFF_MIDDAY_REVERSION.md      # Midday strategy details
├── analysis/SEGMENT_RESULTS.txt      # Time bucket statistics
└── DATA_USAGE_GUIDE.md               # How to use the dataset
```

---

## 🎯 My Recommendation

**Option A: Modify Current Bear Trap**

### Immediate Changes:
1. Lower threshold to **-10%**
2. Add time filter for **midday (11:30-14:00)**
3. Expand symbol universe to **50-100 volatile small-caps**

### Expected Impact:
| Metric | Current (-15%) | New (-10% Midday) |
|--------|----------------|-------------------|
| Trades/month | 0-2 (sporadic) | 10-20 |
| Win Rate | Unknown | 55-60% |
| Opportunity | Very rare | Daily |

### Implementation:
1. Update `config.json` with new threshold
2. Add time filter to `strategy.py`
3. Deploy to EC2
4. Monitor for 1 week paper trading
5. Go live

---

## 💬 Questions to Answer

1. **What is the current exact configuration?** (Need to review config.json)
2. **Is the strategy running but just finding no trades?** (Check logs)
3. **Do we have capital allocated?** (Confirm account setup)
4. **Paper or live trading?** (Confirm environment)

---

*Assessment Created: January 22, 2026*
*Action Required: Review and decide on path forward*
