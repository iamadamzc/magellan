# MIDAS Protocol - AWS Deployment Checklist

**Strategy**: MIDAS Protocol (Asian Session Mean Reversion)  
**Target**: Replace Bear Trap strategy on AWS EC2  
**Account**: PA3DDLQCBJSE  
**Branch**: `deployment/midas-protocol`

---

## Pre-Deployment Checklist

### 1. Code Readiness
- [x] Strategy logic implemented (`strategy.py`)
- [x] Runner script created (`runner.py`)
- [x] Configuration file complete (`config.json`)
- [x] Unit tests written (`tests/test_strategy.py`)
- [x] Systemd service file created (`deployment/systemd/magellan-midas-protocol.service`)
- [x] CI/CD workflow updated (`.github/workflows/deploy-strategies.yml`)

### 2. Configuration Review
- [x] Account ID: PA3DDLQCBJSE
- [x] Symbol: MNQ (Micro Nasdaq-100 Futures)
- [x] Session: 02:00-06:00 UTC
- [x] Max Daily Loss: $300
- [x] Stop Loss: 20 points ($40)
- [x] Take Profit: 120 points ($240)
- [x] Risk/Reward: 6:1

### 3. AWS Prerequisites
- [ ] Alpaca API credentials in SSM Parameter Store
  - Path: `/magellan/alpaca/PA3DDLQCBJSE/API_KEY`
  - Path: `/magellan/alpaca/PA3DDLQCBJSE/API_SECRET`
- [ ] EC2 instance running (i-0cd785630b55dd9a2)
- [ ] SSM agent active on EC2
- [ ] GitHub Actions secrets configured
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - ALPACA_TEST_API_KEY
  - ALPACA_TEST_API_SECRET

---

## Deployment Steps

### Step 1: Remove Old Bear Trap Service (Manual)

SSH into EC2 and disable the old strategy:

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Stop and disable bear-trap service
sudo systemctl stop magellan-bear-trap
sudo systemctl disable magellan-bear-trap

# Backup old service file
sudo mv /etc/systemd/system/magellan-bear-trap.service \
    /etc/systemd/system/magellan-bear-trap.service.backup

# Reload systemd
sudo systemctl daemon-reload
```

### Step 2: Commit and Push to Branch

```bash
# Stage all changes
git add prod/midas_protocol/
git add .github/workflows/deploy-strategies.yml

# Commit
git commit -m "feat: Add MIDAS Protocol strategy to replace Bear Trap

- Implemented Asian session mean reversion for MNQ futures
- Dual entry setups: Crash Reversal + Quiet Drift
- OCO bracket exits: SL=20pts, TP=120pts, Time=60 bars
- Strict session control: 02:00-06:00 UTC only
- Max daily loss: $300
- Updated CI/CD to deploy MIDAS Protocol instead of Bear Trap
"

# Push to branch
git push origin deployment/midas-protocol
```

### Step 3: Monitor CI/CD Pipeline

The GitHub Actions workflow will automatically:
1. Validate strategy code (linting, formatting)
2. Run unit tests with cached data
3. Deploy to EC2 via SSM
4. Install systemd service
5. Restart services
6. Run health checks

**Monitor at**: https://github.com/[your-org]/Magellan/actions

### Step 4: Verify Deployment (Manual)

After CI/CD completes, verify the deployment:

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Check service status
sudo systemctl status magellan-midas-protocol

# View logs
sudo journalctl -u magellan-midas-protocol -f

# Check if session detection works
# (should show "Outside Asian session" if not 02:00-06:00 UTC)

# Verify code is deployed
ls -la /home/ssm-user/magellan/prod/midas_protocol/

# Check Python imports work
cd /home/ssm-user/magellan
source .venv/bin/activate
python -c "from prod.midas_protocol.strategy import MIDASProtocolStrategy; print('✓ Import successful')"
```

### Step 5: Monitor First Session

**Next Asian Session**: 02:00-06:00 UTC

During the first live session:

```bash
# Watch real-time logs
sudo journalctl -u magellan-midas-protocol -f

# Check for:
# - ✓ Strategy initialized
# - ✓ Retrieved Alpaca API credentials
# - ✓ MIDAS Protocol Strategy initialized
# - Health checks showing "In Session: True"
# - Entry signals (if market conditions met)
# - Position management logs
```

