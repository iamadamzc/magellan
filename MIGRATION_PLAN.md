# 🔄 DEV/TEST/PROD MIGRATION PLAN
**Branch**: `refactor/dev-test-prod-structure`  
**Date**: January 21, 2026  
**Status**: Ready to Execute

---

## 🎯 OBJECTIVE

Migrate from current structure to professional dev/test/prod structure:

**From**:
```
deployable_strategies/
├── bear_trap/aws_deployment/
├── daily_trend_hysteresis/aws_deployment/
└── hourly_swing/aws_deployment/
```

**To**:
```
dev/      # Development
test/     # Validation
prod/     # Production (source of truth)
├── bear_trap/
├── daily_trend/
└── hourly_swing/
```

---

## 📋 MIGRATION CHECKLIST

### **Phase 1: Setup (30 min)**
- [x] Create feature branch: `refactor/dev-test-prod-structure`
- [ ] Create folder structure
- [ ] Create templates
- [ ] Document migration plan

### **Phase 2: Migrate Bear Trap (2 hours)**
- [ ] Create prod/bear_trap/ structure
- [ ] Copy production code
- [ ] Add environment detection to runner.py
- [ ] Create tests/
- [ ] Move documentation
- [ ] Test locally with cache
- [ ] Test locally with live API (dry-run)
- [ ] Commit changes

### **Phase 3: Migrate Daily Trend (1.5 hours)**
- [ ] Create prod/daily_trend/ structure
- [ ] Copy production code
- [ ] Add environment detection to runner.py
- [ ] Create tests/
- [ ] Move documentation
- [ ] Test locally with cache
- [ ] Commit changes

### **Phase 4: Migrate Hourly Swing (1.5 hours)**
- [ ] Create prod/hourly_swing/ structure
- [ ] Copy production code
- [ ] Add environment detection to runner.py
- [ ] Create tests/
- [ ] Move documentation
- [ ] Test locally with cache
- [ ] Commit changes

### **Phase 5: Update CI/CD (1 hour)**
- [ ] Update .github/workflows/deploy-strategies.yml
- [ ] Change paths from deployable_strategies/ to prod/
- [ ] Test workflow locally (if possible)
- [ ] Commit changes

### **Phase 6: Update Systemd Services (1 hour)**
- [ ] Update all service files to point to prod/
- [ ] Test service file syntax
- [ ] Document deployment steps
- [ ] Commit changes

### **Phase 7: Testing (2 hours)**
- [ ] Test all strategies locally with cache
- [ ] Run pytest on all tests/
- [ ] Verify configs load correctly
- [ ] Test runner.py environment detection
- [ ] Push to GitHub
- [ ] Verify CI/CD runs successfully

### **Phase 8: EC2 Deployment (2 hours)**
- [ ] Backup current EC2 state
- [ ] Pull new code to EC2
- [ ] Update systemd services
- [ ] Restart services
- [ ] Verify all services running
- [ ] Monitor logs for 1 hour
- [ ] Verify no errors

### **Phase 9: Cleanup (1 hour)**
- [ ] Archive old deployable_strategies/
- [ ] Update all documentation
- [ ] Update README.md
- [ ] Create migration summary
- [ ] Merge to main (or deployment branch)

---

## 🛠️ DETAILED STEPS

### **Step 1: Create Folder Structure**

```bash
# Create main folders
mkdir -p dev
mkdir -p test
mkdir -p prod

# Create prod/ strategy folders
mkdir -p prod/bear_trap/{tests,deployment/systemd,docs}
mkdir -p prod/daily_trend/{tests,deployment/systemd,docs}
mkdir -p prod/hourly_swing/{tests,deployment/systemd,docs}

# Create templates folder
mkdir -p templates
```

---

### **Step 2: Create Runner Template**

