# 🚀 PROD - Production-Ready Strategies

This folder contains **production-ready copies** of validated strategies that are deployed to AWS EC2.

## Purpose

- **Deployment source** - CI/CD deploys from this folder to AWS
- **Production mirror** - Exact copies of what's running on EC2
- **Read-only** - Never edit directly, always copy from test/

## Rules

- ❌ **Do NOT edit directly** - All work happens in test/
- ✅ **Copy from test/** - Only way to update prod/
- ✅ **Deploy to AWS** - CI/CD deploys this folder
- ✅ **Production use** - Uses live Alpaca API on EC2

## Deployment Workflow

```bash
# 1. Work in test/
cd test/bear_trap
vim strategy.py
pytest tests/ -v

# 2. Copy to prod/
Copy-Item test/bear_trap prod/bear_trap -Recurse -Force

# 3. Deploy to AWS
git add prod/bear_trap
git commit -m "Deploy Bear Trap v1.2"
git push origin deployment/aws-paper-trading-setup

# 4. CI/CD automatically:
#    - Tests with cached data
#    - Deploys to EC2
#    - Restarts services
#    - Verifies health
```

## Current Strategies

### 1. Bear Trap
- **Status**: ✅ Live on EC2
- **Account**: PA3DDLQCBJSE
- **Symbols**: MULN, ONDS, AMC, NKLA, WKHS
- **Service**: magellan-bear-trap

### 2. Daily Trend
- **Status**: ✅ Live on EC2
- **Account**: PA3A2699UCJM
- **Symbols**: MAG7 + Index ETFs
- **Service**: magellan-daily-trend

### 3. Hourly Swing
- **Status**: ✅ Live on EC2
- **Account**: PA3ASNTJV624
- **Symbols**: TSLA, NVDA
- **Service**: magellan-hourly-swing

## Structure

```
prod/
├── bear_trap/           # Production copy (deployed to AWS)
│   ├── strategy.py
│   ├── runner.py        # Uses live API on EC2
│   ├── config.json
│   ├── tests/
│   ├── deployment/
│   │   └── systemd/
│   └── docs/
│
├── daily_trend/         # Production copy
└── hourly_swing/        # Production copy
```

## Environment Behavior

### **Local** (if you run prod/ code locally):
```bash
# Still uses cache if env var set
export USE_ARCHIVED_DATA=true
cd prod/bear_trap
python runner.py  # Safe - uses cache
```

### **EC2 Production**:
```bash
# No USE_ARCHIVED_DATA variable
python runner.py  # Uses live Alpaca API
```

## Monitoring

```bash
# Check EC2 service status
sudo systemctl status magellan-bear-trap
sudo systemctl status magellan-daily-trend
sudo systemctl status magellan-hourly-swing

# View logs
sudo journalctl -u magellan-bear-trap -f

# Check trades
tail -f /home/ssm-user/magellan/logs/bear_trap_trades_*.csv
```

## Rollback

If deployment fails:
```bash
# Revert local changes
git revert <commit-hash>
git push

# Or manually on EC2
ssh to EC2
git checkout <previous-commit>
sudo systemctl restart magellan-*
```

---

**Key Principle**: This folder is the **source of truth** for what's deployed to AWS.  
**All development** happens in `test/`, then gets **copied here** when ready.
