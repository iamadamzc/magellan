# 🚀 PROD - Production Strategies

This folder contains production-ready strategies that are deployed and trading live on EC2.

## Purpose

- **Source of truth** for all production code
- Live trading strategies
- Production deployments
- Strategy maintenance and updates

## Rules

- ✅ **Only validated strategies**
- ✅ Comprehensive tests required
- ✅ Full documentation required
- ✅ Environment-aware execution
- ✅ Deployment artifacts included

## Environment Behavior

### Local Testing (Safe)
```bash
export USE_ARCHIVED_DATA=true
cd prod/bear_trap
python runner.py
# Uses cached data - safe for testing
```

### CI/CD Testing (Automated)
```yaml
env:
  USE_ARCHIVED_DATA: 'true'
# Always uses cached data in CI/CD
```

### Production (EC2)
```bash
# No USE_ARCHIVED_DATA variable set
python runner.py
# Uses live Alpaca API - real trading
```

## Strategy Structure

```
prod/
├── strategy_name/
│   ├── strategy.py          # Core strategy logic
│   ├── runner.py            # Universal runner (env-aware)
│   ├── config.json          # Production configuration
│   │
│   ├── tests/               # Unit & integration tests
│   │   ├── test_strategy.py
│   │   └── test_integration.py
│   │
│   ├── deployment/          # Deployment artifacts
│   │   ├── systemd/
│   │   │   └── magellan-strategy-name.service
│   │   └── README.md        # Deployment guide
│   │
│   └── docs/                # Complete documentation
│       ├── README.md        # Overview
│       ├── parameters.md    # Parameter guide
│       ├── validation.md    # Validation results
│       └── performance.md   # Performance tracking
```

## Current Strategies

### 1. Bear Trap
- **Status**: ✅ Live
- **Account**: PA3DDLQCBJSE
- **Symbols**: MULN, ONDS, AMC, NKLA, WKHS
- **Description**: Momentum scalping on -15% crashes

### 2. Daily Trend
- **Status**: ✅ Live
- **Account**: PA3A2699UCJM
- **Symbols**: MAG7 + Index ETFs
- **Description**: RSI hysteresis trend following

### 3. Hourly Swing
- **Status**: ✅ Live
- **Account**: PA3ASNTJV624
- **Symbols**: TSLA, NVDA
- **Description**: Hourly RSI swing trading

## Deployment Workflow

```
1. Edit code in prod/strategy_name/
2. Test locally: USE_ARCHIVED_DATA=true python runner.py
3. Run tests: pytest tests/
4. Commit: git add prod/strategy_name
5. Push: git push origin main
6. CI/CD automatically:
   - Tests with cached data
   - Deploys to EC2
   - Restarts services
   - Verifies health
```

## Rollback Procedure

```bash
# If issues arise:
git log --oneline -5
git revert <bad-commit>
git push origin main
# CI/CD redeploys previous version
```

## Monitoring

- **Logs**: `/home/ssm-user/magellan/logs/`
- **Services**: `sudo systemctl status magellan-*`
- **Health**: Check Alpaca dashboard for orders
