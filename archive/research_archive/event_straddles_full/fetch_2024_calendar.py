"""
Fetch 2024 Economic Calendar from FMP

Retrieves historical economic calendar events from 2024
Focus: FOMC, CPI, NFP, and other high-impact US releases
"""

import requests
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

def fetch_economic_calendar_range(from_date, to_date):
    """Fetch economic calendar for date range"""
    url = "https://financialmodelingprep.com/stable/economic_calendar"
    params = {
        'from': from_date,
        'to': to_date,
        'apikey': FMP_API_KEY
    }
    
    print(f"Fetching calendar: {from_date} to {to_date}")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print(f"  ✅ Retrieved {len(data)} events")
        return data
    else:
        print(f"  ❌ Error {response.status_code}")
        return []

# Fetch 2024 calendar in quarters (API may have limits)
quarters = [
    ('2024-01-01', '2024-03-31'),
    ('2024-04-01', '2024-06-30'),
    ('2024-07-01', '2024-09-30'),
    ('2024-10-01', '2024-12-31'),
]

all_events = []
for start, end in quarters:
    events = fetch_economic_calendar_range(start, end)
    all_events.extend(events)
    print(f"  Total so far: {len(all_events)}")

print(f"\n✅ Total 2024 events fetched: {len(all_events)}")

# Filter for US events only
us_events = [e for e in all_events if e.get('country') == 'US']
print(f"US events: {len(us_events)}")

# Save raw data
with open('economic_calendar_2024_raw.json', 'w') as f:
    json.dump(us_events, f, indent=2)

print(f"✅ Saved to economic_calendar_2024_raw.json")

# Quick summary of event types
from collections import Counter
event_types = Counter([e.get('event', 'Unknown') for e in us_events])

print("\n" + "="*70)
print("TOP 20 EVENT TYPES (2024)")
print("="*70)
for event, count in event_types.most_common(20):
    print(f"{count:3d}  {event}")
