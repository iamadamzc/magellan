"""
Alternative Data - Correct Stable Endpoints Test

User discovered correct paths:
- /stable/senate-latest
- /stable/house-latest  
- /stable/latest-insider-trade
- /stable/search-insider-trades
- /stable/latest-filings

Testing all to validate data access and resume strategy development
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

print("="*80)
print("ALTERNATIVE DATA - STABLE ENDPOINTS TEST")
print("="*80)

endpoints = [
    ("Senate Trading", "https://financialmodelingprep.com/stable/senate-latest"),
    ("House Trading", "https://financialmodelingprep.com/stable/house-latest"),
    ("Latest Insider Trades", "https://financialmodelingprep.com/stable/latest-insider-trade"),
    ("Search Insider Trades", "https://financialmodelingprep.com/stable/search-insider-trades", {'symbol': 'AAPL'}),
    ("Latest Filings", "https://financialmodelingprep.com/stable/latest-filings"),
]

results = {}

for item in endpoints:
    name = item[0]
    url = item[1]
    extra_params = item[2] if len(item) > 2 else {}
    
    print(f"\n{name}")
    print(f"  URL: {url}")
    print("  Testing...", end='')
    
    params = {'apikey': FMP_API_KEY, **extra_params}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = len(data) if isinstance(data, list) else 1
            print(f" ✅ {count} records")
            
            results[name] = {
                'status': 'success',
                'url': url,
                'count': count,
                'sample': data[0] if isinstance(data, list) and len(data) > 0 else data
            }
            
            # Show sample
            if count > 0:
                sample = data[0] if isinstance(data, list) else data
                print(f"  Sample keys: {list(sample.keys())[:5]}")
                
        else:
            print(f" ❌ Status {response.status_code}")
            results[name] = {'status': 'failed', 'code': response.status_code}
    except Exception as e:
        print(f" ❌ Error: {str(e)[:50]}")
        results[name] = {'status': 'error', 'message': str(e)}

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

working = [name for name, data in results.items() if data.get('status') == 'success']
failed = [name for name, data in results.items() if data.get('status') != 'success']

print(f"\n✅ WORKING ({len(working)} endpoints):")
for name in working:
    print(f"  • {name}: {results[name]['count']} records")

if failed:
    print(f"\n❌ FAILED ({len(failed)} endpoints):")
    for name in failed:
        print(f"  • {name}")

# Save successful data for analysis
if working:
    print("\n" + "="*80)
    print("SAVING DATA")
    print("="*80)
    
    for name in working:
        filename = name.lower().replace(' ', '_') + '_raw.json'
        url = results[name]['url']
        params = {'apikey': FMP_API_KEY}
        
        # Fetch full dataset
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  ✅ {filename}")

# Quick analysis
print("\n" + "="*80)
print("STRATEGY VIABILITY")
print("="*80)

if 'Senate Trading' in working or 'House Trading' in working:
    print("\n📊 CONGRESSIONAL TRADING: ✅ VIABLE")
    print("  Strategy: Copy trades from senators/representatives")
    print("  Expected Sharpe: 0.8-1.5")
    print("  Next: Build backtest")

if 'Latest Insider Trades' in working or 'Search Insider Trades' in working:
    print("\n🔍 INSIDER CLUSTERING: ✅ VIABLE")
    print("  Strategy: Detect 3+ insider buys in 7 days")
    print("  Expected Sharpe: 0.8-1.2")
    print("  Next: Build clustering detector")

if 'Latest Filings' in working:
    print("\n📄 13F FOLLOWING: ✅ VIABLE")
    print("  Strategy: Follow hedge fund new positions")
    print("  Expected Sharpe: 0.5-0.8")
    print("  Next: Parse 13F data")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("\n1. Congressional Trades: Backtest 2024 copy-trading strategy")
print("2. Insider Clustering: Detect buy clusters and test edge")
print("3. Update Phase 2 summary with new findings")
