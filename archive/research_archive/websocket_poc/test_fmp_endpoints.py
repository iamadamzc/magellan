"""
FMP Economic Calendar - Test Correct Endpoint
Tests /stable path and respects 90-day limit
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

def test_endpoints():
    """Test both v3 and stable endpoints"""
    
    # Use 90-day range (FMP limit)
    today = datetime.now().strftime('%Y-%m-%d')
    ninety_days = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    
    endpoints = [
        ('v3', f"https://financialmodelingprep.com/api/v3/economic_calendar"),
        ('stable', f"https://financialmodelingprep.com/stable/economic-calendar")
    ]
    
    print(f"\nTesting date range: {today} to {ninety_days} (90 days)\n")
    
    for name, url in endpoints:
        print(f"Testing {name} endpoint:")
        print(f"  URL: {url}")
        
        params = {
            'from': today,
            'to': ninety_days,
            'apikey': FMP_API_KEY
        }
        
        try:
            response = requests.get(url, params=params)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Events: {len(data)}")
                if len(data) > 0:
                    print(f"  ✅ SUCCESS!")
                    print(f"\n  Sample events:")
                    for event in data[:3]:
                        print(f"    - {event.get('date')}: {event.get('event')}")
                    return name, url, data
                else:
                    print(f"  ⚠️  No events returned")
            else:
                print(f"  ❌ Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
        
        print()
    
    return None, None, []

if __name__ == "__main__":
    print("="*60)
    print("FMP Economic Calendar Endpoint Test")
    print("="*60)
    
    if not FMP_API_KEY:
        print("\n❌ FMP_API_KEY not found")
        exit(1)
    
    print(f"✅ API Key: {FMP_API_KEY[:8]}...")
    
    working_endpoint, url, data = test_endpoints()
    
    if working_endpoint:
        print(f"\n🎯 Use this endpoint: {working_endpoint}")
        print(f"   URL: {url}")
    else:
        print(f"\n❌ Neither endpoint returned data")
        print(f"   Fallback: Use manual calendar")
