"""
Simple QQQ optimization - debug version
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')
FRICTION_BPS = 1.0

def fetch_1min_data(symbol, date):
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def test_qqq(df, profit_target=0.375, stop_loss=0.15):
    """Simplified test"""
    if len(df) < 30:
        return []
    
    df['high_roll'] = df['high'].rolling(10).max()
    df['low_roll'] = df['low'].rolling(10).min()
    df['time'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].dt.hour
    
    trades = []
    position = None
    
    for i in range(15, len(df)):
        if position:
            pnl_pct = (df.loc[i, 'close'] - position['entry_price']) / position['entry_price'] * 100
            if position['type'] == 'short':
                pnl_pct = -pnl_pct
            
            if pnl_pct >= profit_target or pnl_pct <= -stop_loss or (i - position['entry_idx']) >= 15:
                pnl_pct -= FRICTION_BPS / 100
                trades.append({'pnl_pct': pnl_pct, 'win': pnl_pct > 0})
                position = None
        
        if not position and not (12 <= df.loc[i, 'hour'] < 14):
            if i >= 3:
                recent_high = df.loc[i-3:i-1, 'high'].max()
                if recent_high > df.loc[i-1, 'high_roll'] and df.loc[i, 'close'] < df.loc[i-1, 'high_roll']:
                    position = {'type': 'short', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
                    continue
                
                recent_low = df.loc[i-3:i-1, 'low'].min()
                if recent_low < df.loc[i-1, 'low_roll'] and df.loc[i, 'close'] > df.loc[i-1, 'low_roll']:
                    position = {'type': 'long', 'entry_price': df.loc[i, 'close'], 'entry_idx': i}
    
    return trades

# Load data
dates = ['2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-08',
         '2024-01-09', '2024-01-10', '2024-01-11', '2024-01-12', '2024-01-16',
         '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-22', '2024-01-23',
         '2024-01-24', '2024-01-25', '2024-01-26', '2024-01-29', '2024-01-30']

print("Loading QQQ data...")
dfs = []
for date in dates:
    bars = fetch_1min_data('QQQ', date)
    if len(bars) >= 50:
        dfs.append(pd.DataFrame(bars).sort_values('date').reset_index(drop=True))

print(f"Loaded {len(dfs)} days\n")

# Test different targets
for target in [0.30, 0.35, 0.40, 0.45, 0.50]:
    all_trades = []
    for df in dfs:
        trades = test_qqq(df.copy(), profit_target=target, stop_loss=0.15)
        all_trades.extend(trades)
    
    if all_trades and len(all_trades) >= 5:
        pnls = [t['pnl_pct'] for t in all_trades]
        wins = [t for t in all_trades if t['win']]
        
        avg_pnl = np.mean(pnls)
        std_pnl = np.std(pnls)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / len(dfs))) if std_pnl > 0 else 0
        win_rate = len(wins) / len(all_trades) * 100
        
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in [t for t in all_trades if not t['win']]]) if len(all_trades) > len(wins) else 0
        
        print(f"Target {target:.2f}%: {len(all_trades)} trades, Win% {win_rate:.1f}%, Sharpe {sharpe:.2f}")
        print(f"  Avg Win: {avg_win:.3f}%, Avg Loss: {avg_loss:.3f}%\n")
