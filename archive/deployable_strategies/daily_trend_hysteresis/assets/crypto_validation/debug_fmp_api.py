"""
Debug FMP Crypto API - Test actual response format
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")

# Test different endpoints
endpoints = [
    (
        "Full EOD",
        f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=BTCUSD&apikey={FMP_API_KEY}",
    ),
    (
        "Light EOD",
        f"https://financialmodelingprep.com/stable/historical-price-eod/light?symbol=BTCUSD&apikey={FMP_API_KEY}",
    ),
    (
        "1day Chart",
        f"https://financialmodelingprep.com/stable/historical-chart/1day?symbol=BTCUSD&apikey={FMP_API_KEY}",
    ),
]

print("=" * 80)
print("FMP CRYPTO API DEBUG")
print("=" * 80)

for name, url in endpoints:
    print(f"\nTesting: {name}")
    print(f"URL: {url[:80]}...")

    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")

        if response.ok:
            data = response.json()
            print(f"Response type: {type(data)}")

            if isinstance(data, list):
                print(f"List length: {len(data)}")
                if len(data) > 0:
                    print(f"First item keys: {list(data[0].keys())}")
                    print(f"First item: {data[0]}")
            elif isinstance(data, dict):
                print(f"Dict keys: {list(data.keys())}")
                if "historical" in data:
                    print(f"Historical length: {len(data['historical'])}")
                    if len(data["historical"]) > 0:
                        print(f"First historical item: {data['historical'][0]}")

            print("✅ SUCCESS")
            break  # Found working endpoint
        else:
            print(f"❌ Error: {response.status_code} - {response.text[:200]}")

    except Exception as e:
        print(f"❌ Exception: {e}")

print("\n" + "=" * 80)
