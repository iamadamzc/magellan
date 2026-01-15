"""
Daily Trend Hysteresis Backtest (Variant F)
Simple, focused backtest for daily RSI Schmidt Trigger strategy
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env file
def load_env_file():
    """Manually load .env file into os.environ."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env_file()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi

# Configuration
SYMBOL = 'SPY'  # Using SPY (no stock splits) instead of NVDA
START_DATE = '2024-01-14'
END_DATE = '2026-01-14'
INITIAL_CAPITAL = 50000.0
POSITION_SIZE_PCT = 1.0  # 100% of capital
TRANSACTION_COST_BPS = 1.5  # 1.5 basis points per trade

# Hysteresis thresholds
UPPER_THRESHOLD = 55  # Enter LONG
LOWER_THRESHOLD = 45  # Exit to FLAT
ENABLE_HYSTERESIS = True

print("=" * 70)
print("VARIANT F: DAILY TREND HYSTERESIS BACKTEST")
print("=" * 70)
print(f"Symbol: {SYMBOL}")
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Capital: ${INITIAL_CAPITAL:,.2f}")
print(f"Strategy: {'Schmidt Trigger (Hysteresis)' if ENABLE_HYSTERESIS else 'Simple Threshold (Baseline)'}")
if ENABLE_HYSTERESIS:
    print(f"Thresholds: Long Entry RSI > {UPPER_THRESHOLD}, Exit RSI < {LOWER_THRESHOLD}")
else:
    print(f"Threshold: Long Entry RSI > 50, Exit RSI <= 50")
print("=" * 70)

# Fetch daily bars
print("\n[1/4] Fetching daily bars from Alpaca...")
client = AlpacaDataClient()
bars = client.fetch_historical_bars(
    symbol=SYMBOL,
    timeframe='1Day',
    start=START_DATE,
    end=END_DATE,
    feed='sip'
)
print(f"✓ Fetched {len(bars)} daily bars")

# Calculate RSI
print("\n[2/4] Calculating RSI-14 on daily timeframe...")
bars['rsi_14'] = calculate_rsi(bars['close'], period=14)
bars = bars.dropna()  # Remove initial NaN values from RSI calculation
print(f"✓ RSI calculated ({len(bars)} bars after warmup)")

# Generate signals with hysteresis
print(f"\n[3/4] Generating {'hysteresis' if ENABLE_HYSTERESIS else 'baseline'} signals...")

if ENABLE_HYSTERESIS:
    # Schmidt Trigger state machine
    position_state = np.zeros(len(bars))
    current_state = 0  # 0 = FLAT, 1 = LONG
    
    for i, (idx, row) in enumerate(bars.iterrows()):
        rsi_value = row['rsi_14']
        
        if current_state == 0:  # Currently FLAT
            if rsi_value > UPPER_THRESHOLD:
                current_state = 1  # Enter LONG
        elif current_state == 1:  # Currently LONG
            if rsi_value < LOWER_THRESHOLD:
                current_state = 0  # Exit to FLAT
        
        position_state[i] = current_state
    
    bars['signal'] = position_state
else:
    # Baseline: simple threshold at 50
    bars['signal'] = np.where(bars['rsi_14'] > 50, 1, 0)

# Count trades (state changes)
bars['signal_change'] = bars['signal'].diff().fillna(0)
num_trades = (bars['signal_change'] != 0).sum()
print(f"✓ Signals generated: {num_trades} trades")

# Simulate P&L
print("\n[4/4] Simulating portfolio P&L...")

bars['daily_return'] = bars['close'].pct_change()
bars['strategy_return'] = bars['signal'].shift(1) * bars['daily_return']  # Trade on next day's open

# Apply transaction costs
bars['trade_cost'] = 0.0
bars.loc[bars['signal_change'] != 0, 'trade_cost'] = TRANSACTION_COST_BPS / 10000.0
bars['strategy_return_net'] = bars['strategy_return'] - bars['trade_cost']

# Calculate equity curve
bars['equity'] = INITIAL_CAPITAL * (1 + bars['strategy_return_net']).cumprod()
bars['buy_hold_equity'] = INITIAL_CAPITAL * (1 + bars['daily_return']).cumprod()

final_equity = bars['equity'].iloc[-1]
final_buy_hold = bars['buy_hold_equity'].iloc[-1]

strategy_return = ((final_equity - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100
buy_hold_return = ((final_buy_hold - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100

# Calculate max drawdown
cumulative_max = bars['equity'].cummax()
drawdown = (bars['equity'] - cumulative_max) / cumulative_max * 100
max_drawdown = drawdown.min()

# Calculate Sharpe ratio (annualized)
daily_returns = bars['strategy_return_net'].dropna()
sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0

# Win rate
winning_days = (bars['strategy_return_net'] > 0).sum()
total_days_invested = (bars['signal'].shift(1) == 1).sum()
win_rate = (winning_days / total_days_invested * 100) if total_days_invested > 0 else 0

print("✓ Backtest complete")

# Print results
print("\n" + "=" * 70)
print("BACKTEST RESULTS")
print("=" * 70)

print(f"\n📊 Performance Metrics:")
print(f"   Strategy Return:     {strategy_return:+.2f}%")
print(f"   Buy & Hold Return:   {buy_hold_return:+.2f}%")
print(f"   Outperformance:      {strategy_return - buy_hold_return:+.2f}%")
print(f"   Final Equity:        ${final_equity:,.2f}")
print(f"   Max Drawdown:        {max_drawdown:.2f}%")
print(f"   Sharpe Ratio:        {sharpe_ratio:.2f}")
print(f"   Win Rate:            {win_rate:.1f}%")

print(f"\n📈 Trading Activity:")
print(f"   Total Trades:        {num_trades}")
print(f"   Days Invested:       {total_days_invested} / {len(bars)} ({total_days_invested/len(bars)*100:.1f}%)")
print(f"   Transaction Costs:   ${(bars['trade_cost'] * INITIAL_CAPITAL).sum():,.2f}")

print(f"\n🎯 Hysteresis Effect:")
long_periods = (bars['signal'] == 1).sum()
flat_periods = (bars['signal'] == 0).sum()
print(f"   Long Periods:        {long_periods} days")
print(f"   Flat Periods:        {flat_periods} days")

# State transition analysis
if ENABLE_HYSTERESIS:
    transitions = (bars['signal_change'] != 0).sum()
    print(f"   State Transitions:   {transitions}")
    
    # Average hold period
    if num_trades > 0:
        avg_hold_period = long_periods / (num_trades / 2) if num_trades > 1 else long_periods
        print(f"   Avg Hold Period:     {avg_hold_period:.1f} days")

print("=" * 70)

# Export equity curves
bars[['equity', 'buy_hold_equity']].to_csv('variant_f_equity_curve.csv')
print(f"\n💾 Equity curve saved to: variant_f_equity_curve.csv")

# Verdict
print("\n" + "=" * 70)
if ENABLE_HYSTERESIS:
    if strategy_return > 0 and num_trades < 100 and max_drawdown > -20:
        print("✅ VARIANT F SUCCESS: Hysteresis reduced whipsaw and captured trend")
    elif strategy_return > 0:
        print("⚠️  PARTIAL SUCCESS: Profitable but check trade count or drawdown")
    else:
        print("❌ VARIANT F FAILED: Hysteresis did not solve whipsaw problem")
else:
    print("📊 BASELINE: Reference performance for comparison")
print("=" * 70)
