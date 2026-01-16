"""
FMP Earnings Calendar Probe
Debug why earnings dates are not being returned.
"""

import requests
import os
import sys

# Load env from .env file manually or require it
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('FMP_API_KEY')
symbol = 'NVDA'

print(f"Testing FMP Earnings Calendar for {symbol}")

# Try historical earning calendar
url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{symbol}"
params = {'apikey': api_key, 'limit': 10}

try:
    print(f"Requesting: {url}")
    r = requests.get(url, params=params)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Data Type: {type(data)}")
        if isinstance(data, list):
            print(f"Length: {len(data)}")
            if len(data) > 0:
                print(f"Sample: {data[0]}")
        else:
            print(f"Content: {data}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
