# Magellan Trading System - Monitoring Guide

## 🎯 Quick Start

### Check Service Status (EC2)
```bash
# SSH into EC2 via SSM
aws ssm start-session --target i-0cd7857b7e6b2e1a8 --region us-east-2

# Check all services
systemctl is-active magellan-bear-trap
systemctl is-active magellan-daily-trend
systemctl is-active magellan-hourly-swing

# View service status details
sudo systemctl status magellan-bear-trap --no-pager
sudo systemctl status magellan-daily-trend --no-pager
sudo systemctl status magellan-hourly-swing --no-pager
```

### Run Monitoring Dashboard (EC2)
```bash
# Navigate to project directory
cd /home/ssm-user/magellan

# Activate virtual environment
source .venv/bin/activate

# Run dashboard
python scripts/monitor_dashboard.py
```

**Dashboard Features:**
- 📊 Real-time portfolio summary across all 3 accounts
- 🟢/🔴 Service health status
- 💰 Equity, positions, and P&L tracking
- 🔄 Auto-refreshes every 5 seconds

Press `Ctrl+C` to exit the dashboard.

---

## 📋 Monitoring Checklist

### Daily (Before Market Open - 9:00 AM ET)
- [ ] **Verify all services are running**
  ```bash
  systemctl is-active magellan-bear-trap magellan-daily-trend magellan-hourly-swing
  ```
- [ ] **Check for errors in logs**
  ```bash
  sudo journalctl -u magellan-bear-trap --since "24 hours ago" | grep -i error
  sudo journalctl -u magellan-daily-trend --since "24 hours ago" | grep -i error
  sudo journalctl -u magellan-hourly-swing --since "24 hours ago" | grep -i error
  ```
- [ ] **Verify SSM credentials are accessible**
  ```bash
  aws ssm get-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --region us-east-2 --with-decryption
  ```

### During Market Hours (9:30 AM - 4:00 PM ET)
- [ ] **Monitor active positions** (via dashboard or Alpaca web interface)
- [ ] **Check for unusual activity** in service logs
- [ ] **Verify orders are executing** (check Alpaca dashboard)

### After Market Close (4:30 PM ET)
- [ ] **Review daily P&L** across all accounts
- [ ] **Check Daily Trend signal generation** (should run at 4:05 PM)
  ```bash
  sudo journalctl -u magellan-daily-trend --since "1 hour ago" | grep "signal"
  ```
- [ ] **Review any errors or warnings**
- [ ] **Verify signal file was created** (Daily Trend)
  ```bash
  cat /home/ssm-user/magellan/deployed/daily_trend/signals.json
  ```

---

## 🔍 Log Monitoring

### View Real-Time Logs
```bash
# Bear Trap (intraday activity)
sudo journalctl -u magellan-bear-trap -f

# Daily Trend (signal generation at 4:05 PM, execution at 9:30 AM)
sudo journalctl -u magellan-daily-trend -f

# Hourly Swing (hourly checks during market hours)
sudo journalctl -u magellan-hourly-swing -f
```

### View Recent Logs
```bash
# Last 50 lines
sudo journalctl -u magellan-bear-trap -n 50 --no-pager

# Since specific time
sudo journalctl -u magellan-daily-trend --since "2 hours ago"

# Today's logs only
sudo journalctl -u magellan-hourly-swing --since today
```

### Search for Specific Events
```bash
# Find errors
sudo journalctl -u magellan-bear-trap | grep -i "error"

# Find credential retrieval
sudo journalctl -u magellan-daily-trend | grep "credentials"

# Find trade executions
sudo journalctl -u magellan-hourly-swing | grep "order\|trade\|position"
```

---

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check service status
sudo systemctl status magellan-bear-trap

# View detailed error
sudo journalctl -u magellan-bear-trap -n 100 --no-pager

# Common fixes:
# 1. Check Python path
which python3

# 2. Verify virtual environment
ls -la /home/ssm-user/magellan/.venv/bin/python

# 3. Test imports manually
/home/ssm-user/magellan/.venv/bin/python -c "from src.data_cache import cache; print('OK')"

# 4. Restart service
sudo systemctl restart magellan-bear-trap
```

### Credential Errors
```bash
# Verify SSM parameters exist
aws ssm describe-parameters --parameter-filters "Key=Name,Option=BeginsWith,Values=/magellan/alpaca" --region us-east-2

# Test credential retrieval
aws ssm get-parameter --name "/magellan/alpaca/PA3DDLQCBJSE/API_KEY" --region us-east-2 --with-decryption

# Check EC2 instance IAM role has SSM permissions
aws sts get-caller-identity
```

### Service Keeps Restarting
```bash
# Check restart count
systemctl show magellan-bear-trap | grep NRestarts

