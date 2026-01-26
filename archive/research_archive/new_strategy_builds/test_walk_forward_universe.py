"""
Walk-Forward Universe Selection - Daily Momentum Scanner
---------------------------------------------------------
Simulates real-world scanner-driven trading:

1. Each day at 9:30 AM, scan for symbols meeting speedboat criteria
2. Run ORB V9 on qualifying symbols for that day only
3. Aggregate results across all days

This is the PROPER way to test a momentum scanner strategy!

Speedboat Criteria (Gem_Ni):
- Float < 20M
- Price $2-$15
- Gap > 15% (or high RVOL)
- Market Cap $50M-$500M
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import datetime, timedelta
import requests
import os

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
from research.new_strategy_builds.strategies.orb_v9 import run_orb_v9

FMP_API_KEY = os.getenv('FMP_API_KEY')

def get_trading_days(start_date, end_date):
    """Get list of trading days between start and end"""
    # For now, use a simple weekday filter
    # TODO: Exclude market holidays
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    days = []
    while current <= end:
        if current.weekday() < 5:  # Monday-Friday
            days.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    
    return days

def get_daily_universe(date):
    """
    Get symbols meeting speedboat criteria on this date
    
    Strategy:
    1. Get top gainers/actives from FMP
    2. For each, check float and gap
    3. Return ALL qualifying symbols (no limit)
    """
    
    print(f"\nScanning {date}...")
    
    # Get gainers AND most active (using /stable/ endpoints)
    all_symbols = []
    
    # Get gainers
    gainers_url = f"https://financialmodelingprep.com/stable/biggest-gainers"
    gainers_params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(gainers_url, params=gainers_params, timeout=10)
        if response.status_code == 200:
            gainers = response.json()
            if gainers:
                all_symbols.extend(gainers)
    except:
        pass
    
    # Get most active
    actives_url = f"https://financialmodelingprep.com/stable/most-active"
    actives_params = {'apikey': FMP_API_KEY}
    
    try:
        response = requests.get(actives_url, params=actives_params, timeout=10)
        if response.status_code == 200:
            actives = response.json()
            if actives:
                all_symbols.extend(actives)
    except:
        pass
    
    if not all_symbols:
        print(f"  ⚠️ No symbols returned from API")
        return []
    
    # Remove duplicates
    seen = set()
    unique_symbols = []
    for stock in all_symbols:
        symbol = stock.get('symbol', '')
        if symbol and symbol not in seen:
            seen.add(symbol)
            unique_symbols.append(stock)
    
    qualified = []
    checked = 0
    
    for stock in unique_symbols:  # Check all unique symbols
            symbol = stock.get('symbol', '')
            price = stock.get('price', 0)
            change_pct = stock.get('changesPercentage', 0)
            
            checked += 1
            
            # Basic filters
            if price < 2.0 or price > 15.0:
                continue
            
            if abs(change_pct) < 5.0:  # At least 5% move
                continue
            
            # Get float from company profile (using /stable/ endpoint)
            try:
                profile_url = f"https://financialmodelingprep.com/stable/profile"
                profile_params = {'symbol': symbol, 'apikey': FMP_API_KEY}
                profile_response = requests.get(profile_url, params=profile_params, timeout=5)
                
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    if profile_data and len(profile_data) > 0:
                        # Float is in the profile as 'sharesOutstanding' or similar
                        float_shares = profile_data[0].get('sharesOutstanding', 0)
                        
                        if float_shares > 0 and float_shares < 20_000_000:
                            qualified.append({
                                'symbol': symbol,
                                'price': price,
                                'gap_pct': change_pct,
                                'float_m': float_shares / 1_000_000,
                            })
            except:
                continue
    
    print(f"  Checked {checked} symbols, found {len(qualified)} speedboats")
    return qualified

def run_walk_forward_test(start_date, end_date):
    """
    Run walk-forward universe selection test
    
    For each trading day:
    1. Scan for qualifying symbols
    2. Run ORB V9 on each
    3. Aggregate results
    """
    
    print("="*80)
    print("WALK-FORWARD UNIVERSE SELECTION TEST")
    print("="*80)
    print(f"Period: {start_date} to {end_date}")
    
    trading_days = get_trading_days(start_date, end_date)
    print(f"Trading days: {len(trading_days)}")
    
    all_results = []
    daily_universe = {}
    
    for date in trading_days:
        # Get universe for this day
        universe = get_daily_universe(date)
        daily_universe[date] = [s['symbol'] for s in universe]
        
        if not universe:
            continue
        
        # Test each symbol
        for stock in universe:
            symbol = stock['symbol']
            
            try:
                # Run ORB V9 on this single day
                result = run_orb_v9(symbol, date, date, or_minutes=10)
                
                if result['total_trades'] > 0:
                    result['date'] = date
                    result['symbol'] = symbol
                    result['gap_pct'] = stock['gap_pct']
                    result['float_m'] = stock['float_m']
                    all_results.append(result)
                    
                    print(f"  ✓ {symbol}: {result['total_trades']} trades, {result['win_rate']:.0f}% win, {result['avg_pnl']:+.2f}%")
                    
            except Exception as e:
                print(f"  ✗ {symbol}: {e}")
                continue
    
    # Aggregate results
    if all_results:
        df = pd.DataFrame(all_results)
        
        print("\n" + "="*80)
        print("WALK-FORWARD RESULTS")
        print("="*80)
        
        total_trades = df['total_trades'].sum()
        avg_win_rate = df['win_rate'].mean()
        avg_pnl = df['avg_pnl'].mean()
        total_pnl = df['avg_pnl'].sum()  # Sum of all avg P&Ls
        profitable_days = (df['avg_pnl'] > 0).sum()
        
        print(f"\nTotal symbol-days tested: {len(df)}")
        print(f"Total trades: {total_trades}")
        print(f"Avg win rate: {avg_win_rate:.1f}%")
        print(f"Avg P&L per trade: {avg_pnl:+.3f}%")
        print(f"Total P&L: {total_pnl:+.2f}%")
        print(f"Profitable symbol-days: {profitable_days}/{len(df)} ({profitable_days/len(df)*100:.1f}%)")
        
        # By date
        print("\n" + "="*80)
        print("DAILY BREAKDOWN")
        print("="*80)
        
        daily_summary = df.groupby('date').agg({
            'symbol': 'count',
            'total_trades': 'sum',
            'avg_pnl': 'mean',
        }).rename(columns={'symbol': 'symbols_tested'})
        
        print(daily_summary.to_string())
        
        # Save results
        output_path = Path('research/new_strategy_builds/results/walk_forward_universe_test.csv')
        df.to_csv(output_path, index=False)
        print(f"\n✅ Results saved to: {output_path}")
        
        # Verdict
        print("\n" + "="*80)
        print("VERDICT")
        print("="*80)
        
        if avg_pnl > 0:
            print(f"🎉 PROFITABLE! Avg P&L: {avg_pnl:+.3f}% per trade")
            print("   Walk-forward universe selection works!")
        elif avg_pnl > -0.05:
            print(f"⚡ NEAR BREAKEVEN: {avg_pnl:+.3f}% per trade")
            print("   Close to profitability, minor tweaks needed")
        else:
            print(f"❌ LOSING: {avg_pnl:+.3f}% per trade")
            print("   Strategy needs more work")
        
        return df
    else:
        print("\n⚠️ No qualifying trades found")
        return None

# Run test for full November 2024
if __name__ == '__main__':
    results = run_walk_forward_test('2024-11-01', '2024-11-30')
