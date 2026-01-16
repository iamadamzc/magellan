"""
Congressional Trading Strategy Research - "Pelosi Tracker"

Strategy: Copy trades disclosed by members of Congress
Hypothesis: Congressional members have access to non-public information, giving them edge

Data Source: FMP congressional trading endpoints
Expected Sharpe: 0.8-1.5 (based on external academic research)

Implementation:
1. Fetch congressional trades from FMP
2. Filter for liquid stocks (>$100k positions)
3. Backtest: Copy trades T+2 days after disclosure, hold 30 days
4. Calculate Sharpe and compare to SPY buy-and-hold
"""

import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

print("="*80)
print("CONGRESSIONAL TRADING RESEARCH")
print("="*80)
print("\nTesting FMP endpoints for congressional trade data...")

# Test multiple potential endpoints
endpoints_to_test = [
    "https://financialmodelingprep.com/v4/senate-trading",
    "https://financialmodelingprep.com/v4/senate-disclosure",
    "https://financialmodelingprep.com/api/v4/senate-trading",
    "https://financialmodelingprep.com/api/v4/senate-disclosure",
    "https://financialmodelingprep.com/stable/senate-trading",
]

def test_endpoint(url, params=None):
    """Test if endpoint returns data"""
    if params is None:
        params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data
        return False, f"Status {response.status_code}"
    except Exception as e:
        return False, str(e)

print("\n" + "="*80)
print("TESTING ENDPOINTS")
print("="*80)

working_endpoint = None
for endpoint in endpoints_to_test:
    print(f"\n{endpoint}")
    print("  Testing...", end='')
    
    success, result = test_endpoint(endpoint)
    
    if success:
        print(f" ✅ WORKS!")
        print(f"  Returned {len(result)} records")
        
        if len(result) > 0:
            working_endpoint = endpoint
            print(f"  Sample record keys: {list(result[0].keys())[:5]}")
            break
    else:
        print(f" ❌ {result}")

if not working_endpoint:
    print("\n" + "="*80)
    print("⚠️  NO WORKING ENDPOINTS FOUND")
    print("="*80)
    print("\nPossible reasons:")
    print("1. FMP Ultimate plan may not include congressional data")
    print("2. Endpoint naming/path may be different")
    print("3. Feature may require special access")
    
    print("\nRecommendations:")
    print("1. Check FMP API documentation for correct endpoint")
    print("2. Contact FMP support to confirm feature availability")
    print("3. Alternative: Use Unusual Whales API or Capitol Trades API")
    
else:
    print("\n" + "="*80)
    print("✅ WORKING ENDPOINT FOUND")
    print("="*80)
    print(f"Endpoint: {working_endpoint}")
    
    # Fetch more data to analyze
    print("\nFetching comprehensive dataset...")
    success, trades = test_endpoint(working_endpoint)
    
    if success and trades:
        print(f"✅ Retrieved {len(trades)} congressional trades")
        
        # Save raw data
        with open('congressional_trades_raw.json', 'w') as f:
            json.dump(trades, f, indent=2)
        
        print(f"\n✅ Saved to congressional_trades_raw.json")
        
        # Analyze data structure
        if len(trades) > 0:
            sample = trades[0]
            print("\n" + "="*80)
            print("SAMPLE TRADE STRUCTURE")
            print("="*80)
            for key, value in sample.items():
                print(f"{key:20s}: {value}")
        
        # Quick statistics
        print("\n" + "="*80)
        print("DATASET STATISTICS")
        print("="*80)
        
        # Extract dates to find range
        dates = []
        for trade in trades:
            if 'disclosureDate' in trade:
                dates.append(trade['disclosureDate'])
            elif 'transactionDate' in trade:
                dates.append(trade['transactionDate'])
        
        if dates:
            dates_clean = [d for d in dates if d]
            if dates_clean:
                print(f"Date Range: {min(dates_clean)} to {max(dates_clean)}")
        
        # Count by year
        from collections import Counter
        years = [d[:4] for d in dates if d and len(d) >= 4]
        year_counts = Counter(years)
        
        print("\nTrades by Year:")
        for year in sorted(year_counts.keys(), reverse=True):
            print(f"  {year}: {year_counts[year]:4d} trades")
        
        # Check if 2024 data exists
        trades_2024 = [t for t in trades if any(
            str(t.get(key, '')).startswith('2024') 
            for key in ['disclosureDate', 'transactionDate', 'filingDate']
        )]
        
        if trades_2024:
            print(f"\n✅ 2024 data available: {len(trades_2024)} trades")
            print("   → Can proceed with backtest")
        else:
            print("\n⚠️  No 2024 data found")
            print("   → May need to adjust date range or use available years")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)

if working_endpoint:
    print("✅ Data access confirmed")
    print("\n1. Filter for liquid stocks (market cap >$1B)")
    print("2. Filter for purchase transactions (ignore sales)")
    print("3. Build backtest: Copy trade T+2 days, hold 30 days")
    print("4. Calculate Sharpe and compare to SPY")
else:
    print("❌ Data access blocked")
    print("\n1. Research alternative data sources")
    print("2. Contact FMP support for endpoint info")
    print("3. Pivot to Insider Trades strategy (different endpoint)")
