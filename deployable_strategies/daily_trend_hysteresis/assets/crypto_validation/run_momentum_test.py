"""
Daily Trend - Momentum Stock Validation
Tests strategy on high-momentum stocks that showed strong trends in 2023-2024

Assets: NVDA (AI boom), TSLA (EV momentum), AMD (chip momentum)
Period: 2023-2024 (known bull market for these assets)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("DAILY TREND - MOMENTUM STOCK VALIDATION")
print("="*80)
print("\nTesting on stocks with PROVEN momentum (2023-2024 AI boom)")
print("If these fail, strategy needs major overhaul\n")

# High-momentum stocks from 2023-2024
MOMENTUM_STOCKS = ['NVDA', 'AMD', 'TSLA', 'META']
START = '2023-01-01'
END = '2024-12-31'

# Parameters
RSI_PERIOD = 14
UPPER_BAND = 55
LOWER_BAND = 45

client = AlpacaDataClient()

def backtest(symbol, data):
    """Daily Trend backtest"""
    delta = data['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = data['close'].values
    
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
    
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else 0
    
    running_max = s.expanding().max()
    drawdown = (s - running_max) / running_max
    max_dd = drawdown.min() * 100
    
    return sharpe, ret, max_dd

results = []

for symbol in MOMENTUM_STOCKS:
    print(f"\nTesting {symbol}...")
    
    try:
        data = client.fetch_historical_bars(symbol, TimeFrame.Day, START, END, feed='sip')
        print(f"  ✓ Fetched {len(data)} bars")
        
        sharpe, ret, max_dd = backtest(symbol, data)
        bh_ret = (data.iloc[-1]['close'] / data.iloc[0]['close'] - 1) * 100
        
        results.append({
            'symbol': symbol,
            'sharpe': sharpe,
            'return': ret,
            'bh_return': bh_ret,
            'max_dd': max_dd,
            'alpha': ret - bh_ret
        })
        
        status = "✅" if sharpe > 0.5 else ("⚠️" if sharpe > 0 else "❌")
        print(f"  {status} Sharpe: {sharpe:.2f}, Return: {ret:+.1f}%, B&H: {bh_ret:+.1f}%, Alpha: {ret-bh_ret:+.1f}%")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Summary
print("\n" + "="*80)
print("MOMENTUM STOCK VALIDATION SUMMARY")
print("="*80)

if results:
    avg_sharpe = np.mean([r['sharpe'] for r in results])
    avg_alpha = np.mean([r['alpha'] for r in results])
    
    print(f"\nAverage Sharpe: {avg_sharpe:.2f}")
    print(f"Average Alpha vs B&H: {avg_alpha:+.1f}%")
    
    if avg_sharpe > 0.5:
        print("\n✅ STRATEGY WORKS ON MOMENTUM STOCKS!")
        print("   Recommendation:")
        print("     1. Add momentum screener (Top 20% RS)")
        print("     2. Add weekly trend filter")
        print("     3. Expected Sharpe: 0.7-1.2")
    elif avg_sharpe > 0:
        print("\n⚠️ MARGINAL PERFORMANCE")
        print("   Strategy barely beats buy & hold")
        print("   Needs major enhancements (dual-timeframe, regime filter)")
    else:
        print("\n❌ STRATEGY FAILS EVEN ON MOMENTUM STOCKS")
        print("   Fundamental logic issue")
        print("   Recommendation: Abandon, focus on Hourly Swing")
    
    # Save
    out_file = Path(__file__).parent / 'momentum_validation_results.csv'
    pd.DataFrame(results).to_csv(out_file, index=False)
    print(f"\n✓ Saved to {out_file}")

print("\n" + "="*80)
