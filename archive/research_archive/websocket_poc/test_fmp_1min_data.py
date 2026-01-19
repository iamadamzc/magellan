"""
Test /stable endpoint for 1-minute data
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

# Test one event: Jan 31, 2024 FOMC (2:00 PM ET)
test_date = '2024-01-31'

print(f"\n{'='*60}")
print(f"Testing FMP /stable 1-minute data")
print(f"{'='*60}")
print(f"\nDate: {test_date} (FOMC event)")
print(f"Endpoint: /stable/historical-chart/1min")

url = "https://financialmodelingprep.com/stable/historical-chart/1min"
params = {
    'symbol': 'SPY',
    'from': test_date,
    'to': test_date,
    'apikey': FMP_API_KEY
}

try:
    print(f"\nFetching SPY 1-minute bars for {test_date}...")
    response = requests.get(url, params=params)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ SUCCESS! Bars returned: {len(data)}")
        
        if len(data) > 0:
            print(f"\nSample bars (first 5):")
            for i, bar in enumerate(data[:5]):
                print(f"  {i+1}. {bar}")
            
            # Look for 2:00 PM bars (FOMC announcement time)
            fomc_time_bars = [b for b in data if '14:00' in b.get('date', '') or '14:01' in b.get('date', '') or '14:05' in b.get('date', '')]
            if fomc_time_bars:
                print(f"\n🎯 Bars around FOMC time (2:00 PM):")
                for bar in fomc_time_bars[:10]:
                    print(f"  {bar.get('date')}: ${bar.get('close')}")
                    
        print(f"\n✅ We can get the data needed for backtesting!")
    else:
        print(f"❌ Error {response.status_code}: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()
