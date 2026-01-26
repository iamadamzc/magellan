# Scanner Development Handoff

> **For**: Next Agent / Developer
> **Project**: Bear Trap ML-Enhanced Scanner
> **Created**: January 22, 2026
> **Status**: Research Complete, Scanner Build Required

---

## 🎯 Project Context

### Original Objective
Build a **dynamic scanner** to identify real-time selloff opportunities for the Bear Trap strategy, replacing the current static 21-symbol watchlist.

### Current State
1. ✅ **Data collection complete**: 8,999 historical events collected
2. ✅ **Analysis complete**: Statistical edge identified
3. ✅ **Strategy defined**: Midday Reversion (~60% win rate)
4. ❌ **Scanner not built**: Need real-time detection system

---

## 📊 What We Learned (Key Scanner Requirements)

### Scanner Detection Criteria
```python
SELLOFF_CRITERIA = {
    'threshold_pct': -10.0,      # Drop from session open
    'deduplication': 'first_cross',  # Only first bar crossing threshold
    'time_window': {
        'start': '09:30',
        'end': '16:00'
    }
}

# Optimal trading windows discovered:
TIME_PRIORITY = {
    'midday': (11, 30, 14, 0),    # 60% reversal - PRIMARY
    'morning': (9, 30, 11, 30),    # 66% reversal - SECONDARY
    'afternoon': (14, 0, 15, 0),   # 38% reversal - LOWER
    'power_hour': (15, 0, 16, 0),  # 15% 60-min, 71% EOD - DIFFERENT
}
```

### Required Scanner Filters
Based on our analysis, the scanner MUST include:

| Filter | Purpose | Implementation |
|--------|---------|----------------|
| **Time Filter** | Focus on high-probability windows | `11:30 < time < 14:00` for midday |
| **SPY Check** | Market tailwind | `SPY change > 0%` increases win rate |
| **Trend Filter** | Avoid falling knives | `close > 200 SMA` |
| **Range Filter** | Avoid 52w lows | `price > 52w_low * 1.20` |
| **Cluster Filter** | Skip recent sellers | `last_selloff > 5 days ago` |

### Alert Priority System
```python
def calculate_priority(event):
    """Score selloff opportunities"""
    score = 0
    
    # Time bucket (most important)
    if event.time_bucket == 'midday':
        score += 30
    elif event.time_bucket == 'morning':
        score += 25
    
    # Market context
    if event.spy_change > 0:
        score += 15
    
    # Trend
    if event.above_200sma:
        score += 10
    
    # Not near lows
    if event.price_range_position > 0.3:
        score += 10
    
    return score  # Max ~65

# Priority tiers:
# 50+: HIGH PRIORITY - Take trade
# 30-50: MEDIUM - Consider with caution
# <30: LOW - Skip or reduce size
```

---

## 🔧 Scanner Architecture Options

### Option 1: Real-Time Streaming (Recommended)
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Alpaca WebSocket │────▶│ Selloff Detector │────▶│ Alert Generator │
│ (1-min bars)     │     │ (Check criteria) │     │ (Prioritize)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │ Trading Decision │
                        │ Engine           │
                        └──────────────────┘
