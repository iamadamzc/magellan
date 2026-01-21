"""
Diagnostic: Check if we're getting ANY intraday data and what the actual drops are
"""
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

fmp_key = os.getenv('FMP_API_KEY')

# Test MULN on a random recent date
symbol = 'MULN'
date = '2024-12-20'  # Recent Friday

url = f"https://financialmodelingprep.com/api/v3/historical-chart/5min/{symbol}"
params = {
    'from': date,
    'to': date,
    'apikey': fmp_key
}

response = requests.get(url, params=params)
data = response.json()

print(f"Testing {symbol} on {date}")
print(f"Response type: {type(data)}")
print(f"Number of bars: {len(data) if isinstance(data, list) else 'N/A'}")

if isinstance(data, list) and len(data) > 0:
    df = pd.DataFrame(data)
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"\nFirst 5 bars:")
    print(df.head())
    
    if 'open' in df.columns and len(df) > 0:
        session_open = df.iloc[0]['open']
        df['drop_from_open'] = ((df['low'] - session_open) / session_open) * 100
        
        print(f"\nSession open: ${session_open:.2f}")
        print(f"Intraday range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        print(f"Max drop: {df['drop_from_open'].min():.2f}%")
        print(f"Max gain: {df['drop_from_open'].max():.2f}%")
else:
    print(f"\nRaw response: {data}")
