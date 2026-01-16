"""
Hourly Swing - AMZN Tuning (ATR Filter)
Tests AMZN with an ATR Volatility Filter to improve performance.

Hypothesis: Only trade AMZN when ATR > 2%.
Expected Improvement: Sharpe 0.36 -> 0.55-0.75
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
print("AMZN TUNING - ATR FILTER TEST")
print("="*80)
print("Hypothesis: Filter low volatility periods (ATR < 2%)")
print("Target: Sharpe > 0.55")

# Params
SYMBOL = 'AMZN'
START_DATE = '2024-01-01'
END_DATE = '2025-12-31'
RSI_PERIOD = 21   # As per roadmap/backtest defaults for "Mean Reversion/Swing"
UPPER_BAND = 60
LOWER_BAND = 40
ATR_PERIOD = 14
ATR_THRESHOLD_PCT = 2.0

INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0

client = AlpacaDataClient()

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close'].shift(1)
    
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def run_backtest(df, use_filter=False):
    # RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ATR
    df['atr'] = calculate_atr(df, ATR_PERIOD)
    df['atr_pct'] = (df['atr'] / df['close']) * 100
    
    # Sim
    cash = INITIAL_CAPITAL
    shares = 0
    position = 'flat'
    equity_curve = []
    trades = 0
    
    for i in range(len(df)):
        if i < max(RSI_PERIOD, ATR_PERIOD):
            equity_curve.append(cash)
            continue
            
        row = df.iloc[i]
        price = row['close']
        rsi = row['rsi']
        atr_pct = row['atr_pct']
        
        # Filter Logic
        is_volatile = True
        if use_filter:
            if atr_pct < ATR_THRESHOLD_PCT:
                is_volatile = False
        
        # Entry
        if position == 'flat' and rsi > UPPER_BAND and is_volatile:
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

# 1. Fetch Data
print(f"\nFetching {SYMBOL} data...")
try:
    raw_df = client.fetch_historical_bars(SYMBOL, TimeFrame.Hour, START_DATE, END_DATE, feed='sip')
    df = raw_df
    # Simple resample check
    if len(df) > 10000:
        print("  Resampling to hourly...")
        df = df.resample('1H').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    print(f"  {len(df)} hourly bars")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# 2. Baseline Test
print("\n--- BASELINE (No Filter) ---")
b_sharpe, b_ret, b_dd, b_trades = run_backtest(df, use_filter=False)
print(f"Sharpe: {b_sharpe:.2f}")
print(f"Return: {b_ret:.1f}%")
print(f"Max DD: {b_dd:.1f}%")
print(f"Trades: {b_trades}")

# 3. Filtered Test
print("\n--- TUNED (ATR > 2%) ---")
t_sharpe, t_ret, t_dd, t_trades = run_backtest(df, use_filter=True)
print(f"Sharpe: {t_sharpe:.2f}")
print(f"Return: {t_ret:.1f}%")
print(f"Max DD: {t_dd:.1f}%")
print(f"Trades: {t_trades}")

# Verdict
print("\n" + "="*80)
if t_sharpe > 0.55:
    print(f"✅ SUCCESS: AMZN Tuned Sharpe {t_sharpe:.2f} > 0.55")
    print("   Recommendation: Keep AMZN with ATR Filter")
else:
    print(f"❌ FAILURE: AMZN Tuned Sharpe {t_sharpe:.2f} < 0.55")
    print("   Recommendation: Drop AMZN")
print("="*80)
