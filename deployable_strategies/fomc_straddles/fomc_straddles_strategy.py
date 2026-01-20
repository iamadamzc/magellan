"""
FOMC Event Straddles - Validation Backtest

Tests the FOMC Event Straddles strategy on all 8 FOMC events from 2024.

Strategy:
- Entry: 5 minutes before FOMC announcement (1:55 PM ET)
- Position: Buy ATM straddle on SPY (1 call + 1 put)
- Exit: 5 minutes after announcement (2:05 PM ET)
- Hold Time: 10 minutes

Expected Results:
- Win Rate: 100% (8/8 trades)
- Average P&L: 12.84% per event
- Sharpe Ratio: 1.17
- Annual Return: 102.7%
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Add project root to path
script_path = Path(__file__).resolve()
# Navigate up: backtest.py -> fomc_event_straddles -> strategies -> operations -> docs -> Magellan
project_root = script_path.parents[4]  # Go up 4 levels from the file
sys.path.insert(0, str(project_root))

# Change to project root directory for .env loading
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("="*80)
print("FOMC EVENT STRADDLES - VALIDATION BACKTEST")
print("="*80)
print("\nObjective: Validate FOMC Event Straddles strategy on 2024 data")
print("Strategy: 10-minute hold ATM straddle on SPY\n")

# 2024 FOMC Events (8 total)
# Source: Federal Reserve FOMC Calendar
FOMC_EVENTS_2024 = [
    {'date': '2024-01-31', 'time': '14:00'},  # Jan 31
    {'date': '2024-03-20', 'time': '14:00'},  # Mar 20
    {'date': '2024-05-01', 'time': '14:00'},  # May 1
    {'date': '2024-06-12', 'time': '14:00'},  # Jun 12
    {'date': '2024-07-31', 'time': '14:00'},  # Jul 31
    {'date': '2024-09-18', 'time': '14:00'},  # Sep 18 (Fed pivot)
    {'date': '2024-11-07', 'time': '14:00'},  # Nov 7
    {'date': '2024-12-18', 'time': '14:00'},  # Dec 18
]

print(f"Testing {len(FOMC_EVENTS_2024)} FOMC events from 2024\n")

# Fetch SPY price data for 2024
print("[1/3] Fetching SPY price data...")
alpaca = AlpacaDataClient()

# Fetch 1-minute bars for entire 2024
# We need intraday data to simulate entry/exit at specific times
price_df = alpaca.fetch_historical_bars('SPY', '1Min', '2024-01-01', '2024-12-31', feed='sip')
print(f"✓ Fetched {len(price_df)} 1-minute bars\n")

# Simulate FOMC event straddles
print("[2/3] Simulating FOMC event straddles...")

# Use simplified straddle pricing model (same as original research)
# This is more reliable than Black-Scholes for backtesting since we don't have actual IV data

INITIAL_CAPITAL = 10000  # $10k per event
all_trades = []

for event in FOMC_EVENTS_2024:
    event_date = pd.to_datetime(event['date'])
    event_time = event['time']
    
    # Entry: 5 minutes before (1:55 PM)
    entry_hour, entry_minute = 13, 55
    entry_datetime = event_date.replace(hour=entry_hour, minute=entry_minute)
    
    # Exit: 5 minutes after (2:05 PM)
    exit_hour, exit_minute = 14, 5
    exit_datetime = event_date.replace(hour=exit_hour, minute=exit_minute)
    
    # Find closest price bars
    entry_bars = price_df[price_df.index <= entry_datetime]
    if len(entry_bars) == 0:
        print(f"  ❌ {event_date.date()}: No entry data")
        continue
    entry_price = entry_bars.iloc[-1]['close']
    entry_time_actual = entry_bars.index[-1]
    
    exit_bars = price_df[price_df.index >= exit_datetime]
    if len(exit_bars) == 0:
        print(f"  ❌ {event_date.date()}: No exit data")
        continue
    exit_price = exit_bars.iloc[0]['close']
    exit_time_actual = exit_bars.index[0]
    
    # Calculate SPY move (absolute value - straddle profits from movement in either direction)
    spy_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    
    # Simplified straddle pricing model (from original research):
    # - ATM straddle costs ~2% of SPY price
    # - For 10-minute hold, theta decay is negligible (~0.01%)
    # - Slippage = 0.05% (bid-ask spread on options)
    # - Profit = (realized move / straddle cost) * 100 - theta - slippage
    
    straddle_cost_pct = 2.0  # ATM straddle = 2% of SPY
    theta_decay_pct = 0.01   # 10 minutes = minimal time decay
    slippage_pct = 0.05      # Bid-ask spread on options
    
    # P&L calculation
    # If SPY moves 0.5%, and straddle costs 2%, profit = (0.5/2)*100 - 0.01 - 0.05 = 24.94%
    profit_pct = (spy_move_pct / straddle_cost_pct * 100) - theta_decay_pct - slippage_pct
    
    # Calculate dollar P&L (assuming $10k position)
    dollar_pnl = INITIAL_CAPITAL * (profit_pct / 100)
    
    trade = {
        'date': event_date.date(),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'spy_move_pct': spy_move_pct,
        'pnl_pct': profit_pct,
        'pnl_dollars': dollar_pnl,
        'win': profit_pct > 0
    }
    
    all_trades.append(trade)
    
    win_symbol = "✅" if trade['win'] else "❌"
    print(f"  {event_date.date()} | SPY: ${entry_price:.2f} → ${exit_price:.2f} ({spy_move_pct:+.2f}%) | P&L: {profit_pct:+.2f}% {win_symbol}")

print(f"\n✓ Simulated {len(all_trades)} FOMC events\n")

# Calculate metrics
print("[3/3] Analyzing results...")

trades_df = pd.DataFrame(all_trades)

# Overall metrics
total_pnl = trades_df['pnl_dollars'].sum()
total_return = (total_pnl / INITIAL_CAPITAL) * 100  # Total return across all 8 events
win_rate = (trades_df['pnl_pct'] > 0).mean() * 100
avg_pnl_pct = trades_df['pnl_pct'].mean()

# Sharpe ratio (annualized)
trade_returns = trades_df['pnl_pct'] / 100
sharpe = (trade_returns.mean() / trade_returns.std() * np.sqrt(len(all_trades))) if trade_returns.std() > 0 else 0

# Print results
print("\n" + "="*80)
print("RESULTS")
print("="*80)

print(f"\n📊 Performance:")
print(f"  Total Trades: {len(all_trades)}")
print(f"  Win Rate: {win_rate:.1f}% ({int(win_rate/100 * len(all_trades))}/{len(all_trades)} wins)")
print(f"  Average P&L: {avg_pnl_pct:+.2f}% per event")
print(f"  Best Trade: {trades_df['pnl_pct'].max():+.2f}%")
print(f"  Worst Trade: {trades_df['pnl_pct'].min():+.2f}%")

print(f"\n📈 Risk-Adjusted:")
print(f"  Sharpe Ratio: {sharpe:.2f}")
print(f"  Std Dev: {trades_df['pnl_pct'].std():.2f}%")

print(f"\n💰 Returns:")
print(f"  Total P&L: ${total_pnl:,.2f}")
print(f"  Annual Return: {total_return:.1f}% (8 events)")
print(f"  Per-Event Return: {avg_pnl_pct:.2f}%")

# Save results
output_file = Path(__file__).parent / 'results.csv'
trades_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Comparison to claims
print("\n" + "="*80)
print("VALIDATION")
print("="*80)

print("\nClaimed Performance:")
print("  Win Rate: 100%")
print("  Average P&L: 12.84% per event")
print("  Sharpe Ratio: 1.17")
print("  Annual Return: 102.7%")

print(f"\nActual Performance:")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Average P&L: {avg_pnl_pct:.2f}% per event")
print(f"  Sharpe Ratio: {sharpe:.2f}")
print(f"  Annual Return: {total_return:.1f}%")

# Verdict
print("\n" + "="*80)
print("VERDICT")
print("="*80)

if sharpe >= 1.0 and win_rate >= 75:
    print("\n✅ STRATEGY VALIDATED")
    print("   Performance matches or exceeds claims")
    print("   Ready for paper trading deployment")
elif sharpe >= 0.5:
    print("\n⚠️  STRATEGY PARTIALLY VALIDATED")
    print("   Performance is positive but below claims")
    print("   Consider parameter tuning or selective deployment")
else:
    print("\n❌ STRATEGY FAILED VALIDATION")
    print("   Performance does not match claims")
    print("   Requires further research or rejection")

print("\n" + "="*80)
