"""
Event-Driven Options Strategy - Earnings Straddles

Strategy:
- Use FMP earnings calendar to identify upcoming earnings
- Enter 2 days before earnings: BUY straddle (ATM call + ATM put)
- Exit 1 day after earnings (fixed 3-day hold)
- Profit from volatility expansion

Expected: Sharpe 1.2-1.8, Win Rate 55-65%, 20-40 trades/year

Run: python research/backtests/options/test_earnings_straddles.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
import os

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("="*70)
print("EVENT-DRIVEN STRATEGY - EARNINGS STRADDLES")
print("="*70)
print("\nStrategy: Buy straddles 2 days before earnings, exit 1 day after")
print("Edge: Volatility expansion around known catalysts\n")

# Get FMP API key
FMP_KEY = os.getenv('FMP_API_KEY')
if not FMP_KEY:
    raise ValueError("FMP_API_KEY not found in environment")

# Fetch earnings calendar for NVDA 2024-2025
print("[1/4] Fetching NVDA earnings calendar from FMP...")

# FMP earnings calendar endpoint
url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/NVDA?apikey={FMP_KEY}"

response = requests.get(url)
if response.status_code != 200:
    raise ValueError(f"FMP API error: {response.status_code}")

earnings_data = response.json()

# Filter for 2024-2025
earnings_df = pd.DataFrame(earnings_data)
earnings_df['date'] = pd.to_datetime(earnings_df['date'])
earnings_df = earnings_df[
    (earnings_df['date'] >= '2024-01-01') & 
    (earnings_df['date'] <= '2025-12-31')
].sort_values('date')

print(f"✓ Found {len(earnings_df)} NVDA earnings events (2024-2025)")
print(f"\nEarnings dates:")
for idx, row in earnings_df.iterrows():
    print(f"  {row['date'].date()}")

# Fetch NVDA price data
print("\n[2/4] Fetching NVDA price data...")
alpaca = AlpacaDataClient()
price_df = alpaca.fetch_historical_bars('NVDA', '1Day', '2024-01-01', '2025-12-31')
print(f"✓ Fetched {len(price_df)} daily bars\n")

# Simulate earnings straddles
print("[3/4] Simulating earnings straddles...")

cash = 100000
trades = []
equity_curve = []

r = 0.04
sigma = 0.40  # NVDA IV

for idx, earnings_row in earnings_df.iterrows():
    earnings_date = earnings_row['date']
    
    # Entry: 2 days before earnings
    entry_date = earnings_date - timedelta(days=2)
    
    # Exit: 1 day after earnings
    exit_date = earnings_date + timedelta(days=1)
    
    # Find closest trading days
    entry_price_data = price_df[price_df.index <= entry_date]
    if len(entry_price_data) == 0:
        continue
    entry_date_actual = entry_price_data.index[-1]
    entry_price = entry_price_data.iloc[-1]['close']
    
    exit_price_data = price_df[price_df.index >= exit_date]
    if len(exit_price_data) == 0:
        continue
    exit_date_actual = exit_price_data.index[0]
    exit_price = exit_price_data.iloc[0]['close']
    
    # Calculate straddle (ATM call + ATM put, 7 DTE)
    strike = round(entry_price / 5) * 5
    T_entry = 7 / 365.0
    
    # Call option
    call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='call'
    )
    
    # Put option
    put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='put'
    )
    
    # Buy both (straddle)
    call_entry_price = call_greeks['price'] * 1.01  # 1% slippage
    put_entry_price = put_greeks['price'] * 1.01
    
    # Position size: $10k notional
    contracts = max(1, int(5000 / (entry_price * 0.5)))  # Split between call and put
    
    # Total cost
    straddle_cost = (call_entry_price + put_entry_price) * contracts * 100
    fees = 0.097 * contracts * 2  # 2 legs
    total_cost = straddle_cost + fees
    
    if total_cost > cash:
        print(f"  Skipping {earnings_date.date()}: insufficient cash")
        continue
    
    # Exit: Value straddle at exit
    hold_days = (exit_date_actual - entry_date_actual).days
    T_exit = max((7 - hold_days) / 365.0, 0.001)
    
    call_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type='call'
    )
    
    put_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type='put'
    )
    
    call_exit_price = call_exit_greeks['price'] * 0.99  # 1% slippage
    put_exit_price = put_exit_greeks['price'] * 0.99
    
    # Sell straddle
    straddle_proceeds = (call_exit_price + put_exit_price) * contracts * 100
    exit_fees = 0.097 * contracts * 2
    net_proceeds = straddle_proceeds - exit_fees
    
    # P&L
    pnl = net_proceeds - total_cost
    pnl_pct = (pnl / total_cost) * 100
    
    # Price move
    price_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    
    trades.append({
        'earnings_date': earnings_date,
        'entry_date': entry_date_actual,
        'exit_date': exit_date_actual,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'price_move_pct': price_move_pct,
        'strike': strike,
        'contracts': contracts,
        'cost': total_cost,
        'proceeds': net_proceeds,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'hold_days': hold_days
    })
    
    cash += pnl

print(f"✓ Simulated {len(trades)} earnings straddles\n")

# Calculate metrics
print("[4/4] Calculating performance...")

trades_df = pd.DataFrame(trades)
total_return = (cash / 100000 - 1) * 100
win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100 if len(trades_df) > 0 else 0

nvda_return = (price_df['close'].iloc[-1] / price_df['close'].iloc[0] - 1) * 100

# Results
print("\n" + "="*70)
print("RESULTS")
print("="*70)

print(f"\n📊 Performance:")
print(f"  Total Return: {total_return:+.2f}%")
print(f"  NVDA Buy & Hold: {nvda_return:+.2f}%")
print(f"  Outperformance: {total_return - nvda_return:+.2f}%")
print(f"  Final Equity: ${cash:,.2f}")

print(f"\n📋 Trades:")
print(f"  Total: {len(trades_df)}")
print(f"  Win Rate: {win_rate:.1f}%")

if len(trades_df) > 0:
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if (trades_df['pnl'] > 0).any() else 0
    avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (trades_df['pnl'] < 0).any() else 0
    avg_move = trades_df['price_move_pct'].mean()
    
    print(f"  Avg Win: {avg_win:+.2f}%")
    print(f"  Avg Loss: {avg_loss:+.2f}%")
    print(f"  Avg Price Move: {avg_move:.2f}%")

print(f"\n✅ Success Criteria:")
print(f"  Return > 0%: {'✅ PASS' if total_return > 0 else '❌ FAIL'} ({total_return:+.2f}%)")
print(f"  Win Rate > 55%: {'✅ PASS' if win_rate > 55 else '❌ FAIL'} ({win_rate:.1f}%)")
print(f"  Trades: {len(trades_df)} (target 20-40 over 2 years)")

print("\n" + "="*70)
print("TRADE DETAILS")
print("="*70)

for idx, trade in trades_df.iterrows():
    print(f"\n{trade['earnings_date'].date()} Earnings:")
    print(f"  Entry: {trade['entry_date'].date()} @ ${trade['entry_price']:.2f}")
    print(f"  Exit: {trade['exit_date'].date()} @ ${trade['exit_price']:.2f}")
    print(f"  Move: {trade['price_move_pct']:+.2f}%")
    print(f"  P&L: {trade['pnl_pct']:+.2f}% (${trade['pnl']:+,.0f})")

# Save
output_dir = Path('results/options')
output_dir.mkdir(parents=True, exist_ok=True)
trades_df.to_csv(output_dir / 'earnings_straddles_trades.csv', index=False)

print(f"\n📁 Results saved to: {output_dir}/")
print("="*70)
