"""
Quick test: Can we get NQUSD (which exists in cache) vs MNQUSD from FMP?
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

print("Testing FMP API for Nasdaq futures data\n")

# Test both symbols with a simple recent date
test_date = "2025-12-15"  # Recent trading day

for symbol in ["NQUSD", "MNQUSD", "MNQ"]:
    url = "https://financialmodelingprep.com/stable/historical-chart/1hour"
    params = {
        "symbol": symbol,
        "from": test_date,
        "to": test_date,
        "apikey": FMP_API_KEY
    }
    
    print(f"\nSymbol: {symbol}")
    response = requests.get(url, params=params, timeout=10)
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"  Bars: {len(data) if data else 0}")
        if data and len(data) > 0:
            print(f"  First bar: {data[0]}")
    else:
        print(f"  Error: {response.text[:100]}")
