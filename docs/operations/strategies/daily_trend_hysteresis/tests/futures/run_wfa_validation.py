"""
Walk-Forward Analysis - Futures Validation

Tests approved and marginal contracts on train/test split:
- Train: 2024 (in-sample)
- Test: 2025 (out-of-sample)

Validates if results hold up in unseen data.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
import requests
import os

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("WALK-FORWARD ANALYSIS - FUTURES VALIDATION")
print("="*80)
print("Train: 2024 (in-sample) | Test: 2025 (out-of-sample)")
print("="*80)

FMP_API_KEY = os.getenv('FMP_API_KEY')

# Approved + Marginal contracts
DAILY_CONTRACTS = {
    # Approved
    'MGC': {'name': 'Micro Gold', 'source': 'fmp', 'symbol': 'GCUSD', 'tier': 'approved'},
    'MSI': {'name': 'Micro Silver', 'source': 'fmp', 'symbol': 'SIUSD', 'tier': 'approved'},
    'MNQ': {'name': 'Micro Nasdaq', 'source': 'alpaca', 'symbol': 'QQQ', 'tier': 'approved'},
    'MES': {'name': 'Micro S&P 500', 'source': 'alpaca', 'symbol': 'SPY', 'tier': 'approved'},
    # Marginal
    'MYM': {'name': 'Micro Dow', 'source': 'alpaca', 'symbol': 'DIA', 'tier': 'marginal'},
    'M6E': {'name': 'Micro EUR/USD', 'source': 'fmp', 'symbol': 'EURUSD', 'tier': 'marginal'},
    'MNG': {'name': 'Micro Natural Gas', 'source': 'fmp', 'symbol': 'NGUSD', 'tier': 'marginal'},
    'M6B': {'name': 'Micro GBP/USD', 'source': 'fmp', 'symbol': 'GBPUSD', 'tier': 'marginal'},
    'MCP': {'name': 'Micro Copper', 'source': 'fmp', 'symbol': 'HGUSD', 'tier': 'marginal'},
}

HOURLY_CONTRACTS = {
    'MGC': {'name': 'Micro Gold Hourly', 'source': 'fmp', 'symbol': 'GCUSD', 'tier': 'approved'},
    'MSI': {'name': 'Micro Silver Hourly', 'source': 'fmp', 'symbol': 'SIUSD', 'tier': 'approved'},
}

RSI_PERIOD = 28
DAILY_UPPER = 55
DAILY_LOWER = 45
HOURLY_UPPER = 60
HOURLY_LOWER = 40
INITIAL_CAPITAL = 10000
DAILY_COST_BPS = 5.0
HOURLY_COST_BPS = 10.0

def fetch_data(source, symbol, start, end, timeframe='daily'):
    """Fetch data from Alpaca or FMP"""
    if source == 'alpaca':
        client = AlpacaDataClient()
        tf = TimeFrame.Day if timeframe == 'daily' else TimeFrame.Hour
        df = client.fetch_historical_bars(symbol, tf, start, end, feed='sip')
        
        # Resample if needed
        if timeframe == 'daily' and len(df) > 1000:
            df = df.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
        elif timeframe == 'hourly' and len(df) > 5000:
            df = df.resample('1h').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
        return df
    else:  # FMP
        if timeframe == 'daily':
            url = f"https://financialmodelingprep.com/stable/historical-price-eod/full"
        else:
            url = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
        
        params = {'symbol': symbol, 'from': start, 'to': end, 'apikey': FMP_API_KEY}
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['date'])
        df = df.set_index('timestamp').sort_index()
        df.columns = df.columns.str.lower()
        return df[['open','high','low','close','volume']]

def calculate_rsi(prices, period=28):
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0).ewm(span=period, adjust=False).mean()
    losses = (-delta).where(delta < 0, 0.0).ewm(span=period, adjust=False).mean()
    rs = gains / losses.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi.loc[losses == 0] = 100.0
    rsi.loc[gains == 0] = 0.0
    return rsi

def backtest(df, upper, lower, cost_bps, capital=10000):
    cash, shares, position = capital, 0, 'flat'
    entry_price, entry_date = None, None
    trades, equity = [], []
    
    for date, row in df.iterrows():
        price, rsi = row['close'], row['rsi']
        if pd.isna(rsi):
            equity.append(cash + shares * price)
            continue
        
        if position == 'flat' and rsi > upper:
            cost = cost_bps / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position, entry_price, entry_date = 'long', price, date
        
        elif position == 'long' and rsi < lower:
            cost = cost_bps / 10000
            proceeds = shares * price * (1 - cost)
            pnl_pct = (price / entry_price - 1) * 100
            trades.append({'pnl_pct': pnl_pct})
            cash += proceeds
            shares, position = 0, 'flat'
        
        equity.append(cash + shares * price)
    
    if position == 'long' and shares > 0:
        cost = cost_bps / 10000
        proceeds = shares * df.iloc[-1]['close'] * (1 - cost)
        pnl_pct = (df.iloc[-1]['close'] / entry_price - 1) * 100
        trades.append({'pnl_pct': pnl_pct})
        cash += proceeds
        shares = 0
    
    final_equity = cash
    total_return = (final_equity / capital - 1) * 100
    
    equity_series = pd.Series(equity)
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    running_max = equity_series.expanding().max()
    dd = ((equity_series - running_max) / running_max).min() * 100
    
    win_rate = (len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100) if trades else 0
    
    return {
        'return': round(total_return, 2),
        'sharpe': round(sharpe, 2),
        'max_dd': round(dd, 2),
        'trades': len(trades),
        'win_rate': round(win_rate, 1)
    }

print("\n[1/2] DAILY TREND - WFA Validation\n")

daily_results = []

for symbol, config in DAILY_CONTRACTS.items():
    print(f"Testing {symbol} ({config['name']}) [{config['tier']}]...")
    
    try:
        # Fetch full 2024-2025
        df = fetch_data(config['source'], config['symbol'], '2024-01-01', '2025-12-31', 'daily')
        if df is None or len(df) < 200:
            print(f"  ❌ Insufficient data\n")
            continue
        
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        # Split train/test
        train = df['2024-01-01':'2024-12-31']
        test = df['2025-01-01':'2025-12-31']
        
        # Run backtest on both
        train_res = backtest(train, DAILY_UPPER, DAILY_LOWER, DAILY_COST_BPS)
        test_res = backtest(test, DAILY_UPPER, DAILY_LOWER, DAILY_COST_BPS)
        
        # Calculate degradation
        sharpe_deg = test_res['sharpe'] - train_res['sharpe']
        
        daily_results.append({
            'symbol': symbol,
            'name': config['name'],
            'tier': config['tier'],
            'train_sharpe': train_res['sharpe'],
            'test_sharpe': test_res['sharpe'],
            'degradation': round(sharpe_deg, 2),
            'train_return': train_res['return'],
            'test_return': test_res['return'],
            'train_trades': train_res['trades'],
            'test_trades': test_res['trades']
        })
        
        status = "✅" if test_res['sharpe'] > 0.7 else "⚠️" if test_res['sharpe'] > 0.3 else "❌"
        print(f"  Train: Sharpe {train_res['sharpe']:.2f}, {train_res['return']:+.1f}%")
        print(f"  Test:  Sharpe {test_res['sharpe']:.2f}, {test_res['return']:+.1f}% {status}")
        print(f"  Degradation: {sharpe_deg:+.2f}\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

print("\n[2/2] HOURLY SWING - WFA Validation\n")

hourly_results = []

for symbol, config in HOURLY_CONTRACTS.items():
    print(f"Testing {symbol} ({config['name']}) [{config['tier']}]...")
    
    try:
        df = fetch_data(config['source'], config['symbol'], '2024-01-01', '2025-12-31', 'hourly')
        if df is None or len(df) < 500:
            print(f"  ❌ Insufficient data\n")
            continue
        
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        
        train = df['2024-01-01':'2024-12-31']
        test = df['2025-01-01':'2025-12-31']
        
        train_res = backtest(train, HOURLY_UPPER, HOURLY_LOWER, HOURLY_COST_BPS)
        test_res = backtest(test, HOURLY_UPPER, HOURLY_LOWER, HOURLY_COST_BPS)
        
        sharpe_deg = test_res['sharpe'] - train_res['sharpe']
        
        hourly_results.append({
            'symbol': symbol,
            'name': config['name'],
            'tier': config['tier'],
            'train_sharpe': train_res['sharpe'],
            'test_sharpe': test_res['sharpe'],
            'degradation': round(sharpe_deg, 2),
            'train_return': train_res['return'],
            'test_return': test_res['return']
        })
        
        status = "✅" if test_res['sharpe'] > 1.0 else "⚠️" if test_res['sharpe'] > 0.5 else "❌"
        print(f"  Train: Sharpe {train_res['sharpe']:.2f}, {train_res['return']:+.1f}%")
        print(f"  Test:  Sharpe {test_res['sharpe']:.2f}, {test_res['return']:+.1f}% {status}")
        print(f"  Degradation: {sharpe_deg:+.2f}\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

# Save results
output_dir = Path(__file__).parent
pd.DataFrame(daily_results).to_csv(output_dir / 'wfa_daily_results.csv', index=False)
pd.DataFrame(hourly_results).to_csv(output_dir / 'wfa_hourly_results.csv', index=False)

print("="*80)
print("WFA SUMMARY")
print("="*80)

if daily_results:
    print("\nDAILY TREND:")
    df_daily = pd.DataFrame(daily_results)
    print(df_daily[['symbol', 'tier', 'train_sharpe', 'test_sharpe', 'degradation']].to_string(index=False))
    
    approved_pass = df_daily[(df_daily['tier']=='approved') & (df_daily['test_sharpe'] > 0.7)]
    print(f"\n✅ Approved contracts passing OOS: {len(approved_pass)}/4")

if hourly_results:
    print("\nHOURLY SWING:")
    df_hourly = pd.DataFrame(hourly_results)
    print(df_hourly[['symbol', 'tier', 'train_sharpe', 'test_sharpe', 'degradation']].to_string(index=False))
    
    approved_pass = df_hourly[(df_hourly['tier']=='approved') & (df_hourly['test_sharpe'] > 1.0)]
    print(f"\n✅ Approved contracts passing OOS: {len(approved_pass)}/2")

print("\n" + "="*80)
print("WFA Complete! Results saved to wfa_daily_results.csv and wfa_hourly_results.csv")
print("="*80)
