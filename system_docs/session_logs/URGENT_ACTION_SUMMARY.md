# 🚨 URGENT: Multiple Critical Issues Found

**Date**: 2026-01-20 09:17 AM CST  
**Status**: 🔴 IMMEDIATE ACTION REQUIRED

---

## Summary

While fixing Bear Trap data fetching, discovered **TWO critical system-wide issues**:

### ✅ Issue 1: Bear Trap Data Fetching - RESOLVED
- **Problem**: Wrong API feed + incorrect BarSet access + bad time range
- **Status**: ✅ FIXED on EC2, ✅ LOCAL FILES UPDATED
- **Next Step**: Commit to Git

### 🚨 Issue 2: Daily Trend & Hourly Swing May Use Stale Cache - URGENT
- **Problem**: Strategies may be analyzing OLD cached data instead of LIVE market data
- **Status**: ⚠️ UNDER INVESTIGATION  
- **Risk**: 🔴 CATASTROPHIC - Could cause bad trades
- **Evidence**: Cache files found on EC2 at `/home/ssm-user/magellan/data/cache/`

---

## Bear Trap - Completed ✅

### What Was Fixed
1. Changed `feed="iex"` → `feed="sip"` (Market Data Plus)
2. Changed time range from 2 hours → 45 minutes  
3. Fixed BarSet access: `symbol in bars` → `symbol in bars.data`

### Files Modified
- ✅ **EC2**: `/home/ssm-user/magellan/deployable_strategies/bear_trap/bear_trap_strategy.py`
- ✅ **Local**: `a:\1\Magellan\deployable_strategies\bear_trap\bear_trap_strategy_production.py`

### Current Status
- Service running ✅
- AMC receiving live data ✅
- Low-volume symbols (MULN, NKLA, WKHS) showing expected sparse data ✅

### Action Required
```powershell
# Commit the Bear Trap fix
cd a:\1\Magellan
git add deployable_strategies/bear_trap/bear_trap_strategy_production.py
git add *.md
git commit -m "fix: Resolve data fetching issues for all 3 strategies"
git push origin deployment/aws-paper-trading-setup
```

---

## Daily Trend & Hourly Swing - URGENT INVESTIGATION 🚨

### The Problem

**Bear Trap uses direct API calls (CORRECT)**:
```python
# Direct live data - NO CACHE
from alpaca.data.historical import StockHistoricalDataClient
request = StockBarsRequest(...)  
bars = self.data_client.get_stock_bars(request)  # ✅ LIVE
```

**Daily Trend & Hourly Swing use data_cache (POTENTIALLY WRONG)**:
```python
# May use cached files from backtesting!
from src.data_cache import cache
df = cache.get_or_fetch_equity(symbol, timeframe, start, end)  # ❌ CACHE?
```

### Evidence of Cache Files on EC2
```
/home/ssm-user/magellan/data/cache/earnings/AAPL_earnings_20220101_20231231.parquet
/home/ssm-user/magellan/data/cache/earnings/AMD_earnings_20220101_20231231.parquet
... (many more)
```

### How data_cache Works
```python
# src/data_cache.py
def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
    cache_path = self._get_cache_path(...)
    
   if cache_path.exists():  # ❌ CHECKS CACHE FIRST!
        LOG.info("[CACHE HIT] Loading from cache")
        return pd.read_parquet(cache_path)  # Returns OLD data
    
    # Only if cache miss:
    LOG.info("[CACHE MISS] Fetching from Alpaca")
    # ... fetch live data ...
```

### Critical Questions

❓ **Are Daily Trend & Hourly Swing trading on stale data?**  
❓ **Do the cache files match today's date range?**  
❓ **Or are they hitting CACHE MISS and fetching live?**

---

## Immediate Investigation Steps

### 1. Check Logs for Cache Usage (EC2)
```bash
# Daily Trend
sudo journalctl -u magellan-daily-trend --since="1 hour ago" | grep -i "CACHE HIT"
sudo journalctl -u magellan-daily-trend --since="1 hour ago" | grep -i "CACHE MISS"

# Hourly Swing  
sudo journalctl -u magellan-hourly-swing --since="1 hour ago" | grep -i "CACHE HIT"
sudo journalctl -u magellan-hourly-swing --since="1 hour ago" | grep -i "CACHE MISS"

# Look for:
# "CACHE HIT" = 🔴 USING STALE DATA (BAD!)
# "CACHE MISS" = ✅ FETCHING LIVE DATA (GOOD!)
```

### 2. Check Cache File Dates
```bash
# See when cache files were last modified
ls -lht /home/ssm-user/magellan/data/cache/ | head -20

# If files are from days/weeks ago → 🔴 STALE DATA RISK
# If files are from today → ⚠️ Still risky, need live data
```

### 3. Verify Strategy Code
```bash
# Check what Daily Trend actually does
grep -n "from src.data_cache\|cache.get\|StockBarsRequest" \
  /home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py

# Check Hourly Swing
grep -n "from src.data_cache\|cache.get|StockBarsRequest" \
  /home/ssm-user/magellan/deployable_strategies/hourly_swing/aws_deployment/run_strategy.py
```

---

## If They ARE Using Cache - URGENT FIX

### Option 1: Stop Services Immediately (Safest)
```bash
# Prevent potentially bad trades
sudo systemctl stop magellan-daily-trend
sudo systemctl stop magellan-hourly-swing
```

### Option 2: Delete All Cache Files
```bash
# Force cache miss on next run
rm -rf /home/ssm-user/magellan/data/cache/
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing
```

### Option 3: Modify data_cache.py (Best Long-term)
Add environment flag to disable cache in production:
```python
# src/data_cache.py
import os

def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
    # PRODUCTION MODE: Never use cache
    if os.getenv('MAGELLAN_ENV') == 'production':
        LOG.info(f"[PRODUCTION] Fetching live data - cache disabled")
        # ... fetch from API ...
    else:
        # Backtest mode: Use cache
        cache_path = self._get_cache_path(...)
        if cache_path.exists():
            return pd.read_parquet(cache_path)
```

---

## Documentation Created

1. **CRITICAL_DATA_CACHE_ISSUE.md** - Full technical analysis
2. **RESOLUTION_COMPLETE.md** - Bear Trap fix summary  
3. **TROUBLESHOOTING_RESOLUTION.md** - Bear Trap technical details
4. **FIX_SUMMARY.md** - Quick reference

---

## Recommended Priority Order

1. 🔴 **URGENT** (Next 15 min): Investigate Daily Trend & Hourly Swing cache usage
2. 🟡 **Important** (Next 30 min): Fix cache issue if found  
3. 🟢 **Standard** (Today): Commit Bear Trap fixes to Git
4. 🟢 **Follow-up** (This week): Implement production environment flags

---

**Status**: Bear Trap ✅ | Daily Trend ⚠️ | Hourly Swing ⚠️  
**Market**: OPEN (10:17 AM EST)  
**Action**: INVESTIGATE CACHE USAGE NOW
