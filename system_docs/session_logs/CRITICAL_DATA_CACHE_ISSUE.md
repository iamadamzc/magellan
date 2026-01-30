# 🚨 CRITICAL: Daily Trend & Hourly Swing Using Stale Cached Data

**Date**: 2026-01-20  
**Severity**: 🔴 CRITICAL  
**Status**: ⚠️ URGENT INVESTIGATION REQUIRED

---

## Issue Summary

**Bear Trap strategy** uses direct Alpaca API calls for live data ✅  
**Daily Trend & Hourly Swing strategies** may be using `src/data_cache.py` which was designed for **BACKTESTING** with downloaded cached files, NOT live trading ❌

---

## Discovery

### Bear Trap (Working Correctly)
```python
# File: deployable_strategies/bear_trap/bear_trap_strategy.py
# Direct API calls - NO CACHE
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest

request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Minute,
    start=datetime.now() - timedelta(minutes=45),
    feed="sip"  # Live data
)
bars = self.data_client.get_stock_bars(request)  # ✅ LIVE DATA
```

### Daily Trend & Hourly Swing (SUSPECTED ISSUE)
```python
# File: deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py
# File: deployable_strategies/hourly_swing/aws_deployment/run_strategy.py
from src.data_cache import cache  # ⚠️ CACHE MODULE!

# Somewhere in the code:
df = cache.get_or_fetch_equity(symbol, timeframe, start, end)  # ❌ MAY USE CACHE
```

### Data Cache Implementation (src/data_cache.py)
```python
def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
    """Get equity data from cache or fetch from Alpaca"""
    cache_path = self._get_cache_path(symbol, timeframe, start, end, 'equities')
    
    # ❌ PROBLEM: Checks cache FIRST
    if cache_path.exists():
        LOG.info(f"[CACHE HIT] Loading {symbol} {timeframe} from cache")
        return pd.read_parquet(cache_path)  # Returns OLD data!
    
    # Only fetches if cache miss
    LOG.info(f"[CACHE MISS] Fetching {symbol} {timeframe} from Alpaca")
    # ... API call ...
```

---

## Critical Questions

### ❓ Are Daily Trend & Hourly Swing Trading on Stale Data?

**If YES**, this means:
- ✅ Services are running
- ✅ No errors showing
- ❌ But strategies are analyzing **yesterday's data** or **last week's data**
- ❌ Trades would be based on completely WRONG market conditions
- ❌ This would lead to CATASTROPHIC trading errors

### ❓ How to Verify

**Check logs for cache hits:**
```bash
# On EC2:
sudo journalctl -u magellan-daily-trend --since="1 hour ago" | grep -i "cache"
sudo journalctl -u magellan-hourly-swing --since="1 hour ago" | grep -i "cache"

# Look for:
# "[CACHE HIT]" = ❌ USING STALE DATA
# "[CACHE MISS]" = ✅ FETCHING LIVE DATA
```

**Check if cache directory exists:**
```bash
# On EC2:
ls -la /home/ssm-user/magellan/.cache/  # or wherever cache is stored
find /home/ssm-user/magellan -name "*.parquet" -type f  # Find cached files
```

---

## Immediate Actions Required

### 1. Verify Current Behavior (EC2)
```bash
# Check recent logs
sudo journalctl -u magellan-daily-trend --since="30 minutes ago" | grep -iE "(cache|fetching|loading)"
sudo journalctl -u magellan-hourly-swing --since="30 minutes ago" | grep -iE "(cache|fetching|loading)"

# Check for parquet cache files
find /home/ssm-user/magellan -name "*.parquet" -mtime -1  # Files modified in last day
```

### 2. If Using Cache - URGENT FIX OPTIONS

**Option A: Disable Cache in Code**
Modify `src/data_cache.py` to always fetch live data:
```python
def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
    """Get equity data from cache or fetch from Alpaca"""
    
    # PRODUCTION MODE: Always fetch live data, never use cache
    LOG.info(f"[LIVE MODE] Fetching {symbol} {timeframe} from Alpaca")
    client = AlpacaDataClient()
    # ... rest of fetch logic ...
```

