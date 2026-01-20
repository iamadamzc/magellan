# AWS Deployment Checklist

**Date:** 2026-01-20  
**Branch:** `deployment/aws-paper-trading-setup`  
**Status:** Ready for Deployment

---

## Pre-Deployment (Local Machine)

### ✅ Phase 1: Account Setup

- [ ] **Create Alpaca Account 2** (Daily Trend)
  - Name: `magellan-daily-trend`
  - Fund: $100,000
  - Enable 4x margin
  - Record Account ID: `________________`
  - Generate API keys
  - Save API Key: `________________`
  - Save API Secret: `________________`

- [ ] **Create Alpaca Account 3** (Hourly Swing)
  - Name: `magellan-hourly-swing`
  - Fund: $100,000
  - Enable 4x margin
  - Record Account ID: `________________`
  - Generate API keys
  - Save API Key: `________________`
  - Save API Secret: `________________`

### ✅ Phase 2: Update Configuration Files

- [ ] **Update Daily Trend config** with Account ID
  - File: `deployable_strategies/daily_trend_hysteresis/aws_deployment/config.json`
  - Replace `"PENDING_CREATION"` with actual account ID
  
- [ ] **Update Daily Trend service** with Account ID
  - File: `deployable_strategies/daily_trend_hysteresis/aws_deployment/magellan-daily-trend.service`
  - Replace `REPLACE_WITH_ACCOUNT_ID` with actual account ID

- [ ] **Update Hourly Swing config** with Account ID
  - File: `deployable_strategies/hourly_swing/aws_deployment/config.json`
  - Replace `"PENDING_CREATION"` with actual account ID
  
- [ ] **Update Hourly Swing service** with Account ID
  - File: `deployable_strategies/hourly_swing/aws_deployment/magellan-hourly-swing.service`
  - Replace `REPLACE_WITH_ACCOUNT_ID` with actual account ID

### ✅ Phase 3: Store Credentials in AWS SSM

Run these commands from PowerShell (replace placeholders):

```powershell
$env:AWS_PROFILE = "magellan_deployer"

# Account 1 (PA3DDLQCBJSE)
aws ssm put-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --value "YOUR_KEY" --type "SecureString" --region us-east-2
aws ssm put-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_SECRET" --value "YOUR_SECRET" --type "SecureString" --region us-east-2

# Account 2 (Daily Trend)
aws ssm put-parameter --name "/magellan/alpaca/ACCOUNT_ID/API_KEY" --value "YOUR_KEY" --type "SecureString" --region us-east-2
aws ssm put-parameter --name "/magellan/alpaca/ACCOUNT_ID/API_SECRET" --value "YOUR_SECRET" --type "SecureString" --region us-east-2

# Account 3 (Hourly Swing)
aws ssm put-parameter --name "/magellan/alpaca/ACCOUNT_ID/API_KEY" --value "YOUR_KEY" --type "SecureString" --region us-east-2
aws ssm put-parameter --name "/magellan/alpaca/ACCOUNT_ID/API_SECRET" --value "YOUR_SECRET" --type "SecureString" --region us-east-2
```

- [ ] Account 1 credentials stored
- [ ] Account 2 credentials stored
- [ ] Account 3 credentials stored
- [ ] Verify: `aws ssm describe-parameters --region us-east-2 | Select-String "magellan"`

### ✅ Phase 4: Commit and Push Code

```powershell
git add .
git commit -m "feat: complete AWS deployment package for 3 strategies"
git push origin deployment/aws-paper-trading-setup
```

- [ ] Code committed
- [ ] Code pushed to GitHub

---

## EC2 Deployment

### ✅ Phase 5: Connect to EC2

```powershell
$env:AWS_PROFILE = "magellan_admin"
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2
```

- [ ] Connected to EC2

### ✅ Phase 6: Pull Code

```bash
cd /home/ec2-user/magellan
git fetch origin
git checkout deployment/aws-paper-trading-setup
git pull origin deployment/aws-paper-trading-setup
```

- [ ] Code pulled to EC2

### ✅ Phase 7: Verify Files

```bash
ls -la deployable_strategies/bear_trap/aws_deployment/
ls -la deployable_strategies/daily_trend_hysteresis/aws_deployment/
ls -la deployable_strategies/hourly_swing/aws_deployment/
```

Expected files in each:
- `config.json`
- `run_strategy.py`
- `magellan-*.service`

- [ ] Bear Trap files present
- [ ] Daily Trend files present
- [ ] Hourly Swing files present

### ✅ Phase 8: Install Dependencies

```bash
cd /home/ec2-user/magellan
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install rich boto3 pytz
```

- [ ] Dependencies installed

### ✅ Phase 9: Install Systemd Services

