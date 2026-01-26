"""
Daily Trend Hysteresis - ETF Gem Hunter

Tests diverse ETFs across sectors to find hidden gems.

Sectors covered:
- Technology (XLK, SOXX, ARKK, HACK)
- Energy (XLE, XOP, TAN)
- Financials (XLF, KRE)
- Healthcare (XLV, XBI, IBB)
- Real Estate (VNQ, IYR)
- International (EEM, EFA, FXI, EWJ)
- Bonds (TLT, HYG, LQD)
- Others (XLI, XLU, XLV)
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
print("ETF GEM HUNTER - DAILY TREND VALIDATION")
print("="*80)
print("Hunting for hidden gems across sectors")
print("Period: 2024-01-01 to 2025-12-31 (2 years)")
print("Strategy: RSI-28, Bands 55/45, Long-Only")
print("="*80)

GEM_HUNT_ETFS = {
    # Technology
    'XLK': {'name': 'Technology Select', 'sector': 'Technology'},
    'SOXX': {'name': 'Semiconductors', 'sector': 'Technology'},
    'ARKK': {'name': 'Innovation/Growth', 'sector': 'Technology'},
    'HACK': {'name': 'Cybersecurity', 'sector': 'Technology'},
    
    # Energy
    'XLE': {'name': 'Energy Select', 'sector': 'Energy'},
    'XOP': {'name': 'Oil & Gas Exploration', 'sector': 'Energy'},
    'TAN': {'name': 'Solar Energy', 'sector': 'Energy'},
    
    # Financials
    'XLF': {'name': 'Financial Select', 'sector': 'Financials'},
    'KRE': {'name': 'Regional Banks', 'sector': 'Financials'},
    
    # Healthcare/Biotech
    'XLV': {'name': 'Healthcare Select', 'sector': 'Healthcare'},
    'XBI': {'name': 'Biotech', 'sector': 'Healthcare'},
    'IBB': {'name': 'Biotech Large Cap', 'sector': 'Healthcare'},
    
    # Real Estate
    'VNQ': {'name': 'Real Estate', 'sector': 'RealEstate'},
    'IYR': {'name': 'Real Estate iShares', 'sector': 'RealEstate'},
    
    # International
    'EEM': {'name': 'Emerging Markets', 'sector': 'International'},
    'EFA': {'name': 'Developed ex-US', 'sector': 'International'},
    'FXI': {'name': 'China Large Cap', 'sector': 'International'},
    'EWJ': {'name': 'Japan', 'sector': 'International'},
    
    # Bonds
    'TLT': {'name': '20-Yr Treasury', 'sector': 'Bonds'},
    'HYG': {'name': 'High Yield Corp', 'sector': 'Bonds'},
    'LQD': {'name': 'Investment Grade', 'sector': 'Bonds'},
    
    # Other Sectors
    'XLI': {'name': 'Industrials', 'sector': 'Industrials'},
    'XLU': {'name': 'Utilities', 'sector': 'Utilities'},
    'XLP': {'name': 'Consumer Staples', 'sector': 'Consumer'},
    'XLY': {'name': 'Consumer Discretionary', 'sector': 'Consumer'},
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
    entry_price = None
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
                position, entry_price = 'long', price
        
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
    
    total_return = (cash / capital - 1) * 100
    equity_series = pd.Series(equity)
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    dd = ((equity_series - equity_series.expanding().max()) / equity_series.expanding().max()).min() * 100
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

print(f"\nHunting across {len(GEM_HUNT_ETFS)} ETFs...\n")

results = []

for symbol, config in GEM_HUNT_ETFS.items():
    try:
        raw_df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=TimeFrame.Day,
            start=START_DATE,
            end=END_DATE,
            feed='sip'
        )
        
        if len(raw_df) > 1000:
            df = raw_df.resample('1D').agg({
                'open':'first','high':'max','low':'min','close':'last','volume':'sum'
            }).dropna()
        else:
            df = raw_df
        
        df['rsi'] = calculate_rsi(df['close'], RSI_PERIOD)
        res = backtest(df, INITIAL_CAPITAL, TRANSACTION_COST_BPS)
        
        results.append({
            'symbol': symbol,
            'name': config['name'],
            'sector': config['sector'],
            **res
        })
        
        status = "💎" if res['sharpe'] > 1.0 else "✅" if res['sharpe'] > 0.7 else "⚠️" if res['sharpe'] > 0.3 else "❌"
        print(f"{status} {symbol:5} ({config['sector']:13}) | Sharpe: {res['sharpe']:5.2f} | Return: {res['return']:+6.1f}% | Trades: {res['trades']:2}")
        
    except Exception as e:
        print(f"❌ {symbol:5} | Error: {str(e)[:30]}")
        results.append({
            'symbol': symbol, 'name': config['name'], 'sector': config['sector'],
            'return': 0, 'bh_return': 0, 'sharpe': 0, 'max_dd': 0, 'trades': 0, 'win_rate': 0
        })

print("\n" + "="*80)
print("GEM HUNTER RESULTS")
print("="*80)

results_df = pd.DataFrame(results)

# Sort by Sharpe
sorted_df = results_df.sort_values('sharpe', ascending=False)

print("\n💎 TOP PERFORMERS (Sharpe > 1.0):")
gems = sorted_df[sorted_df['sharpe'] > 1.0]
if len(gems) > 0:
    print(gems[['symbol', 'name', 'sector', 'sharpe', 'return', 'max_dd', 'trades']].to_string(index=False))
else:
    print("None")

print("\n✅ APPROVED (Sharpe > 0.7):")
approved = sorted_df[(sorted_df['sharpe'] > 0.7) & (sorted_df['sharpe'] <= 1.0)]
if len(approved) > 0:
    print(approved[['symbol', 'name', 'sector', 'sharpe', 'return']].to_string(index=False))
else:
    print("None beyond gems")

print("\n📊 SECTOR SUMMARY:")
sector_summary = results_df.groupby('sector').agg({
    'sharpe': 'mean',
    'return': 'mean'
}).round(2).sort_values('sharpe', ascending=False)
print(sector_summary)

# Save
output_file = Path(__file__).parent / 'gem_hunt_results.csv'
results_df.to_csv(output_file, index=False)
print(f"\n📁 Saved: {output_file}")

print("\n" + "="*80)
print(f"GEMS FOUND: {len(gems)} with Sharpe > 1.0")
print(f"APPROVED:   {len(approved)} with Sharpe 0.7-1.0")
print(f"TOTAL:      {len(gems) + len(approved)} deployable ETFs")
print("="*80)
