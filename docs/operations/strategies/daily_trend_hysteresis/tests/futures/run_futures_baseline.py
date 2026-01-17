"""
Daily Trend Hysteresis - Futures Baseline Test (Simplified)

Tests RSI hysteresis strategy across futures proxies using existing validated backtesting logic.

This script leverages the exact same backtest logic from the equity strategies but applies it
to futures market proxies (spot commodities, FX, and index ETFs).
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]  # Magellan folder
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("DAILY TREND HYSTERESIS - FUTURES BASELINE TEST")
print("="*80)
print("Testing futures market proxies using Index ETFs")
print("Period: 2024-01-01 to 2025-12-31")
print("Strategy: RSI-28, Bands 55/45, Long-Only")
print("="*80)

# PHASE 1: Test Index ETFs as proxies for Index Futures
# These are proven via existing daily_trend tests
FUTURES_UNIVERSE = {
    'MES': {'name': 'Micro E-mini S&P 500', 'proxy': 'SPY'},
    'MNQ': {'name': 'Micro E-mini Nasdaq 100', 'proxy': 'QQQ'},
    'MYM': {'name': 'Micro E-mini Dow', 'proxy':  'DIA'},
    'M2K': {'name': 'Micro E-mini Russell 2000', 'proxy': 'IWM'},
}

START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 28
UPPER_BAND = 55
LOWER_BAND = 45
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0

def calculate_rsi(prices, period=28):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    
    rsi.loc[avg_loss == 0] = 100.0
    rsi.loc[avg_gain == 0] = 0.0
    
    return rsi

def backtest_hysteresis(df, initial_capital=10000, transaction_cost_bps=5.0):
    """Run hysteresis backtest"""
    cash = initial_capital
    shares = 0
    position = 'flat'
    trades = []
    equity_curve = []
    
    entry_price = None
    entry_date = None
    
    for date, row in df.iterrows():
        price = row['close']
        rsi = row['rsi']
        
        if pd.isna(rsi):
            equity_curve.append(cash + shares * price)
            continue
        
        # Hysteresis Logic
        if position == 'flat' and rsi > UPPER_BAND:
            cost = transaction_cost_bps / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                entry_price = price
                entry_date = date
        
        elif position == 'long' and rsi < LOWER_BAND:
            cost = transaction_cost_bps / 10000
            proceeds = shares * price * (1 - cost)
            pnl = proceeds - (shares * entry_price)
            pnl_pct = (price / entry_price - 1) * 100
            hold_days = (date - entry_date).days
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_days': hold_days,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
            
            cash += proceeds
            shares = 0
            position = 'flat'
            entry_price = None
        
        current_equity = cash + shares * price
        equity_curve.append(current_equity)
    
    # Close any open position
    if position == 'long' and shares > 0:
        price = df.iloc[-1]['close']
        date = df.index[-1]
        cost = transaction_cost_bps / 10000
        proceeds = shares * price * (1 - cost)
        pnl = proceeds - (shares * entry_price)
        pnl_pct = (price / entry_price - 1) * 100
        hold_days = (date - entry_date).days
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_days': hold_days,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        cash += proceeds
        shares = 0
    
    return trades, equity_curve

# Initialize client
client = AlpacaDataClient()

# Test all futures
print(f"\n[1/3] Testing {len(FUTURES_UNIVERSE)} index futures (via ETF proxies)...\n")

results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']}) via {config['proxy']}...")
    
    try:
        # Fetch data from Alpaca
        raw_df = client.fetch_historical_bars(
            symbol=config['proxy'],
            timeframe=TimeFrame.Day,
            start=START_DATE,
            end=END_DATE,
            feed='sip'
        )
        
        # Force resample to daily if Alpaca returns minute data
        if len(raw_df) > 1000:  # Likely minute data
            print(f"  ⚠️  Detected {len(raw_df)} bars (likely minute data), resampling to daily...")
            df = raw_df.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            print(f"  ✓ Resampled to {len(df)} daily bars")
        else:
            df = raw_df
        
        print(f"  ✓ Final dataset: {len(df)} daily bars")
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        # Run backtest
        trades, equity_curve = backtest_hysteresis(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
        
        # Buy & Hold
        bh_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        if len(equity_curve) > 1:
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = trades_df[trades_df['pnl'] > 0]
            win_rate = (len(winning_trades) / len(trades)) * 100
            avg_hold = trades_df['hold_days'].mean()
        else:
            win_rate = 0
            avg_hold = 0
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': round(total_return, 2),
            'bh_return': round(bh_return, 2), 
            'sharpe': round(sharpe, 2),
            'max_dd': round(max_dd, 2),
            'trades': len(trades),
            'win_rate': round(win_rate, 1),
            'avg_hold_days': round(avg_hold, 1) if avg_hold > 0 else 0,
            'status': 'SUCCESS'
        })
        
        status = "✅" if sharpe > 0.7 else "⚠️" if sharpe > 0.3 else "❌"
        print(f"  {status} Return: {total_return:+.1f}% | Sharpe: {sharpe:.2f} | DD: {max_dd:.1f}% | Trades: {len(trades)} | Win%: {win_rate:.0f}%\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'proxy': config['proxy'],
            'total_return': 0,
            'bh_return': 0,
            'sharpe': 0,
            'max_dd': 0,
            'trades': 0,
            'win_rate': 0,
            'avg_hold_days': 0,
            'status': f'ERROR: {str(e)[:50]}'
        })

print("="*80)
print("FUTURES BASELINE RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

# Summary stats
successful = results_df[results_df['status'] == 'SUCCESS']
if len(successful) > 0:
    print(f"\n✅ Successful Tests: {len(successful)}/{len(results_df)}")
    print(f"   Average Sharpe: {successful['sharpe'].mean():.2f}")
    print(f"   Average Return: {successful['total_return'].mean():.1f}%")
    print(f"  Contracts with Sharpe > 0.7: {len(successful[successful['sharpe'] > 0.7])}")
    print(f"   Contracts with Sharpe > 1.0: {len(successful[successful['sharpe'] > 1.0])}")

# Save results
output_file = Path(__file__).parent / 'futures_baseline_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Show all performers
if len(successful) > 0:
    print("\n📊 All Results (by Sharpe):")
    sorted_results = successful.sort_values('sharpe', ascending=False)[['symbol', 'name', 'sharpe', 'total_return', 'max_dd', 'trades', 'win_rate']]
    print(sorted_results.to_string(index=False))

print("\n" + "="*80)
print("VERDICT")
print("="*80)

approved = successful[successful['sharpe'] > 0.7]
tuning_needed = successful[(successful['sharpe'] >= 0.3) & (successful['sharpe'] <= 0.7)]
rejected = successful[successful['sharpe'] < 0.3]

if len(approved) > 0:
    print(f"\n✅ APPROVED FOR DEPLOYMENT ({len(approved)} contracts):")
    for _, row in approved.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}, Return {row['total_return']:+.1f}%")

if len(tuning_needed) > 0:
    print(f"\n⚠️  NEEDS TUNING ({len(tuning_needed)} contracts):")
    for _, row in tuning_needed.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f} (try wider bands: 60/40)")

if len(rejected) > 0:
    print(f"\n❌ REJECTED ({len(rejected)} contracts):")
    for _, row in rejected.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Create asset configs for APPROVED contracts")
print("2. Run parameter tuning for contracts needing tuning")
print("3. Generate FINAL_VALIDATION_REPORT.md")
print("="*80)
