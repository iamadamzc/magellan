"""
BATCH TEST: Strategy 4 (FOMC Event Volatility)
Testing SPY, QQQ
±5 minute window around FOMC announcements
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# Configuration
SYMBOLS = ['SPY', 'QQQ']
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 5
FRICTION_DEGRADED_BPS = 10

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

# FOMC meeting dates (8 per year, approximate)
FOMC_DATES = {
    '2024': ['2024-01-31', '2024-03-20', '2024-05-01', '2024-06-12', '2024-07-31', '2024-09-18', '2024-11-07', '2024-12-18'],
    '2025': ['2025-01-29', '2025-03-19', '2025-04-30', '2025-06-18', '2025-07-30', '2025-09-17', '2025-10-29', '2025-12-17'],
    '2022': ['2022-01-26', '2022-03-16', '2022-05-04', '2022-06-15', '2022-07-27', '2022-09-21', '2022-11-02', '2022-12-14'],
    '2023': ['2023-02-01', '2023-03-22', '2023-05-03', '2023-06-14', '2023-07-26', '2023-09-20', '2023-11-01', '2023-12-13']
}

def get_fomc_for_period(period_name):
    if period_name == 'Primary':
        return FOMC_DATES['2024'] + FOMC_DATES['2025']
    else:
        return FOMC_DATES['2022'] + FOMC_DATES['2023']

def run_fomc_backtest(df, fomc_dates, friction_bps):
    """
    Simplified FOMC backtest - buy at close day before, sell at close day after
    (Real ±5min window would require minute data which is very large)
    """
    trades = []
    
    for fomc_date_str in fomc_dates:
        fomc_date = pd.to_datetime(fomc_date_str)
        
        # Find day before FOMC
        entry_date = fomc_date - pd.Timedelta(days=1)
        # Find day after FOMC
        exit_date = fomc_date + pd.Timedelta(days=1)
        
        # Find actual trading days
        entry_candidates = df[(df.index >= entry_date - pd.Timedelta(days=5)) & (df.index <= entry_date)]
        exit_candidates = df[(df.index >= exit_date) & (df.index <= exit_date + pd.Timedelta(days=5))]
        
        if len(entry_candidates) == 0 or len(exit_candidates) == 0:
            continue
        
        entry_price = entry_candidates.iloc[-1]['close']
        exit_price = exit_candidates.iloc[0]['close']
        
        # Calculate P&L
        friction_cost = (friction_bps / 10000) * (entry_price + exit_price) * SHARES_PER_TRADE
        gross_pnl = (exit_price - entry_price) * SHARES_PER_TRADE
        net_pnl = gross_pnl - friction_cost
        pnl_pct = ((exit_price / entry_price) - 1) * 100
        
        trades.append({
            'fomc_date': fomc_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_dollars': net_pnl,
            'pnl_pct': pnl_pct
        })
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    total_pnl = trades_df['pnl_dollars'].sum()
    total_return = (total_pnl / (SHARES_PER_TRADE * trades_df.iloc[0]['entry_price'])) * 100
    
    winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
    losing_trades = trades_df[trades_df['pnl_dollars'] <= 0]
    win_rate = (len(winning_trades) / len(trades)) * 100
    
    avg_pnl_pct = trades_df['pnl_pct'].mean()
    
    profit_factor = abs(winning_trades['pnl_dollars'].sum() / losing_trades['pnl_dollars'].sum()) if len(losing_trades) > 0 and losing_trades['pnl_dollars'].sum() != 0 else np.inf
    
    # Sharpe (simplified)
    returns = trades_df['pnl_pct'] / 100
    sharpe = (returns.mean() / returns.std()) * np.sqrt(8) if returns.std() > 0 else 0  # 8 events per year
    
    return {
        'total_return': total_return,
        'avg_pnl_pct': avg_pnl_pct,
        'sharpe': sharpe,
        'total_events': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor
    }

print("=" * 80)
print("BATCH TEST: Strategy 4 (FOMC Event Volatility)")
print("=" * 80)
print("NOTE: Using daily close-to-close as proxy for ±5min window")
print("=" * 80)

all_results = []
client = AlpacaDataClient()

for symbol in SYMBOLS:
    print(f"\n{'#' * 80}")
    print(f"TESTING: {symbol}")
    print(f"{'#' * 80}")
    
    for period in TEST_PERIODS:
        print(f"\n  Period: {period['name']} ({period['start']} to {period['end']})")
        
        try:
            # Fetch with buffer
            buffer_start = (pd.to_datetime(period['start']) - pd.Timedelta(days=10)).strftime('%Y-%m-%d')
            buffer_end = (pd.to_datetime(period['end']) + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
            
            df = client.fetch_historical_bars(
                symbol=symbol,
                timeframe=TimeFrame.Day,
                start=buffer_start,
                end=buffer_end,
                feed='sip'
            )
            print(f"  ✓ Fetched {len(df)} daily bars")
            
            fomc_dates = get_fomc_for_period(period['name'])
            
            result_baseline = run_fomc_backtest(df.copy(), fomc_dates, FRICTION_BASELINE_BPS)
            if result_baseline:
                print(f"  Baseline: {result_baseline['total_return']:+.2f}% | Avg P&L: {result_baseline['avg_pnl_pct']:+.2f}% | Events: {result_baseline['total_events']}")
            
            result_degraded = run_fomc_backtest(df.copy(), fomc_dates, FRICTION_DEGRADED_BPS)
            if result_degraded:
                print(f"  Degraded: {result_degraded['total_return']:+.2f}% | Avg P&L: {result_degraded['avg_pnl_pct']:+.2f}% | Events: {result_degraded['total_events']}")
            
            for result, friction_name in [(result_baseline, 'Baseline'), (result_degraded, 'Degraded')]:
                if result:
                    all_results.append({
                        'Symbol': symbol,
                        'Period': period['name'],
                        'Friction': friction_name,
                        'Return (%)': f"{result['total_return']:+.2f}",
                        'Avg P&L (%)': f"{result['avg_pnl_pct']:+.2f}",
                        'Sharpe': f"{result['sharpe']:.2f}",
                        'Events': result['total_events'],
                        'Win Rate (%)': f"{result['win_rate']:.1f}",
                        'PF': f"{result['profit_factor']:.2f}"
                    })
            
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")

output_dir = Path(__file__).parent / 'batch_results'
output_dir.mkdir(exist_ok=True)

summary_df = pd.DataFrame(all_results)
summary_df.to_csv(output_dir / 'strategy4_fomc_summary.csv', index=False)

print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy 4 (FOMC Event Volatility)")
print(f"{'=' * 80}\n")
print(summary_df.to_string(index=False))
print(f"\n✓ Results saved to: {output_dir / 'strategy4_fomc_summary.csv'}")
print("\n⚠️  NOTE: This is a simplified test using daily data")
print("    Real ±5min window would require minute-level data")
