"""
Daily Trend Hysteresis - Commodity ETFs Test

Tests ETFs vs Futures comparison:
- GLD vs MGC (Gold)
- SLV vs MSI (Silver)
- USO vs MCL (Crude)
- UNG vs MNG (Nat Gas)
- DBA (Agriculture)
- COPX (Copper miners)

Goal: Validate futures findings and identify if ETFs are tradeable alternatives
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("DAILY TREND - COMMODITY ETFs VALIDATION")
print("="*80)
print("Testing commodity ETFs vs Futures comparison")
print("Period: 2024-01-01 to 2025-12-31 (2 years)")
print("Strategy: RSI-28, Bands 55/45, Long-Only")
print("="*80)

COMMODITY_ETFS = {
    'GLD': {'name': 'Gold ETF', 'compares_to': 'MGC'},
    'SLV': {'name': 'Silver ETF', 'compares_to': 'MSI'},
    'USO': {'name': 'Crude Oil ETF', 'compares_to': 'MCL'},
    'UNG': {'name': 'Natural Gas ETF', 'compares_to': 'MNG'},
    'DBA': {'name': 'Agriculture ETF', 'compares_to': 'N/A'},
    'COPX': {'name': 'Copper Miners ETF', 'compares_to': 'MCP'},
}

START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 28
UPPER_BAND = 55
LOWER_BAND = 45
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0

def calculate_rsi(prices, period=28):
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0).ewm(span=period, adjust=False).mean()
    losses = (-delta).where(delta < 0, 0.0).ewm(span=period, adjust=False).mean()
    rs = gains / losses.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi.loc[losses == 0] = 100.0
    rsi.loc[gains == 0] = 0.0
    return rsi

def backtest(df, capital=10000, cost_bps=5.0):
    cash, shares, position = capital, 0, 'flat'
    entry_price, entry_date = None, None
    trades, equity = [], []
    
    for date, row in df.iterrows():
        price, rsi = row['close'], row['rsi']
        if pd.isna(rsi):
            equity.append(cash + shares * price)
            continue
        
        if position == 'flat' and rsi > UPPER_BAND:
            cost = cost_bps / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position, entry_price, entry_date = 'long', price, date
        
        elif position == 'long' and rsi < LOWER_BAND:
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
    
    final_equity = cash
    total_return = (final_equity / capital - 1) * 100
    
    equity_series = pd.Series(equity)
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    running_max = equity_series.expanding().max()
    dd = ((equity_series - running_max) / running_max).min() * 100
    
    bh_return = (df.iloc[-1]['close'] / df.iloc[0]['close'] - 1) * 100
    
    win_rate = (len([t for t in trades if t['pnl_pct'] > 0]) / len(trades) * 100) if trades else 0
    
    return {
        'return': round(total_return, 2),
        'bh_return': round(bh_return, 2),
        'sharpe': round(sharpe, 2),
        'max_dd': round(dd, 2),
        'trades': len(trades),
        'win_rate': round(win_rate, 1)
    }

client = AlpacaDataClient()

print(f"\nTesting {len(COMMODITY_ETFS)} commodity ETFs...\n")

results = []

for symbol, config in COMMODITY_ETFS.items():
    print(f"Testing {symbol} ({config['name']}) [compares to {config['compares_to']}]...")
    
    try:
        # Fetch daily data
        raw_df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=TimeFrame.Day,
            start=START_DATE,
            end=END_DATE,
            feed='sip'
        )
        
        # Resample if minute data
        if len(raw_df) > 1000:
            df = raw_df.resample('1D').agg({
                'open':'first','high':'max','low':'min','close':'last','volume':'sum'
            }).dropna()
        else:
            df = raw_df
        
        print(f"  ✓ Fetched {len(df)} daily bars")
        
        # Calculate RSI and backtest
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        res = backtest(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'compares_to': config['compares_to'],
            'total_return': res['return'],
            'bh_return': res['bh_return'],
            'sharpe': res['sharpe'],
            'max_dd': res['max_dd'],
            'trades': res['trades'],
            'win_rate': res['win_rate']
        })
        
        status = "✅" if res['sharpe'] > 0.7 else "⚠️" if res['sharpe'] > 0.3 else "❌"
        print(f"  {status} Sharpe: {res['sharpe']:.2f} | Return: {res['return']:+.1f}% | DD: {res['max_dd']:.1f}% | Trades: {res['trades']}\n")
        
    except Exception as e:
        print(f"  ❌ Error: {e}\n")
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'compares_to': config['compares_to'],
            'total_return': 0,
            'bh_return': 0,
            'sharpe': 0,
            'max_dd': 0,
            'trades': 0,
            'win_rate': 0
        })

print("="*80)
print("COMMODITY ETFs RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

print("\n📊 All Results (by Sharpe):")
sorted_df = results_df.sort_values('sharpe', ascending=False)
print(sorted_df[['symbol', 'name', 'sharpe', 'total_return', 'max_dd', 'trades']].to_string(index=False))

# Comparison to futures
print("\n📊 ETF vs Futures Comparison:")
print("="*80)
futures_map = {
    'MGC': 1.35, 'MSI': 1.29, 'MCL': -0.28, 
    'MNG': 0.51, 'MCP': 0.32
}

for _, row in results_df.iterrows():
    if row['compares_to'] in futures_map:
        futures_sharpe = futures_map[row['compares_to']]
        diff = row['sharpe'] - futures_sharpe
        print(f"{row['symbol']} (ETF): {row['sharpe']:.2f} | {row['compares_to']} (Futures): {futures_sharpe:.2f} | Diff: {diff:+.2f}")

# Save
output_file = Path(__file__).parent / 'commodity_etf_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Saved: {output_file}")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

approved = results_df[results_df['sharpe'] > 0.7]
if len(approved) > 0:
    print(f"\n✅ APPROVED ({len(approved)} ETFs):")
    for _, row in approved.iterrows():
        print(f"   {row['symbol']} - Sharpe {row['sharpe']:.2f}, Return {row['total_return']:+.1f}%")
else:
    print("\n❌ NO APPROVALS among commodity ETFs")

print("\n" + "="*80)
print("Next: Test diverse ETFs across sectors for hidden gems")
print("="*80)
