"""
Hourly Swing - Commodities/Currencies/Crypto Futures Test

Tests hourly RSI hysteresis on high-volatility futures using FMP hourly data.

Assets (9 contracts):
- Commodities: MCL, MGC, MSI, MNG, MCP
- Currencies: M6E, M6B, M6A
- Crypto: MBT

Expected: High-volatility assets (MBT, MCL, MNG) to show positive results
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
import requests
import os

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("="*80)
print("HOURLY SWING - COMMODITIES/FX/CRYPTO FUTURES TEST")
print("="*80)
print("Testing hourly volatility strategy via FMP data")
print("Period: 2024-01-01 to 2025-12-31")
print("Strategy: RSI-28, Bands 60/40, Long-Only")
print("="*80)

FMP_API_KEY = os.getenv('FMP_API_KEY')

# High-volatility futures (via FMP spot hourly data)
FUTURES_UNIVERSE = {
    'MCL': {'name': 'Micro Crude Oil', 'fmp_symbol': 'CLUSD'},
    'MGC': {'name': 'Micro Gold', 'fmp_symbol': 'GCUSD'},
    'MSI': {'name': 'Micro Silver', 'fmp_symbol': 'SIUSD'},
    'MNG': {'name': 'Micro Natural Gas', 'fmp_symbol': 'NGUSD'},
    'MCP': {'name': 'Micro Copper', 'fmp_symbol': 'HGUSD'},
    'M6E': {'name': 'Micro EUR/USD', 'fmp_symbol': 'EURUSD'},
    'M6B': {'name': 'Micro GBP/USD', 'fmp_symbol': 'GBPUSD'},
    'M6A': {'name': 'Micro AUD/USD', 'fmp_symbol': 'AUDUSD'},
    'MBT': {'name': 'Micro Bitcoin', 'fmp_symbol': 'BTCUSD'},
}

START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 28
UPPER_BAND = 60  # Wider for hourly
LOWER_BAND = 40
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 10.0  # Higher for hourly

def fetch_fmp_hourly_data(symbol, start_date, end_date):
    """Fetch hourly OHLC data from FMP"""
    url = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
    params = {
        'symbol': symbol,
        'from': start_date,
        'to': end_date,
        'apikey': FMP_API_KEY
    }
    
    print(f"  Fetching {symbol} hourly data from FMP...")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data or len(data) == 0:
            return None
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['date'])
        df = df.set_index('timestamp')
        df = df.sort_index(ascending=True)
        df.columns = df.columns.str.lower()
        
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume']
        df = df[[col for col in ohlcv_cols if col in df.columns]]
        
        print(f"  ✓ Fetched {len(df)} hourly bars")
        return df
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

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

def backtest_hysteresis(df, initial_capital=10000, transaction_cost_bps=10.0):
    """Run hysteresis backtest on hourly data"""
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
            hold_hours = (date - entry_date).total_seconds() / 3600
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': date,
                'entry_price': entry_price,
                'exit_price': price,
                'hold_hours': hold_hours,
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
        hold_hours = (date - entry_date).total_seconds() / 3600
        
        trades.append({
            'entry_date': entry_date,
            'exit_date': date,
            'entry_price': entry_price,
            'exit_price': price,
            'hold_hours': hold_hours,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
        
        cash += proceeds
        shares = 0
    
    return trades, equity_curve

# Test all futures
print(f"\n[1/3] Testing {len(FUTURES_UNIVERSE)} commodity/FX/crypto futures on HOURLY...\n")

results = []

for symbol, config in FUTURES_UNIVERSE.items():
    print(f"Testing {symbol} ({config['name']})...")
    
    try:
        # Fetch hourly data from FMP
        df = fetch_fmp_hourly_data(config['fmp_symbol'], START_DATE, END_DATE)
        
        if df is None or len(df) < 100:
            print(f"  ❌ Insufficient data\n")
            results.append({
                'symbol': symbol,
                'name': config['name'],
                'fmp_symbol': config['fmp_symbol'],
                'total_return': 0,
                'bh_return': 0,
                'sharpe': 0,
                'max_dd': 0,
                'trades': 0,
                'win_rate': 0,
                'avg_hold_hours': 0,
                'status': 'NO_DATA'
            })
            continue
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        # Run backtest
        trades, equity_curve = backtest_hysteresis(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
        
        bh_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
        
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_dd = drawdown.min() * 100
        
        # Annualize Sharpe for hourly (252 days * 24 hours)
        if len(equity_curve) > 1:
            returns = equity_series.pct_change().dropna()
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 24) if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        if trades:
            trades_df = pd.DataFrame(trades)
            winning_trades = trades_df[trades_df['pnl'] > 0]
            win_rate = (len(winning_trades) / len(trades)) * 100
            avg_hold_hours = trades_df['hold_hours'].mean()
        else:
            win_rate = 0
            avg_hold_hours = 0
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'fmp_symbol': config['fmp_symbol'],
            'total_return': round(total_return, 2),
            'bh_return': round(bh_return, 2),
            'sharpe': round(sharpe, 2),
            'max_dd': round(max_dd, 2),
            'trades': len(trades),
            'win_rate': round(win_rate, 1),
            'avg_hold_hours': round(avg_hold_hours, 1) if avg_hold_hours > 0 else 0,
            'status': 'SUCCESS'
        })
        
        status = "✅" if sharpe > 1.0 else "⚠️" if sharpe > 0.5 else "❌"
        print(f"  {status} Return: {total_return:+.1f}% | Sharpe: {sharpe:.2f} | DD: {max_dd:.1f}% | Trades: {len(trades)} | Win%: {win_rate:.0f}%\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'fmp_symbol': config['fmp_symbol'],
            'total_return': 0,
            'bh_return': 0,
            'sharpe': 0,
            'max_dd': 0,
            'trades': 0,
            'win_rate': 0,
            'avg_hold_hours': 0,
            'status': f'ERROR: {str(e)[:50]}'
        })

print("="*80)
print("HOURLY SWING COMMODITIES/FX/CRYPTO RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

# Summary
successful = results_df[results_df['status'] == 'SUCCESS']
if len(successful) > 0:
    print(f"\n✅ Successful Tests: {len(successful)}/{len(results_df)}")
    print(f"   Average Sharpe: {successful['sharpe'].mean():.2f}")
    print(f"   Average Return: {successful['total_return'].mean():.1f}%")
    print(f"   Contracts with Sharpe > 1.0: {len(successful[successful['sharpe'] > 1.0])}")
    print(f"   Contracts with Sharpe > 0.5: {len(successful[successful['sharpe'] > 0.5])}")

# Save
output_file = Path(__file__).parent / 'futures_hourly_commodities_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Show all
if len(successful) > 0:
    print("\n📊 All Results (by Sharpe):")
    sorted_results = successful.sort_values('sharpe', ascending=False)[['symbol', 'name', 'sharpe', 'total_return', 'max_dd', 'trades', 'win_rate']]
    print(sorted_results.to_string(index=False))

print("\n" + "="*80)
print("VERDICT")
print("="*80)

approved = successful[successful['sharpe'] > 1.0]
tuning_needed = successful[(successful['sharpe'] >= 0.5) & (successful['sharpe'] <= 1.0)]
rejected = successful[successful['sharpe'] < 0.5]

if len(approved) > 0:
    print(f"\n✅ APPROVED FOR DEPLOYMENT ({len(approved)} contracts):")
    for _, row in approved.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}, Return {row['total_return']:+.1f}%")

if len(tuning_needed) > 0:
    print(f"\n⚠️  NEEDS TUNING ({len(tuning_needed)} contracts):")
    for _, row in tuning_needed.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f} (try wider bands: 65/35 or 70/30)")

if len(rejected) > 0:
    print(f"\n❌ REJECTED ({len(rejected)} contracts):")
    for _, row in rejected.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Create asset configs for APPROVED contracts")
print("2. Combine with index futures hourly results")
print("3. Generate comprehensive HOURLY_COMPLETE_VALIDATION.md")
print("="*80)
