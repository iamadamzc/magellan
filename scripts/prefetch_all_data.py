"""
Comprehensive Data Prefetch for Strategy Testing
-------------------------------------------------
Fetches and caches all data needed for backtesting across multiple periods.

This ensures:
1. Fast backtests (no API delays)
2. Consistent data (same cache for all tests)
3. Offline testing capability

Run this once, then all backtests use cached data.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_cache import cache

# Define test universe
EQUITIES = ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMZN", "TSLA", "NFLX", "AMD", "COIN", "PLTR", "SPY", "QQQ", "IWM"]

FUTURES = ["SIUSD", "GCUSD", "CLUSD", "ESUSD", "NQUSD"]

# Define all test periods (past, present, future)
PERIODS = [
    ("2018-2019", "2018-01-01", "2019-12-31"),  # Pre-COVID
    ("2020-2021", "2020-01-01", "2021-12-31"),  # COVID + Recovery
    ("2022-2023", "2022-01-01", "2023-12-31"),  # Bear Market
    ("2024-2025", "2024-01-01", "2025-12-31"),  # Bull Market
]


def main():
    print("=" * 80)
    print("COMPREHENSIVE DATA PREFETCH")
    print("=" * 80)
    print(f"Equities: {len(EQUITIES)} symbols")
    print(f"Futures: {len(FUTURES)} symbols")
    print(f"Periods: {len(PERIODS)} periods")
    print(f"Total: {(len(EQUITIES) + len(FUTURES)) * len(PERIODS)} datasets")
    print("=" * 80)

    total_fetched = 0
    total_cached = 0

    # Fetch Equities
    print("\n[1/3] FETCHING EQUITY PRICE DATA")
    print("-" * 80)

    for symbol in EQUITIES:
        for period_name, start, end in PERIODS:
            try:
                df = cache.get_or_fetch_equity(symbol, "1day", start, end)
                print(f"✓ {symbol:6} {period_name:10} {len(df):4} bars")
                total_fetched += 1
            except Exception as e:
                print(f"✗ {symbol:6} {period_name:10} ERROR: {e}")

    # Fetch Futures
    print("\n[2/3] FETCHING FUTURES PRICE DATA")
    print("-" * 80)

    for symbol in FUTURES:
        for period_name, start, end in PERIODS:
            try:
                df = cache.get_or_fetch_futures(symbol, "1day", start, end)
                print(f"✓ {symbol:6} {period_name:10} {len(df):4} bars")
                total_fetched += 1
            except Exception as e:
                print(f"✗ {symbol:6} {period_name:10} ERROR: {e}")

    # Fetch News (Equities only, futures don't have news)
    print("\n[3/3] FETCHING NEWS SENTIMENT DATA")
    print("-" * 80)

    for symbol in EQUITIES:
        for period_name, start, end in PERIODS:
            try:
                news = cache.get_or_fetch_historical_news(symbol, start, end)
                print(f"✓ {symbol:6} {period_name:10} {len(news):4} articles")
                total_fetched += 1
            except Exception as e:
                print(f"✗ {symbol:6} {period_name:10} ERROR: {e}")

    print("\n" + "=" * 80)
    print("PREFETCH COMPLETE")
    print("=" * 80)
    print(f"Total datasets fetched: {total_fetched}")
    print(f"All data cached in: data/cache/")
    print("\nYou can now run backtests offline with instant speed!")


if __name__ == "__main__":
    main()
