"""
CLEAN-ROOM BACKTEST: STRATEGY C - AAPL EARNINGS
Independent implementation - no reference to prior results

Strategy Rules:
- Instrument: AAPL (Equity)
- Type: Event-driven (earnings)
- Entry: Buy 100 shares at T-2 close (2 trading days before earnings)
- Exit: Sell 100 shares at T+1 open (1 trading day after earnings)
- Position: 100 shares per event
- Friction: 5 bps baseline, 10 bps degraded
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
# From: clean_room_test -> earnings_straddles -> strategies -> operations -> docs -> Magellan
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root: {project_root}")

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("=" * 80)
print("CLEAN-ROOM BACKTEST: STRATEGY C - AAPL EARNINGS")
print("=" * 80)
print("Instrument: AAPL (Equity)")
print("Type: Event-driven (earnings)")
print("Logic: Buy T-2 close, Sell T+1 open")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================

SYMBOL = 'AAPL'
SHARES_PER_TRADE = 100
FRICTION_BASELINE_BPS = 5.0  # 0.05%
FRICTION_DEGRADED_BPS = 10.0  # 0.10%

# AAPL Earnings Dates (Researched independently)
# AAPL typically reports in late Jan, late Apr, late Jul, late Oct
EARNINGS_DATES = {
    # 2022
    '2022-01-27': 'Q1 2022',
    '2022-04-28': 'Q2 2022',
    '2022-07-28': 'Q3 2022',
    '2022-10-27': 'Q4 2022',
    # 2023
    '2023-02-02': 'Q1 2023',
    '2023-05-04': 'Q2 2023',
    '2023-08-03': 'Q3 2023',
    '2023-11-02': 'Q4 2023',
    # 2024
    '2024-02-01': 'Q1 2024',
    '2024-05-02': 'Q2 2024',
    '2024-08-01': 'Q3 2024',
    '2024-11-01': 'Q4 2024',
    # 2025
    '2025-01-30': 'Q1 2025',
    '2025-05-01': 'Q2 2025',
    '2025-07-31': 'Q3 2025',
    '2025-10-30': 'Q4 2025',
}

# Test periods
TEST_PERIODS = [
    {'name': 'Primary', 'start': '2024-01-01', 'end': '2025-12-31'},
    {'name': 'Secondary', 'start': '2022-01-01', 'end': '2023-12-31'}
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_trading_day_offset(df, target_date, offset_days):
    """
    Get trading day at offset from target date
    offset_days: negative for before, positive for after
    """
    try:
        target_dt = pd.to_datetime(target_date)
        
        # Find nearest trading day to target
        if target_dt in df.index:
            target_idx = df.index.get_loc(target_dt)
        else:
            # Find next available trading day
            future_dates = df.index[df.index >= target_dt]
            if len(future_dates) == 0:
                return None
            target_idx = df.index.get_loc(future_dates[0])
        
        # Apply offset
        result_idx = target_idx + offset_days
        
        if result_idx < 0 or result_idx >= len(df):
            return None
        
        return df.index[result_idx]
    
    except Exception as e:
        print(f"  Warning: Could not calculate offset for {target_date}: {e}")
        return None


def run_backtest(df, friction_bps, test_name, period_start, period_end):
    """Run earnings event backtest"""
    
    print(f"\n{'=' * 80}")
    print(f"Running backtest: {test_name}")
    print(f"Friction: {friction_bps} bps")
    print(f"{'=' * 80}")
    
    # Filter earnings dates for this period
    period_start_dt = pd.to_datetime(period_start)
    period_end_dt = pd.to_datetime(period_end)
    
    relevant_earnings = {
        date: label for date, label in EARNINGS_DATES.items()
        if period_start_dt <= pd.to_datetime(date) <= period_end_dt
    }
    
    print(f"\nFound {len(relevant_earnings)} earnings events in this period:")
    for date, label in relevant_earnings.items():
        print(f"  {date}: {label}")
    
    # Initialize tracking
    trades = []
    initial_capital = 100000
    cash = initial_capital
    
    # Process each earnings event
    for earnings_date, earnings_label in relevant_earnings.items():
        
        # Calculate entry date (T-2)
        entry_date = get_trading_day_offset(df, earnings_date, -2)
        
        # Calculate exit date (T+1)
        exit_date = get_trading_day_offset(df, earnings_date, +1)
        
        if entry_date is None or exit_date is None:
            print(f"\n  Skipping {earnings_label}: Missing entry or exit date")
            continue
        
        # Get prices
        try:
            entry_price = df.loc[entry_date]['close']  # Buy at T-2 close
            exit_price = df.loc[exit_date]['open']    # Sell at T+1 open
        except KeyError:
            print(f"\n  Skipping {earnings_label}: Missing price data")
            continue
        
        # Calculate P&L
        entry_cost = entry_price * SHARES_PER_TRADE
        entry_friction = (friction_bps / 10000) * entry_cost
        
        exit_proceeds = exit_price * SHARES_PER_TRADE
        exit_friction = (friction_bps / 10000) * exit_proceeds
        
        total_cost = entry_cost + entry_friction
        total_proceeds = exit_proceeds - exit_friction
        
        pnl_dollars = total_proceeds - total_cost
        pnl_pct = ((exit_price / entry_price) - 1) * 100
        
        hold_days = (exit_date - entry_date).days
        
        trades.append({
            'earnings_date': earnings_date,
            'earnings_label': earnings_label,
            'entry_date': entry_date,
            'exit_date': exit_date,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_dollars': pnl_dollars,
            'pnl_pct': pnl_pct,
            'hold_days': hold_days
        })
        
        cash += pnl_dollars
        
        print(f"\n  {earnings_label}:")
        print(f"    Entry: {entry_date.date()} @ ${entry_price:.2f}")
        print(f"    Exit:  {exit_date.date()} @ ${exit_price:.2f}")
        print(f"    P&L:   {pnl_pct:+.2f}% (${pnl_dollars:+,.2f})")
    
    # Calculate metrics
    if not trades:
        print("\n❌ No trades executed")
        return None
    
    trades_df = pd.DataFrame(trades)
    
    final_capital = cash
    total_return = ((final_capital / initial_capital) - 1) * 100
    
    # Trade statistics
    winning_trades = trades_df[trades_df['pnl_dollars'] > 0]
    losing_trades = trades_df[trades_df['pnl_dollars'] <= 0]
    win_rate = (len(winning_trades) / len(trades)) * 100
    avg_win = winning_trades['pnl_pct'].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['pnl_pct'].mean() if len(losing_trades) > 0 else 0
    avg_pnl = trades_df['pnl_pct'].mean()
    avg_hold = trades_df['hold_days'].mean()
    
    profit_factor = abs(winning_trades['pnl_dollars'].sum() / losing_trades['pnl_dollars'].sum()) if len(losing_trades) > 0 and losing_trades['pnl_dollars'].sum() != 0 else np.inf
    
    # Sharpe ratio (annualized)
    returns = trades_df['pnl_pct'] / 100
    sharpe = (returns.mean() / returns.std()) * np.sqrt(4) if returns.std() > 0 else 0  # 4 events per year
    
    # Max drawdown (event-based)
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    # Print results
    print(f"\n{'=' * 80}")
    print(f"RESULTS: {test_name}")
    print(f"{'=' * 80}")
    print(f"\nPERFORMANCE:")
    print(f"  Total Return:        {total_return:+.2f}%")
    print(f"  Avg P&L per Event:   {avg_pnl:+.2f}%")
    print(f"  Max Drawdown:        {max_dd:.2f}%")
    print(f"  Sharpe Ratio:        {sharpe:.2f}")
    print(f"\nTRADING STATS:")
    print(f"  Total Events:        {len(trades)}")
    print(f"  Win Rate:            {win_rate:.1f}%")
    print(f"  Profit Factor:       {profit_factor:.2f}")
    print(f"  Avg Win:             {avg_win:+.2f}%")
    print(f"  Avg Loss:            {avg_loss:+.2f}%")
    print(f"  Avg Hold:            {avg_hold:.1f} days")
    print(f"\nBEST/WORST:")
    print(f"  Best Event:          {trades_df.loc[trades_df['pnl_pct'].idxmax()]['earnings_label']} ({trades_df['pnl_pct'].max():+.2f}%)")
    print(f"  Worst Event:         {trades_df.loc[trades_df['pnl_pct'].idxmin()]['earnings_label']} ({trades_df['pnl_pct'].min():+.2f}%)")
    
    return {
        'test_name': test_name,
        'total_return': total_return,
        'avg_pnl_pct': avg_pnl,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'total_events': len(trades),
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'avg_hold_days': avg_hold,
        'trades_df': trades_df
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

all_results = []

for period in TEST_PERIODS:
    print(f"\n\n{'#' * 80}")
    print(f"TEST PERIOD: {period['name']} ({period['start']} to {period['end']})")
    print(f"{'#' * 80}")
    
    try:
        # Fetch data (need extra buffer for T-2 and T+1)
        buffer_start = (pd.to_datetime(period['start']) - timedelta(days=30)).strftime('%Y-%m-%d')
        buffer_end = (pd.to_datetime(period['end']) + timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"\nFetching daily data for {SYMBOL} (with buffer)...")
        client = AlpacaDataClient()
        df = client.fetch_historical_bars(
            symbol=SYMBOL,
            timeframe=TimeFrame.Day,
            start=buffer_start,
            end=buffer_end,
            feed='sip'
        )
        print(f"✓ Fetched {len(df)} daily bars")
        
        # Run baseline test
        baseline_result = run_backtest(df, FRICTION_BASELINE_BPS, f"{period['name']} - Baseline Friction", period['start'], period['end'])
        if baseline_result:
            all_results.append(baseline_result)
        
        # Run degraded test
        degraded_result = run_backtest(df, FRICTION_DEGRADED_BPS, f"{period['name']} - Degraded Friction", period['start'], period['end'])
        if degraded_result:
            all_results.append(degraded_result)
        
        # Save trades
        output_dir = Path(__file__).parent
        if baseline_result:
            baseline_result['trades_df'].to_csv(output_dir / f"trades_{period['name'].lower()}_baseline.csv", index=False)
        if degraded_result:
            degraded_result['trades_df'].to_csv(output_dir / f"trades_{period['name'].lower()}_degraded.csv", index=False)
        
    except Exception as e:
        print(f"❌ ERROR in {period['name']}: {str(e)}")
        import traceback
        traceback.print_exc()

# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n\n{'#' * 80}")
print("STRATEGY C - SUMMARY OF ALL TESTS")
print(f"{'#' * 80}")

if all_results:
    summary_df = pd.DataFrame([{
        'Test': r['test_name'],
        'Return (%)': f"{r['total_return']:+.2f}",
        'Avg P&L (%)': f"{r['avg_pnl_pct']:+.2f}",
        'Sharpe': f"{r['sharpe']:.2f}",
        'Max DD (%)': f"{r['max_dd']:.2f}",
        'Events': r['total_events'],
        'Win Rate (%)': f"{r['win_rate']:.1f}",
        'Profit Factor': f"{r['profit_factor']:.2f}"
    } for r in all_results])
    
    print("\n" + summary_df.to_string(index=False))
    
    # Save summary
    output_dir = Path(__file__).parent
    summary_df.to_csv(output_dir / "summary_strategy_c.csv", index=False)
    
    print(f"\n✓ All results saved to: {output_dir}")
else:
    print("\n❌ No results to summarize")

print("\nDone!")
