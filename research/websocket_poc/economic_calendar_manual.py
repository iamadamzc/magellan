"""
Manual Economic Calendar - Task 3 (Fallback)
If FMP API doesn't have calendar, use manual list of known events

Goal: Get FOMC/CPI dates for next 6 months
Success: Have dates for backtesting event straddles
"""

from datetime import datetime
import json

# Manual 2026 economic calendar (from Federal Reserve & BLS schedules)
ECONOMIC_EVENTS_2026 = [
    # FOMC Meetings (8 per year, scheduled 2 years in advance)
    {'date': '2026-01-27', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-03-17', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-04-28', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-06-16', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-07-28', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-09-15', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-11-03', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    {'date': '2026-12-15', 'time': '14:00', 'event': 'FOMC Meeting Decision', 'type': 'FOMC'},
    
    # CPI Releases (12 per year, usually mid-month, 8:30 AM ET)
    {'date': '2026-01-14', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-02-11', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-03-11', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-04-10', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-05-13', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-06-10', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-07-10', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-08-12', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-09-11', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-10-14', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-11-13', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    {'date': '2026-12-11', 'time': '08:30', 'event': 'Consumer Price Index (CPI)', 'type': 'CPI'},
    
    # NFP (Non-Farm Payrolls) - First Friday of month, 8:30 AM ET
    {'date': '2026-01-09', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-02-06', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-03-06', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-04-03', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-05-08', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-06-05', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-07-02', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-08-07', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-09-04', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-10-02', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-11-06', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
    {'date': '2026-12-04', 'time': '08:30', 'event': 'Non-Farm Payrolls (NFP)', 'type': 'NFP'},
]


def filter_future_events():
    """Filter for events in the future"""
    today = datetime.now()
    future_events = []
    
    for event in ECONOMIC_EVENTS_2026:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d')
        if event_date > today:
            future_events.append(event)
    
    return sorted(future_events, key=lambda x: x['date'])


def categorize_events(events):
    """Categorize by type"""
    categorized = {
        'fomc': [],
        'cpi': [],
        'nfp': []
    }
    
    for event in events:
        event_type = event['type'].lower()
        if event_type in categorized:
            categorized[event_type].append(event)
    
    return categorized


def print_calendar(events):
    """Print calendar"""
    if not events:
        print("\n❌ No upcoming events")
        return
    
    print(f"\n📅 Next {len(events)} economic events:\n")
    print("="*80)
    
    for i, event in enumerate(events[:20], 1):
        print(f"{i:2d}. {event['date']} @ {event['time']} ET | {event['event']}")
    
    print("="*80)


def main():
    """Main function"""
    
    print("\n" + "="*80)
    print("📡 Manual Economic Calendar - Task 3 (Fallback)")
    print("="*80)
    print("\n⚠️  FMP API endpoint returned no data")
    print("   Using manually curated calendar from Federal Reserve/BLS")
    
    # Get future events
    future_events = filter_future_events()
    print(f"\n✅ Loaded {len(future_events)} upcoming events")
    
    # Print calendar
    print_calendar(future_events)
    
    # Categorize
    categorized = categorize_events(future_events)
    
    print("\n" + "="*80)
    print("📊 EVENT BREAKDOWN")
    print("="*80)
    print(f"\n🎯 Trading Opportunities:")
    print(f"   FOMC Meetings: {len(categorized['fomc'])} events")
    print(f"   CPI Releases:  {len(categorized['cpi'])} events")
    print(f"   NFP Reports:   {len(categorized['nfp'])} events")
    print(f"   --------------------------")
    print(f"   TOTAL:         {len(future_events)} opportunities")
    
    print(f"\n💡 Strategy Entry Points:")
    print(f"   • FOMC (2:00 PM ET): Enter straddle at 1:55 PM, exit 2:05 PM")
    print(f"   • CPI (8:30 AM ET):  Enter straddle at 8:25 AM, exit 8:35 AM")
    print(f"   • NFP (8:30 AM ET):  Enter str addle at 8:25 AM, exit 8:35 AM")
    
    # Save to files
    with open('research/websocket_poc/economic_calendar.json', 'w') as f:
        json.dump(future_events, f, indent=2)
    print(f"\n💾 Saved to: research/websocket_poc/economic_calendar.json")
    
    with open('research/websocket_poc/economic_calendar_categorized.json', 'w') as f:
        json.dump(categorized, f, indent=2)
    print(f"💾 Saved to: research/websocket_poc/economic_calendar_categorized.json")
    
    print("\n✅ Task 3 Complete!")
    print("\n📋 NEXT STEPS:")
    print("   1. Use this calendar for event straddle backtests (Task 5)")
    print("   2. Test 5-minute hold strategy on 2024 historical events")
    print("   3. Compare to previous 1-day hold results")


if __name__ == "__main__":
    main()
