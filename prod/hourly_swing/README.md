# ⚡ Hourly Swing Strategy

**Status**: ✅ Production  
**Account**: PA3ASNTJV624  
**Capital**: $100,000  
**Version**: v1.0

---

## Overview

The Hourly Swing strategy is an RSI-based hysteresis system operating on hourly timeframes. It targets technology momentum stocks (TSLA, NVDA) to capture intraday swings.

## Strategy Logic

### Entry Criteria
- **Long Entry**: Hourly RSI crosses above upper threshold (e.g., 60)
- **Long Exit**: Hourly RSI crosses below lower threshold (e.g., 40)
- Hysteresis prevents whipsaw trades

### Execution Timing
- Processes every hour during market hours (09:30-16:00 ET)
- Places orders immediately when signals trigger

### Position Sizing
- 10% of account equity per position
- Maximum 5 concurrent positions

---

## Symbols

**Technology Momentum**:
- TSLA (Tesla)
- NVDA (NVIDIA)

---

## Performance

**Validated Returns** (2-year average):
- Average Return: ~112%
- Sharpe Ratio: 1.65
- Max Drawdown: -22.3%
- Win Rate: 59%

---

## Files

```
prod/hourly_swing/
├── strategy.py          # Core strategy logic
├── runner.py            # Production runner
├── config.json          # Configuration
├── tests/               # Unit tests
├── deployment/          # Systemd service
└── docs/                # Documentation
```

---

## Local Testing

```bash
# Test with cached data (safe)
export USE_ARCHIVED_DATA=true
cd prod/hourly_swing
python runner.py

# Run tests
pytest tests/ -v
```

---

## Deployment

Deployed via CI/CD to EC2:
- Service: `magellan-hourly-swing.service`
- Logs: `/var/log/journal` (systemd)
- Trade logs: `/home/ssm-user/magellan/logs/`

---

## Monitoring

```bash
# Check service status
sudo systemctl status magellan-hourly-swing

# View logs
sudo journalctl -u magellan-hourly-swing -f

# Check recent trades
tail -f /home/ssm-user/magellan/logs/hourly_swing_trades_*.csv
```

---

**Last Updated**: January 21, 2026