```bash
sudo cp deployable_strategies/bear_trap/aws_deployment/magellan-bear-trap.service /etc/systemd/system/
sudo cp deployable_strategies/daily_trend_hysteresis/aws_deployment/magellan-daily-trend.service /etc/systemd/system/
sudo cp deployable_strategies/hourly_swing/aws_deployment/magellan-hourly-swing.service /etc/systemd/system/

sudo chmod 644 /etc/systemd/system/magellan-*.service
sudo systemctl daemon-reload
sudo systemctl enable magellan-bear-trap
sudo systemctl enable magellan-daily-trend
sudo systemctl enable magellan-hourly-swing
```

- [ ] Services copied
- [ ] Services enabled

### ✅ Phase 10: Test Credential Retrieval

```bash
# Test SSM access
aws ssm get-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --with-decryption --region us-east-2
```

- [ ] Credentials retrievable from EC2

---

## Service Startup

### ✅ Phase 11: Start Services (One at a Time)

#### Bear Trap

```bash
sudo systemctl start magellan-bear-trap
sudo systemctl status magellan-bear-trap
sudo journalctl -u magellan-bear-trap -f
```

Look for:
- ✓ "Retrieved Alpaca API credentials from SSM"
- ✓ "Strategy initialized"
- ✓ No errors

- [ ] Bear Trap started successfully

#### Daily Trend

```bash
sudo systemctl start magellan-daily-trend
sudo systemctl status magellan-daily-trend
sudo journalctl -u magellan-daily-trend -f
```

- [ ] Daily Trend started successfully

#### Hourly Swing

```bash
sudo systemctl start magellan-hourly-swing
sudo systemctl status magellan-hourly-swing
sudo journalctl -u magellan-hourly-swing -f
```

- [ ] Hourly Swing started successfully

### ✅ Phase 12: Verify All Running

```bash
sudo systemctl status magellan-*
```

All should show: **active (running)**

- [ ] All 3 services running

---

## Monitoring Setup

### ✅ Phase 13: Test Monitoring Dashboard

```bash
cd /home/ec2-user/magellan
source .venv/bin/activate
python scripts/monitor_dashboard.py
```

- [ ] Dashboard displays all 3 strategies
- [ ] Service status shows green (🟢)

### ✅ Phase 14: Check Alpaca Dashboards

Log into each account:
- https://app.alpaca.markets/paper/dashboard

- [ ] Account 1 (PA3DDLQCBJSE) accessible
- [ ] Account 2 (Daily Trend) accessible
- [ ] Account 3 (Hourly Swing) accessible

---

## Validation (First 24 Hours)

### ✅ Phase 15: Monitor First Day

#### Morning (9:00 AM ET)

```bash
# Check services still running
sudo systemctl status magellan-*

# Check logs for errors
sudo journalctl -u "magellan-*" --since "today" | grep ERROR
```

- [ ] All services running
- [ ] No critical errors

#### After Market Open (10:00 AM ET)

```bash
# Check for trade activity
sudo journalctl -u magellan-bear-trap --since "09:30" -n 100
sudo journalctl -u magellan-hourly-swing --since "09:30" -n 100
```

- [ ] Bear Trap processing market data
- [ ] Hourly Swing checking signals

#### After Market Close (4:30 PM ET)

```bash
# Check Daily Trend generated signals
cat deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json

# Review day's activity
python scripts/monitor_dashboard.py
```

- [ ] Daily Trend signals generated (16:05)
- [ ] Review P&L for all accounts

---

## Success Criteria (Week 1)

- [ ] All 3 services run without crashes for 5 consecutive trading days
- [ ] No emergency stop triggers activated
- [ ] Trades execute as expected (compare to backtest logic)
- [ ] Slippage within acceptable range (<1% for Bear Trap, <0.5% for others)
- [ ] No data feed gaps or missing signals

---

## Emergency Contacts

- **AWS Console:** https://console.aws.amazon.com/
- **Alpaca Dashboard:** https://app.alpaca.markets/
- **CloudWatch Logs:** https://console.aws.amazon.com/cloudwatch/

---

## Notes

**Important Reminders:**
1. Services auto-restart on failure (configured in systemd)
2. Services auto-start on EC2 reboot (enabled)
3. All logs go to systemd journal AND CloudWatch
4. Risk gates will auto-stop trading if limits breached
5. Monitor daily for first 2 weeks, then weekly

**Files Created:**
- 3 × `config.json` (strategy configurations)
- 3 × `run_strategy.py` (production runners)
- 3 × `magellan-*.service` (systemd services)
- 1 × `monitor_dashboard.py` (monitoring tool)
- 1 × `AWS_DEPLOYMENT_OPERATIONS_GUIDE.md` (full guide)
- 1 × `AWS_DEPLOYMENT_STRATEGY.md` (strategy analysis)

**Next Steps After Validation:**
- Week 2: Continue monitoring, document any issues
- Week 3-4: Compare results to backtest expectations
- Month 2: Decision on live trading (separate process)

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete
