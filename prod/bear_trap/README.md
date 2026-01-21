# 🐻 Bear Trap Strategy

**Status**: ✅ Production  
**Account**: PA3DDLQCBJSE  
**Capital**: $100,000  
**Version**: Baseline v1.0

---

## Overview

The Bear Trap strategy is a momentum scalping system that capitalizes on extreme intraday crashes (-15% or more) followed by rapid reversals. It targets high-volatility, low-float stocks that experience panic selling and subsequent recovery.

## Strategy Logic

### Entry Criteria
- Stock down ≥15% from previous close
- Price reclaims session low (bear trap signal)
- High volume (2x+ average)
- Specific wick/body ratios indicating reversal

### Exit Criteria
- Trailing stop (ATR-based)
- End of day (all positions closed)
- Risk management triggers

### Position Sizing
- 10% of account equity per position
- Maximum 5 concurrent positions
- ATR-based stop loss

---

## Symbols

**Tier 1** (High Priority):
- MULN
- ONDS
- AMC
- NKLA
- WKHS

---

## Performance

**Validated Returns** (4-year backtest):
- Total Return: +135.6%
- Sharpe Ratio: 1.82
- Max Drawdown: -12.3%
- Win Rate: 58%

See `docs/VALIDATION_SUMMARY.md` for full validation results.

---

## Files

```
prod/bear_trap/
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
cd prod/bear_trap
python runner.py

# Run tests
pytest tests/ -v
```

---

## Deployment

Deployed via CI/CD to EC2:
- Service: `magellan-bear-trap.service`
- Logs: `/var/log/journal` (systemd)
- Trade logs: `/home/ssm-user/magellan/logs/`

---

## Monitoring

```bash
# Check service status
sudo systemctl status magellan-bear-trap

# View logs
sudo journalctl -u magellan-bear-trap -f

# Check recent trades
tail -f /home/ssm-user/magellan/logs/bear_trap_trades_*.csv
```

---

## Documentation

- `VALIDATION_SUMMARY.md` - Full validation results
- `DEPLOYMENT_DECISION.md` - Deployment rationale
- `DEPLOYMENT_CHECKLIST.md` - Deployment steps
- `parameters_bear_trap.md` - Parameter documentation

---

**Last Updated**: January 21, 2026
