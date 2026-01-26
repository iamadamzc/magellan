"""
ORB Final - Balanced Optimization
----------------------------------
Analysis: V1 had 285 trades, 42% win rate, -0.15% avg
         V2 had 0 trades (too strict)
         
Strategy: Keep frequency high, improve quality slightly
- Remove gap filter (too restrictive for small caps)
- Keep RVOL but lower to 1.5× (was 2.5×)
- Widen stop to 0.6 ATR (reduce whipsaw)
- Add min price filter ($3+, avoid penny stocks)
- Tighter scaling (take profits faster)
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

def run_orb_final(symbol, start, end):
    """ORB Final - Balanced parameters"""
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.5,           # Lower (was 2.0)
        'STOP_ATR': 0.6,           # Wider (was 0.4)
        'MIN_PRICE': 3.0,          # NEW: Avoid penny stocks
        'TRAIL_ACTIVATE_R': 1.0,   # Earlier (was 1.5)
        'MAX_HOLD_MINUTES': 30,    # Longer (was 20)
        'SCALE_1R_PCT': 0.50,      # More aggressive
        'SCALE_2R_PCT': 0.30,
    }
    
    print(f"Testing {symbol} ({start} to {end})...")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate OR efficiently
    or_mask = df['minutes_since_open'] <= params['OR_MINUTES']
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) > 0:
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    # Entry
    entry_signal = (
        (df['close'] > df['or_high']) &
        (df['volume_spike'] >= params['VOL_MULT']) &
        (df['close'] > df['vwap']) &
        (df['minutes_since_open'] > params['OR_MINUTES']) &
        (df['close'] >= params['MIN_PRICE'])
    )
    
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    position_size = 1.0
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_atr = df.iloc[i]['atr']
        current_or_low = df.iloc[i]['or_low']
        
        if position is None and entry_signal.iloc[i]:
            position = 1.0
            entry_time = current_time
            entry_price = current_price
            stop_loss = current_or_low - (params['STOP_ATR'] * current_atr)
        
        elif position is not None and position > 0:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Stop
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0})
                position = None
                continue
            
            # Scale 1R
            if current_r >= 1.0 and position == 1.0:
                pnl_pct = risk / entry_price * 100 * params['SCALE_1R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 1.0})
                position -= params['SCALE_1R_PCT']
            
            # Scale 2R
            if current_r >= 2.0 and position >= 0.5:
                pnl_pct = (risk * 2) / entry_price * 100 * params['SCALE_2R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 2.0})
                position -= params['SCALE_2R_PCT']
            
            # Trail
            if current_r >= params['TRAIL_ACTIVATE_R']:
                stop_loss = max(stop_loss, entry_price)
            
            # Time
            if time_in_position >= params['MAX_HOLD_MINUTES'] and position > 0:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': current_r})
                position = None
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'sharpe': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125  # Friction
    
    return {
        'symbol': symbol,
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_net'] > 0).sum() / len(trades_df) * 100,
        'avg_pnl': trades_df['pnl_net'].mean(),
        'total_pnl': trades_df['pnl_net'].sum(),
        'sharpe': (trades_df['pnl_net'].mean() / trades_df['pnl_net'].std() * np.sqrt(252)) if trades_df['pnl_net'].std() > 0 else 0
    }
