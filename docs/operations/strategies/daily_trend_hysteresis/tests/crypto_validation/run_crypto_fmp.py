"""
Daily Trend - Crypto Test via FMP
Tests BTC and ETH using FMP's crypto historical data API

This is the CRITICAL test to validate if Daily Trend logic works on pure momentum assets.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import requests
import os

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

print("="*80)
print("DAILY TREND - CRYPTO VALIDATION (FMP)")
print("="*80)
print("\nTesting BTC and ETH (2020-2025)")
print("If Sharpe > 1.0: Strategy is SALVAGEABLE")
print("If Sharpe < 0.5: Strategy logic is FLAWED\n")

# FMP API
FMP_API_KEY = os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    print("❌ FMP_API_KEY not found in environment")
    exit(1)

# Crypto symbols (FMP format)
CRYPTO_SYMBOLS = ['BTCUSD', 'ETHUSD']

# Strategy parameters
RSI_PERIOD = 14
UPPER_BAND = 55
LOWER_BAND = 45

def fetch_crypto_data(symbol):
    """Fetch daily crypto data from FMP"""
    # Correct endpoint - returns a LIST not a dict
    url = f"https://financialmodelingprep.com/stable/historical-price-eod/full"
    params = {
        'symbol': symbol,
        'apikey': FMP_API_KEY
    }
    
    print(f"  Fetching {symbol}...")
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    # FMP returns a LIST of daily bars
    if not data or len(data) == 0:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()
    
    # Filter to 2020-2025
    df = df[(df.index >= '2020-01-01') & (df.index <= '2025-12-31')]
    
    return df

def backtest_crypto(symbol, data):
    """Run Daily Trend backtest"""
    # Calculate RSI
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = data['close'].values
    
    # Simulation
    cash, shares, position = 10000.0, 0, 0
    equity = []
    
    for i in range(len(data)):
        if i < RSI_PERIOD:
            equity.append(cash)
            continue
            
        cur_rsi = rsi_vals[i]
        price = prices[i]
        
        if position == 0 and cur_rsi > UPPER_BAND:
            shares = cash / price
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < LOWER_BAND:
            cash = shares * price
            shares = 0
            position = 0
            
        equity.append(cash + (shares * price))
        
    equity = np.array(equity)
    ret = (equity[-1] / 10000 - 1) * 100
    
    # Sharpe
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * np.sqrt(365)) if r.std() > 0 else 0
    
    # Max DD
    running_max = s.expanding().max()
    drawdown = (s - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    return sharpe, ret, max_dd

# Test each crypto
results = []

for symbol in CRYPTO_SYMBOLS:
    try:
        data = fetch_crypto_data(symbol)
        if data is None or len(data) == 0:
            print(f"  ❌ No data for {symbol}")
            continue
        
        print(f"  ✓ Fetched {len(data)} daily bars")
        
        sharpe, ret, max_dd = backtest_crypto(symbol, data)
        bh_ret = (data.iloc[-1]['close'] / data.iloc[0]['close'] - 1) * 100
        
        results.append({
            'symbol': symbol,
            'sharpe': sharpe,
            'return': ret,
            'bh_return': bh_ret,
            'max_dd': max_dd,
            'alpha': ret - bh_ret
        })
        
        status = "✅" if sharpe > 1.0 else ("⚠️" if sharpe > 0.5 else "❌")
        print(f"\n  {symbol} {status}")
        print(f"    Sharpe: {sharpe:.2f}")
        print(f"    Return: {ret:+.1f}%")
        print(f"    Buy & Hold: {bh_ret:+.1f}%")
        print(f"    Alpha: {ret-bh_ret:+.1f}%")
        print(f"    Max DD: {max_dd:.1f}%")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Summary
print("\n" + "="*80)
print("CRYPTO VALIDATION VERDICT")
print("="*80)

if results:
    avg_sharpe = np.mean([r['sharpe'] for r in results])
    avg_alpha = np.mean([r['alpha'] for r in results])
    
    print(f"\nAverage Sharpe: {avg_sharpe:.2f}")
    print(f"Average Alpha: {avg_alpha:+.1f}%")
    
    if avg_sharpe > 1.0:
        print("\n✅ STRATEGY IS SALVAGEABLE!")
        print("   Daily Trend logic WORKS on pure momentum assets")
        print("\n   Next Steps:")
        print("     1. Deploy on BTC/ETH")
        print("     2. Add momentum stock screener (Top 20% RS)")
        print("     3. Add weekly trend filter")
        print("     4. Expected Sharpe: 1.0-1.5")
    elif avg_sharpe > 0.5:
        print("\n⚠️ STRATEGY IS MARGINAL")
        print("   Works but needs enhancements")
        print("   Add dual-timeframe + regime filters")
    else:
        print("\n❌ STRATEGY LOGIC IS FLAWED")
        print("   Even pure momentum assets don't work")
        print("   Recommendation: Abandon Daily Trend")
    
    # Save
    out_file = Path(__file__).parent / 'crypto_fmp_results.csv'
    pd.DataFrame(results).to_csv(out_file, index=False)
    print(f"\n✓ Saved to {out_file}")
else:
    print("\n❌ No results - data fetch failed")

print("\n" + "="*80)
