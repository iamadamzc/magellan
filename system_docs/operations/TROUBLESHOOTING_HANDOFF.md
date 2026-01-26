# Magellan Trading System - Data Fetching Issue Handoff

## CRITICAL ISSUE
**The Bear Trap strategy is running but getting "No data" responses from Alpaca API despite the user having a paid Market Data Plus plan.**

Market opened at 9:30 AM ET (currently ~9:56 AM ET). AMC has 100,000+ volume but the strategy logs show "No data for AMC" and all other symbols.

---

## System Status

### Services Running
- ✅ **Bear Trap**: ACTIVE (but not getting data)
- ✅ **Daily Trend**: ACTIVE (sleeping until 4:05 PM - expected)
- ✅ **Hourly Swing**: ACTIVE (sleeping until 10:00 AM - expected)

### Current Behavior
```
2026-01-20 14:53:21 - magellan.bear_trap - WARNING - No data for WKHS
2026-01-20 14:53:21 - magellan.bear_trap - WARNING - No data for AMC
2026-01-20 14:53:21 - magellan.bear_trap - WARNING - No data for MULN
```

The strategy IS running and calling the Alpaca API, but `bars[symbol]` is returning empty/None.

---

## Environment Details

### AWS Infrastructure
- **EC2 Instance ID**: `i-0cd785630b55dd9a2`
- **Region**: `us-east-2`
- **Instance Type**: t3.micro
- **OS**: Amazon Linux 2023
- **User**: `ssm-user` (NOT ec2-user)

### Access Method
**AWS Systems Manager (SSM) - NO SSH KEYS**

```powershell
# Set AWS profile
$env:AWS_PROFILE="magellan_deployer"

# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Once connected
cd /home/ssm-user/magellan
source .venv/bin/activate
```

**Active SSM Session**: There's currently an open SSM session (running for 33+ minutes). You may be able to use the existing terminal.

### File Locations on EC2
```
/home/ssm-user/magellan/
├── deployable_strategies/bear_trap/
│   ├── bear_trap_strategy.py          # Production implementation (410 lines)
│   └── aws_deployment/
│       ├── run_strategy.py            # Main runner
│       └── config.json                # Strategy config
├── src/
│   ├── data_cache.py
│   ├── trade_logger.py
│   └── executor.py
└── logs/                               # Created when strategies run
```

### Systemd Services
```bash
# Check status
systemctl is-active magellan-bear-trap magellan-daily-trend magellan-hourly-swing

# View logs
sudo journalctl -u magellan-bear-trap --since "5 minutes ago" | tail -30

# Restart
sudo systemctl restart magellan-bear-trap
```

---

## Alpaca Configuration

### Accounts (Paper Trading)
1. **Bear Trap**: PA3DDLQCBJSE
2. **Daily Trend**: PA3A2699UCJM
3. **Hourly Swing**: PA3ASNTJV624

### API Credentials
Stored in AWS SSM Parameter Store:
- `/magellan/alpaca/PA3DDLQCBJSE/API_KEY`
- `/magellan/alpaca/PA3DDLQCBJSE/API_SECRET`

Retrieved at runtime via boto3 in the strategy code.

### Market Data Plan
**User has Market Data Plus plan** (paid subscription) which should provide access to SIP data for all symbols including penny stocks.

---

## Code Analysis

### Current Data Fetching Implementation
**File**: `/home/ssm-user/magellan/deployable_strategies/bear_trap/bear_trap_strategy.py`

**Lines 67-72** (the problematic section):
```python
request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Minute,
    start=datetime.now() - timedelta(hours=2),
    feed="iex"
)
bars = self.data_client.get_stock_bars(request)
```

**Lines 73-76** (the check):
```python
if bars and symbol in bars:
    self._evaluate_symbol(symbol, bars[symbol])
else:
    self.logger.warning(f"No data for {symbol}")
```

### Data Client Initialization
**Line 47**:
```python
self.data_client = StockHistoricalDataClient(api_key, api_secret)
```

This connects to `https://data.alpaca.markets` (separate from trading API).

### Symbols Being Monitored
From `config.json`:
- MULN (penny stock)
- ONDS (penny stock)
- AMC (high volume - 100k+ today)
- NKLA (penny stock)
- WKHS (penny stock)

---

## What We've Tried

1. ✅ **Verified services are running** - All 3 active
2. ✅ **Confirmed production code is deployed** - 410 lines, has full implementation
3. ✅ **Added `feed="iex"` parameter** - Based on docs saying paper accounts get IEX
4. ❌ **Still getting "No data"** - Even for AMC which has significant volume

