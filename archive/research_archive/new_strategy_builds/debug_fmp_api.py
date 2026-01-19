"""
Debug: Check actual FMP API call and response
"""
import requests
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('FMP_API_KEY')

symbol = 'GCUSD'
start = '2024-01-01'
end = '2024-12-31'

# Test the actual API call
url = "https://financialmodelingprep.com/stable/historical-chart/1min"
params = {'symbol': symbol, 'from': start, 'to': end, 'apikey': api_key}

print("="*80)
print("FMP API DEBUG")
print("="*80)
print(f"URL: {url}")
print(f"Params: {params}")
print()

response = requests.get(url, params=params)
print(f"Status Code: {response.status_code}")
print(f"Response Length: {len(response.text)} chars")
print()

data = response.json()
print(f"Data type: {type(data)}")
print(f"Number of records: {len(data) if isinstance(data, list) else 'N/A'}")
print()

if isinstance(data, list) and len(data) > 0:
    print("First 3 records:")
    for i, record in enumerate(data[:3]):
        print(f"  {i+1}. {record}")
    print()
    print("Last 3 records:")
    for i, record in enumerate(data[-3:]):
        print(f"  {len(data)-2+i}. {record}")
    print()
    
    # Check date range
    dates = [r.get('date') for r in data if 'date' in r]
    if dates:
        print(f"Date range in response: {dates[-1]} to {dates[0]}")

print("\n" + "="*80)
print("CHECKING ALTERNATE ENDPOINT")
print("="*80)

# Try without from/to parameters (maybe it defaults to max range?)
url2 = f"https://financialmodelingprep.com/stable/historical-chart/1min/{symbol}"
params2 = {'apikey': api_key}

print(f"URL: {url2}")
print(f"Params: {params2}")
print()

response2 = requests.get(url2, params=params2)
print(f"Status Code: {response2.status_code}")
print(f"Response Length: {len(response2.text)} chars")

data2 = response2.json()
print(f"Number of records: {len(data2) if isinstance(data2, list) else 'N/A'}")

if isinstance(data2, list) and len(data2) > 0:
    dates2 = [r.get('date') for r in data2 if 'date' in r]
    if dates2:
        print(f"Date range: {dates2[-1]} to {dates2[0]}")

print("\n" + "="*80)
