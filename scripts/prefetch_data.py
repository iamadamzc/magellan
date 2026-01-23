"""
Pre-fetch and cache all data needed for Magellan experiments
Run this once to download all data, then all future backtests will be instant
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_cache import cache
from src.logger import LOG

print("=" * 80)
print("PRE-FETCHING DATA FOR MAGELLAN EXPERIMENTS")
print("=" * 80)
print("This will download and cache all data needed for testing")
print("Future backtests will be 10-100x faster!")
print("=" * 80)

# Define all assets and timeframes we need
DATASETS = {
    "equities_daily": {
        "symbols": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "NFLX", "AMD", "COIN", "PLTR"],
        "timeframe": "1day",
        "periods": [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")],  # Bear market  # Bull market
    },
    "equities_hourly": {
        "symbols": ["NVDA", "TSLA", "AAPL", "MSFT", "META", "AMZN"],
        "timeframe": "1hour",
        "periods": [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")],
    },
    "futures_hourly": {
        "symbols": ["SIUSD", "GCUSD", "CLUSD", "NGUSD"],
        "timeframe": "1hour",
        "periods": [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")],
        "type": "futures",
    },
    "futures_daily": {
        "symbols": ["SIUSD", "GCUSD", "CLUSD", "ESUSD", "NQUSD"],
        "timeframe": "1day",
        "periods": [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")],
        "type": "futures",
    },
    "earnings_calendar": {
        "symbols": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "NFLX", "AMD", "COIN", "PLTR"],
        "periods": [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")],
    },
}

total_downloads = 0
total_cached = 0

# Fetch equities daily
print("\n" + "=" * 80)
print("FETCHING EQUITIES - DAILY")
print("=" * 80)
dataset = DATASETS["equities_daily"]
for symbol in dataset["symbols"]:
    for start, end in dataset["periods"]:
        try:
            df = cache.get_or_fetch_equity(symbol, dataset["timeframe"], start, end)
            print(f"✓ {symbol} {dataset['timeframe']} {start} to {end}: {len(df)} bars")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} {dataset['timeframe']} {start} to {end}: ERROR - {e}")

# Fetch equities hourly
print("\n" + "=" * 80)
print("FETCHING EQUITIES - HOURLY")
print("=" * 80)
dataset = DATASETS["equities_hourly"]
for symbol in dataset["symbols"]:
    for start, end in dataset["periods"]:
        try:
            df = cache.get_or_fetch_equity(symbol, dataset["timeframe"], start, end)
            print(f"✓ {symbol} {dataset['timeframe']} {start} to {end}: {len(df)} bars")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} {dataset['timeframe']} {start} to {end}: ERROR - {e}")

# Fetch futures hourly
print("\n" + "=" * 80)
print("FETCHING FUTURES - HOURLY")
print("=" * 80)
dataset = DATASETS["futures_hourly"]
for symbol in dataset["symbols"]:
    for start, end in dataset["periods"]:
        try:
            df = cache.get_or_fetch_futures(symbol, dataset["timeframe"], start, end)
            print(f"✓ {symbol} {dataset['timeframe']} {start} to {end}: {len(df)} bars")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} {dataset['timeframe']} {start} to {end}: ERROR - {e}")

# Fetch futures daily
print("\n" + "=" * 80)
print("FETCHING FUTURES - DAILY")
print("=" * 80)
dataset = DATASETS["futures_daily"]
for symbol in dataset["symbols"]:
    for start, end in dataset["periods"]:
        try:
            df = cache.get_or_fetch_futures(symbol, dataset["timeframe"], start, end)
            print(f"✓ {symbol} {dataset['timeframe']} {start} to {end}: {len(df)} bars")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} {dataset['timeframe']} {start} to {end}: ERROR - {e}")

# Fetch earnings calendars
print("\n" + "=" * 80)
print("FETCHING EARNINGS CALENDARS")
print("=" * 80)
dataset = DATASETS["earnings_calendar"]
for symbol in dataset["symbols"]:
    for start, end in dataset["periods"]:
        try:
            dates = cache.get_or_fetch_earnings_calendar(symbol, start, end)
            print(f"✓ {symbol} earnings {start} to {end}: {len(dates)} events")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} earnings {start} to {end}: ERROR - {e}")

# Fetch historical news for sentiment strategies
print("\n" + "=" * 80)
print("FETCHING HISTORICAL NEWS (For Sentiment Strategies)")
print("=" * 80)
news_symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA"]
news_periods = [("2022-01-01", "2023-12-31"), ("2024-01-01", "2025-12-31")]
for symbol in news_symbols:
    for start, end in news_periods:
        try:
            news = cache.get_or_fetch_historical_news(symbol, start, end)
            print(f"✓ {symbol} news {start} to {end}: {len(news)} articles")
            total_downloads += 1
        except Exception as e:
            print(f"✗ {symbol} news {start} to {end}: ERROR - {e}")

print("\n" + "=" * 80)
print("PRE-FETCH COMPLETE")
print("=" * 80)
print(f"Total datasets downloaded: {total_downloads}")
print(f"Cache location: {cache.cache_dir}")
print("\nAll future backtests will use cached data (instant!)")
print("=" * 80)
