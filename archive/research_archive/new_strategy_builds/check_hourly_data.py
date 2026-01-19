import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('FMP_API_KEY')

# Check hourly data range
r = requests.get(
    'https://financialmodelingprep.com/stable/historical-chart/1hour',
    params={'symbol': 'GCUSD', 'from': '2024-01-01', 'to': '2024-12-31', 'apikey': api_key}
)

data = r.json()
print(f"Hourly bars: {len(data)}")
if data:
    dates = [x.get('date') for x in data if 'date' in x]
    print(f"Range: {dates[-1]} to {dates[0]}" if dates else "No dates")