### No Exceptions Thrown
```bash
sudo journalctl -u magellan-bear-trap --since "5 minutes ago" | grep -i "exception\|error\|traceback"
# Returns: (empty - no errors)
```

The API calls are succeeding (no exceptions), but returning empty data.

---

## Hypotheses to Investigate

### 1. Feed Parameter Issue
**Current**: `feed="iex"`
**Should try**: 
- `feed="sip"` (for paid plan)
- No feed parameter (use default)
- Check if Market Data Plus requires different feed specification

### 2. API Client Configuration
The `StockHistoricalDataClient` might need additional configuration for paid plans:
- Check if there's a subscription tier parameter
- Verify the API keys have the right permissions
- Check if there's a separate set of API keys for market data

### 3. Data Format Issue
Maybe `bars[symbol]` is the wrong way to access the data:
- Check actual structure of `bars` object
- Add debug logging: `self.logger.info(f"Bars response: {bars}")`
- Check if it's a BarSet vs dict

### 4. Time Range Issue
`start=datetime.now() - timedelta(hours=2)` might be problematic:
- Market just opened (9:30 AM)
- Requesting 2 hours back might be before market open
- Try: `start=datetime.now() - timedelta(minutes=30)`

### 5. API Endpoint Issue
Verify the data client is using the right endpoint for paid plans.

---

## Debugging Steps

### 1. Add Debug Logging
Edit line 72 to add:
```python
bars = self.data_client.get_stock_bars(request)
self.logger.info(f"API Response for {symbol}: {type(bars)}, {bars}")
```

### 2. Test API Directly
Create a simple test script:
```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import boto3

ssm = boto3.client('ssm', region_name='us-east-2')
api_key = ssm.get_parameter(Name='/magellan/alpaca/PA3DDLQCBJSE/API_KEY', WithDecryption=True)['Parameter']['Value']
api_secret = ssm.get_parameter(Name='/magellan/alpaca/PA3DDLQCBJSE/API_SECRET', WithDecryption=True)['Parameter']['Value']

client = StockHistoricalDataClient(api_key, api_secret)
request = StockBarsRequest(
    symbol_or_symbols="AMC",
    timeframe=TimeFrame.Minute,
    start=datetime.now() - timedelta(minutes=30),
    feed="sip"  # Try SIP for paid plan
)
bars = client.get_stock_bars(request)
print(f"Response: {bars}")
print(f"Type: {type(bars)}")
if bars:
    print(f"Keys: {bars.keys() if hasattr(bars, 'keys') else 'N/A'}")
```

### 3. Check Alpaca Dashboard
Log into https://app.alpaca.markets/paper/dashboard with account PA3DDLQCBJSE and verify:
- Market data subscription is active
- API keys have data permissions
- No rate limiting or errors

### 4. Check alpaca-py Version
```bash
pip show alpaca-py
```
Ensure it's a recent version that supports the Market Data Plus plan.

---

## Expected Resolution

Once data fetching works, you should see logs like:
```
2026-01-20 XX:XX:XX - magellan.bear_trap - INFO - Evaluating AMC: price=$X.XX, volume=XXXXX
```

Instead of:
```
2026-01-20 XX:XX:XX - magellan.bear_trap - WARNING - No data for AMC
```

---

## Quick Reference Commands

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Navigate to project
cd /home/ssm-user/magellan
source .venv/bin/activate

# Check service status
systemctl is-active magellan-bear-trap

# View recent logs
sudo journalctl -u magellan-bear-trap --since "2 minutes ago" | tail -30

# Edit the strategy file
nano deployable_strategies/bear_trap/bear_trap_strategy.py

# Restart after changes
sudo systemctl restart magellan-bear-trap

# Watch logs in real-time
sudo journalctl -u magellan-bear-trap -f
```

---

## Git Information

**Current Branch**: `deployment/aws-paper-trading-setup`
**Repository**: https://github.com/iamadamzc/magellan (public)

To pull latest changes:
```bash
cd /home/ssm-user/magellan
git pull origin deployment/aws-paper-trading-setup
```

---

## Success Criteria

The issue is resolved when:
1. Logs show actual price/volume data for symbols
2. No more "No data for {symbol}" warnings
3. Strategy begins evaluating entry criteria
4. (Eventually) Places test orders when criteria are met

---

## Contact Information

**User**: Has Market Data Plus plan (paid)
**Time**: Market opened 9:30 AM ET, currently ~9:56 AM ET
**Urgency**: HIGH - Market is open and system should be trading

---

**GOOD LUCK!** The infrastructure is solid - this is purely a data API configuration issue.
