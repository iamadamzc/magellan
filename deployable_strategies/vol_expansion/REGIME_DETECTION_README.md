# Regime Detection System

## Overview

The Regime Detection System is a critical component that determines when market conditions are favorable for trading. It prevents losses by identifying when the market regime does NOT match historically profitable periods.

## Core Concept

1. **Learn from history**: Identify the best-performing 90/60/30-day windows from 2022-2024
2. **Extract signatures**: Capture market characteristics (volatility, trend, ATR expansion, volume) during those periods
3. **Match daily**: Each session, compare current market to those signatures
4. **Binary decision**: Trade (if match) or Don't Trade (if no match)

## Key Finding

**2025 matched 90-day favorable regime 80% of the time** - explaining why optimized strategies worked so well this year.

---

## Files

| File | Purpose |
|------|---------|
| `regime_detection.py` | Build regime signatures from historical data |
| `regime_signatures.json` | Saved signatures (volatility, trend, ATR expansion, etc.) |
| `check_regime_daily.py` | **Daily session checker** - run before market open |
| `regime_log.jsonl` | Historical log of daily regime checks |

---

## Daily Workflow

### Before Market Open

```bash
cd a:\1\Magellan
python test/vol_expansion/check_regime_daily.py
```

### Interpret Output

- ✅ **90-day regime** → SAFE - Trade with full position size
- ⚠️ **60-day regime** → MODERATE - Trade but monitor closely  
- ⚠️⚠️ **30-day regime** → CAUTION - Reduce position size 50%
- ❌ **NO MATCH** → DO NOT TRADE - Conditions don't match any profitable period

---

## Technical Details

### Regime Features

The system analyzes 5 market characteristics:

1. **Volatility** = ATR(20) / Price
   - Measures absolute volatility level

2. **Trend** = 20-day price slope
   - Captures directional bias

3. **ATR Expansion** = ATR(20) / ATR(50)
   - Detects if volatility is expanding or contracting

4. **Volume Trend** = Vol(20) / Vol(50)
   - Identifies volume shifts

5. **Price Range** = (High - Low) / Close
   - Measures intraday movement

### Matching Algorithm

- Each feature has min/max bounds from historical favorable periods
- Bounds expanded by 30% tolerance for robustness
- Current values must match 80%+ of features to qualify
- Priority: 90-day > 60-day > 30-day windows

---

## Integration with Magellan

### Recommended Approach

1. **Run regime check every morning** before deploying strategies
2. **Log results** to track regime persistence
3. **Disable all trading** on NO MATCH days
4. **Reduce position sizing** on 30-day/60-day matches
5. **Update signatures quarterly** (optional) as more data accumulates

### Example Integration

```python
from check_regime_daily import check_regime

# Before deploying strategies
regime = check_regime('IVV')

if regime['status'] == 'NO_TRADE':
    print("Regime unfavorable - skipping trading today")
    sys.exit(0)
elif regime['status'] == 'CAUTION':
    print("Reducing position size to 50%")
    position_multiplier = 0.5
else:
    position_multiplier = 1.0

# Proceed with trading...
```

---

## Validation Results

### 2025 Performance
- **90-day matches**: 172/216 days (80%)
- **60-day matches**: 16 days
- **30-day matches**: 4 days  
- **No matches**: 24 days

This explains why strategies performed exceptionally well in 2025.

### Walk-Forward Validation
Revealed that strategies are **regime-specific**:
- **2024**: Different regime → strategies failed
- **2025**: Favorable regime (80% match) → strategies succeeded

The regime filter would have prevented trading during unfavorable 2024 periods.

---

## Maintenance

### Quarterly Updates (Optional)

Re-run signature detection as more data accumulates:

```bash
python test/vol_expansion/regime_detection.py
```

This refreshes `regime_signatures.json` with updated thresholds.

### Monitoring

Check `regime_log.jsonl` periodically:
- If seeing consecutive NO MATCH days, market may be shifting
- If regime changes rapidly, consider pausing trading
- Long stretches of 90-day matches = high confidence period

---

## Why This Works

Traditional strategies fail because they don't adapt to market regimes. This system:
- **Learns** what profitable markets look like
- **Filters** out unprofitable regimes automatically  
- **Binary decision** - no gray area, clear ON/OFF signal
- **Historical validation** - learned from 2022-2024, validated on 2025

It's not predicting the future - it's recognizing when current conditions match past success.