---

## Post-Deployment Validation

### Health Checks

**Every 15 minutes during session**:
- [ ] Service is active: `systemctl is-active magellan-midas-protocol`
- [ ] No error logs: `sudo journalctl -u magellan-midas-protocol -p err`
- [ ] Session detection working correctly
- [ ] Indicators calculating properly (EMA, Velocity, ATR Ratio)

### Trade Validation

**After first trade**:
- [ ] Entry logic triggered correctly (Setup A or B)
- [ ] Stop loss placed at -20 points
- [ ] Take profit placed at +120 points
- [ ] Position tracked correctly
- [ ] Time-based exit working (60 bars)
- [ ] P&L calculation accurate ($2/point)
- [ ] Daily loss limit enforced ($300 max)

### Log Files

Check for trade logs:
```bash
ls -lh /home/ssm-user/magellan/logs/midas_protocol_*
```

---

## Rollback Plan

If issues occur, rollback to Bear Trap:

```bash
# Stop MIDAS Protocol
sudo systemctl stop magellan-midas-protocol
sudo systemctl disable magellan-midas-protocol

# Restore Bear Trap
sudo systemctl enable magellan-bear-trap
sudo systemctl start magellan-bear-trap
sudo systemctl status magellan-bear-trap
```

Then revert the branch:
```bash
git checkout main
git push origin deployment/midas-protocol --delete
```

---

## Expected Behavior

### Outside Session (Most of the day)
```
Outside Asian session (02:00-06:00 UTC), sleeping...
Health Check - Positions: 0, P&L Today: $0.00, Trades Today: 0, In Session: False
```

### During Session (02:00-06:00 UTC)
```
✓ MIDAS Protocol Strategy initialized
  Symbol: MNQ
  Max Daily Loss: $300
  Session: 02:00-06:00 UTC
Fetched 300 bars for MNQ
Health Check - Positions: 0, P&L Today: $0.00, Trades Today: 0, In Session: True
```

### On Entry Signal
```
SETUP A (Crash Reversal) TRIGGERED:
  Velocity: -95.50 (range: -150 to -67)
  EMA Distance: 180.25 (<= 220)
  ATR Ratio: 0.6500 (> 0.50)
📈 LONG ENTRY - MNQ (setup_a)
  Entry Price: 14950.00
  Stop Loss: 14930.00 (-20 pts / $40)
  Take Profit: 15070.00 (+120 pts / $240)
  Time Exit: 60 bars (60 minutes)
```

### On Exit
```
📉 LONG EXIT - MNQ
  Reason: Take Profit Hit
  Entry: 14950.00
  Exit: 15070.00
  P&L: +120.00 points / +$240.00
  Setup: setup_a
  Bars Held: 35
  Daily P&L: +$240.00
```

---

## Monitoring Commands Reference

```bash
# Service management
sudo systemctl status magellan-midas-protocol
sudo systemctl stop magellan-midas-protocol
sudo systemctl start magellan-midas-protocol
sudo systemctl restart magellan-midas-protocol

# Logs
sudo journalctl -u magellan-midas-protocol -f                # Follow logs
sudo journalctl -u magellan-midas-protocol -n 100            # Last 100 lines
sudo journalctl -u magellan-midas-protocol --since today     # Today's logs
sudo journalctl -u magellan-midas-protocol -p err            # Errors only

# Trade files
tail -f /home/ssm-user/magellan/logs/midas_protocol_trades_*.csv
cat /home/ssm-user/magellan/logs/midas_protocol_decisions_*.csv
```

---

## Support & Escalation

**Strategy Owner**: Magellan Development Team  
**Documentation**: See `prod/midas_protocol/README.md`  
**Issues**: Check `/var/log/journal` and strategy logs

**Common Issues**:
1. **Service won't start**: Check Python imports and API credentials
2. **No trades**: Verify session time (02:00-06:00 UTC) and market conditions
3. **Glitch Guard triggered**: Expected if velocity < -150 (protects from bad data)
4. **Session halted**: Daily loss hit -$300 (will reset next session)

---

**Deployment Date**: January 30, 2026  
**Last Updated**: January 30, 2026  
**Status**: Ready for Production
