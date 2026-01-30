# 🏗️ STANDARD DEV/TEST/PROD STRUCTURE
**Date**: January 21, 2026  
**Status**: FINAL PROPOSAL - Standard Nomenclature

---

## 🎯 STANDARD THREE-TIER MODEL

```
dev/     ← Development & experimentation
test/    ← Validation & staging  
prod/    ← Production-ready code (source of truth)
```

**This aligns with industry standard!** ✅

---

## 📊 FOLDER STRUCTURE

```
Magellan/
│
├── dev/                     # DEVELOPMENT
│   ├── new_ml_strategy/     # Active research
│   ├── bear_trap_v2/        # Experimental versions
│   └── ideas/               # Strategy ideas
│
├── test/                    # VALIDATION/STAGING
│   ├── bear_trap/           # Final validation before prod
│   ├── daily_trend/         # Testing new features
│   └── hourly_swing/        # Pre-production testing
│
├── prod/                    # PRODUCTION (source of truth)
│   ├── bear_trap/
│   │   ├── strategy.py      # Core strategy logic
│   │   ├── runner.py        # Universal runner (env-aware)
│   │   ├── config.json      # Configuration
│   │   ├── tests/           # Unit tests
│   │   ├── deployment/      # Systemd, etc.
│   │   └── docs/            # Documentation
│   │
│   ├── daily_trend/
│   │   ├── strategy.py
│   │   ├── runner.py
│   │   ├── config.json
│   │   ├── tests/
│   │   ├── deployment/
│   │   └── docs/
│   │
│   └── hourly_swing/
│       ├── strategy.py
│       ├── runner.py
│       ├── config.json
│       ├── tests/
│       ├── deployment/
│       └── docs/
│
├── src/                     # Shared utilities
├── scripts/                 # Helper scripts
├── tests/                   # Integration tests
└── docs/                    # Documentation
```

---

## 🔄 LIFECYCLE WORKFLOW

```
┌─────────────────────────────────────────────────────────┐
│  DEV (dev/)                                              │
│  • New strategy ideas                                    │
│  • Backtesting & experimentation                         │
│  • Parameter tuning                                      │
│  • Jupyter notebooks                                     │
│  • Always uses cached data                               │
│                                                          │
│  Exit Criteria:                                          │
│  ✅ Positive backtest results                            │
│  ✅ Basic validation complete                            │
│                                                          │
│  Next: Move to test/                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  TEST (test/)                                            │
│  • Final validation                                      │
│  • Walk-forward analysis                                 │
│  • Perturbation testing                                  │
│  • Production code structure                             │
│  • Integration testing                                   │
│  • Uses cached data for testing                          │
│                                                          │
│  Exit Criteria:                                          │
│  ✅ All validation tests pass                            │
│  ✅ Code meets production standards                      │
│  ✅ Documentation complete                               │
│  ✅ Approved for production                              │
│                                                          │
│  Next: Promote to prod/                                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  PROD (prod/)                                            │
│  • Production-ready code (SOURCE OF TRUTH)               │
│  • Live on EC2                                           │
│  • Uses live Alpaca API                                  │
│  • Real trading                                          │
│                                                          │
│  Local Testing:                                          │
│  • USE_ARCHIVED_DATA=true → cache (safe testing)        │
│                                                          │
│  CI/CD Testing:                                          │
│  • USE_ARCHIVED_DATA=true → cache (automated tests)     │
│                                                          │
│  Production (EC2):                                       │
│  • No USE_ARCHIVED_DATA → live API (real trading)       │
│                                                          │
│  Updates:                                                │
│  • Edit in prod/                                         │
│  • Test locally with cache                               │
│  • Git push → CI/CD → EC2                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 ENVIRONMENT MAPPING

| Folder | Environment | Data Source | Purpose |
|--------|-------------|-------------|---------|
| **dev/** | Development | Cache only | Experimentation |
| **test/** | Staging | Cache only | Validation |
| **prod/** (local) | Staging | Cache (USE_ARCHIVED_DATA=true) | Safe testing |
| **prod/** (CI/CD) | Testing | Cache (USE_ARCHIVED_DATA=true) | Automated tests |
| **prod/** (EC2) | Production | Live API (no env var) | Real trading |

---

## 🔑 KEY PRINCIPLE: Environment-Aware Runner

**Same code in prod/, different behavior based on environment**:

```python
# prod/bear_trap/runner.py

