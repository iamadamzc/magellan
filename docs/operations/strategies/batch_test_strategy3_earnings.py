"""
BATCH TEST: Strategy 3 (Earnings Volatility) - All Tiers
Testing TSLA, NVDA, GOOGL, META, MSFT, AMZN, NFLX, AMD, COIN, PLTR
T-2 entry, T+1 exit
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
SYMBOLS = ['TSLA', 'NVDA', 'GOOGL', 'META', 'MSFT', 'AMZN', 'NFLX', 'AMD', 'COIN', 'PLTR']
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 5
FRICTION_DEGRADED_BPS = 10

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

# Quarterly earnings dates (approximate - late Jan/Apr/Jul/Oct)
EARNINGS_DATES = {
    '2024': ['2024-02-01', '2024-05-02', '2024-08-01', '2024-11-01'],
    '2025': ['2025-01-30', '2025-05-01', '2025-07-31', '2025-10-30'],
    '2022': ['2022-01-27', '2022-04-28', '2022-07-28', '2022-10-27'],
    '2023': ['2023-02-02', '2023-05-04', '2023-08-03', '2023-11-02']
}

def get_earnings_for_period(period_name):
    if period_name == 'Primary':
        return EARNINGS_DATES['2024'] + EARNINGS_DATES['2025']
    else:
        return EARNINGS_DATES['2022'] + EARNINGS_DATES['2023']

def run_earnings_backtest(df, earnings_dates, friction_bps):
    trades = []
    
    for earnings_date_str in earnings_dates:
        earnings_date = pd.to_datetime(earnings_date_str)
        
        # Find T-2 (2 trading days before)
        entry_date = earnings_date - pd.Timedelta(days=4)  # Approximate
        # Find T+1 (1 trading day after)
        exit_date = earnings_date + pd.Timedelta(days=1)
        
        # Find actual trading days
        entry_candidates = df[(df.index >= entry_date - pd.Timedelta(days=5)) & (df.index <= entry_date)]
        exit_candidates = df[(df.index >= exit_date) & (df.index <= exit_date + pd.Timedelta(days=5))]
        
        if len(entry_candidates) == 0 or len(exit_candidates) == 0:
            continue
        
        entry_price = entry_candidates.iloc[-1]['close']
        exit_price = exit_candidates.iloc[0]['open'] if 'open' in exit_candidates.columns else exit_candidates.iloc[0]['close']
        
        # Calculate P&L
        friction_cost = (friction_bps / 10000) * (entry_price + exit_price) * SHARES_PER_TRADE
        gross_pnl = (exit_price - entry_price) * SHARES_PER_TRADE
        net_pnl = gross_pnl - friction_cost
        pnl_pct = ((exit_price / entry_price) - 1) * 100
        
        trades.append({
            'earnings_date': earnings_date,
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
    sharpe = (returns.mean() / returns.std()) * np.sqrt(4) if returns.std() > 0 else 0  # 4 events per year
    
    return {
        'total_return': total_return,
        'avg_pnl_pct': avg_pnl_pct,
        'sharpe': sharpe,
        'total_events': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor
    }

print("=" * 80)
print("BATCH TEST: Strategy 3 (Earnings Volatility) - All Tiers")
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
            # Fetch with buffer for T-2 lookback
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
            
            earnings_dates = get_earnings_for_period(period['name'])
            
            result_baseline = run_earnings_backtest(df.copy(), earnings_dates, FRICTION_BASELINE_BPS)
            if result_baseline:
                print(f"  Baseline: {result_baseline['total_return']:+.2f}% | Avg P&L: {result_baseline['avg_pnl_pct']:+.2f}% | Events: {result_baseline['total_events']}")
            
            result_degraded = run_earnings_backtest(df.copy(), earnings_dates, FRICTION_DEGRADED_BPS)
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
summary_df.to_csv(output_dir / 'strategy3_earnings_summary.csv', index=False)

print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy 3 (Earnings Volatility) - All Tiers")
print(f"{'=' * 80}\n")
print(summary_df.to_string(index=False))
print(f"\n✓ Results saved to: {output_dir / 'strategy3_earnings_summary.csv'}")
