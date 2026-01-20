"""
EXPERIMENT G: Earnings Straddles NO RSI Expansion
Test 5 marginal assets with corrected NO RSI approach

Based on AAPL corrective retest findings:
- Removing RSI improved returns by +12.53% (primary) and +2.35% (secondary)
- Strategy has structural edge when RSI filter is removed

Assets to test: NVDA, GOOGL, MSFT, AMZN, NFLX
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame
import requests
import os

print("=" * 80)
print("EXPERIMENT G: Earnings Straddles NO RSI Expansion")
print("=" * 80)
print("Testing: NVDA, GOOGL, MSFT, AMZN, NFLX")
print("Method: Pure T-2 to T+1, NO RSI filter")
print("=" * 80)

# Configuration
ASSETS = ['NVDA', 'GOOGL', 'MSFT', 'AMZN', 'NFLX']
FRICTION_BASELINE_BPS = 10
FRICTION_DEGRADED_BPS = 20

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

def get_earnings_dates(symbol, start_date, end_date):
    """Get earnings dates from FMP"""
    api_key = os.getenv('FMP_API_KEY')
    url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{symbol}"
    
    params = {
        'apikey': api_key,
        'from': start_date,
        'to': end_date
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if not data:
        return []
    
    # Convert to dates
    earnings_dates = [datetime.strptime(item['date'], '%Y-%m-%d').date() for item in data]
    return sorted(earnings_dates)

def run_earnings_backtest(symbol, df, earnings_dates, friction_bps):
    """Run earnings straddle backtest - NO RSI VERSION"""
    
    initial_capital = 100000
    cash = initial_capital
    trades = []
    
    for earnings_date in earnings_dates:
        # Entry: T-2 close
        entry_date = earnings_date - timedelta(days=2)
        
        # Exit: T+1 open
        exit_date = earnings_date + timedelta(days=1)
        
        # Find actual trading days
        entry_bars = df[df.index.date == entry_date]
        exit_bars = df[df.index.date == exit_date]
        
        if len(entry_bars) == 0 or len(exit_bars) == 0:
            continue
        
        entry_price = entry_bars.iloc[0]['close']
        exit_price = exit_bars.iloc[0]['open']
        
        # Calculate P&L (assume $10k position per event)
        position_size = 10000
        friction_cost = (friction_bps / 10000) * position_size * 2  # Round trip
        
        pnl_pct = ((exit_price / entry_price) - 1) * 100
        pnl_dollars = (pnl_pct / 100) * position_size - friction_cost
        
        trades.append({
            'earnings_date': earnings_date,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'pnl_dollars': pnl_dollars
        })
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    total_return = (trades_df['pnl_dollars'].sum() / initial_capital) * 100
    avg_pnl_pct = trades_df['pnl_pct'].mean()
    
    winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
    win_rate = (len(winning_trades) / len(trades)) * 100 if trades else 0
    
    return {
        'total_return': total_return,
        'avg_pnl_pct': avg_pnl_pct,
        'total_trades': len(trades),
        'win_rate': win_rate,
        'trades_df': trades_df
    }

# Run tests
all_results = []

client = AlpacaDataClient()

for symbol in ASSETS:
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol}")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            # Fetch price data
            df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe=TimeFrame.Day,
                start=period['start'],
                end=period['end'],
                feed='sip'
            )
            
            print(f"  ✓ Fetched {len(df)} daily bars")
            
            # Get earnings dates
            earnings_dates = get_earnings_dates(symbol, period['start'], period['end'])
            print(f"  ✓ Found {len(earnings_dates)} earnings events")
            
            if not earnings_dates:
                print(f"  ⚠️ No earnings data available")
                continue
            
            # Run baseline test
            baseline_result = run_earnings_backtest(symbol, df, earnings_dates, FRICTION_BASELINE_BPS)
            
            if baseline_result:
                baseline_result['symbol'] = symbol
                baseline_result['period'] = period['name']
                baseline_result['friction'] = 'baseline'
                all_results.append(baseline_result)
                
                print(f"  Baseline: {baseline_result['total_return']:+.2f}% | "
                      f"Avg P&L: {baseline_result['avg_pnl_pct']:+.2f}% | "
                      f"Win Rate: {baseline_result['win_rate']:.1f}% | "
                      f"Trades: {baseline_result['total_trades']}")
            
            # Run degraded test
            degraded_result = run_earnings_backtest(symbol, df, earnings_dates, FRICTION_DEGRADED_BPS)
            
            if degraded_result:
                degraded_result['symbol'] = symbol
                degraded_result['period'] = period['name']
                degraded_result['friction'] = 'degraded'
                all_results.append(degraded_result)
                
                print(f"  Degraded: {degraded_result['total_return']:+.2f}%")
        
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

# Summary
print(f"\n\n{'#' * 80}")
print("EXPERIMENT G SUMMARY")
print(f"{'#' * 80}")

summary_df = pd.DataFrame([{
    'Symbol': r['symbol'],
    'Period': r['period'],
    'Friction': r['friction'],
    'Return (%)': f"{r['total_return']:+.2f}",
    'Avg P&L (%)': f"{r['avg_pnl_pct']:+.2f}",
    'Win Rate (%)': f"{r['win_rate']:.1f}",
    'Trades': r['total_trades']
} for r in all_results])

print("\n" + summary_df.to_string(index=False))

# Save results
output_dir = Path(__file__).parent
summary_df.to_csv(output_dir / 'experiment_g_results.csv', index=False)

print(f"\n✓ Results saved to: {output_dir / 'experiment_g_results.csv'}")
print("\nDone!")
