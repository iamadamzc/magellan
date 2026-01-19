"""
Simplified Walk-Forward Test - Test on Top Movers
--------------------------------------------------
Forget the speedboat criteria for now - just test ORB V9 on:
- Top 10 gainers each day
- Top 10 most active each day

This will show us if the strategy works on ANY momentum stocks.
"""

import pandas as pd
from pathlib import Path
import sys
from datetime import datetime, timedelta
import requests
import os

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from research.new_strategy_builds.strategies.orb_v9 import run_orb_v9

FMP_API_KEY = os.getenv('FMP_API_KEY')

def get_trading_days(start_date, end_date):
    """Get list of trading days"""
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    days = []
    while current <= end:
        if current.weekday() < 5:
            days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return days

def get_daily_movers(date):
    """Get top gainers and actives for the day"""
    
    print(f"\nScanning {date}...")
    
    movers = []
    
    # Get top 10 gainers
    try:
        url = f"https://financialmodelingprep.com/stable/biggest-gainers"
        params = {'apikey': FMP_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            gainers = response.json()
            if gainers:
                for stock in gainers[:10]:  # Top 10
                    symbol = stock.get('symbol', '')
                    price = stock.get('price', 0)
                    
                    if price >= 2.0 and price <= 50.0:  # Reasonable price range
                        movers.append({
                            'symbol': symbol,
                            'price': price,
                            'type': 'gainer',
                        })
    except:
        pass
    
    # Get top 10 actives
    try:
        url = f"https://financialmodelingprep.com/stable/most-active"
        params = {'apikey': FMP_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            actives = response.json()
            if actives:
                for stock in actives[:10]:  # Top 10
                    symbol = stock.get('symbol', '')
                    price = stock.get('price', 0)
                    
                    if price >= 2.0 and price <= 50.0:
                        # Check if not already in movers
                        if symbol not in [m['symbol'] for m in movers]:
                            movers.append({
                                'symbol': symbol,
                                'price': price,
                                'type': 'active',
                            })
    except:
        pass
    
    print(f"  Found {len(movers)} symbols to test")
    return movers

# Run test
print("="*80)
print("SIMPLIFIED WALK-FORWARD TEST - TOP MOVERS")
print("="*80)

trading_days = get_trading_days('2024-11-01', '2024-11-08')  # Just 1 week
print(f"Testing {len(trading_days)} days\n")

all_results = []

for date in trading_days:
    movers = get_daily_movers(date)
    
    for stock in movers:
        symbol = stock['symbol']
        
        try:
            result = run_orb_v9(symbol, date, date, or_minutes=10)
            
            if result['total_trades'] > 0:
                result['date'] = date
                result['symbol'] = symbol
                result['stock_type'] = stock['type']
                all_results.append(result)
                
                print(f"  ✓ {symbol}: {result['total_trades']} trades, {result['win_rate']:.0f}% win, {result['avg_pnl']:+.3f}%")
        except Exception as e:
            print(f"  ✗ {symbol}: {e}")

# Results
if all_results:
    df = pd.DataFrame(all_results)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    print(f"\nTotal symbol-days: {len(df)}")
    print(f"Total trades: {df['total_trades'].sum()}")
    print(f"Avg win rate: {df['win_rate'].mean():.1f}%")
    print(f"Avg P&L/trade: {df['avg_pnl'].mean():+.3f}%")
    print(f"Total P&L: {df['avg_pnl'].sum():+.2f}%")
    
    # Save
    output_path = Path('research/new_strategy_builds/results/simplified_walk_forward.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved to: {output_path}")
    
    if df['avg_pnl'].mean() > 0:
        print("\n🎉 PROFITABLE!")
    else:
        print(f"\n❌ Not profitable yet: {df['avg_pnl'].mean():+.3f}% avg")
else:
    print("\n⚠️ No trades found")
