"""
Insider Trading Clustering Strategy

Strategy: Detect when 3+ company insiders buy stock within 7-day window
Hypothesis: Clustered insider buying signals confidence in company prospects

Signal: 3+ insider purchases within 7 days
Entry: T+5 days after cluster detected (allow for public awareness)
Hold: 20-30 days
Expected Sharpe: 0.8-1.2 (based on academic research)

Data Source: FMP insider trading endpoint
"""

import requests
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

print("="*80)
print("INSIDER TRADING CLUSTERING RESEARCH")
print("="*80)

# Test insider trading endpoints
endpoints_to_test = [
    ("Stable Insider Rosters", "https://financialmodelingprep.com/stable/insider-rosters-trading"),
    ("V4 Insider Trading", "https://financialmodelingprep.com/api/v4/insider-trading"),
    ("V3 Insider Trading", "https://financialmodelingprep.com/api/v3/insider-trading"),
    ("Stable Insider Trading", "https://financialmodelingprep.com/stable/insider-trading"),
]

def test_endpoint(url, params=None, symbol_param=None):
    """Test endpoint with optional symbol parameter"""
    if params is None:
        params = {'apikey': FMP_API_KEY}
    
    if symbol_param:
        params['symbol'] = 'AAPL'  # Test with AAPL
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, data
        return False, f"Status {response.status_code}"
    except Exception as e:
        return False, str(e)

print("\n" + "="*80)
print("TESTING ENDPOINTS")
print("="*80)

working_endpoint = None
for name, endpoint in endpoints_to_test:
    print(f"\n{name}")
    print(f"  {endpoint}")
    
    # Try without symbol
    print("  Testing (no symbol)...", end='')
    success, result = test_endpoint(endpoint)
    
    if success:
        print(f" ✅ {len(result)} records")
        if len(result) > 0:
            working_endpoint = (name, endpoint, None)
            break
    else:
        print(f" ❌ {result}")
        
        # Try with symbol parameter
        print("  Testing (with symbol=AAPL)...", end='')
        success, result = test_endpoint(endpoint, symbol_param=True)
        
        if success:
            print(f" ✅ {len(result)} records")
            if len(result) > 0:
                working_endpoint = (name, endpoint, True)
                break
        else:
            print(f" ❌ {result}")

if not working_endpoint:
    print("\n" + "="*80)
    print("⚠️  NO WORKING INSIDER TRADING ENDPOINTS")
    print("="*80)
    print("\nFMP Ultimate may not include insider trading data.")
    print("Alternative: Focus on strategies that use available data.")
    
