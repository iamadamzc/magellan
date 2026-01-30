# 📊 MIDAS Protocol Strategy

**Status**: ✅ Ready for Deployment  
**Account**: PA3DDLQCBJSE  
**Capital**: $100,000  
**Version**: Baseline v1.0

---

## Overview

The MIDAS Protocol (Asian Session Mean Reversion) is a high-frequency futures strategy targeting Micro Nasdaq-100 (MNQ) during the Asian trading session. It capitalizes on mean reversion patterns during low-liquidity hours with strict risk management.

## Strategy Logic

### Instrument
- **Symbol**: MNQ (Micro Nasdaq-100 Futures)
- **Timeframe**: 1-Minute Candles
- **Session**: 02:00:00 to 06:00:00 UTC (Asian Session)
- **Direction**: LONG ONLY

### Indicators (Calculated on Every Bar Close)

1. **EMA 200**: Exponential Moving Average (Length 200)
2. **Velocity (5m)**: Current Close - Close[5 bars ago]
3. **ATR Ratio**: ATR(14) / ATR_Avg(50)

### Entry Logic

**Global Filter (Glitch Guard)**:
- IF Velocity < -150: **DO NOT TRADE** (Data spike/Flash Crash event)

**Setup A: "The Crash Reversal"**
- Velocity: Between -150 and -67
- Price distance to EMA 200: ≤ 220 points
- ATR Ratio: > 0.50
- **Action**: BUY MARKET

**Setup B: "The Quiet Drift"**
- Velocity: ≤ 10
- Price distance to EMA 200: ≤ 220 points
- ATR Ratio: Between 0.06 and 0.50
- **Action**: BUY MARKET

### Exit Logic (OCO Bracket)

**Optimized "Champion" Settings from Grid Search**:
- **Stop Loss**: 20 Points ($40 per micro contract)
- **Take Profit**: 120 Points ($240 per micro contract)
- **Time-Based Exit**: 60 Minutes (Bars)
  - If trade open for 60 bars and neither SL nor TP hit: Close at Market

**Risk/Reward**: 6.0 ($240 profit / $40 risk)

### Risk Management

- **Max Daily Loss**: $300 per contract
  - If Net P&L hits -$300, **HALT all trading** until next session
- **Max Positions**: 1 (No pyramiding)
- **Direction**: LONG ONLY
- **Point Value**: $2.00 per point (MNQ micro contract)

---

## Trading Hours

**Asian Session Only**:
- **Start**: 02:00:00 UTC
- **End**: 06:00:00 UTC
- **Duration**: 4 hours
- **Status**: Strictly FLAT outside these hours

**No trading**:
- Before 02:00:00 UTC
- After 06:00:00 UTC
- Weekends

---

## Files

```
prod/midas_protocol/
├── strategy.py          # Core strategy logic
├── runner.py            # Production runner
├── config.json          # Configuration
├── tests/               # Unit tests
├── deployment/          # Systemd service
└── docs/                # Documentation
```

---

## Expected Performance

**Backtest Metrics** (From Grid Search Optimization):
- Setup: Asian Session MNQ Mean Reversion
- Optimal Parameters: SL=20pts, TP=120pts, Time=60 bars
- Risk/Reward: 6:1
- Max Daily Risk: $300

See optimization conversation for full validation results.

---

## Local Testing

```bash
# Test with cached data (safe)
export USE_ARCHIVED_DATA=true
export ENVIRONMENT=testing
cd prod/midas_protocol
python runner.py

# Run tests
pytest tests/ -v
```

---

## Deployment

Deployed via CI/CD to EC2:
- **Service**: `magellan-midas-protocol.service`
- **Logs**: `/var/log/journal` (systemd)
- **Trade logs**: `/home/ssm-user/magellan/logs/`

**This strategy will replace**: `bear_trap` strategy on deployment.

---

## Monitoring

```bash
# Check service status
sudo systemctl status magellan-midas-protocol

# View logs
sudo journalctl -u magellan-midas-protocol -f

# Check recent trades
tail -f /home/ssm-user/magellan/logs/midas_protocol_trades_*.csv
```

---

## Session Schedule (UTC)

| Time (UTC) | Status | Action |
|------------|--------|--------|
| 00:00-01:59 | FLAT | No trading, system monitoring |
| 02:00-06:00 | **ACTIVE** | **Asian Session Trading** |
| 06:00-23:59 | FLAT | No trading, positions closed |

---

## Key Features

✅ **Strict Session Control**: Only trades 02:00-06:00 UTC  
✅ **Data Spike Protection**: Glitch Guard blocks velocity < -150  
✅ **Dual Entry Setups**: Crash Reversal + Quiet Drift  
✅ **OCO Bracket Exits**: Automated SL/TP/Time management  
✅ **Daily Loss Circuit Breaker**: Halts at -$300  
✅ **Long-Only**: No short positions  
✅ **Single Position**: No pyramiding or position averaging  

---

## Documentation

- `STRATEGY_SPECIFICATION.md` - Full strategy specification
- `OPTIMIZATION_RESULTS.md` - Grid search optimization results
- `DEPLOYMENT_CHECKLIST.md` - Deployment steps

---

**Last Updated**: January 30, 2026  
**Created By**: Magellan Development Team  
**Strategy Type**: Futures Mean Reversion (Asian Session)
