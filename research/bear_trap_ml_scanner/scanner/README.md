# Selloff Scanner - Real-Time Opportunity Detection

> **Status**: MVP Complete  
> **Version**: 1.0.0  
> **Created**: January 22, 2026

---

## 🎯 Overview

The Selloff Scanner is a real-time detection system for intraday selloff opportunities. It monitors a universe of volatile small-cap stocks and alerts when -10% selloffs occur, with priority scoring based on research findings.

### Key Features
- ✅ **Real-time detection** - Polls every 60 seconds
- ✅ **First-cross deduplication** - One alert per symbol per day
- ✅ **Time filtering** - Optional midday-only mode (11:30-14:00)
- ✅ **Priority scoring** - Research-based ranking (0-70 points)
- ✅ **Multiple outputs** - Console + JSON files
- ✅ **Configurable universe** - 50 or 250 symbols

---

## 📊 Research Foundation

Based on analysis of 8,999 selloff events:
- **Midday selloffs**: 59.8% reversal rate (vs 42.4% baseline)
- **Time is strongest predictor**: +17% edge from timing alone
- **Market context matters**: SPY up days = +5% win rate
- **Trend helps**: Above 200 SMA = +3% win rate

---

## 🏗️ Architecture

```
scanner/
├── __init__.py              # Package exports
├── selloff_detector.py      # Core detection logic
├── universe_manager.py      # Symbol list management
├── priority_scorer.py       # Opportunity ranking
├── alert_manager.py         # Output and notifications
└── scanner_runner.py        # Main execution loop
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **SelloffDetector** | Fetches 1-min bars, detects -10% crosses |
| **UniverseManager** | Manages symbol lists (50/250/custom) |
| **PriorityScorer** | Scores events 0-70 based on research |
| **AlertManager** | Console + JSON output |
| **scanner_runner** | Main loop, market hours checking |

---

## 🚀 Quick Start

### Installation
```bash
cd a:\1\Magellan
pip install alpaca-py python-dotenv pytz
```

### Configuration
Set environment variables in `.env`:
```bash
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
```

### Run Scanner
```bash
python research\bear_trap_ml_scanner\scanner\scanner_runner.py
```

---

## ⚙️ Configuration

Edit `scanner_runner.py` to configure:

```python
# Detection threshold
THRESHOLD = -10.0  # -10% drop from session open

# Symbol universe
UNIVERSE_MODE = "static_50"  # or "static_250"

# Time filter
MIDDAY_ONLY = True  # Only scan 11:30-14:00 ET

# Scan frequency
SCAN_INTERVAL = 60  # seconds
```

---

## 📈 Priority Scoring

Events are scored 0-70 points based on:

| Factor | Max Points | Criteria |
|--------|------------|----------|
| **Time Bucket** | 30 | Midday/Morning = 30, Afternoon = 15, Power Hour = 5 |
| **Market Context** | 15 | SPY >0.5% = 15, SPY >0% = 10, SPY flat = 5 |
| **Trend** | 10 | Above 200 SMA = 10 |
| **Range Position** | 10 | Upper half of 52w range = 10 |
| **Severity** | 5 | Drop <-15% = 5, <-12% = 3 |

### Priority Tiers
- **HIGH (50+)**: TRADE - Take position
- **MEDIUM (30-49)**: CONSIDER - Review carefully
- **LOW (<30)**: SKIP - Ignore

---

## 📤 Output

### Console Alert Example
```
================================================================================
[HIGH] SELLOFF DETECTED - TRADE
================================================================================
Symbol:       RIOT
Drop:         -11.5%
Price:        $11.06 (Open: $12.50)
Time:         12:45:32 (midday)
Priority:     55/70

Score Breakdown:
  Time (midday): 30
  Market (up, SPY +0.5%): 15
  Trend (above 200 SMA: True): 10
  Range (position: 45%): 5
  Severity (-11.5%): 0
