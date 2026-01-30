# Production AWS Deployment Files - Data Fetching Audit

## FINDINGS ✅

### CONFIRMED: Production deployment files ARE using data_cache

**Daily Trend AWS Deployment:**
- File: `/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
- Line 17: `from src.data_cache import cache`

**Hourly Swing AWS Deployment:**
- File: `/home/ssm-user/magellan/deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`  
- Line 17: `from src.data_cache import cache`

**Bear Trap AWS Deployment:**
- Uses direct `StockHistoricalDataClient` ✅ (Correct - no cache)

---

##  What This Means

The `/aws_deployment` folders DO contain the cache import, which means:

1. **If cache files exist** → They will use cached data (STALE)
2. **If cache files DON'T exist for the requested date range** → Cache MISS → Fetch live data (CORRECT)

---

## Cache Files Found on EC2

```
/home/ssm-user/magellan/data/cache/earnings/*.parquet
```

These appear to be earnings-related cache files (not bar data), so Daily Trend/Hourly Swing likely hit CACHE MISS for bar data and fetch live.

---

## REQUIRED ACTIONS

### 1. Apply Same Fixes to Daily Trend & Hourly Swing

Both strategies likely need the SAME THREE FIXES as Bear Trap:

**Fix 1: Change feed from IEX to SIP**
```python
# Search for: feed="iex" or no feed parameter
# Change to: feed="sip"
```

**Fix 2: Fix BarSet access pattern**
```python
# Search for: if bars and symbol in bars:
# Change to: if bars and bars.data and symbol in bars.data:

# Search for: bars[symbol]
# Change to: bars.data[symbol]
```

**Fix 3: Adjust time ranges** (if applicable)
- Ensure not requesting data before market open

---

## Recommendation: Replace Cache with Direct API Calls

To match Bear Trap's production-ready approach, **remove cache dependency** from Daily Trend and Hourly Swing production files:

### Current (Using Cache):
```python
from src.data_cache import cache

# Somewhere in code:
df = cache.get_or_fetch_equity(symbol, timeframe, start, end)
```

### Recommended (Direct API):
```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Initialize once
data_client = StockHistoricalDataClient(api_key, api_secret)

# Fetch live data
request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Day,  # or TimeFrame.Hour
    start=start_date,
    end=end_date,
    feed="sip"
)
bars = data_client.get_stock_bars(request)

# Access data correctly
if bars and bars.data and symbol in bars.data:
    bar_list = bars.data[symbol]
    # Convert to DataFrame if needed
    df = pd.DataFrame([{
        'timestamp': bar.timestamp,
        'open': bar.open,
        'high': bar.high,
        'low': bar.low,
        'close': bar.close,
        'volume': bar.volume
    } for bar in bar_list])
```

---

## Strategy-Specific Considerations

### Daily Trend (Runs at 4:05 PM ET)
- Uses **daily bars**
- Signals at market close, executes next day at open
- Likely requests last N days of data
- **Time range**: Should request from market open today back X days

### Hourly Swing (Runs every hour during market)
- Uses **hourly bars**  
- Intraday strategy
- **Time range**: Should request from market open until current hour

Both need to ensure:
- ✅ Using `feed="sip"`
- ✅ Correct BarSet access (`bars.data`)
- ✅ Time ranges don't go before market open

---

## Next Steps

1. **Audit both aws_deployment/run_strategy.py files** for:
   - How they use `cache.get_or_fetch_equity`
   - What parameters they pass
   - Whether they handle BarSet responses

2. **Check if data_cache.py already has the feed/BarSet fixes**
   - If yes, strategies inherit the fixes ✅
   - If no, need to fix data_cache.py OR replace with direct calls

3. **Decide**: Keep cache (with fixes) vs. Remove cache (like Bear Trap)
   - Cache pros: Reduce API calls, consistent with backtest code
   - Cache cons: Risk of stale data, complexity
   - Direct API pros: Simple, guaranteed live data
   - Direct API cons: More API calls

---

## File Locations to Check/Modify

### On EC2:
- `/home/ssm-user/magellan/src/data_cache.py`
- `/home/ssm-user/magellan/deployable_strategies/daily_trend_hysteresis/aws_deployment/run_strategy.py`
- `/home/ssm-user/magellan/deployable_strategies/hourly_swing/aws_deployment/run_strategy.py`

### Locally:
- `a:\1\Magellan\src\data_cache.py`
- `a:\1\Magellan\deployable_strategies\daily_trend_hysteresis\aws_deployment\run_strategy.py`
- `a:\1\Magellan\deployable_strategies\hourly_swing\aws_deployment\run_strategy.py`

---

**Status**: Investigation complete - cache IS being used in production deployment files  
**Impact**: Likely hitting CACHE MISS (no matching cache files) and fetching live, but MUST verify and apply SIP/BarSet fixes
