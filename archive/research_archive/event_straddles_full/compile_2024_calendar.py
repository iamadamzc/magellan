"""
2024 Economic Event Calendar - Historical Events

Manually compiled from official sources:
- Federal Reserve FOMC schedule
- Bureau of Labor Statistics (CPI, NFP)
- Bureau of Economic Analysis (GDP)

All times in Eastern Time (ET)
"""

import json
from datetime import datetime

# 2024 FOMC Meeting Decisions (announced at 2:00 PM ET)
# Source: Federal Reserve official schedule
FOMC_2024 = [
    {"date": "2024-01-31", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-03-20", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-05-01", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-06-12", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-07-31", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-09-18", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-11-07", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
    {"date": "2024-12-18", "time": "14:00", "event": "FOMC Rate Decision", "impact": "High"},
]

# 2024 CPI Releases (released at 8:30 AM ET)
# Source: Bureau of Labor Statistics schedule
CPI_2024 = [
    {"date": "2024-01-11", "time": "08:30", "event": "CPI YoY (Dec 2023)", "impact": "High"},
    {"date": "2024-02-13", "time": "08:30", "event": "CPI YoY (Jan 2024)", "impact": "High"},
    {"date": "2024-03-12", "time": "08:30", "event": "CPI YoY (Feb 2024)", "impact": "High"},
    {"date": "2024-04-10", "time": "08:30", "event": "CPI YoY (Mar 2024)", "impact": "High"},
    {"date": "2024-05-15", "time": "08:30", "event": "CPI YoY (Apr 2024)", "impact": "High"},
    {"date": "2024-06-12", "time": "08:30", "event": "CPI YoY (May 2024)", "impact": "High"},
    {"date": "2024-07-11", "time": "08:30", "event": "CPI YoY (Jun 2024)", "impact": "High"},
    {"date": "2024-08-14", "time": "08:30", "event": "CPI YoY (Jul 2024)", "impact": "High"},
    {"date": "2024-09-11", "time": "08:30", "event": "CPI YoY (Aug 2024)", "impact": "High"},
    {"date": "2024-10-10", "time": "08:30", "event": "CPI YoY (Sep 2024)", "impact": "High"},
    {"date": "2024-11-13", "time": "08:30", "event": "CPI YoY (Oct 2024)", "impact": "High"},
    {"date": "2024-12-11", "time": "08:30", "event": "CPI YoY (Nov 2024)", "impact": "High"},
]

# 2024 Non-Farm Payrolls (released at 8:30 AM ET, first Friday of month)
# Source: Bureau of Labor Statistics employment report schedule
NFP_2024 = [
    {"date": "2024-01-05", "time": "08:30", "event": "Non-Farm Payrolls (Dec 2023)", "impact": "High"},
    {"date": "2024-02-02", "time": "08:30", "event": "Non-Farm Payrolls (Jan 2024)", "impact": "High"},
    {"date": "2024-03-08", "time": "08:30", "event": "Non-Farm Payrolls (Feb 2024)", "impact": "High"},
    {"date": "2024-04-05", "time": "08:30", "event": "Non-Farm Payrolls (Mar 2024)", "impact": "High"},
    {"date": "2024-05-03", "time": "08:30", "event": "Non-Farm Payrolls (Apr 2024)", "impact": "High"},
    {"date": "2024-06-07", "time": "08:30", "event": "Non-Farm Payrolls (May 2024)", "impact": "High"},
    {"date": "2024-07-05", "time": "08:30", "event": "Non-Farm Payrolls (Jun 2024)", "impact": "High"},
    {"date": "2024-08-02", "time": "08:30", "event": "Non-Farm Payrolls (Jul 2024)", "impact": "High"},
    {"date": "2024-09-06", "time": "08:30", "event": "Non-Farm Payrolls (Aug 2024)", "impact": "High"},
    {"date": "2024-10-04", "time": "08:30", "event": "Non-Farm Payrolls (Sep 2024)", "impact": "High"},
    {"date": "2024-11-01", "time": "08:30", "event": "Non-Farm Payrolls (Oct 2024)", "impact": "High"},
    {"date": "2024-12-06", "time": "08:30", "event": "Non-Farm Payrolls (Nov 2024)", "impact": "High"},
]

# 2024 GDP Releases (Advanced Estimate at 8:30 AM ET)
# Source: Bureau of Economic Analysis
GDP_2024 = [
    {"date": "2024-01-25", "time": "08:30", "event": "GDP QoQ (Q4 2023 Advance)", "impact": "High"},
    {"date": "2024-04-25", "time": "08:30", "event": "GDP QoQ (Q1 2024 Advance)", "impact": "High"},
    {"date": "2024-07-25", "time": "08:30", "event": "GDP QoQ (Q2 2024 Advance)", "impact": "High"},
    {"date": "2024-10-30", "time": "08:30", "event": "GDP QoQ (Q3 2024 Advance)", "impact": "High"},
]

# 2024 Retail Sales (released at 8:30 AM ET, mid-month)
# Source: Census Bureau
RETAIL_SALES_2024 = [
    {"date": "2024-01-17", "time": "08:30", "event": "Retail Sales MoM (Dec 2023)", "impact": "Medium"},
    {"date": "2024-02-15", "time": "08:30", "event": "Retail Sales MoM (Jan 2024)", "impact": "Medium"},
    {"date": "2024-03-14", "time": "08:30", "event": "Retail Sales MoM (Feb 2024)", "impact": "Medium"},
    {"date": "2024-04-15", "time": "08:30", "event": "Retail Sales MoM (Mar 2024)", "impact": "Medium"},
    {"date": "2024-05-15", "time": "08:30", "event": "Retail Sales MoM (Apr 2024)", "impact": "Medium"},
    {"date": "2024-06-18", "time": "08:30", "event": "Retail Sales MoM (May 2024)", "impact": "Medium"},
    {"date": "2024-07-16", "time": "08:30", "event": "Retail Sales MoM (Jun 2024)", "impact": "Medium"},
    {"date": "2024-08-15", "time": "08:30", "event": "Retail Sales MoM (Jul 2024)", "impact": "Medium"},
    {"date": "2024-09-17", "time": "08:30", "event": "Retail Sales MoM (Aug 2024)", "impact": "Medium"},
    {"date": "2024-10-17", "time": "08:30", "event": "Retail Sales MoM (Sep 2024)", "impact": "Medium"},
    {"date": "2024-11-15", "time": "08:30", "event": "Retail Sales MoM (Oct 2024)", "impact": "Medium"},
    {"date": "2024-12-17", "time": "08:30", "event": "Retail Sales MoM (Nov 2024)", "impact": "Medium"},
]

# Compile all events
ALL_EVENTS = {
    "fomc": FOMC_2024,
    "cpi": CPI_2024,
    "nfp": NFP_2024,
    "gdp": GDP_2024,
    "retail_sales": RETAIL_SALES_2024
}

# Summary
print("="*70)
print("2024 ECONOMIC EVENT CALENDAR - COMPILED")
print("="*70)
print(f"FOMC:         {len(FOMC_2024):2d} events (2:00 PM ET)")
print(f"CPI:          {len(CPI_2024):2d} events (8:30 AM ET)")
print(f"NFP:          {len(NFP_2024):2d} events (8:30 AM ET)")
print(f"GDP:          {len(GDP_2024):2d} events (8:30 AM ET)")
print(f"Retail Sales: {len(RETAIL_SALES_2024):2d} events (8:30 AM ET)")
print(f"\nTotal High-Impact: {len(FOMC_2024) + len(CPI_2024) + len(NFP_2024)} events")
print(f"Total All:         {sum(len(v) for v in ALL_EVENTS.values())} events")

# Save to JSON
with open('economic_events_2024.json', 'w') as f:
    json.dump(ALL_EVENTS, f, indent=2)

print(f"\n✅ Saved to economic_events_2024.json")

# Create flat list for backtesting
flat_events = []
for category, events in ALL_EVENTS.items():
    for event in events:
        flat_events.append({
            **event,
            "category": category,
            "country": "US"
        })

# Sort by date
flat_events.sort(key=lambda x: x['date'])

with open('economic_events_2024_flat.json', 'w') as f:
    json.dump(flat_events, f, indent=2)

print(f"✅ Saved flat list to economic_events_2024_flat.json")

# Print first 10 events
print("\n" + "="*70)
print("FIRST 10 EVENTS (CHRONOLOGICAL)")
print("="*70)
for i, event in enumerate(flat_events[:10], 1):
    print(f"{i:2d}. {event['date']} @ {event['time']} | {event['category']:12s} | {event['event']}")
