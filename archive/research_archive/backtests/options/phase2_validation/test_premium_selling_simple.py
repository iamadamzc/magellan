"""
Premium Selling Strategy - THE THETA HARVESTER

STRATEGIC PIVOT: Sell options (collect theta) instead of buy (pay theta)

Strategy:
- RSI <30 → SELL PUT (oversold, expect bounce, collect premium)
- RSI >70 → SELL CALL (overbought, expect pullback, collect premium)  
- Exit: Collect 60% of premium OR 21 DTE OR stop at -150%

Expected: Sharpe 1.5-2.5, Win Rate 70-80%

Run: python research/backtests/options/phase2_validation/test_premium_selling_simple.py
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
from src.logger import LOG

LOG.verbosity = LOG.NORMAL

print("="*70)
print("PREMIUM SELLING STRATEGY - THE THETA HARVESTER")
print("="*70)
print("\nStrategy: SELL options on RSI extremes, collect theta decay")
print("Entry: RSI <30 (sell put) or RSI >70 (sell call)")
print("Exit: 60% profit OR 21 DTE OR -150% stop\n")

# Fetch SPY data (2025 only for clean test)
print("[1/4] Fetching SPY data (2025)...")
alpaca = AlpacaDataClient()
df = alpaca.fetch_historical_bars('SPY', '1Day', '2025-01-01', '2026-01-15')
print(f"✓ Fetched {len(df)} bars\n")

# Calculate RSI
print("[2/4] Calculating RSI signals...")
df['rsi'] = calculate_rsi(df['close'], period=21)

# Generate signals: SELL_PUT when oversold, SELL_CALL when overbought
signals = []
for idx, row in df.iterrows():
    rsi = row['rsi']
    if pd.isna(rsi):
        signals.append('HOLD')
    elif rsi < 30:  # Oversold → sell put
        signals.append('SELL_PUT')
    elif rsi > 70:  # Overbought → sell call
        signals.append('SELL_CALL')
    else:
        signals.append('HOLD')

df['signal'] = signals

sell_put_days = (df['signal'] == 'SELL_PUT').sum()
sell_call_days = (df['signal'] == 'SELL_CALL').sum()
print(f"✓ SELL_PUT signals: {sell_put_days} days ({sell_put_days/len(df)*100:.1f}%)")
print(f"✓ SELL_CALL signals: {sell_call_days} days ({sell_call_days/len(df)*100:.1f}%)\n")

# Simulate premium selling
print("[3/4] Simulating premium selling...")

cash = 100000
position = None
trades = []
equity_curve = []

r = 0.04  # Risk-free rate
sigma = 0.20  # SPY IV

for date, row in df.iterrows():
    price = row['close']
    signal = row['signal']
    
    # Mark-to-market existing position
    position_value = 0
    if position:
        dte = (position['expiration'] - date).days
        T = max(dte / 365.0, 0.001)
        
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=price,
            K=position['strike'],
            T=T,
            r=r,
            sigma=sigma,
            option_type=position['type']
        )
        
        current_price = greeks['price']
        position_value = current_price * position['contracts'] * 100
        
        # For SOLD options, P&L is INVERTED:
        # We collected premium at entry, so profit = premium collected - current value
        unrealized_pnl = position['premium_collected'] - position_value
        unrealized_pnl_pct = (unrealized_pnl / position['premium_collected']) * 100
        
        # Exit conditions for premium selling
        should_exit = False
        exit_reason = None
        
        # 1. Profit target: Collected 60% of premium (option worth 40% of original)
        if unrealized_pnl_pct >= 60:
            should_exit = True
            exit_reason = 'PROFIT_TARGET'
        
        # 2. Time exit: 21 DTE (theta acceleration slows)
        elif dte <= 21:
            should_exit = True
            exit_reason = 'TIME_EXIT'
        
        # 3. Stop loss: Loss > 150% of premium (position moved against us)
        elif unrealized_pnl_pct <= -150:
            should_exit = True
            exit_reason = 'STOP_LOSS'
        
        if should_exit:
            # Buy back the option to close (pay current price)
            buyback_cost = current_price * position['contracts'] * 100 * 1.01  # 1% slippage
            fees = 0.097 * position['contracts']
            total_cost = buyback_cost + fees
            
            # Final P&L = premium collected - buyback cost
            final_pnl = position['premium_collected'] - total_cost
            final_pnl_pct = (final_pnl / position['premium_collected']) * 100
            
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': date,
                'type': position['type'],
                'strike': position['strike'],
                'contracts': position['contracts'],
                'premium_collected': position['premium_collected'],
                'buyback_cost': total_cost,
                'pnl': final_pnl,
                'pnl_pct': final_pnl_pct,
                'reason': exit_reason,
                'hold_days': (date - position['entry_date']).days
            })
            
            cash += final_pnl  # Add profit or subtract loss
            position = None
            position_value = 0
    
    # Enter new position if no position and signal present
    if position is None and signal in ['SELL_PUT', 'SELL_CALL']:
        option_type = 'put' if signal == 'SELL_PUT' else 'call'
        
        # Use ATM strike (delta ~0.50 for sold options)
        strike = round(price / 5) * 5
        
        # 45 DTE
        expiration = date + timedelta(days=45)
        T = 45 / 365.0
        
        greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=price,
            K=strike,
            T=T,
            r=r,
            sigma=sigma,
            option_type=option_type
        )
        
        # SELL at bid (collect less premium due to slippage)
        sell_price = greeks['price'] * 0.99  # 1% slippage
        
        # Position size: target $10k notional
        contracts = max(1, int(10000 / (price * abs(greeks['delta']))))
        
        # Premium collected (this is our CREDIT)
        premium_collected = sell_price * contracts * 100
        fees = 0.097 * contracts
        net_premium = premium_collected - fees
        
        if net_premium > 0 and net_premium < cash:  # Have enough margin
            position = {
                'entry_date': date,
                'type': option_type,
                'strike': strike,
                'expiration': expiration,
                'contracts': contracts,
                'premium_collected': net_premium,
                'entry_price': sell_price
            }
            
            # For sold options, we COLLECT cash upfront
            cash += net_premium
            position_value = sell_price * contracts * 100  # Liability
    
    # Track equity (cash - liability from sold options)
    total_equity = cash - position_value if position else cash
    
    equity_curve.append({
        'date': date,
        'equity': total_equity,
        'cash': cash,
        'position_value': position_value
    })

# Close final position
if position:
    final_date = df.index[-1]
    final_price = df.iloc[-1]['close']
    dte = (position['expiration'] - final_date).days
    T = max(dte / 365.0, 0.001)
    
    greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=final_price,
        K=position['strike'],
        T=T,
        r=r,
        sigma=sigma,
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
        'strike': position['strike'],
        'contracts': position['contracts'],
        'premium_collected': position['premium_collected'],
        'buyback_cost': total_cost,
        'pnl': final_pnl,
        'pnl_pct': final_pnl_pct,
        'reason': 'END_OF_BACKTEST',
        'hold_days': (final_date - position['entry_date']).days
    })
    
    cash += final_pnl

print(f"✓ Simulated {len(trades)} trades\n")

# Calculate metrics
print("[4/4] Calculating performance metrics...")

trades_df = pd.DataFrame(trades)
equity_df = pd.DataFrame(equity_curve).set_index('date')

total_return = (equity_df['equity'].iloc[-1] / 100000 - 1) * 100
returns = equity_df['equity'].pct_change().dropna()
sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

cummax = equity_df['equity'].cummax()
drawdown = (equity_df['equity'] / cummax - 1) * 100
max_dd = drawdown.min()

spy_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100

win_rate = (trades_df['pnl'] > 0).sum() / len(trades_df) * 100 if len(trades_df) > 0 else 0
avg_win = trades_df[trades_df['pnl'] > 0]['pnl_pct'].mean() if (trades_df['pnl'] > 0).any() else 0
avg_loss = trades_df[trades_df['pnl'] < 0]['pnl_pct'].mean() if (trades_df['pnl'] < 0).any() else 0

# Print results
print("\n" + "="*70)
print("RESULTS")
print("="*70)

print(f"\n📊 Performance:")
print(f"  Total Return: {total_return:+.2f}%")
print(f"  Sharpe Ratio: {sharpe:.2f}")
print(f"  Max Drawdown: {max_dd:.2f}%")
print(f"  Final Equity: ${equity_df['equity'].iloc[-1]:,.2f}")

print(f"\n📈 vs SPY Buy & Hold:")
print(f"  SPY Return: {spy_return:+.2f}%")
print(f"  Outperformance: {total_return - spy_return:+.2f}%")

print(f"\n📋 Trades:")
print(f"  Total: {len(trades_df)}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Avg Win: {avg_win:+.2f}%")
print(f"  Avg Loss: {avg_loss:+.2f}%")

print(f"\n✅ Success Criteria:")
print(f"  Sharpe > 1.5: {'✅ PASS' if sharpe > 1.5 else '❌ FAIL'} ({sharpe:.2f})")
print(f"  Win Rate > 70%: {'✅ PASS' if win_rate > 70 else '❌ FAIL'} ({win_rate:.1f}%)")
print(f"  Return > 0%: {'✅ PASS' if total_return > 0 else '❌ FAIL'} ({total_return:+.2f}%)")

# Save results
output_dir = Path('results/options')
output_dir.mkdir(parents=True, exist_ok=True)

trades_df.to_csv(output_dir / 'premium_selling_trades.csv', index=False)
equity_df.to_csv(output_dir / 'premium_selling_equity_curve.csv')

print(f"\n📁 Results saved to: {output_dir}/")
print("="*70)
