"""
Premium Selling Validation - QQQ (2025)

Testing tech-heavy index (more volatile than SPY, more stable than NVDA)
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
from src.features import calculate_rsi
from src.options.features import OptionsFeatureEngineer

print("="*70)
print("PREMIUM SELLING - QQQ VALIDATION (2025)")
print("="*70)
print("Testing tech-heavy index (QQQ vol ~1.2% vs SPY ~0.8%)\n")

# Fetch QQQ 2025 data
alpaca = AlpacaDataClient()
df = alpaca.fetch_historical_bars('QQQ', '1Day', '2025-01-01', '2026-01-15')
print(f"✓ Fetched {len(df)} bars (2025)\n")

# Calculate RSI and signals
df['rsi'] = calculate_rsi(df['close'], period=21)

signals = []
for idx, row in df.iterrows():
    rsi = row['rsi']
    if pd.isna(rsi):
        signals.append('HOLD')
    elif rsi < 30:
        signals.append('SELL_PUT')
    elif rsi > 70:
        signals.append('SELL_CALL')
    else:
        signals.append('HOLD')

df['signal'] = signals

sell_put_days = (df['signal'] == 'SELL_PUT').sum()
sell_call_days = (df['signal'] == 'SELL_CALL').sum()
print(f"SELL_PUT signals: {sell_put_days} days")
print(f"SELL_CALL signals: {sell_call_days} days\n")

# Simulate premium selling
cash = 100000
position = None
trades = []

r = 0.04
sigma = 0.25  # QQQ has slightly higher vol than SPY (0.25 vs 0.20)

for date, row in df.iterrows():
    price = row['close']
    signal = row['signal']
    
    if position:
        dte = (position['expiration'] - date).days
        T = max(dte / 365.0, 0.001)
        
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=price, K=position['strike'], T=T, r=r, sigma=sigma,
            option_type=position['type']
        )
        
        current_price = greeks['price']
        unrealized_pnl = position['premium_collected'] - (current_price * position['contracts'] * 100)
        unrealized_pnl_pct = (unrealized_pnl / position['premium_collected']) * 100
        
        should_exit = False
        exit_reason = None
        
        if unrealized_pnl_pct >= 60:
            should_exit, exit_reason = True, 'PROFIT_TARGET'
        elif dte <= 21:
            should_exit, exit_reason = True, 'TIME_EXIT'
        elif unrealized_pnl_pct <= -150:
            should_exit, exit_reason = True, 'STOP_LOSS'
        
        if should_exit:
            buyback_cost = current_price * position['contracts'] * 100 * 1.01
            fees = 0.097 * position['contracts']
            total_cost = buyback_cost + fees
            
            final_pnl = position['premium_collected'] - total_cost
            final_pnl_pct = (final_pnl / position['premium_collected']) * 100
            
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': date,
                'type': position['type'],
                'pnl': final_pnl,
                'pnl_pct': final_pnl_pct,
                'reason': exit_reason,
                'hold_days': (date - position['entry_date']).days
            })
            
            cash += final_pnl
            position = None
    
    if position is None and signal in ['SELL_PUT', 'SELL_CALL']:
        option_type = 'put' if signal == 'SELL_PUT' else 'call'
        strike = round(price / 5) * 5
        expiration = date + timedelta(days=45)
        T = 45 / 365.0
        
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=price, K=strike, T=T, r=r, sigma=sigma, option_type=option_type
        )
        
        sell_price = greeks['price'] * 0.99
        contracts = max(1, int(10000 / (price * abs(greeks['delta']))))
        
        premium_collected = sell_price * contracts * 100
        fees = 0.097 * contracts
        net_premium = premium_collected - fees
        
        if net_premium > 0 and net_premium < cash:
            position = {
                'entry_date': date,
                'type': option_type,
                'strike': strike,
                'expiration': expiration,
                'contracts': contracts,
                'premium_collected': net_premium
            }
            cash += net_premium

# Close final position
if position:
    final_date = df.index[-1]
    final_price = df.iloc[-1]['close']
    dte = (position['expiration'] - final_date).days
    T = max(dte / 365.0, 0.001)
    
    greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=final_price, K=position['strike'], T=T, r=r, sigma=sigma,
        option_type=position['type']
    )
    
    buyback_cost = greeks['price'] * position['contracts'] * 100 * 1.01
    fees = 0.097 * position['contracts']
    total_cost = buyback_cost + fees
    
    final_pnl = position['premium_collected'] - total_cost
    final_pnl_pct = (final_pnl / position['premium_collected']) * 100
    
    trades.append({
        'entry_date': position['entry_date'],
        'exit_date': final_date,
        'type': position['type'],
        'pnl': final_pnl,
        'pnl_pct': final_pnl_pct,
        'reason': 'END_OF_BACKTEST',
        'hold_days': (final_date - position['entry_date']).days
    })
    
    cash += final_pnl

# Results
trades_df = pd.DataFrame(trades)
total_return = (cash / 100000 - 1) * 100
win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100 if len(trades_df) > 0 else 0

qqq_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100

print("="*70)
print("QQQ RESULTS (2025)")
print("="*70)
print(f"\n📊 Performance:")
print(f"  Total Return: {total_return:+.2f}%")
print(f"  QQQ Buy & Hold: {qqq_return:+.2f}%")
print(f"  Outperformance: {total_return - qqq_return:+.2f}%")
print(f"  Trades: {len(trades_df)}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Final Equity: ${cash:,.2f}")

if len(trades_df) > 0:
    avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if (trades_df['pnl'] > 0).any() else 0
    avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (trades_df['pnl'] < 0).any() else 0
    print(f"  Avg Win: {avg_win:+.2f}%")
    print(f"  Avg Loss: {avg_loss:+.2f}%")

print("\n" + "="*70)
print("MULTI-ASSET COMPARISON")
print("="*70)
print(f"\nSPY 2024:  +796.54% return, 11 trades, 81.8% win rate")
print(f"SPY 2025:  +575.84% return, 10 trades, 60.0% win rate")
print(f"QQQ 2025:  {total_return:+.2f}% return, {len(trades_df)} trades, {win_rate:.1f}% win rate")
print(f"NVDA 2025: +0.00% return, 0 trades (no RSI extremes)")

if total_return > 400:
    print("\n✅ QQQ validates premium selling strategy!")
else:
    print("\n⚠️ QQQ underperformed SPY")
    
print("="*70)

# Save
output_dir = Path('results/options')
output_dir.mkdir(parents=True, exist_ok=True)
trades_df.to_csv(output_dir / 'qqq_premium_selling_trades.csv', index=False)
