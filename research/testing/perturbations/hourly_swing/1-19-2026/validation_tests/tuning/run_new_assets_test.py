"""
Hourly Swing - New Assets Expansion
Tests candidate assets (AMD, META, COIN, PLTR) for Hourly Swing strategy.

Hypothesis: Find 2-3 new assets with Sharpe > 0.5 to diversify portfolio.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("="*80)
print("HOURLY SWING - NEW ASSET EXPANSION")
print("="*80)
print("Candidates: AMD, META, COIN, PLTR")
print("Target: Sharpe > 0.5")

CANDIDATES = ['AMD', 'META', 'COIN', 'PLTR']
START_DATE = '2024-01-01'
END_DATE = '2025-12-31'

# Standard Params (NVDA-style usually works best for momentum)
# Using generic settings from Roadmap: RSI-21, 60/40
RSI_PERIOD = 21
UPPER_BAND = 60
LOWER_BAND = 40

INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0

client = AlpacaDataClient()

def run_backtest(symbol, df):
    # RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Sim
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'
    equity_curve = []
    trades = 0
    
    for i in range(len(df)):
        if i < RSI_PERIOD:
            equity_curve.append(cash)
            continue
            
        row = df.iloc[i]
        price = row['close']
        rsi = row['rsi']
        
        # Entry
        if position == 'flat' and rsi > UPPER_BAND:
            cost = TRANSACTION_COST_BPS / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = 'long'
                trades += 1
        
        # Exit
        elif position == 'long' and rsi < LOWER_BAND:
            cost = TRANSACTION_COST_BPS / 10000
            proceeds = shares * price * (1 - cost)
            cash += proceeds
            shares = 0
            position = 'flat'
            
        equity_curve.append(cash + (shares * price))
        
    # Metrics
    equity_series = pd.Series(equity_curve)
    ret = (equity_series.iloc[-1] / INITIAL_CAPITAL - 1) * 100
    
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252 * 6.5) if returns.std() > 0 else 0
    
    running_max = equity_series.expanding().max()
    dd = (equity_series - running_max) / running_max
    max_dd = dd.min() * 100
    
    return sharpe, ret, max_dd, trades

results = []

for symbol in CANDIDATES:
    print(f"\nProcessing {symbol}...")
    try:
        raw_df = client.fetch_historical_bars(symbol, TimeFrame.Hour, START_DATE, END_DATE, feed='sip')
        df = raw_df
        if len(df) > 10000:
            df = df.resample('1H').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
        
        print(f"  {len(df)} bars")
        sharpe, ret, max_dd, trades = run_backtest(symbol, df)
        
        results.append({
            'symbol': symbol,
            'sharpe': sharpe,
            'return': ret,
            'max_dd': max_dd,
            'trades': trades
        })
        
        status = "✅" if sharpe > 0.5 else "❌"
        print(f"  Sharpe: {sharpe:.2f} {status}")
        print(f"  Return: {ret:.1f}%")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# Summary
print("\n" + "="*80)
print("EXPANSION CANDIDATE RESULTS")
print("="*80)

for r in results:
    status = "✅ PASS" if r['sharpe'] > 0.5 else "❌ FAIL"
    print(f"{r['symbol']}: Sharpe {r['sharpe']:.2f}, Return {r['return']:.1f}% -> {status}")

print("="*80)
