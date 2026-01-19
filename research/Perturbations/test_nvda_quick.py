"""Quick test of NVDA with split handling"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
import pandas as pd
import numpy as np

# Test config
config = {"rsi_period": 28, "upper_band": 58, "lower_band": 42}
friction_bps = 15

# Fetch post-split data
df = cache.get_or_fetch_equity('NVDA', '1day', '2024-06-10', '2026-01-18')

print(f"NVDA Post-Split Test")
print(f"Bars: {len(df)}")
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Price: ${df['close'].iloc[0]:.2f} → ${df['close'].iloc[-1]:.2f}")
print(f"Buy-hold: {(df['close'].iloc[-1]/df['close'].iloc[0]-1)*100:+.2f}%")

# Calculate RSI
delta = df['close'].diff()
gains = delta.where(delta > 0, 0.0)
losses = (-delta).where(delta < 0, 0.0)
avg_gain = gains.ewm(span=config['rsi_period'], adjust=False).mean()
avg_loss = losses.ewm(span=config['rsi_period'], adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, np.inf)
rsi = 100 - (100 / (1 + rs))
rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
df['rsi'] = rsi

# Generate signals
position = 0
signals = []

for i in range(len(df)):
    rsi_val = df['rsi'].iloc[i]
    
    if pd.isna(rsi_val):
        signals.append(position)
        continue
    
    if position == 0:
        if rsi_val > config['upper_band']:
            position = 1
    elif position == 1:
        if rsi_val < config['lower_band']:
            position = 0
    
    signals.append(position)

df['signal'] = signals
df['returns'] = df['close'].pct_change()
df['strategy_returns'] = df['signal'].shift(1) * df['returns']

trades = (df['signal'].diff() != 0).sum()
friction_cost = trades * (friction_bps / 10000)
total_return = (1 + df['strategy_returns']).prod() - 1 - friction_cost

print(f"\nStrategy Test (15 bps friction):")
print(f"Trades: {trades}")
print(f"Friction cost: {friction_cost*100:.2f}%")
print(f"Net return: {total_return*100:+.2f}%")
print(f"Status: {'✅ PASS' if total_return > 0 else '❌ FAIL'}")
