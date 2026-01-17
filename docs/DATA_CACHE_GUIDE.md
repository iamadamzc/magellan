# Data Caching System - User Guide

**Location**: `src/data_cache.py`  
**Cache Storage**: `data/cache/`  
**Pre-fetch Script**: `scripts/prefetch_data.py`

---

## Overview

The data caching system stores historical price data locally to avoid repeated API calls during backtesting. This provides:

- **10-100x faster backtests** (no API calls after first fetch)
- **No API rate limits** (unlimited local reads)
- **Consistent data** across all tests
- **Offline testing** capability

---

## Cache Structure

```
data/cache/
├── equities/
│   ├── AAPL_1day_20220101_20231231.parquet
│   ├── AAPL_1day_20240101_20251231.parquet
│   ├── AAPL_1hour_20220101_20231231.parquet
│   └── NVDA_1day_20240101_20251231.parquet
├── futures/
│   ├── SIUSD_1hour_20220101_20231231.parquet
│   └── GCUSD_1day_20240101_20251231.parquet
├── crypto/
│   └── BTCUSD_1day_20220101_20251231.parquet
└── earnings/
    └── AAPL_earnings_20220101_20251231.parquet
```

Each file is named: `{SYMBOL}_{TIMEFRAME}_{START}_{END}.parquet`

---

## Quick Start

### 1. Pre-fetch All Data (Run Once)

```bash
python scripts/prefetch_data.py
```

This downloads and caches all data needed for Magellan experiments (takes ~10-15 minutes first time).

### 2. Use Cache in Your Scripts

```python
from src.data_cache import cache

# Equities (Alpaca)
df = cache.get_or_fetch_equity(
    symbol='AAPL',
    timeframe='1day',  # '1min', '1hour', or '1day'
    start='2024-01-01',
    end='2025-12-31',
    feed='sip'
)

# Futures/Commodities (FMP)
df = cache.get_or_fetch_futures(
    symbol='SIUSD',
    timeframe='1hour',  # '1hour' or '1day'
    start='2024-01-01',
    end='2025-12-31'
)

# Earnings Calendar (FMP)
earnings_dates = cache.get_or_fetch_earnings_calendar(
    symbol='AAPL',
    start='2024-01-01',
    end='2025-12-31'
)
```

---

## How It Works

### First Call (Cache Miss)
1. Checks if file exists in `data/cache/`
2. File not found → Fetches from API (Alpaca or FMP)
3. Saves to `.parquet` file
4. Returns DataFrame

### Subsequent Calls (Cache Hit)
1. Checks if file exists in `data/cache/`
2. File found → Loads from disk (instant!)
3. Returns DataFrame

---

## API Methods

### `cache.get_or_fetch_equity(symbol, timeframe, start, end, feed='sip')`

**Fetches equity data from Alpaca (or cache)**

- **symbol**: Stock ticker (e.g., 'AAPL', 'TSLA')
- **timeframe**: '1min', '1hour', or '1day'
- **start**: Start date ('YYYY-MM-DD')
- **end**: End date ('YYYY-MM-DD')
- **feed**: 'sip' (default) or 'iex'

**Returns**: DataFrame with OHLCV columns

### `cache.get_or_fetch_futures(symbol, timeframe, start, end)`

**Fetches futures/commodity data from FMP (or cache)**

- **symbol**: FMP symbol (e.g., 'SIUSD', 'GCUSD', 'CLUSD')
- **timeframe**: '1hour' or '1day'
- **start**: Start date ('YYYY-MM-DD')
- **end**: End date ('YYYY-MM-DD')

**Returns**: DataFrame with OHLCV columns

### `cache.get_or_fetch_earnings_calendar(symbol, start, end)`

**Fetches earnings calendar from FMP (or cache)**

- **symbol**: Stock ticker (e.g., 'AAPL')
- **start**: Start date ('YYYY-MM-DD')
- **end**: End date ('YYYY-MM-DD')

**Returns**: List of datetime objects (earnings dates)

### `cache.clear_cache(asset_type=None)`

**Clears cached data**

- **asset_type**: 'equities', 'futures', 'crypto', 'earnings', or None (all)

```python
cache.clear_cache('equities')  # Clear only equity data
cache.clear_cache()  # Clear everything
```

---

## Example: Converting Existing Backtest to Use Cache

### Before (Slow - API calls every run)

```python
from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

client = AlpacaDataClient()
df = client.fetch_historical_bars(
    symbol='AAPL',
    timeframe=TimeFrame.Day,
    start='2024-01-01',
    end='2025-12-31',
    feed='sip'
)
```

### After (Fast - cached)

