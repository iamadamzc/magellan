"""
Economic Calendar Filter - Extract High-Impact US Events

Filters the FMP economic calendar to identify tradeable events:
- FOMC meetings
- CPI releases
- Non-Farm Payrolls (NFP)
- Other high-impact US economic data

Focus: Events that create significant volatility spikes suitable for straddle strategies
"""

import json
from datetime import datetime
from collections import defaultdict

# Load calendar
import os
calendar_path = os.path.join(os.path.dirname(__file__), '..', 'websocket_poc', 'economic_calendar.json')
with open(calendar_path, 'r') as f:
    calendar = json.load(f)

print(f"Loaded {len(calendar)} total events")

# Filter for US events only
us_events = [e for e in calendar if e.get('country') == 'US']
print(f"US events: {len(us_events)}")

# Filter for 2024 events only
events_2024 = []
for event in us_events:
    date_str = event.get('date', '')
    if date_str.startswith('2024'):
        events_2024.append(event)

print(f"2024 US events: {len(events_2024)}")

# Categorize by event type
event_categories = defaultdict(list)

# High-impact event keywords
FOMC_KEYWORDS = ['FOMC', 'Fed Interest Rate', 'Federal Funds Rate']
CPI_KEYWORDS = ['CPI', 'Inflation Rate YoY', 'Core Inflation Rate YoY']
NFP_KEYWORDS = ['Non-Farm Payrolls', 'Nonfarm Payrolls', 'NFP']
UNEMPLOYMENT_KEYWORDS = ['Unemployment Rate']
RETAIL_KEYWORDS = ['Retail Sales']
GDP_KEYWORDS = ['GDP Growth Rate', 'Gross Domestic Product']
PCE_KEYWORDS = ['PCE Price Index', 'Core PCE']
PPI_KEYWORDS = ['PPI', 'Producer Price Index']

for event in events_2024:
    event_name = event.get('event', '')
    impact = event.get('impact', '')
    
    # FOMC
    if any(kw in event_name for kw in FOMC_KEYWORDS):
        event_categories['FOMC'].append(event)
    
    # CPI
    elif any(kw in event_name for kw in CPI_KEYWORDS):
        event_categories['CPI'].append(event)
    
    # NFP
    elif any(kw in event_name for kw in NFP_KEYWORDS):
        event_categories['NFP'].append(event)
    
    # Unemployment (often released with NFP)
    elif any(kw in event_name for kw in UNEMPLOYMENT_KEYWORDS):
        event_categories['Unemployment'].append(event)
    
    # Retail Sales
    elif any(kw in event_name for kw in RETAIL_KEYWORDS) and impact in ['High', 'Medium']:
        event_categories['Retail Sales'].append(event)
    
    # GDP
    elif any(kw in event_name for kw in GDP_KEYWORDS) and impact == 'High':
        event_categories['GDP'].append(event)
    
    # PCE (Fed's preferred inflation gauge)
    elif any(kw in event_name for kw in PCE_KEYWORDS):
        event_categories['PCE'].append(event)
    
    # PPI
    elif any(kw in event_name for kw in PPI_KEYWORDS) and impact == 'High':
        event_categories['PPI'].append(event)

# Print summary
print("\n" + "="*70)
print("2024 HIGH-IMPACT EVENT SUMMARY")
print("="*70)

total_tradeable = 0
for category, events in sorted(event_categories.items(), key=lambda x: -len(x[1])):
    count = len(events)
    total_tradeable += count
    print(f"{category:20s}: {count:3d} events")

print(f"\nTotal tradeable events: {total_tradeable}")

# Extract unique dates for each category
def get_unique_dates(events):
    """Extract unique dates and times"""
    unique = {}
    for event in events:
        date = event['date'][:10]  # YYYY-MM-DD
        time = event['date'][11:16]  # HH:MM
        if date not in unique:
            unique[date] = {
                'date': date,
                'time': time,
                'events': []
            }
        unique[date]['events'].append(event['event'])
    return sorted(unique.values(), key=lambda x: x['date'])

# Create tradeable events list
tradeable_events = {
    'FOMC': get_unique_dates(event_categories['FOMC']),
    'CPI': get_unique_dates(event_categories['CPI']),
    'NFP': get_unique_dates(event_categories['NFP']),
    'Unemployment': get_unique_dates(event_categories['Unemployment']),
    'Retail Sales': get_unique_dates(event_categories['Retail Sales']),
    'GDP': get_unique_dates(event_categories['GDP']),
    'PCE': get_unique_dates(event_categories['PCE']),
    'PPI': get_unique_dates(event_categories['PPI']),
}

# Save filtered events
output = {
    'generated_at': datetime.now().isoformat(),
    'total_events': total_tradeable,
    'categories': {}
}

for category, dates in tradeable_events.items():
    output['categories'][category] = {
        'count': len(dates),
        'events': dates
    }

with open('tradeable_events_2024.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✅ Saved to tradeable_events_2024.json")

# Print details for top 3 categories
print("\n" + "="*70)
print("DETAILED EVENT LISTING (Top 3 Categories)")
print("="*70)

for category in ['FOMC', 'CPI', 'NFP']:
    if category in tradeable_events and tradeable_events[category]:
        print(f"\n{category} ({len(tradeable_events[category])} dates):")
        print("-" * 70)
        for event in tradeable_events[category][:10]:  # First 10
            print(f"  {event['date']} @ {event['time']} - {', '.join(event['events'][:2])}")
        if len(tradeable_events[category]) > 10:
            print(f"  ... and {len(tradeable_events[category]) - 10} more")
