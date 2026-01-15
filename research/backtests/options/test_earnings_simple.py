"""
Event-Driven Earnings Straddles - Simplified

Testing earnings straddles on NVDA (2024-2025)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("="*70)
print("EVENT-DRIVEN STRATEGY - EARNINGS STRADDLES")
print("="*70)

# NVDA earnings dates (2024-2025)
earnings_dates = [
    '2024-02-21',  # Q4 FY2024
    '2024-05-22',  # Q1 FY2025
    '2024-08-28',  # Q2 FY2025
    '2024-11-20',  # Q3 FY2025
    '2025-02-26',  # Q4 FY2025
    '2025-05-28',  # Q1 FY2026
    '2025-08-27',  # Q2 FY2026
    '2025-11-19',  # Q3 FY2026
]

earnings_df = pd.DataFrame({'date': pd.to_datetime(earnings_dates)})
print(f"\n✓ Testing {len(earnings_df)} NVDA earnings events\n")

# Fetch NVDA price data
alpaca = AlpacaDataClient()
price_df = alpaca.fetch_historical_bars('NVDA', '1Day', '2024-01-01', '2025-12-31')
print(f"✓ Fetched {len(price_df)} daily bars\n")

# Simulate earnings straddles
cash = 100000
trades = []

r = 0.04
sigma = 0.40  # NVDA IV

for idx, earnings_row in earnings_df.iterrows():
    earnings_date = earnings_row['date']
    
    # Entry: 2 days before earnings
    entry_date = earnings_date - timedelta(days=2)
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
    
    # Call + Put
    call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='call'
    )
    
    put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='put'
    )
    
    # Buy both (straddle)
    call_entry_price = call_greeks['price'] * 1.01
    put_entry_price = put_greeks['price'] * 1.01
    
    contracts = max(1, int(5000 / (entry_price * 0.5)))
    
    straddle_cost = (call_entry_price + put_entry_price) * contracts * 100
    fees = 0.097 * contracts * 2
    total_cost = straddle_cost + fees
    
    if total_cost > cash:
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
    
    call_exit_price = call_exit_greeks['price'] * 0.99
    put_exit_price = put_exit_greeks['price'] * 0.99
    
    straddle_proceeds = (call_exit_price + put_exit_price) * contracts * 100
    exit_fees = 0.097 * contracts * 2
    net_proceeds = straddle_proceeds - exit_fees
    
    pnl = net_proceeds - total_cost
    pnl_pct = (pnl / total_cost) * 100
    price_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    
    trades.append({
        'earnings_date': earnings_date,
        'entry_date': entry_date_actual,
        'exit_date': exit_date_actual,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'price_move_pct': price_move_pct,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'hold_days': hold_days
    })
    
    cash += pnl

# Results
trades_df = pd.DataFrame(trades)
total_return = (cash / 100000 - 1) * 100
win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100 if len(trades_df) > 0 else 0

print("="*70)
print("RESULTS")
print("="*70)

print(f"\n📊 Performance:")
print(f"  Total Return: {total_return:+.2f}%")
print(f"  Trades: {len(trades_df)}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Final Equity: ${cash:,.2f}")

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

print("\n" + "="*70)
print("TRADE DETAILS")
print("="*70)

for idx, trade in trades_df.iterrows():
    print(f"\n{trade['earnings_date'].date()} Earnings:")
    print(f"  Entry: {trade['entry_date'].date()} @ ${trade['entry_price']:.2f}")
    print(f"  Exit: {trade['exit_date'].date()} @ ${trade['exit_price']:.2f}")
    print(f"  Move: {trade['price_move_pct']:+.2f}%")
    print(f"  P&L: {trade['pnl_pct']:+.2f}%")

# Save
output_dir = Path('results/options')
output_dir.mkdir(parents=True, exist_ok=True)
trades_df.to_csv(output_dir / 'earnings_straddles_trades.csv', index=False)

print(f"\n📁 Results saved!")
print("="*70)