```python
from src.data_cache import cache

df = cache.get_or_fetch_equity(
    symbol='AAPL',
    timeframe='1day',
    start='2024-01-01',
    end='2025-12-31',
    feed='sip'
)
```

**Result**: First run takes same time (fetches from API), all subsequent runs are instant!

---

## Pre-fetch Script Details

**Location**: `scripts/prefetch_data.py`

**What it downloads**:

1. **Equities (Daily)**: AAPL, MSFT, GOOGL, NVDA, META, AMZN, TSLA, NFLX, AMD, COIN, PLTR
2. **Equities (Hourly)**: NVDA, TSLA, AAPL, MSFT, META, AMZN
3. **Futures (Hourly)**: SIUSD, GCUSD, CLUSD, NGUSD
4. **Futures (Daily)**: SIUSD, GCUSD, CLUSD, ESUSD, NQUSD
5. **Earnings Calendars**: All 11 equities above

**Periods**: 
- 2022-01-01 to 2023-12-31 (Bear market)
- 2024-01-01 to 2025-12-31 (Bull market)

**Total downloads**: ~55 datasets

---

## When to Refresh Cache

### Refresh Daily Data
- When new trading days occur
- Run: `cache.clear_cache('equities')` then `python scripts/prefetch_data.py`

### Refresh Earnings Calendar
- At start of each quarter
- Run: `cache.clear_cache('earnings')` then fetch again

### Add New Assets
- Edit `scripts/prefetch_data.py` to add new symbols
- Run: `python scripts/prefetch_data.py` (only fetches missing data)

---

## Troubleshooting

### "No module named 'src'" Error

Make sure your script adds project root to path:
```python
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
```

### Cache Not Working (Always Fetching)

Check cache directory exists:
```python
from src.data_cache import cache
print(cache.cache_dir)  # Should print: data/cache
```

### FMP API 403 Error

Earnings calendar endpoint changed. Cache handles fallback automatically:
- Tries: `/stable/earnings-calendar` first
- Falls back to: `/api/v4/earning_calendar` if 403

### Wrong Data Returned

Clear cache and re-fetch:
```python
from src.data_cache import cache
cache.clear_cache()  # Clears all
```

Then run: `python scripts/prefetch_data.py`

---

## Performance Comparison

| Action | Without Cache | With Cache | Speedup |
|--------|---------------|------------|---------|
| Fetch AAPL daily (2 years) | ~2-3 seconds | ~0.05 seconds | **40-60x** |
| Fetch NVDA hourly (2 years) | ~10-15 seconds | ~0.1 seconds | **100-150x** |
| Run 10-asset backtest | ~30-40 seconds | ~0.5-1 seconds | **30-80x** |

---

## Storage Requirements

| Dataset Type | Size per Asset | Total (all assets) |
|--------------|----------------|-------------------|
| Daily (2 years) | ~50 KB | ~1 MB |
| Hourly (2 years) | ~500 KB | ~10 MB |
| Earnings Calendar | ~5 KB | ~50 KB |
| **Total Cache** | - | **~50-100 MB** |

Very small - cache everything!

---

## Best Practices

1. **Run pre-fetch first**: `python scripts/prefetch_data.py` before starting experiments
2. **Use cache in all scripts**: Replace direct API calls with `cache.get_or_fetch_*`
3. **Clear cache monthly**: Fresh data for live trading development
4. **Check cache hits**: Look for `[CACHE HIT]` in logs to confirm caching works
5. **Add new assets**: Edit `prefetch_data.py` and add to symbol lists

---

## Integration with Existing Scripts

All new backtest scripts should use cache:

```python
# At top of any backtest script
from src.data_cache import cache

# Replace all data fetching with cache calls
df = cache.get_or_fetch_equity(symbol, timeframe, start, end)
```

**Existing scripts to update**:
- ✅ `experiment_g_no_rsi_expansion.py` - Will update to use cache
- ✅ `experiment_e_real_hourly_silver_gold.py` - Will update to use cache
- ⚠️ `batch_test_strategy1_mag7.py` - Should be updated
- ⚠️ All clean room tests - Should be updated

---

## Questions?

**Where is the cache?** → `data/cache/` in project root

**How do I clear it?** → `cache.clear_cache()` or delete `data/cache/` directory

**How do I add new data?** → Edit `scripts/prefetch_data.py` and add symbols

**Does it work offline?** → Yes! Once data is cached, no internet needed

**Can I use it in production?** → Yes for backtesting, but live trading should fetch fresh data

---

**Last Updated**: 2026-01-17  
**Version**: 1.0  
**Maintainer**: Magellan Development Team
