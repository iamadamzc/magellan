"""
Earnings Calendar Research - MAG7 + High-Volume Stocks

Goal: Identify earnings dates for liquid stocks to test precision timing strategies

Strategy Ideas:
1. Short-hold straddles (T-15min to T+30min) - capture initial volatility spike
2. Post-earnings momentum (T+30min to T+4hrs) - ride directional moves
3. IV crush fade (sell volatility before earnings, cover after)

Hypothesis: With 67ms latency, we can capture earnings moves faster than legacy WFA assumed
"""

import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

# MAG7 stocks
MAG7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']

# Additional high-volume tech stocks
HIGH_VOLUME_TECH = ['NFLX', 'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'PYPL', 'UBER']

ALL_STOCKS = MAG7 + HIGH_VOLUME_TECH

print("="*80)
print("EARNINGS CALENDAR RESEARCH")
print("="*80)
print(f"\nTargets: {len(ALL_STOCKS)} liquid stocks")
print(f"MAG7: {', '.join(MAG7)}")
print(f"Tech: {', '.join(HIGH_VOLUME_TECH)}")

def get_earnings_calendar_2024(symbol):
    """Fetch 2024 earnings dates for a symbol"""
    
    # Try historical earnings endpoint
    url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{symbol}"
    params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            # Filter for 2024
            earnings_2024 = [e for e in data if e.get('date', '').startswith('2024')]
            return earnings_2024
        return []
    except:
        return []


# Collect earnings for all symbols
print("\n" + "="*80)
print("FETCHING EARNINGS DATES")
print("="*80)

all_earnings = {}
total_events = 0

for symbol in ALL_STOCKS:
    print(f"\n{symbol}...", end='')
    earnings = get_earnings_calendar_2024(symbol)
    
    if earnings:
        all_earnings[symbol] = earnings
        total_events += len(earnings)
        print(f" ✅ {len(earnings)} earnings in 2024")
        
        # Print dates
        for e in earnings[:4]:  # First 4
            date = e.get('date', 'Unknown')
            time = e.get('time', 'Unknown')
            eps = e.get('eps', 'N/A')
            eps_est = e.get('epsEstimated', 'N/A')
            print(f"  {date} @ {time} | EPS: {eps} (est: {eps_est})")
    else:
        print(" ❌ No data")

print(f"\n{'='*80}")
print(f"Total earnings events: {total_events}")
print(f"Stocks with data: {len(all_earnings)}/{len(ALL_STOCKS)}")

# Save raw data
with open('earnings_calendar_2024.json', 'w') as f:
    json.dump(all_earnings, f, indent=2)

print(f"\n✅ Saved to earnings_calendar_2024.json")

# Analyze timing patterns
print("\n" + "="*80)
print("TIMING ANALYSIS")
print("="*80)

# Group by time of day
from collections import Counter

all_times = []
for symbol, earnings in all_earnings.items():
    for event in earnings:
        time = event.get('time', 'unknown')
        all_times.append(time)

time_dist = Counter(all_times)

print("\nEarnings Time Distribution:")
for time, count in time_dist.most_common():
    print(f"  {time:10s}: {count:3d} events ({count/len(all_times)*100:.1f}%)")

# Strategy implications
print("\n" + "="*80)
print("STRATEGY OPPORTUNITIES")
print("="*80)

amc_count = time_dist.get('amc', 0)  # After market close
bmo_count = time_dist.get('bmo', 0)  # Before market open

print(f"\nAfter-Hours (AMC): {amc_count} events")
print("  → Entry:  3:59 PM (before close)")
print("  → Exit:   4:30 PM (after release)")
print("  → Risk:   Low liquidity in after-hours")

print(f"\nPre-Market (BMO): {bmo_count} events")
print("  → Entry:  9:29 AM (before open)")
print("  → Exit:   9:45 AM (after open vol spike)")
print("  → Risk:   Pre-market data needed (67ms latency helps!)")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Backtest AMC earnings (easier - market hours)")
print("2. Build IV model (estimate straddle costs)")
print("3. Test precision timing (T-15min to T+30min windows)")
print("4. Compare to existing 1-day hold (Sharpe 2.91)")