# View crash logs
sudo journalctl -u magellan-bear-trap --since "1 hour ago" | tail -100

# Disable auto-restart temporarily for debugging
sudo systemctl stop magellan-bear-trap
sudo systemctl disable magellan-bear-trap

# Run manually to see errors
cd /home/ssm-user/magellan
source .venv/bin/activate
export PYTHONPATH=/home/ssm-user/magellan
export CONFIG_PATH=/home/ssm-user/magellan/deployed/bear_trap/config.json
export ACCOUNT_ID=PA3DDLQCBJSE
python deployable_strategies/bear_trap/runner.py
```

---

## 📊 Performance Monitoring

### Check Alpaca Account Status (Web)
1. Go to https://app.alpaca.markets/paper/dashboard
2. Log in with each account:
   - **Bear Trap**: PA3DDLQCBJSE
   - **Daily Trend**: PA3A2699UCJM  
   - **Hourly Swing**: PA3ASNTJV624

3. Review:
   - Current equity
   - Open positions
   - Order history
   - P&L charts

### Export Performance Data
```bash
# From EC2, you can query Alpaca API
# (Requires implementing API calls in monitor script)

# For now, manually check via Alpaca web interface
```

---

## 🔧 Service Management

### Restart Services
```bash
# Restart individual service
sudo systemctl restart magellan-bear-trap

# Restart all services
sudo systemctl restart magellan-bear-trap magellan-daily-trend magellan-hourly-swing
```

### Stop Services (Emergency)
```bash
# Stop all trading immediately
sudo systemctl stop magellan-bear-trap magellan-daily-trend magellan-hourly-swing

# Verify stopped
systemctl is-active magellan-bear-trap magellan-daily-trend magellan-hourly-swing
```

### Update Code and Redeploy
```bash
# Pull latest code
cd /home/ssm-user/magellan
git pull origin deployment/aws-paper-trading-setup

# Restart services to pick up changes
sudo systemctl restart magellan-bear-trap magellan-daily-trend magellan-hourly-swing
```

---

## 📈 Expected Behavior

### Bear Trap (Intraday Scalping)
- **Active**: 9:30 AM - 4:00 PM ET
- **Frequency**: High (multiple trades per day possible)
- **Symbols**: MULN, ONDS, AMC, NKLA, WKHS
- **Logs**: Frequent activity during market hours

### Daily Trend (End-of-Day)
- **Signal Generation**: 4:05 PM ET daily
- **Order Execution**: 9:30 AM ET next day
- **Frequency**: Low (~7 trades/month across all symbols)
- **Symbols**: GOOGL, GLD, META, AAPL, QQQ, SPY, MSFT, TSLA, AMZN, IWM
- **Logs**: Activity at 4:05 PM and 9:30 AM only

### Hourly Swing (Hourly Checks)
- **Active**: 9:30 AM - 4:00 PM ET
- **Check Frequency**: Every hour on the hour
- **Frequency**: Medium (~25 trades/month)
- **Symbols**: TSLA, NVDA
- **Logs**: Activity at start of each hour during market

---

## 🎯 Key Metrics to Watch

### Red Flags
- ⚠️ Service status shows "inactive" during market hours
- ⚠️ No log activity when expected (e.g., Daily Trend at 4:05 PM)
- ⚠️ Repeated "error" messages in logs
- ⚠️ Daily loss exceeds 10% ($10,000 per account)
- ⚠️ Positions not closing at EOD (Bear Trap)

### Healthy Indicators
- ✅ All services show "active" status
- ✅ Logs show "✓ Retrieved Alpaca API credentials from SSM"
- ✅ Logs show "✓ Executor initialized"
- ✅ Orders executing successfully (check Alpaca dashboard)
- ✅ P&L tracking matches expectations

---

## 📞 Emergency Contacts

### Stop All Trading
```bash
# SSH to EC2
aws ssm start-session --target i-0cd7857b7e6b2e1a8 --region us-east-2

# Stop all services
sudo systemctl stop magellan-bear-trap magellan-daily-trend magellan-hourly-swing

# Verify stopped
systemctl is-active magellan-bear-trap magellan-daily-trend magellan-hourly-swing
```

### Close All Positions (via Alpaca Web)
1. Log into https://app.alpaca.markets/paper/dashboard
2. Navigate to "Positions"
3. Click "Close All Positions"

---

## 📝 Notes

- All times are in **Eastern Time (ET)**
- Services run 24/7 but only trade during market hours
- Logs are stored in systemd journal (not files)
- Credentials are encrypted in AWS SSM Parameter Store
- Each strategy runs on a separate $100k paper trading account