```bash
# Create universal runner template
cat > templates/runner_template.py << 'EOF'
#!/usr/bin/env python3
"""
Universal Strategy Runner
Supports both cached data (local/CI/CD) and live API (production)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_credentials():
    """Get API credentials based on environment"""
    env = os.getenv('ENVIRONMENT', 'production')
    
    if env == 'production':
        # Production: AWS SSM Parameter Store
        import boto3
        ssm = boto3.client('ssm', region_name='us-east-2')
        
        account_id = os.getenv('ALPACA_ACCOUNT_ID')
        if not account_id:
            raise ValueError("ALPACA_ACCOUNT_ID environment variable not set")
        
        api_key = ssm.get_parameter(
            Name=f'/magellan/alpaca/{account_id}/API_KEY',
            WithDecryption=True
        )['Parameter']['Value']
        
        api_secret = ssm.get_parameter(
            Name=f'/magellan/alpaca/{account_id}/API_SECRET',
            WithDecryption=True
        )['Parameter']['Value']
        
        return api_key, api_secret
    else:
        # Local/Testing: Environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('ALPACA_API_KEY')
        api_secret = os.getenv('ALPACA_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET must be set")
        
        return api_key, api_secret

def get_data_client(api_key, api_secret):
    """Get data client based on environment"""
    use_cache = os.getenv('USE_ARCHIVED_DATA', 'false').lower() == 'true'
    
    if use_cache:
        # Testing/CI/CD: Cached data
        from src.data_cache import DataCache
        logging.info("📦 Using cached data (USE_ARCHIVED_DATA=true)")
        return DataCache(api_key, api_secret)
    else:
        # Production: Live API
        from alpaca.data.historical import StockHistoricalDataClient
        logging.info("🔴 Using live Alpaca API (production mode)")
        return StockHistoricalDataClient(api_key, api_secret)

def get_trading_client(api_key, api_secret):
    """Get trading client"""
    from alpaca.trading.client import TradingClient
    
    # Use paper trading (for now)
    paper = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
    return TradingClient(api_key, api_secret, paper=paper)

def load_config():
    """Load strategy configuration"""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path) as f:
        return json.load(f)

def main():
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger('magellan.{STRATEGY_NAME}')
    
    logger.info("=" * 60)
    logger.info("Starting {STRATEGY_DISPLAY_NAME} Strategy")
    logger.info("=" * 60)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'production')}")
    logger.info(f"Use cached data: {os.getenv('USE_ARCHIVED_DATA', 'false')}")
    logger.info(f"Paper trading: {os.getenv('ALPACA_PAPER', 'true')}")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"✓ Configuration loaded")
        
        # Get credentials
        api_key, api_secret = get_credentials()
        logger.info(f"✓ Credentials retrieved")
        
        # Get clients
        data_client = get_data_client(api_key, api_secret)
        trading_client = get_trading_client(api_key, api_secret)
        logger.info(f"✓ Clients initialized")
        
        # Import and initialize strategy
        from strategy import {STRATEGY_CLASS}
        
        strategy = {STRATEGY_CLASS}(
            config=config,
            data_client=data_client,
            trading_client=trading_client
        )
        logger.info(f"✓ Strategy initialized")
        
        # Run strategy
        logger.info("Starting strategy execution...")
        strategy.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF
```

---

### **Step 3: Migrate Bear Trap**

```bash
# Navigate to prod/bear_trap
cd prod/bear_trap

# Copy strategy logic
cp ../../deployable_strategies/bear_trap/bear_trap_strategy_production.py \
   strategy.py

# Copy config
cp ../../deployable_strategies/bear_trap/aws_deployment/config.json \
   config.json

# Create runner from template
cp ../../templates/runner_template.py runner.py

# Edit runner.py to customize for Bear Trap
sed -i 's/{STRATEGY_NAME}/bear_trap/g' runner.py
sed -i 's/{STRATEGY_DISPLAY_NAME}/Bear Trap/g' runner.py
sed -i 's/{STRATEGY_CLASS}/BearTrapStrategy/g' runner.py

# Copy systemd service
cp ../../deployable_strategies/bear_trap/aws_deployment/*.service \
   deployment/systemd/

# Update service file paths
sed -i 's|deployable_strategies/bear_trap/aws_deployment/run_strategy.py|prod/bear_trap/runner.py|g' \
   deployment/systemd/*.service

# Copy documentation
cp ../../deployable_strategies/bear_trap/*.md docs/

# Create basic test
cat > tests/test_strategy.py << 'EOF'
import pytest
from strategy import BearTrapStrategy

def test_strategy_imports():
    """Test that strategy can be imported"""
    assert BearTrapStrategy is not None

def test_strategy_initialization():
    """Test basic strategy initialization"""
    # TODO: Add proper initialization test
    pass
EOF

# Test locally
export USE_ARCHIVED_DATA=true
python runner.py --help  # Should show help or run validation mode
```

