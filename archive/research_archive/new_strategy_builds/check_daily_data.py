import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('FMP_API_KEY')

# Check daily data range
r = requests.get(
    'https://financialmodelingprep.com/stable/historical-price-eod/full',
    params={'symbol': 'GCUSD', 'from': '2024-01-01', 'to': '2024-12-31', 'apikey': api_key}
)

data = r.json()
print(f"Response type: {type(data)}")
print(f"Keys: {data.keys() if isinstance(data, dict) else 'N/A'}")

if isinstance(data, dict) and 'historical' in data:
    hist = data['historical']
    print(f"Daily bars: {len(hist)}")
    if hist:
        dates = [x['date'] for x in hist if 'date' in x]
        print(f"Range: {dates[-1]} to {dates[0]}")
elif isinstance(data, list):
    print(f"List with {len(data)} items")
    if data:
        dates = [x['date'] for x in data if 'date' in x]
        print(f"Range: {dates[-1]} to {dates[0]}" if dates else "No dates")
