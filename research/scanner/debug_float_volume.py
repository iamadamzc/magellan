"""
Debug script to find correct FMP endpoints for float and real-time volume
"""
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_STABLE_URL = "https://financialmodelingprep.com/stable"

def test_symbol(symbol):
    print(f"\n{'='*60}")
    print(f"Testing {symbol}")
    print(f"{'='*60}")
    
    # 1. Quote endpoint
    print("\n1. QUOTE ENDPOINT (current data)")
    url = f"{FMP_STABLE_URL}/quote?symbol={symbol}&apikey={FMP_API_KEY}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        data = resp.json()[0]
        print(f"   Price: ${data.get('price')}")
        print(f"   Volume: {data.get('volume'):,}")
        print(f"   Market Cap: ${data.get('marketCap'):,}")
        print(f"   Shares Outstanding: {data.get('sharesOutstanding')}")
        print(f"   Avg Volume: {data.get('avgVolume')}")
    
    # 2. Profile endpoint
    print("\n2. PROFILE ENDPOINT (company data)")
    url = f"{FMP_STABLE_URL}/profile?symbol={symbol}&apikey={FMP_API_KEY}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        data = resp.json()[0]
        print(f"   Shares Outstanding: {data.get('sharesOutstanding'):,}" if data.get('sharesOutstanding') else "   Shares Outstanding: None")
        print(f"   Float Shares: {data.get('floatShares')}")
        print(f"   Market Cap: ${data.get('mktCap'):,}" if data.get('mktCap') else "   Market Cap: None")
    
    # 3. Key Metrics endpoint
    print("\n3. KEY METRICS ENDPOINT (fundamental data)")
    url = f"{FMP_STABLE_URL}/key-metrics?symbol={symbol}&limit=1&apikey={FMP_API_KEY}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        if data:
            print(f"   Number of Shares: {data[0].get('numberOfShares')}")
            print(f"   Market Cap: {data[0].get('marketCap')}")
    
    # 4. Enterprise Value endpoint
    print("\n4. ENTERPRISE VALUE ENDPOINT")
    url = f"{FMP_STABLE_URL}/enterprise-values?symbol={symbol}&limit=1&apikey={FMP_API_KEY}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        if data:
            print(f"   Number of Shares: {data[0].get('numberOfShares')}")
            print(f"   Market Cap: {data[0].get('marketCapitalization')}")

if __name__ == "__main__":
    # Test with GORO (user's example)
    test_symbol("GORO")
    
    # Test with AAPL (known large cap)
    test_symbol("AAPL")
