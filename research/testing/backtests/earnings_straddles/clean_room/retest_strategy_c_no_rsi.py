"""
CORRECTIVE RETEST: Strategy C - Earnings Volatility (RSI REMOVED)

Purpose: Validate whether prior Strategy C failures were due to:
(a) RSI signal misuse, or
(b) Lack of structural edge

CHANGE: RSI completely removed from strategy
- Entry: T-2 close before earnings
- Exit: T+1 open after earnings
- No RSI signal
- No RSI filter
- Pure event-driven equity trade

This is a CONTROLLED VALIDATION, not exploratory testing.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

# Configuration - UNCHANGED from prior test
SYMBOL = 'AAPL'  # Control asset from prior test
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 5
FRICTION_DEGRADED_BPS = 10

TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

# Quarterly earnings dates (same as before)
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

def run_earnings_backtest_no_rsi(df, earnings_dates, friction_bps):
    """
    Pure event-driven backtest - NO RSI
    Entry: T-2 close
    Exit: T+1 open
    """
    trades = []
    
    for earnings_date_str in earnings_dates:
        earnings_date = pd.to_datetime(earnings_date_str)
        
        # Find T-2 (2 trading days before earnings)
        entry_date = earnings_date - pd.Timedelta(days=4)  # Approximate
        # Find T+1 (1 trading day after earnings)
        exit_date = earnings_date + pd.Timedelta(days=1)
        
        # Find actual trading days
        entry_candidates = df[(df.index >= entry_date - pd.Timedelta(days=5)) & (df.index <= entry_date)]
        exit_candidates = df[(df.index >= exit_date) & (df.index <= exit_date + pd.Timedelta(days=5))]
        
        if len(entry_candidates) == 0 or len(exit_candidates) == 0:
            continue
        
        # Entry: T-2 close
        entry_price = entry_candidates.iloc[-1]['close']
        entry_actual_date = entry_candidates.index[-1]
        
        # Exit: T+1 open (or close if open not available)
        if 'open' in exit_candidates.columns:
            exit_price = exit_candidates.iloc[0]['open']
        else:
            exit_price = exit_candidates.iloc[0]['close']
        exit_actual_date = exit_candidates.index[0]
        
        # Calculate P&L
        friction_cost = (friction_bps / 10000) * (entry_price + exit_price) * SHARES_PER_TRADE
        gross_pnl = (exit_price - entry_price) * SHARES_PER_TRADE
        net_pnl = gross_pnl - friction_cost
        pnl_pct = ((exit_price / entry_price) - 1) * 100
        
        trades.append({
            'earnings_date': earnings_date,
            'entry_date': entry_actual_date,
            'exit_date': exit_actual_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'gross_pnl': gross_pnl,
            'friction_cost': friction_cost,
            'net_pnl': net_pnl,
            'pnl_pct': pnl_pct
        })
    
    if not trades:
        return None
    
    trades_df = pd.DataFrame(trades)
    
    # Performance metrics
    total_pnl = trades_df['net_pnl'].sum()
    initial_capital = SHARES_PER_TRADE * trades_df.iloc[0]['entry_price']
    total_return = (total_pnl / initial_capital) * 100
    
    # Win rate
    winning_trades = trades_df[trades_df['net_pnl'] > 0]
    losing_trades = trades_df[trades_df['net_pnl'] <= 0]
    win_rate = (len(winning_trades) / len(trades)) * 100
    
    # Average P&L per trade
    avg_pnl_pct = trades_df['pnl_pct'].mean()
    avg_pnl_dollars = trades_df['net_pnl'].mean()
    
    # Profit factor
    total_wins = winning_trades['net_pnl'].sum() if len(winning_trades) > 0 else 0
    total_losses = abs(losing_trades['net_pnl'].sum()) if len(losing_trades) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else np.inf
    
    # Max drawdown (cumulative P&L)
    cumulative_pnl = trades_df['net_pnl'].cumsum()
    running_max = cumulative_pnl.expanding().max()
    drawdown = cumulative_pnl - running_max
    max_dd_dollars = drawdown.min()
    max_dd_pct = (max_dd_dollars / initial_capital) * 100
    
    # Sharpe ratio (simplified)
    returns = trades_df['pnl_pct'] / 100
    sharpe = (returns.mean() / returns.std()) * np.sqrt(4) if returns.std() > 0 else 0  # 4 events per year
    
    # Top-decile contribution
    sorted_pnl = trades_df['net_pnl'].sort_values(ascending=False)
    top_decile_count = max(1, len(trades) // 10)
    top_decile_pnl = sorted_pnl.head(top_decile_count).sum()
    top_decile_contribution = (top_decile_pnl / total_pnl * 100) if total_pnl > 0 else 0
    
    return {
        'total_return': total_return,
        'avg_pnl_pct': avg_pnl_pct,
        'avg_pnl_dollars': avg_pnl_dollars,
        'max_dd_pct': max_dd_pct,
        'max_dd_dollars': max_dd_dollars,
        'sharpe': sharpe,
        'total_events': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'top_decile_contribution': top_decile_contribution,
        'trades_df': trades_df
    }

print("=" * 80)
print("CORRECTIVE RETEST: Strategy C - Earnings Volatility (RSI REMOVED)")
print("=" * 80)
print("Asset: AAPL (control)")
print("Change: RSI completely removed")
print("Purpose: Validate signal vs. structural edge")
print("=" * 80)

all_results = []
client = AlpacaDataClient()

for period in TEST_PERIODS:
    print(f"\n{'#' * 80}")
    print(f"TEST PERIOD: {period['name']} ({period['start']} to {period['end']})")
    print(f"{'#' * 80}")
    
    try:
        # Fetch data with buffer
        buffer_start = (pd.to_datetime(period['start']) - pd.Timedelta(days=10)).strftime('%Y-%m-%d')
        buffer_end = (pd.to_datetime(period['end']) + pd.Timedelta(days=10)).strftime('%Y-%m-%d')
        
        df = client.fetch_historical_bars(
            symbol=SYMBOL,
            timeframe=TimeFrame.Day,
            start=buffer_start,
            end=buffer_end,
            feed='sip'
        )
        print(f"✓ Fetched {len(df)} daily bars")
        
        earnings_dates = get_earnings_for_period(period['name'])
        print(f"✓ Testing {len(earnings_dates)} earnings events")
        
        # Baseline friction
        print(f"\n--- Baseline Friction ({FRICTION_BASELINE_BPS} bps) ---")
        result_baseline = run_earnings_backtest_no_rsi(df.copy(), earnings_dates, FRICTION_BASELINE_BPS)
        
        if result_baseline:
            print(f"Total Return:        {result_baseline['total_return']:+.2f}%")
            print(f"Avg P&L per Event:   {result_baseline['avg_pnl_pct']:+.2f}%")
            print(f"Sharpe Ratio:        {result_baseline['sharpe']:.2f}")
            print(f"Max Drawdown:        {result_baseline['max_dd_pct']:.2f}%")
            print(f"Win Rate:            {result_baseline['win_rate']:.1f}%")
            print(f"Profit Factor:       {result_baseline['profit_factor']:.2f}")
            print(f"Top-Decile Contrib:  {result_baseline['top_decile_contribution']:.1f}%")
            print(f"Events Traded:       {result_baseline['total_events']}")
            
            all_results.append({
                'Period': period['name'],
                'Friction': 'Baseline',
                'Total Return (%)': f"{result_baseline['total_return']:+.2f}",
                'Avg P&L (%)': f"{result_baseline['avg_pnl_pct']:+.2f}",
                'Sharpe': f"{result_baseline['sharpe']:.2f}",
                'Max DD (%)': f"{result_baseline['max_dd_pct']:.2f}",
                'Win Rate (%)': f"{result_baseline['win_rate']:.1f}",
                'PF': f"{result_baseline['profit_factor']:.2f}",
                'Top-Decile (%)': f"{result_baseline['top_decile_contribution']:.1f}",
                'Events': result_baseline['total_events']
            })
            
            # Save trades
            output_dir = Path(__file__).parent
            result_baseline['trades_df'].to_csv(
                output_dir / f"retest_strategy_c_no_rsi_{period['name'].lower()}_baseline.csv",
                index=False
            )
        
        # Degraded friction
        print(f"\n--- Degraded Friction ({FRICTION_DEGRADED_BPS} bps) ---")
        result_degraded = run_earnings_backtest_no_rsi(df.copy(), earnings_dates, FRICTION_DEGRADED_BPS)
        
        if result_degraded:
            print(f"Total Return:        {result_degraded['total_return']:+.2f}%")
            print(f"Avg P&L per Event:   {result_degraded['avg_pnl_pct']:+.2f}%")
            print(f"Sharpe Ratio:        {result_degraded['sharpe']:.2f}")
            print(f"Max Drawdown:        {result_degraded['max_dd_pct']:.2f}%")
            print(f"Win Rate:            {result_degraded['win_rate']:.1f}%")
            print(f"Profit Factor:       {result_degraded['profit_factor']:.2f}")
            print(f"Top-Decile Contrib:  {result_degraded['top_decile_contribution']:.1f}%")
            print(f"Events Traded:       {result_degraded['total_events']}")
            
            all_results.append({
                'Period': period['name'],
                'Friction': 'Degraded',
                'Total Return (%)': f"{result_degraded['total_return']:+.2f}",
                'Avg P&L (%)': f"{result_degraded['avg_pnl_pct']:+.2f}",
                'Sharpe': f"{result_degraded['sharpe']:.2f}",
                'Max DD (%)': f"{result_degraded['max_dd_pct']:.2f}",
                'Win Rate (%)': f"{result_degraded['win_rate']:.1f}",
                'PF': f"{result_degraded['profit_factor']:.2f}",
                'Top-Decile (%)': f"{result_degraded['top_decile_contribution']:.1f}",
                'Events': result_degraded['total_events']
            })
            
            result_degraded['trades_df'].to_csv(
                output_dir / f"retest_strategy_c_no_rsi_{period['name'].lower()}_degraded.csv",
                index=False
            )
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

# Summary
print(f"\n\n{'=' * 80}")
print("SUMMARY - Strategy C Corrective Retest (RSI REMOVED)")
print(f"{'=' * 80}\n")

summary_df = pd.DataFrame(all_results)
print(summary_df.to_string(index=False))

output_dir = Path(__file__).parent
summary_df.to_csv(output_dir / "retest_strategy_c_no_rsi_summary.csv", index=False)

print(f"\n✓ Results saved to: {output_dir}")
print("\nDone!")