import os

def get_data_client(api_key, api_secret):
    """Get data client based on environment"""
    
    # Check environment variable
    use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
    
    if use_cache:
        # LOCAL TESTING or CI/CD: Use cache
        from src.data_cache import DataCache
        return DataCache(api_key, api_secret)
    else:
        # PRODUCTION (EC2): Use live API
        from alpaca.data.historical import StockHistoricalDataClient
        return StockHistoricalDataClient(api_key, api_secret)

def main():
    # Get credentials
    api_key, api_secret = get_credentials()
    
    # Get appropriate data client
    data_client = get_data_client(api_key, api_secret)
    
    # Run strategy (same code, different data source)
    strategy = BearTrapStrategy(config, data_client)
    strategy.run()
```

**Usage**:

```bash
# LOCAL: Test with cache
export USE_ARCHIVED_DATA=true
python prod/bear_trap/runner.py

# LOCAL: Test with live API (careful!)
unset USE_ARCHIVED_DATA
python prod/bear_trap/runner.py

# CI/CD: Always uses cache
# (workflow sets USE_ARCHIVED_DATA=true)

# EC2: Always uses live API
# (no env var set in systemd service)
```

---

## 📋 MIGRATION PLAN

### **Step 1: Create Structure**

```bash
# Create new folders
mkdir -p dev
mkdir -p test
mkdir -p prod

# Current state
ls deployable_strategies/
# bear_trap/
# daily_trend_hysteresis/
# hourly_swing/
```

### **Step 2: Migrate to prod/**

```bash
# For each production strategy:

# Bear Trap
mkdir -p prod/bear_trap/{tests,deployment/systemd,docs}

# Copy production code
cp deployable_strategies/bear_trap/aws_deployment/run_strategy.py \
   prod/bear_trap/runner.py

cp deployable_strategies/bear_trap/bear_trap_strategy_production.py \
   prod/bear_trap/strategy.py

cp deployable_strategies/bear_trap/aws_deployment/config.json \
   prod/bear_trap/config.json