**Option B: Add Environment Flag**
```python
USE_CACHE = os.getenv('MAGELLAN_USE_CACHE', 'false').lower() == 'true'

def get_or_fetch_equity(self, symbol, timeframe, start, end, feed='sip'):
    cache_path = self._get_cache_path(symbol, timeframe, start, end, 'equities')
    
    # Only use cache if explicitly enabled (for backtesting)
    if USE_CACHE and cache_path.exists():
        LOG.info(f"[CACHE HIT] Loading {symbol} {timeframe} from cache")
        return pd.read_parquet(cache_path)
    
    # Default: Always fetch live
    LOG.info(f"[LIVE MODE] Fetching {symbol} {timeframe} from Alpaca")
    # ... API call ...
```

**Option C: Clear All Cache**
```bash
# On EC2 - DELETE ALL CACHED FILES
rm -rf /home/ssm-user/magellan/.cache/
# Or wherever the cache directory is located
```

**Option D: Rewrite Daily Trend & Hourly Swing (Like Bear Trap)**
Convert them to use direct `StockHistoricalDataClient` calls instead of `data_cache`.

###  3. Verify Fix
After applying fix:
```bash
# Restart services
sudo systemctl restart magellan-daily-trend
sudo systemctl restart magellan-hourly-swing

# Watch logs for CACHE MISS or LIVE MODE messages
sudo journalctl -u magellan-daily-trend -f
sudo journalctl -u magellan-hourly-swing -f
```

---

## Impact Assessment

### If Strategies ARE Using Cache

| Impact | Severity |
|--------|----------|
| **Trading on Old Data** | 🔴 CRITICAL |
| **Risk of Bad Trades** | 🔴 CRITICAL |
| **Capital Loss Potential** | 🔴 HIGH |
| **System Appears Normal** | ⚠️ Silent Failure |

### If Cache is Empty (No .parquet files)
- ✅ Strategies would hit CACHE MISS every time
- ✅ Would fetch live data from Alpaca
- ✅ System working correctly (by accident)

---

## Files to Investigate

### On EC2
1. `/home/ssm-user/magellan/src/data_cache.py` - Cache implementation
2. `/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
3. `/home/ssm-user/magellan/deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`  
4. Cache directory location (find it!)

### Locally
1. `a:\1\Magellan\src\data_cache.py`
2. `a:\1\Magellan\deployable_strategies\daily_trend_hysteresis\` - Check all strategy files
3. `a:\1\Magellan\deployable_strategies\hourly_swing\` - Check all strategy files

---

## Technical Debt Note

The `data_cache` module was designed for:
- ✅ **Backtesting**: Download data once, use repeatedly
- ✅ **Development**: Avoid API rate limits during testing
- ✅ **Research**: Consistent datasets for analysis

It was **NOT** designed for:
- ❌ **Live Trading**: Needs real-time data
- ❌ **Paper Trading**: Needs current market prices
- ❌ **Production**: No stale data tolerance

---

## Recommended Long-Term Solution

**Separate backtest and production code paths:**

```python
# For BACKTESTING
from src.data_cache import cache
df = cache.get_or_fetch_equity(symbol, '1day', start, end)

# For PRODUCTION LIVE TRADING
from alpaca.data.historical import StockHistoricalDataClient
client = StockHistoricalDataClient(api_key, secret)
bars = client.get_stock_bars(request)  # Always live
```

Or use a flag:
```python
if ENVIRONMENT == 'production':
    # Direct API calls
else:
    # Cache allowed
```

---

## Next Steps

1. ✅ **Investigate immediately** - Check logs for cache usage
2. ⚠️ **Stop services if using cache** - Prevent bad trades
3. 🔧 **Apply fix** - Disable cache or rewrite strategies
4. ✅ **Verify** - Confirm live data flowing
5. 📝 **Document** - Update deployment procedures

---

**PRIORITY**: 🔴 **HIGHEST - INVESTIGATE NOW**  
**RISK**: Trading on stale data could cause significant losses  
**TIMELINE**: Verify within next 30 minutes (while market is open)
