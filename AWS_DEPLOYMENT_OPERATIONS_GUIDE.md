# AWS Deployment - Complete Operations Guide

**Last Updated:** 2026-01-20  
**Environment:** AWS EC2 us-east-2  
**Instance:** i-0cd785630b55dd9a2  
**Deployment Model:** 3 Strategies, 3 Accounts, 3 Systemd Services

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Account Setup](#account-setup)
3. [EC2 Deployment](#ec2-deployment)
4. [Service Management](#service-management)
5. [Monitoring & Dashboards](#monitoring--dashboards)
6. [Daily Operations](#daily-operations)
7. [Troubleshooting](#troubleshooting)
8. [Emergency Procedures](#emergency-procedures)

---

## Quick Reference

### Account Mapping

| Account | Account ID | Strategy | Symbols | Capital |
|---------|-----------|----------|---------|---------|
| **Account 1** | PA3DDLQCBJSE | Bear Trap | MULN, ONDS, AMC, NKLA, WKHS | $100,000 |
| **Account 2** | _(pending)_ | Daily Trend | GOOGL, GLD, META, AAPL, QQQ, SPY, MSFT, TSLA, AMZN, IWM | $100,000 |
| **Account 3** | _(pending)_ | Hourly Swing | TSLA, NVDA | $100,000 |

### Service Names

- `magellan-bear-trap.service`
- `magellan-daily-trend.service`
- `magellan-hourly-swing.service`

### Key Commands (Run on EC2)

```bash
# View all services status
sudo systemctl status magellan-*

# View live logs
sudo journalctl -u magellan-bear-trap -f
sudo journalctl -u magellan-daily-trend -f
sudo journalctl -u magellan-hourly-swing -f

# Start/Stop/Restart
sudo systemctl start magellan-bear-trap
sudo systemctl stop magellan-bear-trap
sudo systemctl restart magellan-bear-trap

# View monitoring dashboard
cd /home/ec2-user/magellan
source .venv/bin/activate
python scripts/monitor_dashboard.py
```

---

## Account Setup

### Step 1: Create Alpaca Paper Trading Accounts

You need to create **2 new Alpaca paper trading accounts** (Account 1 already exists).

#### Create Account 2 (Daily Trend)

1. Log into Alpaca dashboard: https://app.alpaca.markets/
2. Navigate to **Paper Trading** section
3. Click **"Create New Paper Account"**
4. Name: `magellan-daily-trend`
5. Enable **4x margin** (Day Trader buying power)
6. Fund with **$100,000** paper money
7. **Record the Account ID** (format: PAXXXXXXXXXX)
8. Generate API keys:
   - Click **"Generate API Keys"**
   - Record both **API_KEY** and **API_SECRET**
   - ⚠️ **Save these immediately** - you can't retrieve the secret later

#### Create Account 3 (Hourly Swing)

1. Repeat the same process
2. Name: `magellan-hourly-swing`
3. Enable **4x margin**
4. Fund with **$100,000**
5. **Record the Account ID**
6. Generate and **save API keys**

### Step 2: Store Credentials in AWS SSM

For **each account**, you need to store the API credentials in AWS SSM Parameter Store.

#### From Your Local Machine (Windows PowerShell):

```powershell
# Set AWS profile
$env:AWS_PROFILE = "magellan_deployer"

# === Account 1 (PA3DDLQCBJSE) - Already Created ===
aws ssm put-parameter `
  --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" `
  --value "YOUR_API_KEY_HERE" `
  --type "SecureString" `
  --region us-east-2

aws ssm put-parameter `
  --name "/magellan/alpaca/PA3DDLQCBJSE/API_SECRET" `
  --value "YOUR_API_SECRET_HERE" `
  --type "SecureString" `
  --region us-east-2

# === Account 2 (Daily Trend) ===
# Replace ACCOUNT_ID_HERE with the actual account ID from Alpaca
aws ssm put-parameter `
  --name "/magellan/alpaca/ACCOUNT_ID_HERE/API_KEY" `
  --value "YOUR_API_KEY_HERE" `
  --type "SecureString" `
  --region us-east-2

aws ssm put-parameter `
  --name "/magellan/alpaca/ACCOUNT_ID_HERE/API_SECRET" `
  --value "YOUR_API_SECRET_HERE" `
  --type "SecureString" `
  --region us-east-2

# === Account 3 (Hourly Swing) ===
aws ssm put-parameter `
  --name "/magellan/alpaca/ACCOUNT_ID_HERE/API_KEY" `
  --value "YOUR_API_KEY_HERE" `
  --type "SecureString" `
  --region us-east-2

aws ssm put-parameter `
  --name "/magellan/alpaca/ACCOUNT_ID_HERE/API_SECRET" `
  --value "YOUR_API_SECRET_HERE" `
  --type "SecureString" `
  --region us-east-2
```

#### Verify Parameters Were Stored:

```powershell
# List all magellan parameters
aws ssm describe-parameters --region us-east-2 | Select-String "magellan"

# Test retrieval (should return the API key)
aws ssm get-parameter `
  --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" `
  --with-decryption `
  --region us-east-2
```

### Step 3: Update Configuration Files

Once you have the Account IDs, update the config files:

#### Daily Trend Config

Edit: `deployable_strategies/daily_trend_hysteresis/aws_deployment/config.json`

```json
{
  "account_info": {
    "account_id": "REPLACE_WITH_ACTUAL_ACCOUNT_ID",
    ...
```

Change `"REPLACE_WITH_ACTUAL_ACCOUNT_ID"` to the real Alpaca account ID.

Also update the service file:
Edit: `deployable_strategies/daily_trend_hysteresis/aws_deployment/magellan-daily-trend.service`

```
Environment="ACCOUNT_ID=REPLACE_WITH_ACCOUNT_ID"
```

#### Hourly Swing Config

Same process for `deployable_strategies/hourly_swing/aws_deployment/config.json` and `magellan-hourly-swing.service`

---

## EC2 Deployment

### Step 1: Connect to EC2

From your local machine:

```powershell
# Windows PowerShell
$env:AWS_PROFILE = "magellan_admin"  # or magellan_deployer
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2
```

### Step 2: Sync Code to EC2

Back on your local machine (in the Magellan directory):

```powershell
# Commit your changes first
git add .
git commit -m "feat: add AWS deployment configurations"
git push origin deployment/aws-paper-trading-setup

# SSH into EC2 and pull
# (After you're connected via SSM)
```

On EC2:

```bash
cd /home/ec2-user/magellan

# Pull latest code
git fetch origin
git checkout deployment/aws-paper-trading-setup
git pull origin deployment/aws-paper-trading-setup

# Verify files exist
ls -la deployable_strategies/bear_trap/aws_deployment/
ls -la deployable_strategies/daily_trend_hysteresis/aws_deployment/
ls -la deployable_strategies/hourly_swing/aws_deployment/
```

### Step 3: Install Python Dependencies

```bash
cd /home/ec2-user/magellan

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional monitoring dependencies
pip install rich boto3 pytz
```

### Step 4: Install Systemd Services

```bash
# Copy service files to systemd directory
sudo cp deployable_strategies/bear_trap/aws_deployment/magellan-bear-trap.service /etc/systemd/system/
sudo cp deployable_strategies/daily_trend_hysteresis/aws_deployment/magellan-daily-trend.service /etc/systemd/system/
sudo cp deployable_strategies/hourly_swing/aws_deployment/magellan-hourly-swing.service /etc/systemd/system/

# Set permissions
sudo chmod 644 /etc/systemd/system/magellan-*.service

# Reload systemd to recognize new services
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable magellan-bear-trap
sudo systemctl enable magellan-daily-trend
sudo systemctl enable magellan-hourly-swing

# Verify services are registered
systemctl list-unit-files | grep magellan
```

Expected output:
```
magellan-bear-trap.service        enabled
magellan-daily-trend.service      enabled
magellan-hourly-swing.service     enabled
```

### Step 5: Test Service Startup

Start ONE service at a time to test:

```bash
# Start Bear Trap (Account 1)
sudo systemctl start magellan-bear-trap

# Check status (should show "active (running)")
sudo systemctl status magellan-bear-trap

# View live logs (Ctrl+C to exit)
sudo journalctl -u magellan-bear-trap -f
```

Look for:
- ✓ "Retrieved Alpaca API credentials from SSM"
- ✓ "Strategy initialized"
- ✓ No errors about missing credentials or files

If successful, start the others:

```bash
sudo systemctl start magellan-daily-trend
sudo systemctl start magellan-hourly-swing

# Check all services
sudo systemctl status magellan-*
```

---

## Service Management

### Check Service Status

```bash
# All services
sudo systemctl status magellan-*

# Individual service
sudo systemctl status magellan-bear-trap
```

### View Logs

```bash
# Real-time logs (live tail)
sudo journalctl -u magellan-bear-trap -f

# Last 100 lines
sudo journalctl -u magellan-bear-trap -n 100

# Since specific time
sudo journalctl -u magellan-bear-trap --since "1 hour ago"

# All magellan services combined
sudo journalctl -u "magellan-*" -f
```

### Start/Stop/Restart

```bash
# Start
sudo systemctl start magellan-bear-trap

# Stop
sudo systemctl stop magellan-bear-trap

# Restart (stop and start)
sudo systemctl restart magellan-bear-trap

# Stop all
sudo systemctl stop magellan-bear-trap magellan-daily-trend magellan-hourly-swing
```

### Enable/Disable Auto-Start

```bash
# Enable (start on boot)
sudo systemctl enable magellan-bear-trap

# Disable (don't start on boot)
sudo systemctl disable magellan-bear-trap

# Check if enabled
systemctl is-enabled magellan-bear-trap
```

---

## Monitoring & Dashboards

### Real-Time Dashboard

Run the monitoring dashboard to see all 3 strategies at once:

```bash
cd /home/ec2-user/magellan
source .venv/bin/activate
python scripts/monitor_dashboard.py
```

This shows:
- ✅ Service status (running/stopped)
- 💰 Account equity and P&L
- 📊 Open positions count
- 🎯 Daily and total P&L

Press **Ctrl+C** to exit.

### Alpaca Dashboard

Log into Alpaca web interface to see:
- Real-time positions
- Order history
- Account balance
- Trade fills

https://app.alpaca.markets/paper/dashboard

### CloudWatch Logs

View logs in AWS Console:

1. Go to: https://console.aws.amazon.com/cloudwatch/
2. Navigate to **Logs** > **Log groups**
3. Select:
   - `/magellan/bear-trap`
   - `/magellan/daily-trend`
   - `/magellan/hourly-swing`
4. View log streams

---

## Daily Operations

### Morning Checklist (Before Market Open - 9:00 AM ET)

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Check all services are running
sudo systemctl status magellan-*

# Check yesterday's performance (if implemented)
cd /home/ec2-user/magellan
source .venv/bin/activate
python scripts/daily_report.py

# View recent logs for errors
sudo journalctl -u "magellan-*" --since "24 hours ago" | grep ERROR
```

### End of Day Checklist (After Market Close - 4:30 PM ET)

```bash
# Check positions are properly managed
python scripts/monitor_dashboard.py

# Review logs for any issues
sudo journalctl -u magellan-bear-trap --since "09:00" -n 500

# Check Alpaca dashboard for trade history

# Verify Daily Trend generated signals (should happen at 16:05)
cat deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json
```

### Weekly Review

- Review total P&L across all 3 accounts
- Compare to backtest expectations
- Check win rates are within expected ranges
- Verify no unusual slippage or execution issues
- Review any emergency stop triggers

---

## Troubleshooting

### Service Won't Start

**Symptom:** `sudo systemctl start magellan-bear-trap` fails

**Check:**

```bash
# View full error details
sudo systemctl status magellan-bear-trap -l

# Check journal logs
sudo journalctl -u magellan-bear-trap -n 50

# Common issues:
# 1. Python file not found
ls -la /home/ec2-user/magellan/deployable_strategies/bear_trap/aws_deployment/run_strategy.py

# 2. Virtual environment missing
ls -la /home/ec2-user/magellan/.venv/bin/python

# 3. Permissions
sudo chown -R ec2-user:ec2-user /home/ec2-user/magellan
```

### Can't Retrieve SSM Credentials

**Symptom:** "Failed to retrieve credentials" in logs

**Fix:**

```bash
# Verify parameters exist
aws ssm describe-parameters --region us-east-2 | grep magellan

# Test retrieval
aws ssm get-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --with-decryption --region us-east-2

# Check EC2 instance role has SSM permissions
aws iam get-role --role-name MagellanInstanceRole
```

### No Trades Executing

**Bear Trap:**
- Check if market hours (9:30-16:00 ET)
- Verify symbols meet -15% day change criteria
- Check logs for "No valid entry signals"

**Daily Trend:**
- Check if signals were generated yesterday (16:05 ET)
- View signals file: `cat deployable_strategies/daily_trend_hysteresis/aws_deployment/signals.json`
- Verify execution at 9:30 AM

**Hourly Swing:**
- Check if hourly bars are being fetched
- Verify RSI calculation (need 84 bars warmup)
- Check logs for RSI values

### High Memory/CPU Usage

```bash
# Check resource usage
top -u ec2-user

# Check process details
ps aux | grep python

# Restart service if needed
sudo systemctl restart magellan-bear-trap
```

---

## Emergency Procedures

### STOP ALL TRADING IMMEDIATELY

```bash
# Stop all services
sudo systemctl stop magellan-bear-trap magellan-daily-trend magellan-hourly-swing

# Verify all stopped
sudo systemctl status magellan-*

# Close all positions via Alpaca dashboard
# Log into: https://app.alpaca.markets/paper/dashboard
# Manually close any open positions
```

### Emergency Loss Limit Hit (Daily Loss > $10,000 any account)

1. **STOP the affected service:**
   ```bash
   sudo systemctl stop magellan-STRATEGY-NAME
   ```

2. **Close all positions** in that account via Alpaca dashboard

3. **Review logs** to understand what happened:
   ```bash
   sudo journalctl -u magellan-STRATEGY-NAME --since "today" > /tmp/emergency_log.txt
   ```

4. **Document the incident** before restarting

5. **DO NOT restart** until root cause is identified

### Service Crash Loop

**Symptom:** Service keeps restarting

```bash
# Disable service to stop restart loop
sudo systemctl stop magellan-bear-trap
sudo systemctl disable magellan-bear-trap

# Review crash logs
sudo journalctl -u magellan-bear-trap -n 200

# Fix the issue, then re-enable
sudo systemctl enable magellan-bear-trap
sudo systemctl start magellan-bear-trap
```

###AWS Instance Reboot

If EC2 instance reboots:

1. **Services auto-start** (they're enabled)
2. **Verify all started:**
   ```bash
   sudo systemctl status magellan-*
   ```
3. **Check logs** for any startup issues

---

## Configuration Reference

### Per-Symbol Parameters

#### Bear Trap (Account 1)
- **All symbols use same parameters:**
  - Min day change: -15%
  - Reclaim wick ratio: 0.15
  - Volume multiplier: 0.2x
  - Stop: 0.45 ATR
  - Max hold: 30 minutes

#### Daily Trend (Account 2)

| Symbol | RSI Period | Upper/Lower | Notes |
|--------|-----------|-------------|-------|
| GOOGL | 28 | 55/45 | Best performer, very selective |
| GLD | 21 | 65/35 | Ultra-wide, only 2 trades/year |
| META | 28 | 55/45 | Standard bands |
| AAPL | 28 | 65/35 | Ultra-wide, 100% win rate |
| QQQ | 21 | 60/40 | Tech-heavy, higher return |
| SPY | 21 | 58/42 | Best Sharpe (1.37) |
| MSFT | 21 | 58/42 | Low volatility |
| TSLA | 28 | 58/42 | Highest volatility |
| AMZN | 21 | 55/45 | Most trades (19/year) |
| IWM | 28 | 65/35 | Small caps, ultra-selective |

#### Hourly Swing (Account 3)

| Symbol | RSI Period | Upper/Lower | Notes |
|--------|-----------|-------------|-------|
| TSLA | 14 | 60/40 | Aggressive, wide bands |
| NVDA | 28 | 55/45 | Smoother, standard bands |

---

## Next Steps After Deployment

1. **Monitor for 2 weeks** (paper trading validation)
2. **Compare results** to backtest expectations
3. **Measure slippage** and execution quality
4. **Document any issues** and fix iteratively
5. **Scale to live trading** once validated (separate decision)

---

## Support Contacts

- **AWS Console:** https://console.aws.amazon.com/
- **Alpaca Dashboard:** https://app.alpaca.markets/
- **CloudWatch Logs:** https://console.aws.amazon.com/cloudwatch/

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-20  
**Status:** Ready for Deployment
