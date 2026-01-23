import requests
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('FMP_API_KEY')

print('Testing Correct Stable Endpoints:')

# 1. Quote (contains sharesOutstanding)
r1 = requests.get(f'https://financialmodelingprep.com/stable/quote?symbol=AAPL&apikey={key}')
print(f'1. Quote (for float): {r1.status_code}')
if r1.status_code == 200:
    data = r1.json()[0]
    print(f'   sharesOutstanding: {data.get("sharesOutstanding")}')

# 2. Institutional Ownership
r2 = requests.get(f'https://financialmodelingprep.com/stable/institutional-ownership/symbol-positions-summary?symbol=AAPL&year=2024&quarter=3&apikey={key}')
print(f'2. Institutional: {r2.status_code}')
if r2.status_code == 200:
    print(f'   Data: {r2.json()[:1]}')

# 3. Economic Calendar
r3 = requests.get(f'https://financialmodelingprep.com/stable/economic-calendar?apikey={key}')
print(f'3. Econ Calendar: {r3.status_code}')
if r3.status_code == 200:
    print(f'   Events today: {len(r3.json())}')
