# All 3 Strategies Fixed - Production Deployment Update

**Date**: 2026-01-20  
**Time**: 9:42 AM CST  
**Status**: ✅ ALL FIXED LOCALLY - READY FOR EC2 DEPLOYMENT

---

## Summary of Fixes

### ✅ Bear Trap (COMPLETED)
- **EC2**: Already fixed and running  
- **Local**: Fixed
- **Changes**: SIP feed + BarSet.data access + time range

### ✅ Daily Trend (FIXED LOCALLY)
- **EC2**: Needs update
- **Local**: Fixed  
- **Changes**: Removed cache, added direct API calls with SIP feed

### ✅ Hourly Swing (FIXED LOCALLY)  
- **EC2**: Needs update
- **Local**: Fixed
- **Changes**: Removed cache, added direct API calls with SIP feed

---

## Changes Made to Production Deployment Files

### All Three Strategies Now Use:

1. **Direct Alpaca API calls** (NO CACHE)
   ```python
   from alpaca.data.historical import StockHistoricalDataClient
   from alpaca.data.requests import StockBarsRequest
   from alpaca.data.timeframe import TimeFrame
   ```

2. **SIP feed** for Market Data Plus plan
   ```python
   feed="sip"  # Market Data Plus (paid plan)
   ```

3. **Correct BarSet.data access pattern**
   ```python
   if bars and bars.data and symbol in bars.data:
       bar_list = bars.data[symbol]
   ```

---

## Files Modified Locally

### Bear Trap
- ✅ `deployable_strategies/bear_trap/bear_trap_strategy_production.py`

### Daily Trend
- ✅ `deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
  - Removed line 17: `from src.data_cache import cache`
  - Added: Direct API imports
  - Added: `self.data_client = StockHistoricalDataClient(api_key, api_secret)`
  - Replaced: `cache.get_or_fetch_equity()` with direct API call (lines 115-143)

### Hourly Swing
- ✅ `deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`
  - Removed line 17: `from src.data_cache import cache`
  - Added: Direct API imports
  - Added: `self.data_client = StockHistoricalDataClient(api_key, api_secret)`
  - Replaced: `cache.get_or_fetch_equity()` with direct API call (lines 90-119)

---

## EC2 Update Commands

Run these commands to update Daily Trend and Hourly Swing on EC2:

```bash
# Connect to EC2
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# Navigate to project
cd /home/ssm-user/magellan

# Pull latest changes from Git (after you push)
git pull origin deployment/aws-paper-trading-setup

# OR manually update the files directly on EC2:

# Restart services after update
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing

# Verify services running
systemctl is-active magellan-daily-trend magellan-hourly-swing magellan-bear-trap

# Check logs for success
sudo journalctl -u magellan-daily-trend -f
sudo journalctl -u magellan-hourly-swing -f
```

---

## Git Commit Command

```powershell
cd a:\1\Magellan

git status

git add deployable_strategies/bear_trap/bear_trap_strategy_production.py
git add deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py
git add deployable_strategies/hourly_swing/aws_deployment/run_strategy.py
git add *.md

git commit -m "fix: Remove cache from production, use direct API for all strategies

BREAKING CHANGES:
- All 3 production deployment files now use direct Alpaca API calls
- Removed data_cache dependency from Daily Trend and Hourly Swing
- Applied consistent SIP feed + BarSet.data access across all strategies

Bear Trap:
- Changed feed from IEX to SIP (Market Data Plus)
- Fixed BarSet access pattern (bars.data)
- Adjusted time range to 45 minutes

Daily Trend:
- Removed src.data_cache import
- Added StockHistoricalDataClient for live data
- Direct API calls with SIP feed for daily bars
- Correct BarSet.data access pattern

Hourly Swing:
- Removed src.data_cache import
- Added StockHistoricalDataClient for live data
- Direct API calls with SIP feed for hourly bars
- Correct BarSet.data access pattern

VERIFIED: All strategies now fetch LIVE market data only.
NO CACHE FILES should exist in /aws_deployment directories."

git push origin deployment/aws-paper-trading-setup
```

---

## Verification Checklist

After deploying to EC2:

- [ ] Git changes pushed to `deployment/aws-paper-trading-setup`
- [ ] EC2 pulled latest changes
- [ ] magellan-daily-trend service restarted
- [ ] magellan-hourly-swing service restarted
- [ ] All 3 services showing `active`
- [ ] No "No data" errors in logs (except for low-volume symbols)
- [ ] No "CACHE HIT" messages in logs
- [ ] Confirm "Market Data Plus" or "SIP" in debug logs (if enabled)

---

## Expected Behavior After Fix

### Bear Trap (Runs continuously during market hours)
- ✅ Fetching 1-minute bars with SIP feed
- ✅ Processing AMC successfully
- ⚠️ Low-volume penny stocks may show intermittent "No data" (NORMAL)

### Daily Trend (Runs at 4:05 PM to generate signals, 9:30 AM to execute)
- ✅ Will fetch last 150 days of daily bars at 4:05 PM
- ✅ Calculate RSI and save signals to file
- ✅ Execute signals next morning at 9:30 AM market open

### Hourly Swing (Checks once per hour during market)
- ✅ Will fetch last 30 days of hourly bars each hour
- ✅ Calculate RSI on hourly timeframe
- ✅ Enter/exit positions based on hysteresis bands

---

## Architecture Decision

**CONFIRMED**: Production `/aws_deployment` files should:
- ✅ Use direct API calls (NO CACHE)
- ✅ Fetch live market data every time
- ✅ Use SIP feed for Market Data Plus plan
- ✅ Handle BarSet responses correctly with `.data` access

**Research/Backtest files** can continue using `src/data_cache` for development efficiency.

---

**Status**: Ready for deployment  
**Priority**: Deploy during next maintenance window or after market close  
**Risk**: Low - code tested pattern from working Bear Trap strategy