================================================================================
```

### JSON Output
Alerts are saved to:
```
research/bear_trap_ml_scanner/scanner/alerts/alerts_2026-01-22.json
```

Format:
```json
{
  "timestamp": "2026-01-22T12:45:32",
  "event": {
    "symbol": "RIOT",
    "drop_pct": -11.5,
    "current_price": 11.06,
    "time_bucket": "midday"
  },
  "score": {
    "total_score": 55,
    "tier": "HIGH",
    "action": "TRADE"
  }
}
```

---

## 🔧 Symbol Universe

### Static 50 (Default)
Validated volatile small-caps from research:
```
ONDS, ACB, AMC, WKHS, MULN, GOEV, BTCS, SENS, GME,
PLUG, TLRY, NVAX, MARA, RIOT, OCGN, NKLA, ...
```

### Static 250
Full research universe (set `UNIVERSE_MODE = "static_250"`)

### Custom
Create `custom_universe.json`:
```json
{
  "symbols": ["RIOT", "MARA", "AMC", "GME", ...]
}
```

Set `UNIVERSE_MODE = "custom"`

---

## 🕐 Operating Hours

### Market Hours
- **Monday-Friday**: 9:30 AM - 4:00 PM ET
- **Closed**: Weekends and holidays

### Midday Window (if enabled)
- **11:30 AM - 2:00 PM ET**
- Highest probability window (60% win rate)

---

## 📊 Expected Performance

### Scan Rate
- **50 symbols**: ~3-5 seconds per scan
- **250 symbols**: ~15-20 seconds per scan
- **Frequency**: Every 60 seconds

### Alert Volume
- **Midday only**: 2-5 alerts per day
- **All day**: 5-15 alerts per day
- **High volatility days**: 10-30 alerts

---

## 🔌 Integration

### With Midday Reversion Strategy
```python
# In test/midday_reversion/strategy.py
from research.bear_trap_ml_scanner.scanner import SelloffDetector

# Use scanner to detect opportunities
# instead of polling all symbols
```

### With Trading Bot
```python
# Subscribe to scanner alerts
# Execute trades based on priority tier
if alert["score"]["tier"] == "HIGH":
    execute_trade(alert["event"]["symbol"])
```

---

## 🐛 Troubleshooting

### No Alerts
- Check market hours (9:30-16:00 ET weekdays)
- Check midday filter (11:30-14:00 if enabled)
- Verify API credentials
- Check threshold (-10% may be too strict on calm days)

### API Rate Limits
- Reduce scan frequency (increase `SCAN_INTERVAL`)
- Reduce universe size (use static_50)
- Check Alpaca subscription tier

### Missing Data
- Verify Market Data Plus subscription
- Check symbol validity
- Review scanner.log for errors

---

## 📝 Logs

Scanner logs are written to:
```
research/bear_trap_ml_scanner/scanner/scanner.log
```

Log levels:
- **INFO**: Normal operation, scan results
- **WARNING**: Issues, missing data
- **ERROR**: API errors, exceptions

---

## 🚀 Next Steps

### Phase 2 Enhancements
- [ ] WebSocket streaming (faster detection)
- [ ] SPY context auto-fetch
- [ ] 200 SMA calculation
- [ ] 52-week range calculation
- [ ] Discord/Telegram notifications

### Phase 3 ML Integration
- [ ] Load XGBoost model
- [ ] Probability-based scoring
- [ ] Position sizing recommendations
- [ ] Confidence intervals

---

## 📚 Related Documentation

- **Research**: `research/bear_trap_ml_scanner/README.md`
- **Data Guide**: `research/bear_trap_ml_scanner/DATA_USAGE_GUIDE.md`
- **Strategy**: `test/midday_reversion/README.md`
- **Scanner Handoff**: `research/bear_trap_ml_scanner/HANDOFF_SCANNER_BUILD.md`

---

*Scanner MVP created: January 22, 2026*  
*Based on 8,999 event research*  
*Ready for testing and enhancement*
