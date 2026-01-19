"""
FMP Economic Calendar - Task 3
Fetches upcoming economic events for event straddle strategy

Goal: Get exact dates/times for FOMC, CPI, NFP, GDP releases
Success: Identify next 10+ high-impact events with timestamps
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')


def get_economic_calendar(start_date, end_date):
    """Fetch economic events from FMP"""
    # Use /stable endpoint (v3 is deprecated)
    url = "https://financialmodelingprep.com/stable/economic-calendar"
    params = {
        'from': start_date,
        'to': end_date,
        'apikey': FMP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching calendar: {e}")
        return []


def filter_high_impact(events):
    """Filter for high-impact events only"""
    
    # Keywords for high-impact events
    keywords = [
        'FOMC', 'Federal Open Market Committee', 'Interest Rate',
        'CPI', 'Consumer Price Index', 'Inflation',
        'Non-Farm', 'NFP', 'Nonfarm Payrolls', 'Employment',
        'GDP', 'Gross Domestic Product',
        'PCE', 'Personal Consumption',
        'Retail Sales',
        'Unemployment Rate'
    ]
    
    filtered = []
    seen = set()  # Avoid duplicates
    
    for event in events:
        event_name = event.get('event', '')
        event_key = f"{event.get('date')}_{event_name}"
        
        # Skip if already seen
        if event_key in seen:
            continue
        
        # Check if matches any keyword
        for keyword in keywords:
            if keyword.lower() in event_name.lower():
                filtered.append(event)
                seen.add(event_key)
                break
    
    return filtered


def parse_event(event):
    """Parse event details"""
    return {
        'date': event.get('date'),
        'time': event.get('time', 'TBD'),
        'event': event.get('event'),
        'country': event.get('country', 'US'),
        'actual': event.get('actual'),
        'estimate': event.get('estimate'),
        'previous': event.get('previous'),
        'impact': event.get('impact', 'High')
    }


def print_events(events):
    """Print events in nice format"""
    if not events:
        print("\n❌ No events found")
        return
    
    print(f"\n📅 Found {len(events)} high-impact events:\n")
    print("="*80)
    
    for i, event in enumerate(events, 1):
        parsed = parse_event(event)
        print(f"{i:2d}. {parsed['date']} @ {parsed['time']:8s} | {parsed['event']}")
        if parsed['estimate']:
            print(f"     Estimate: {parsed['estimate']} | Previous: {parsed['previous']}")
    
    print("="*80)


def save_calendar(events, filename='research/websocket_poc/economic_calendar.json'):
    """Save calendar to JSON file"""
    with open(filename, 'w') as f:
        json.dump(events, f, indent=2)
    print(f"\n💾 Saved {len(events)} events to: {filename}")


def analyze_for_trading(events):
    """Analyze which events are best for straddle strategy"""
    print("\n" + "="*80)
    print("📊 TRADING OPPORTUNITY ANALYSIS")
    print("="*80)
    
    # Categorize by event type
    fomc_events = []
    cpi_events = []
    nfp_events = []
    other_events = []
    
    for event in events:
        name = event.get('event', '').lower()
        if 'fomc' in name or 'interest rate' in name:
            fomc_events.append(event)
        elif 'cpi' in name or 'inflation' in name:
            cpi_events.append(event)
        elif 'non-farm' in name or 'nfp' in name or 'payroll' in name:
            nfp_events.append(event)
        else:
            other_events.append(event)
    
    print(f"\n🎯 Best Opportunities for Event Straddles:")
    print(f"   FOMC Meetings: {len(fomc_events)} events")
    print(f"   CPI Releases:  {len(cpi_events)} events")
    print(f"   NFP Reports:   {len(nfp_events)} events")
    print(f"   Other:         {len(other_events)} events")
    
    print(f"\n💡 Strategy Recommendations:")
    print(f"   • FOMC (8x/year): SPY/QQQ ATM straddles, enter 5min before")
    print(f"   • CPI (12x/year): SPY ATM straddles, enter 5min before 8:30 AM ET")
    print(f"   • NFP (12x/year): SPY/QQQ, volatility spike at 8:30 AM ET")
    print(f"   • Total opportunities: ~{len(fomc_events) + len(cpi_events) + len(nfp_events)} trades/year")
    
    return {
        'fomc': fomc_events,
        'cpi': cpi_events,
        'nfp': nfp_events,
        'other': other_events
    }


def main():
    """Main function"""
    
    print("\n" + "="*80)
    print("📡 FMP Economic Calendar - Task 3")
    print("="*80)
    
    if not FMP_API_KEY:
        print("\n❌ FMP_API_KEY not found in .env")
        return
    
    print(f"✅ FMP API Key loaded: {FMP_API_KEY[:8]}...")
    
    # Get next 90 days of events (FMP limit is 90 days per request)
    today = datetime.now().strftime('%Y-%m-%d')
    future = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
    
    print(f"\n🔍 Fetching events from {today} to {future} (90 days)...")
    
    all_events = get_economic_calendar(today, future)
    print(f"   Total events returned: {len(all_events)}")
    
    # Filter for high-impact
    high_impact = filter_high_impact(all_events)
    print(f"   High-impact events: {len(high_impact)}")
    
    # Print events
    print_events(high_impact[:20])  # Show first 20
    
    # Analyze for trading
    categorized = analyze_for_trading(high_impact)
    
    # Save to file
    save_calendar(high_impact)
    
    # Save categorized version
    save_calendar(categorized, 'research/websocket_poc/economic_calendar_categorized.json')
    
    print("\n✅ Task 3 Complete!")
    print("\n📋 NEXT STEPS:")
    print("   1. Review saved calendar files")
    print("   2. Build event straddle backtest (Task 5)")
    print("   3. Test on historical FOMC/CPI events")


if __name__ == "__main__":
    main()
