"""
Test what futures symbols are available in FMP and what time intervals/date ranges exist
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

print("=" * 80)
print("FMP FUTURES DATA AVAILABILITY TEST")
print("=" * 80)

# Test different symbols for MNQ (Micro Nasdaq futures)
test_symbols = [
    "MNQUSD",   # What we tried
    "MNQ",      # Short form
    "NQUSD",    # What exists in cache (regular E-mini)
    "NQ",       # Alternative
]

# Test different endpoints
endpoints = {
    "1min": "https://financialmodelingprep.com/stable/historical-chart/1min",
    "1hour": "https://financialmodelingprep.com/stable/historical-chart/1hour",
    "1day": "https://financialmodelingprep.com/stable/historical-price-eod/full",
}

# Test recent date (last 30 days)
test_date_recent = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
test_date_end = datetime.now().strftime('%Y-%m-%d')

print(f"\nTest Date Range: {test_date_recent} to {test_date_end}")
print(f"API Key: {FMP_API_KEY[:4]}...\n")

results = []

for symbol in test_symbols:
    print(f"\nTesting symbol: {symbol}")
    print("-" * 60)
    
    for interval, url in endpoints.items():
        params = {
            "symbol": symbol,
            "from": test_date_recent,
            "to": test_date_end,
            "apikey": FMP_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    print(f"  ✅ {interval:6s}: {len(data):5d} bars | First: {data[0].get('date', 'N/A')}")
                    results.append({
                        'symbol': symbol,
                        'interval': interval,
                        'bars': len(data),
                        'status': 'SUCCESS'
                    })
                else:
                    print(f"  ⚠️  {interval:6s}: No data")
            elif response.status_code == 403:
                print(f"  ❌ {interval:6s}: 403 Forbidden (endpoint restricted)")
            else:
                print(f"  ❌ {interval:6s}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {interval:6s}: Error - {str(e)[:50]}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if results:
    print("\n✅ Available data found:")
    for r in results:
        print(f"   {r['symbol']:10s} @ {r['interval']:6s}: {r['bars']} bars")
else:
    print("\n❌ No futures data available for any tested symbol/interval combination")
    print("\nPossible reasons:")
    print("  1. FMP may not provide minute-level futures data for MNQ")
    print("  2. Symbol name format may be different")
    print("  3. Data may only be available for limited date ranges")
    
print("\n" + "=" * 80)
print("Recommendation: Check existing cache files to see what symbols/intervals exist")
print("=" * 80)