else:
    endpoint_name, endpoint_url, needs_symbol = working_endpoint
    
    print("\n" + "="*80)
    print("✅ WORKING ENDPOINT FOUND")
    print("="*80)
    print(f"Endpoint: {endpoint_name}")
    print(f"URL: {endpoint_url}")
    print(f"Requires symbol: {'Yes' if needs_symbol else 'No'}")
    
    # Fetch data for multiple symbols to build dataset
    if needs_symbol:
        print("\n" + "="*80)
        print("BUILDING DATASET (Symbol-based endpoint)")
        print("="*80)
        
        # Test with MAG7
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
        all_trades = []
        
        for symbol in symbols:
            print(f"\n{symbol}...", end='')
            params = {'apikey': FMP_API_KEY, 'symbol': symbol}
            success, trades = test_endpoint(endpoint_url, params=params)
            
            if success and trades:
                print(f" ✅ {len(trades)} trades")
                all_trades.extend(trades)
            else:
                print(" ❌ No data")
        
        print(f"\nTotal trades collected: {len(all_trades)}")
        
    else:
        print("\nFetching comprehensive dataset...")
        success, all_trades = test_endpoint(endpoint_url)
        print(f"✅ Retrieved {len(all_trades)} insider trades")
    
    if all_trades:
        # Save raw data
        with open('insider_trades_raw.json', 'w') as f:
            json.dump(all_trades, f, indent=2)
        
        print(f"\n✅ Saved to insider_trades_raw.json")
        
        # Analyze data structure
        if len(all_trades) > 0:
            sample = all_trades[0]
            print("\n" + "="*80)
            print("SAMPLE TRADE STRUCTURE")
            print("="*80)
            for key, value in list(sample.items())[:10]:
                print(f"{key:25s}: {value}")
        
        # Quick statistics
        print("\n" + "="*80)
        print("DATASET STATISTICS")
        print("="*80)
        
        # Filter for purchases only
        purchases = [t for t in all_trades if 
                    ('transactionType' in t and 'P-Purchase' in str(t.get('transactionType', ''))) or
                    ('acquisitionOrDisposition' in t and t.get('acquisitionOrDisposition') == 'A')]
        
        print(f"Total trades:     {len(all_trades)}")
        print(f"Purchases (buys): {len(purchases)}")
        print(f"Purchase %:       {len(purchases)/len(all_trades)*100 if all_trades else 0:.1f}%")
        
        # Check date range
        date_fields = ['filingDate', 'transactionDate', 'date']
        dates = []
        for trade in all_trades:
            for field in date_fields:
                if field in trade and trade[field]:
                    dates.append(str(trade[field]))
                    break
        
        if dates:
            print(f"\nDate Range: {min(dates)} to {max(dates)}")
            
            # Check for 2024 data
            trades_2024 = [d for d in dates if d.startswith('2024')]
            if trades_2024:
                print(f"✅ 2024 data: {len(trades_2024)} trades")
            else:
                print("⚠️  No 2024 data found")
        
        # Analyze clustering potential
        print("\n" + "="*80)
        print("CLUSTERING ANALYSIS")
        print("="*80)
        
        # Group purchases by symbol and date
        purchases_by_symbol = defaultdict(list)
        for trade in purchases[:1000]:  # Limit for performance
            symbol = trade.get('symbol') or trade.get('issuerTradingSymbol') or trade.get('tickerSymbol')
            date = None
            for field in date_fields:
                if field in trade and trade[field]:
                    date = str(trade[field])
                    break
            
            if symbol and date:
                purchases_by_symbol[symbol].append({
                    'date': date,
                    'trade': trade
                })
        
        # Detect clusters (3+ buys in 7 days)
        clusters_found = []
        for symbol, trades_list in purchases_by_symbol.items():
            if len(trades_list) < 3:
                continue
            
            # Sort by date
            trades_sorted = sorted(trades_list, key=lambda x: x['date'])
            
            # Check for clusters
            for i in range(len(trades_sorted) - 2):
                date1 = datetime.fromisoformat(trades_sorted[i]['date'][:10])
                cluster = [trades_sorted[i]]
                
                for j in range(i+1, len(trades_sorted)):
                    date_j = datetime.fromisoformat(trades_sorted[j]['date'][:10])
                    if (date_j - date1).days <= 7:
                        cluster.append(trades_sorted[j])
                
                if len(cluster) >= 3:
                    clusters_found.append({
                        'symbol': symbol,
                        'start_date': trades_sorted[i]['date'],
                        'cluster_size': len(cluster)
                    })
                    break  # Found a cluster for this symbol
        
        print(f"Symbols analyzed: {len(purchases_by_symbol)}")
        print(f"Clusters found (3+ buys in 7 days): {len(clusters_found)}")
        
        if clusters_found:
            print("\nSample clusters:")
            for cluster in clusters_found[:5]:
                print(f"  {cluster['symbol']:6s} | {cluster['start_date']} | {cluster['cluster_size']} insiders")
            
            print("\n✅ Clustering signal is viable!")
            print("   → Can build backtest")
        else:
            print("\n⚠️  No clusters detected in sample")
            print("   → May need larger dataset or adjust parameters")

print("\n" + "="*80)
print("SUMMARY & NEXT STEPS")
print("="*80)

if working_endpoint and 'all_trades' in locals() and all_trades:
    print("✅ Insider trading data accessible")
    print(f"✅ {len(all_trades)} trades available")
    
    if 'clusters_found' in locals() and clusters_found:
        print(f"✅ {len(clusters_found)} clusters detected")
        print("\nNext: Build backtest")
        print("1. Detect all clusters in 2024")
        print("2. Enter position T+5 days after cluster")
        print("3. Hold 30 days")
        print("4. Calculate Sharpe ratio")
    else:
        print("\n⚠️  Clustering signal needs refinement")
        print("   Consider adjusting parameters or expanding dataset")
else:
    print("❌ Cannot proceed with insider clustering strategy")
    print("\nAlternatives:")
    print("1. Focus on FOMC strategy (already validated)")
    print("2. Test news momentum during market hours")
    print("3. Research other alternative data sources")
