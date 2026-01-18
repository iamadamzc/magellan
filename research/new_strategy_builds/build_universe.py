"""
Universe Builder - Identify and Cache Momentum Stocks
------------------------------------------------------
Step 1: For each day, identify stocks meeting criteria
Step 2: Cache all their data for the test period
Step 3: Run ORB tests on the cached universe

Criteria:
- Price $2-$50
- Top gainers or most active
- Save list for testing
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import datetime, timedelta
import requests
import os

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

FMP_API_KEY = os.getenv('FMP_API_KEY')

def get_trading_days(start_date, end_date):
    """Get list of trading days"""
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    days = []
    while current <= end:
        if current.weekday() < 5:
            days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return days

def get_daily_candidates(date):
    """Get candidate stocks for this day"""
    
    candidates = set()
    
    # Get top gainers
    try:
        url = f"https://financialmodelingprep.com/stable/biggest-gainers"
        params = {'apikey': FMP_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            gainers = response.json()
            if gainers:
                for stock in gainers[:20]:  # Top 20
                    symbol = stock.get('symbol', '')
                    price = stock.get('price', 0)
                    
                    if price >= 2.0 and price <= 50.0:
                        candidates.add(symbol)
    except:
        pass
    
    # Get most active
    try:
        url = f"https://financialmodelingprep.com/stable/most-active"
        params = {'apikey': FMP_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            actives = response.json()
            if actives:
                for stock in actives[:20]:  # Top 20
                    symbol = stock.get('symbol', '')
                    price = stock.get('price', 0)
                    
                    if price >= 2.0 and price <= 50.0:
                        candidates.add(symbol)
    except:
        pass
    
    return list(candidates)

# Build universe
print("="*80)
print("UNIVERSE BUILDER - IDENTIFY MOMENTUM STOCKS")
print("="*80)

test_period_start = '2024-11-01'
test_period_end = '2024-11-30'

print(f"\nTest period: {test_period_start} to {test_period_end}")

trading_days = get_trading_days(test_period_start, test_period_end)
print(f"Trading days: {len(trading_days)}")

# Collect all unique symbols across all days
all_symbols = set()
daily_symbols = {}

for date in trading_days:
    print(f"\nScanning {date}...")
    candidates = get_daily_candidates(date)
    daily_symbols[date] = candidates
    all_symbols.update(candidates)
    print(f"  Found {len(candidates)} candidates")

print("\n" + "="*80)
print("UNIVERSE SUMMARY")
print("="*80)
print(f"\nTotal unique symbols: {len(all_symbols)}")
print(f"Symbols: {sorted(list(all_symbols))}")

# Save universe
universe_df = pd.DataFrame([
    {'date': date, 'symbols': ','.join(syms)}
    for date, syms in daily_symbols.items()
])

output_path = Path('research/new_strategy_builds/results/momentum_universe_nov2024.csv')
universe_df.to_csv(output_path, index=False)
print(f"\n✅ Universe saved to: {output_path}")

# Now cache data for all symbols
print("\n" + "="*80)
print("CACHING DATA FOR UNIVERSE")
print("="*80)

cached = []
failed = []

for symbol in sorted(all_symbols):
    print(f"\nCaching {symbol}...")
    try:
        df = cache.get_or_fetch_equity(symbol, '1min', test_period_start, test_period_end)
        if df is not None and len(df) > 0:
            print(f"  ✅ {len(df):,} bars cached")
            cached.append(symbol)
        else:
            print(f"  ⚠️ No data")
            failed.append(symbol)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        failed.append(symbol)

print("\n" + "="*80)
print("CACHE SUMMARY")
print("="*80)
print(f"Successfully cached: {len(cached)}")
print(f"Failed: {len(failed)}")

if cached:
    print(f"\n✅ Ready to test: {', '.join(cached)}")

if failed:
    print(f"\n⚠️ Failed: {', '.join(failed)}")

# Save cached list
cached_df = pd.DataFrame({
    'symbol': cached,
    'status': 'cached'
})

cached_path = Path('research/new_strategy_builds/results/cached_universe_nov2024.csv')
cached_df.to_csv(cached_path, index=False)
print(f"\n✅ Cached symbols saved to: {cached_path}")

print("\n" + "="*80)
print("NEXT STEP")
print("="*80)
print("Run ORB V9 tests on the cached universe:")
print(f"  {len(cached)} symbols × Nov 2024 = {len(cached) * len(trading_days)} symbol-days")