# Copy deployment artifacts
cp deployable_strategies/bear_trap/aws_deployment/*.service \
   prod/bear_trap/deployment/systemd/

# Copy documentation
cp deployable_strategies/bear_trap/*.md \
   prod/bear_trap/docs/

# Repeat for daily_trend and hourly_swing
```

### **Step 3: Update runner.py**

```python
# Add environment detection to prod/bear_trap/runner.py

import os

# Add this function
def get_data_client(api_key, api_secret):
    use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
    
    if use_cache:
        from src.data_cache import DataCache
        return DataCache(api_key, api_secret)
    else:
        from alpaca.data.historical import StockHistoricalDataClient
        return StockHistoricalDataClient(api_key, api_secret)

# Use it in main()
def main():
    api_key, api_secret = get_credentials()
    data_client = get_data_client(api_key, api_secret)  # ← Environment-aware
    # ... rest of code
```

### **Step 4: Update CI/CD**

```yaml
# .github/workflows/deploy-strategies.yml

on:
  push:
    branches:
      - main
    paths:
      - 'prod/**'  # Only trigger on prod/ changes

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test strategies with cached data
        env:
          USE_ARCHIVED_DATA: 'true'  # ← Use cache in CI/CD
        run: |
          cd prod/bear_trap
          python -m pytest tests/
          python runner.py --validate  # Run validation mode

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to EC2
        run: |
          # Deploy prod/ folder to EC2
          # EC2 runs without USE_ARCHIVED_DATA (live API)
          aws ssm send-command \
            --instance-ids i-0cd785630b55dd9a2 \
            --document-name "AWS-RunShellScript" \
            --parameters 'commands=[
              "cd /home/ssm-user/magellan",
              "git pull origin main",
              "sudo systemctl restart magellan-bear-trap"
            ]'
```

### **Step 5: Update Systemd Services**

```ini
# prod/bear_trap/deployment/systemd/magellan-bear-trap.service

[Unit]
Description=Magellan Bear Trap Strategy
After=network.target

[Service]
Type=simple
User=ssm-user
WorkingDirectory=/home/ssm-user/magellan
ExecStart=/home/ssm-user/magellan/.venv/bin/python \
    /home/ssm-user/magellan/prod/bear_trap/runner.py
# Changed from: deployable_strategies/bear_trap/aws_deployment/run_strategy.py

# NO USE_ARCHIVED_DATA environment variable
# This ensures production uses live API

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Step 6: Deploy to EC2**

```bash
# On EC2
cd /home/ssm-user/magellan
git pull origin main

# Update systemd service
sudo cp prod/bear_trap/deployment/systemd/magellan-bear-trap.service \
        /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl restart magellan-bear-trap
sudo systemctl status magellan-bear-trap
```

### **Step 7: Archive Old Structure**

```bash
# Once verified working
mkdir -p archive/old_deployable_strategies
mv deployable_strategies/* archive/old_deployable_strategies/
rmdir deployable_strategies
```

---

## 🎯 FINAL STRUCTURE

```
Magellan/
│
├── dev/                     # Development
│   └── (experimental strategies)
│
├── test/                    # Validation/Staging
│   └── (strategies being validated)
│
├── prod/                    # Production (SOURCE OF TRUTH)
│   ├── bear_trap/
│   │   ├── strategy.py
│   │   ├── runner.py        # ← Environment-aware
│   │   ├── config.json
│   │   ├── tests/
│   │   ├── deployment/
│   │   └── docs/
│   │
│   ├── daily_trend/
│   └── hourly_swing/
│
├── src/                     # Shared utilities
├── scripts/                 # Helper scripts
├── tests/                   # Integration tests
└── docs/                    # Documentation
```

---

## ✅ BENEFITS

1. ✅ **Standard nomenclature** - Everyone understands dev/test/prod
2. ✅ **Clear lifecycle** - Obvious progression
3. ✅ **Single source of truth** - prod/ is canonical
4. ✅ **Environment-aware** - Same code, different data
5. ✅ **Safe testing** - Can test prod/ code with cache locally
6. ✅ **Professional** - Industry standard

---

## 🔄 WORKFLOW EXAMPLES

### **New Strategy**:
```bash
# 1. Develop in dev/
cd dev/new_strategy
jupyter notebook backtest.ipynb

# 2. Validate in test/
mv dev/new_strategy test/new_strategy
cd test/new_strategy
python validation_suite.py

# 3. Promote to prod/
mv test/new_strategy prod/new_strategy
cd prod/new_strategy

# 4. Deploy
git add prod/new_strategy
git commit -m "Deploy new strategy"
git push origin main
# CI/CD automatically deploys to EC2
```

### **Update Existing**:
```bash
# 1. Work in prod/ (source of truth)
cd prod/bear_trap
vim strategy.py

# 2. Test locally with cache
export USE_ARCHIVED_DATA=true
python runner.py

# 3. Run tests
python -m pytest tests/

# 4. Deploy
git add .
git commit -m "Update Bear Trap parameters"
git push origin main
# CI/CD automatically deploys to EC2
```

---

## 📊 COMPARISON

| Aspect | Old Structure | New Structure |
|--------|--------------|---------------|
| **Naming** | deployable_strategies/aws_deployment/ | prod/bear_trap/ |
| **Clarity** | Confusing | Clear (dev/test/prod) |
| **Lifecycle** | Unclear | Explicit stages |
| **Testing** | Separate scripts | Environment-aware runner |
| **Deployment** | Manual paths | Standard CI/CD |
| **Maintenance** | Hard to find code | Easy navigation |

---

## ⏱️ TIMELINE

**Incremental Migration** (Recommended):

```
Day 1: Create structure, migrate Bear Trap
Day 2: Test Bear Trap, verify CI/CD
Day 3: Migrate Daily Trend
Day 4: Migrate Hourly Swing
Day 5: Update all documentation
Day 6-7: Final testing, archive old structure
```

**Total**: 1 week

---

## ❓ READY TO PROCEED?

This is the **cleanest, most professional** structure:

- ✅ Standard dev/test/prod naming
- ✅ Clear lifecycle stages
- ✅ Environment-aware execution
- ✅ Industry best practice

**Shall I start the migration?** 🚀

I can:
1. Create the folder structure
2. Migrate Bear Trap (pilot)
3. Test thoroughly
4. Migrate the others
5. Update CI/CD

**Your approval to proceed?**
