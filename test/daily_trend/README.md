# 📈 Daily Trend Strategy

**Status**: ✅ Production  
**Account**: PA3A2699UCJM  
**Capital**: $100,000  
**Version**: v1.0

---

## Overview

The Daily Trend strategy is an RSI-based hysteresis system that follows intermediate-term trends in large-cap stocks and index ETFs. It uses dual RSI thresholds to reduce whipsaw and capture sustained directional moves.

## Strategy Logic

### Entry Criteria
- **Long Entry**: RSI crosses above upper threshold (e.g., 55)
- **Long Exit**: RSI crosses below lower threshold (e.g., 45)
- Hysteresis prevents rapid flip-flopping

### Execution Timing
- **Signal Generation**: 16:05 ET (after market close)
- **Order Execution**: 09:30 ET next day (market open)

### Position Sizing
- 10% of account equity per position
- Maximum 5 concurrent positions

---

## Symbols

**MAG7 + Index ETFs**:
- AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
- SPY, QQQ, IWM
- GLD (gold ETF)

Each symbol has custom RSI thresholds optimized via walk-forward analysis.

---

## Performance

**Validated Returns** (2-year average):
- Average Return: ~45.2%
- Sharpe Ratio: 1.45
- Max Drawdown: -18.5%
- Win Rate: 62%

See `docs/` for full validation results.

---

## Files

```
prod/daily_trend/
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
cd prod/daily_trend
python runner.py

# Run tests
pytest tests/ -v
```

---

## Deployment

Deployed via CI/CD to EC2:
- Service: `magellan-daily-trend.service`
- Logs: `/var/log/journal` (systemd)
- Trade logs: `/home/ssm-user/magellan/logs/`

---

## Monitoring

```bash
# Check service status
sudo systemctl status magellan-daily-trend

# View logs
sudo journalctl -u magellan-daily-trend -f

# Check recent trades
tail -f /home/ssm-user/magellan/logs/daily_trend_trades_*.csv
```

---

**Last Updated**: January 21, 2026
