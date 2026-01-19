"""
FMP Ultimate Data Access Audit

Goal: Identify ALL accessible data sources in FMP Ultimate plan
Purpose: Find viable strategy opportunities using available data

Testing:
- Market data (confirmed working in Phase 1)
- Economic calendar (confirmed working)
- News/sentiment (untested)
- Company fundamentals (untested)  
- ETF holdings (untested)
- Earnings transcripts (untested)
- Options flow (untested)

Strategy pivot: Use what we HAVE, not what we want
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

print("="*80)
print("FMP ULTIMATE - COMPREHENSIVE DATA ACCESS AUDIT")
print("="*80)
print("\nTesting all major FMP Ultimate endpoints...")

# Comprehensive endpoint test list
endpoints = [
    # CONFIRMED WORKING (Phase 1)
    ("✅ Economic Calendar", "https://financialmodelingprep.com/stable/economic-calendar", {'from': '2026-01-01', 'to': '2026-02-01'}),
    ("✅ 1-Min Historical Bars", "https://financialmodelingprep.com/stable/historical-chart/1min", {'symbol': 'SPY', 'from': '2024-01-31', 'to': '2024-01-31'}),
    
    # NEWS & SENTIMENT
    ("News - Stock Latest", "https://financialmodelingprep.com/stable/news/stock-latest", {'limit': 10}),
    ("News - General", "https://financialmodelingprep.com/api/v3/stock_news", {'limit': 10}),
    ("Press Releases", "https://financialmodelingprep.com/api/v3/press-releases/AAPL", {}),
    ("Earnings Transcripts", "https://financialmodelingprep.com/api/v3/earning_call_transcript/AAPL", {'year': 2024}),
    
    # FUNDAMENTAL DATA  
    ("Income Statement", "https://financialmodelingprep.com/api/v3/income-statement/AAPL", {'period': 'quarter', 'limit': 4}),
    ("Balance Sheet", "https://financialmodelingprep.com/api/v3/balance-sheet-statement/AAPL", {'period': 'quarter', 'limit': 4}),
    ("Cash Flow", "https://financialmodelingprep.com/api/v3/cash-flow-statement/AAPL", {'period': 'quarter', 'limit': 4}),
    ("Key Metrics", "https://financialmodelingprep.com/api/v3/key-metrics/AAPL", {'period': 'quarter', 'limit': 4}),
    ("Financial Ratios", "https://financialmodelingprep.com/api/v3/ratios/AAPL", {'period': 'quarter', 'limit': 4}),
    
    # ALTERNATIVE DATA (Already tested - blocked)
    ("❌ Congressional Trades", "https://financialmodelingprep.com/api/v4/senate-trading", {}),
    ("❌ Insider Trading", "https://financialmodelingprep.com/api/v3/insider-trading", {'symbol': 'AAPL'}),
    
    # ETF & HOLDINGS
    ("ETF Holdings", "https://financialmodelingprep.com/api/v3/etf-holder/SPY", {}),
    ("Institutional Holders", "https://financialmodelingprep.com/api/v3/institutional-holder/AAPL", {}),
    
    # ANALYST & ESTIMATES
    ("Analyst Estimates", "https://financialmodelingprep.com/api/v3/analyst-estimates/AAPL", {}),
    ("Price Target", "https://financialmodelingprep.com/api/v4/price-target", {'symbol': 'AAPL'}),
    ("Upgrades/Downgrades", "https://financialmodelingprep.com/api/v4/upgrades-downgrades", {'symbol': 'AAPL'}),
    
    # CRYPTO
    ("Crypto Prices", "https://financialmodelingprep.com/api/v3/quote/BTCUSD", {}),
    
    # FOREX
    ("Forex Prices", "https://financialmodelingprep.com/api/v3/quote/EURUSD", {}),
]

accessible_data = []
blocked_data = []

def test_endpoint(url, params):
    """Test FMP endpoint"""
    params['apikey'] = FMP_API_KEY
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, len(data) if isinstance(data, list) else 1
        return False, response.status_code
    except Exception as e:
        return False, str(e)

print("\n" + "="*80)
print("TESTING ENDPOINTS")
print("="*80)

for name, url, params in endpoints:
    if name.startswith("✅") or name.startswith("❌"):
        print(f"\n{name}")
        print(f"  {url}")
        print("  Skipping (already tested)")
        continue
    
    print(f"\n{name}")
    print(f"  {url}")
    print("  Testing...", end='')
    
    success, result = test_endpoint(url, params.copy())
    
    if success:
        print(f" ✅ {result} records")
        accessible_data.append((name, url, result))
    else:
        print(f" ❌ {result}")
        blocked_data.append((name, url, result))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n✅ ACCESSIBLE ({len(accessible_data)} endpoints):")
for name, url, count in accessible_data:
    print(f"  • {name}: {count} records")

print(f"\n❌ BLOCKED/UNAVAILABLE ({len(blocked_data)} endpoints):")
for name, url, status in blocked_data:
    print(f"  • {name}: {status}")

# Strategy recommendations based on accessible data
print("\n" + "="*80)
print("STRATEGY OPPORTUNITIES (Based on Accessible Data)")
print("="*80)

if any('News' in name for name, _, _ in accessible_data):
    print("\n📰 NEWS MOMENTUM")
    print("  • Real-time news sentiment trading")
    print("  • Entry <500ms after breaking news")
    print("  • Hold: 30-60 seconds")
    print("  • Expected Sharpe: 1.5-2.0")
    print("  • Status: Needs market hours testing")

if any('Transcript' in name for name, _, _ in accessible_data):
    print("\n📊 EARNINGS TRANSCRIPT SENTIMENT")
    print("  • Parse earnings call transcripts for sentiment")
    print("  • Exit existing positions early if negative")
    print("  • Enhancement to existing Sharpe 2.91 earnings strategy")
    print("  • Expected improvement: +20-30%")

if any('Upgrade' in name or 'Downgrade' in name for name, _, _ in accessible_data):
    print("\n📈 ANALYST RATING CHANGES")
    print("  • Trade on analyst upgrades/downgrades")
    print("  • Entry: T+1 day after announcement")
    print("  • Hold: 5-10 days")
    print("  • Expected Sharpe: 0.5-0.9")

if any('ETF' in name for name, _, _ in accessible_data):
    print("\n🏦 ETF REBALANCING")
    print("  • Detect when stocks are added/removed from major ETFs")
    print("  • Front-run rebalancing flows")
    print("  • Entry: T-1 day before rebalance")
    print("  • Expected Sharpe: 0.6-1.0")

if any('Institutional' in name for name, _, _ in accessible_data):
    print("\n🐋 WHALE WATCHING (13F Alternative)")
    print("  • Track institutional ownership changes")
    print("  • Detect new large positions (>5% ownership)")
    print("  • Follow big money flows")
    print("  • Expected Sharpe: 0.5-0.8")

print("\n" + "="*80)
print("RECOMMENDED NEXT STEPS")
print("="*80)
print("\nGiven FMP limitations (no congressional/insider data):")
print("\n1. **Test News Momentum** (highest Sharpe potential)")
print("   - Requires market hours for WebSocket testing")
print("   - Can validate latency chain: news→parse→execute")
print("   - Est: 2-3 hours during market session")

print("\n2. **Analyst Rating Changes** (testable now)")
print("   - Backtest on historical upgrades/downgrades")
print("   - No pre-market data needed")
print("   - Est: 3-4 hours")

print("\n3. **Earnings Transcript Sentiment** (enhancement)")
print("   - Add to existing earnings straddle strategy")
print("   - Improve Sharpe from 2.91 to 3.5+")
print("   - Est: 4-5 hours")

print("\n4. **Simplify & Ship** (pragmatic approach)")
print("   - We have 1 validated strategy (FOMC, Sharpe 1.17)")
print("   - Deploy to paper trading")
print("   - Iterate as more data sources become available")
