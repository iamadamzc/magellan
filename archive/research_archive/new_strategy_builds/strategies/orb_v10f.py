"""
ORB V10F - No Scaling, Pure Trail
----------------------------------
V10E problem: Scaling reduces position before runners develop

NEW: No scaling. Move to BE at 0.5R, then trail to capture full runners.
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

def calculate_vwap(df):
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['date'] = df.index.date
    df['cumulative_tp_volume'] = df.groupby('date')['tp_volume'].cumsum()
    df['cumulative_volume'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']
    return df

def calculate_atr(df, period=14):
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df

def run_orb_v10f(symbol, start, end):
    """ORB V10F - No scaling, pure trail"""
    
    params = {
        'OR_MINUTES': 10,
        'ENTRY_WINDOW_START': 10,
        'ENTRY_WINDOW_END': 60,
        'VOL_MULT': 1.2,
        'MIN_PRICE': 3.0,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'TRAIL_ATR': 0.3,  # Tight trail
    }
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    or_mask = df['minutes_since_open'] <= params['OR_MINUTES']
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
    entry_time = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    lowest_price = 999999
    moved_to_be = False
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_or_low = df.iloc[i]['or_low']
        current_vwap = df.iloc[i]['vwap']
        minutes_since_open = df.iloc[i]['minutes_since_open']
        volume_spike = df.iloc[i]['volume_spike']
        
        if minutes_since_open <= params['OR_MINUTES']:
            continue
        
        if position is None:
            if minutes_since_open < params['ENTRY_WINDOW_START'] or minutes_since_open > params['ENTRY_WINDOW_END']:
                continue
            
            if (current_price > current_or_high and 
                volume_spike >= params['VOL_MULT'] and 
                current_price >= params['MIN_PRICE']):
                
                position = 1.0
                entry_time = current_time
                entry_price = current_price
                stop_loss = current_or_low
                highest_price = current_price
                lowest_price = current_price
                moved_to_be = False
        
        elif position is not None:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            if current_low < lowest_price:
                lowest_price = current_low
            
            mae = (lowest_price - entry_price) / risk if risk > 0 else 0
            mfe = (highest_price - entry_price) / risk if risk > 0 else 0
            
            # Hard stop
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': -1.0,
                    'type': 'stop',
                    'mae': mae,
                    'mfe': mfe,
                })
                position = None
                continue
            
            # Move to BE at 0.5R
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            # Trailing stop
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP loss
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': current_r,
                    'type': 'vwap_loss',
                    'mae': mae,
                    'mfe': mfe,
                })
                position = None
                continue
            
            # EOD
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                pnl_pct = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': current_r,
                    'type': 'eod',
                    'mae': mae,
                    'mfe': mfe,
                })
                position = None
    
    return trades