```

**Pros**: Fastest detection, lowest latency
**Cons**: Complex, requires persistent connection

### Option 2: Polling-Based (Simpler)
```
Every 1 minute:
1. Query Alpaca for bar data on universe
2. Calculate drop from open for each
3. Filter for -10% threshold
4. Apply time/trend filters
5. Generate alerts
```

**Pros**: Simple, robust, easy to debug
**Cons**: 1-minute lag, may miss fast moves

### Option 3: FMP Gainers/Losers Scan (Existing)
```
Use FMP /stock_market/losers endpoint
Filter for >-10%
Cross-reference with Alpaca for bars
```

**Pros**: Pre-filtered universe
**Cons**: FMP has limitations (see below)

---

## 📡 API Resources

### Alpaca Market Data Plus
- **Status**: Working, used for historical collection
- **Endpoint**: Real-time and historical bars
- **Keys**: `APCA_API_KEY_ID`, `APCA_API_SECRET_KEY`
- **Rate Limits**: 200 requests/minute

### FMP Ultimate
- **Status**: Partially working
- **Working Endpoints**:
  - `/v3/quote/{symbol}` - Real-time quotes
  - `/v3/historical-chart/1min/{symbol}` - Intraday
  - `/v3/market-hours` - Market status
- **NOT Working (Legacy)**:
  - `/stock_market/losers` - Returns empty
  - Historical screeners - Tier restricted
- **Key**: `FMP_API_KEY`

### Recommendation
**Primary**: Alpaca WebSocket for real-time
**Fallback**: Alpaca REST polling every minute
**Universe**: Pre-defined list of volatile small-caps (250 symbols from our collection)

---

## 📁 Code Assets

### Existing Collection Scripts
```
research/bear_trap_ml_scanner/data_collection/
├── collect_resumable.py          # Multi-year data collector
├── collect_ultimate_dataset.py   # Full 250-symbol collector
├── extract_outcomes.py           # Post-selloff recovery data
├── extract_ultimate_features.py  # Feature extraction
└── ...
```

### Scanner To Be Built
```
research/bear_trap_ml_scanner/scanner/
├── __init__.py
├── selloff_detector.py           # Core detection logic
├── priority_scorer.py            # Opportunity ranking
├── alert_manager.py              # Notification system
├── universe_manager.py           # Symbol list management
└── real_time_runner.py           # Main execution loop
```

### Integration with Trading
```
prod/bear_trap/
├── strategy.py                   # Current Bear Trap (modify or extend)
└── scanner_integration.py        # Connect scanner to strategy
```

---

## 🔢 Universe Management

### Static Universe (Quick Start)
Use the 250 symbols from our data collection:
```python
# Located in: research/bear_trap_ml_scanner/data_collection/collect_resumable.py
# Look for: get_symbol_universe() method
```

### Dynamic Universe (Future)
1. Morning scan for pre-market movers
2. FMP active stocks
3. High RVOL filters
4. Sector rotation

---

## ✅ Scanner Build Checklist

### Phase 1: MVP Scanner
- [ ] Symbol universe loader (250 symbols)
- [ ] 1-minute bar polling loop
- [ ] -10% threshold detector
- [ ] First-cross deduplication
- [ ] Console logging of alerts

### Phase 2: Smart Scanner
- [ ] Time bucket filter (midday priority)
- [ ] SPY context check
- [ ] 200 SMA filter (requires daily data)
- [ ] Priority scoring
- [ ] Structured alert output (JSON)

### Phase 3: Integrated Scanner
- [ ] WebSocket streaming (faster)
- [ ] Integration with Bear Trap strategy
- [ ] Position sizing from ML model
- [ ] Dashboard/notification system

---

## ⚠️ Lessons Learned

### FMP API Issues
- `/stock_market/losers` returns empty for historical dates
- Screener endpoints require higher tier
- **Solution**: Use Alpaca for all bar data, FMP only for supplementary

### Alpaca Considerations
- Historical intraday limited by subscription
- Need to handle market hours correctly (9:30-16:00 ET)
- Rate limiting important for large universes

### Time Zone Handling
- All times should be Eastern Time
- Be careful with daylight saving transitions
- Alpaca returns UTC - convert to ET for logic

---

## 📊 Expected Scanner Output

### Alert Format
```json
{
  "timestamp": "2026-01-23T12:45:00-05:00",
  "symbol": "RIOT",
  "event": "selloff_detected",
  "drop_pct": -11.5,
  "session_open": 12.50,
  "current_low": 11.06,
  "time_bucket": "midday",
  "priority_score": 55,
  "priority_tier": "HIGH",
  "context": {
    "spy_change": 0.45,
    "above_200sma": true,
    "days_since_last_selloff": 12
  },
  "action": "TRADE",
  "suggested_entry": 11.10,
  "suggested_stop": 10.50,
  "suggested_target": 11.85
}
```

---

## 🚀 Next Steps

1. **Choose architecture**: Streaming vs Polling
2. **Build MVP scanner**: Detection only, no trading
3. **Test on paper**: Run for 1 week, validate detections
4. **Integrate**: Connect to Bear Trap trading logic
5. **Deploy to EC2**: Run alongside other strategies

---

## 💬 Questions for Developer

1. Should scanner run as separate service or in strategy process?
2. What notification method preferred (console, email, Discord)?
3. Should we start with reduced universe (50 symbols) for testing?
4. Integration preference: modify Bear Trap or new strategy file?

---

*Scanner Handoff Created: January 22, 2026*
*Strategy Validated, Scanner Build Ready*
