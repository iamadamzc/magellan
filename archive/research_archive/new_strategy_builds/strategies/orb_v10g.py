"""
ORB V10G - FINAL TEST: Does ANY edge exist?
--------------------------------------------
Absolute simplest: Breakout + volume, stop at OR low, exit at 1R or EOD.
No scaling, no VWAP, no trailing. Just test if basic ORB has ANY edge.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

def calculate_atr(df, period=14):
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df

def run_orb_v10g(symbol, start, end):
    """ORB V10G - Absolute simplest test"""
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate OR
    or_mask = df['minutes_since_open'] <= 10
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) > 0:
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    trades = []
    position = None
    entry_price = None
    stop_loss = None
    target = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['or_high']):
            continue
        
        mins = df.iloc[i]['minutes_since_open']
        if mins <= 10:
            continue
        
        if position is None:
            if mins < 10 or mins > 60:
                continue
            
            # ENTRY: Breakout + volume
            if (df.iloc[i]['close'] > df.iloc[i]['or_high'] and 
                df.iloc[i]['volume_spike'] >= 1.2):
                
                position = 1.0
                entry_price = df.iloc[i]['close']
                stop_loss = df.iloc[i]['or_low']
                risk = entry_price - stop_loss
                target = entry_price + risk  # 1R target
        
        elif position is not None:
            # EXIT: Stop or Target or EOD
            if df.iloc[i]['low'] <= stop_loss:
                pnl = (stop_loss - entry_price) / entry_price * 100
                trades.append({'symbol': symbol, 'pnl_pct': pnl, 'type': 'stop'})
                position = None
            elif df.iloc[i]['high'] >= target:
                pnl = (target - entry_price) / entry_price * 100
                trades.append({'symbol': symbol, 'pnl_pct': pnl, 'type': 'target'})
                position = None
            elif df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                pnl = (df.iloc[i]['close'] - entry_price) / entry_price * 100
                trades.append({'symbol': symbol, 'pnl_pct': pnl, 'type': 'eod'})
                position = None
    
    return trades