---

### **Step 4: Update CI/CD Workflow**

```yaml
# .github/workflows/deploy-strategies.yml

name: Deploy Trading Strategies to AWS

on:
  push:
    branches:
      - main
      - deployment/aws-paper-trading-setup
    paths:
      - 'prod/**'  # ← Changed from 'deployable_strategies/**'

jobs:
  validate-strategies:
    name: Validate Strategy Code
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        strategy: [bear_trap, daily_trend, hourly_swing]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest black
      
      - name: Run tests with cached data
        env:
          USE_ARCHIVED_DATA: 'true'  # ← Use cache in CI/CD
        run: |
          cd prod/${{ matrix.strategy }}
          python -m pytest tests/ -v
      
      - name: Validate runner
        env:
          USE_ARCHIVED_DATA: 'true'
        run: |
          cd prod/${{ matrix.strategy }}
          python runner.py --validate  # Run in validation mode

  deploy-to-aws:
    name: Deploy to AWS EC2
    needs: validate-strategies
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to EC2 via SSM
        run: |
          aws ssm send-command \
            --instance-ids i-0cd785630b55dd9a2 \
            --document-name "AWS-RunShellScript" \
            --parameters 'commands=[
              "cd /home/ssm-user/magellan",
              "git fetch origin",
              "git reset --hard origin/${{ github.ref_name }}",
              "sudo systemctl restart magellan-bear-trap",
              "sudo systemctl restart magellan-daily-trend",
              "sudo systemctl restart magellan-hourly-swing"
            ]'
```

---

### **Step 5: EC2 Deployment**

```bash
# On EC2
cd /home/ssm-user/magellan

# Pull new code
git fetch origin
git checkout refactor/dev-test-prod-structure
git pull origin refactor/dev-test-prod-structure

# Update systemd services
sudo cp prod/bear_trap/deployment/systemd/*.service /etc/systemd/system/
sudo cp prod/daily_trend/deployment/systemd/*.service /etc/systemd/system/
sudo cp prod/hourly_swing/deployment/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Restart services
sudo systemctl restart magellan-bear-trap
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing

# Verify services
sudo systemctl status magellan-bear-trap
sudo systemctl status magellan-daily-trend
sudo systemctl status magellan-hourly-swing

# Check logs
sudo journalctl -u magellan-bear-trap -n 50 --no-pager
```

---

## ⚠️ ROLLBACK PLAN

If anything goes wrong:

```bash
# On feature branch
git log --oneline -5  # Find commit before migration
git reset --hard <commit-hash>

# Or switch back to deployment branch
git checkout deployment/aws-paper-trading-setup

# On EC2
cd /home/ssm-user/magellan
git checkout deployment/aws-paper-trading-setup
git pull origin deployment/aws-paper-trading-setup

# Restore old services
sudo systemctl restart magellan-bear-trap
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing
```

---

## ✅ SUCCESS CRITERIA

Migration is successful when:

- [ ] All 3 strategies in prod/ folder
- [ ] Local testing works with USE_ARCHIVED_DATA=true
- [ ] CI/CD pipeline passes
- [ ] EC2 services start successfully
- [ ] EC2 services run without errors for 1 hour
- [ ] Logs show correct environment detection
- [ ] No trading errors
- [ ] Documentation updated

---

## 📊 TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Setup | 30 min | ⏳ In Progress |
| Bear Trap Migration | 2 hours | ⏸️ Pending |
| Daily Trend Migration | 1.5 hours | ⏸️ Pending |
| Hourly Swing Migration | 1.5 hours | ⏸️ Pending |
| CI/CD Updates | 1 hour | ⏸️ Pending |
| Systemd Updates | 1 hour | ⏸️ Pending |
| Testing | 2 hours | ⏸️ Pending |
| EC2 Deployment | 2 hours | ⏸️ Pending |
| Cleanup | 1 hour | ⏸️ Pending |
| **Total** | **~12 hours** | **0% Complete** |

**Estimated Completion**: 2 days (with breaks and monitoring)

---

## 🎯 CURRENT STATUS

**Branch**: `refactor/dev-test-prod-structure` ✅  
**Proposal**: Documented ✅  
**Ready to Start**: YES ✅

**Next Step**: Create folder structure and templates

---

**Shall I proceed with Step 1 (Create Folder Structure)?** 🚀
