"""
ORB V19 FUTURES - Futures-Specific Session Times
-------------------------------------------------
Same as V19 but handles futures RTH (Regular Trading Hours)
Futures RTH: 9:00 AM - 5:00 PM ET (varies by contract)

For most futures:
- OR: 9:00-9:10 AM (first 10 minutes of RTH)
- Entry window: 9:10-10:00 AM
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

def run_orb_v19_futures(symbol, start, end, rth_open_hour=9, rth_open_min=0):
    """
    V19 for futures - adjusted for RTH session times
    
    Args:
        rth_open_hour: RTH open hour (default 9 for 9 AM)
        rth_open_min: RTH open minute (default 0)
    """
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'SCALE_13R_PCT': 0.50,
        'TRAIL_ATR': 0.6,
        'MIN_PRICE': 0.01,  # Lower for futures
        'ENTRY_WINDOW_START': 10,   # 10 min after RTH open
        'ENTRY_WINDOW_END': 60,      # 60 min after RTH open
        'RTH_OPEN_HOUR': rth_open_hour,
        'RTH_OPEN_MIN': rth_open_min,
    }
    
    print(f"\nTesting {symbol} - V19 FUTURES (RTH {rth_open_hour}:{rth_open_min:02d}) [{start} to {end}]")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        print(f"❌ No data")
        return None
    
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # Calculate minutes since RTH open
    df['minutes_since_rth'] = (df['hour'] - params['RTH_OPEN_HOUR']) * 60 + (df['minute'] - params['RTH_OPEN_MIN'])
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Filter for RTH only (9:00 AM - 5:00 PM)
    rth_mask = (df['hour'] >= params['RTH_OPEN_HOUR']) & (df['hour'] < 17)
    df = df[rth_mask].copy()
    
    if len(df) == 0:
        print(f"❌ No RTH data")
        return None
    
    # Calculate OR
    or_mask = df['minutes_since_rth'] <= params['OR_MINUTES']
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) >= 5:  # Need at least 5 bars for valid OR
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    df['above_vwap'] = df['close'] > df['vwap']
    
    trades = []
    position = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    breakout_seen = False
    moved_to_be = False
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_or_low = df.iloc[i]['or_low']
        current_vwap = df.iloc[i]['vwap']
        minutes_since_rth = df.iloc[i]['minutes_since_rth']
        
        if minutes_since_rth <= params['OR_MINUTES']:
            continue
        
        # Entry with time window
        if position is None:
            if minutes_since_rth < params['ENTRY_WINDOW_START'] or minutes_since_rth > params['ENTRY_WINDOW_END']:
                breakout_seen = False
                continue
            
            if df.iloc[i]['breakout'] and not breakout_seen:
                breakout_seen = True
            
            if breakout_seen:
                pullback_zone_low = current_or_high - (params['PULLBACK_ATR'] * current_atr)
                pullback_zone_high = current_or_high + (params['PULLBACK_ATR'] * current_atr)
                in_pullback_zone = (current_low <= pullback_zone_high) and (current_high >= pullback_zone_low)
                
                if (in_pullback_zone and 
                    current_price > current_or_high and
                    current_price > current_vwap and
                    df.iloc[i]['volume_spike'] >= params['VOL_MULT'] and
                    current_price >= params['MIN_PRICE']):
                    
                    position = 1.0
                    entry_price = current_price
                    stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                    highest_price = current_price
                    breakout_seen = False
                    moved_to_be = False
        
        # Position management (same as V7)
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0, 'type': 'stop'})
                position = None
                continue
            
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            if current_r >= 1.3 and position == 1.0:
                pnl_pct = (risk * 1.3) / entry_price * 100 * params['SCALE_13R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 1.3, 'type': 'scale_13r'})
                position -= params['SCALE_13R_PCT']
            
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'vwap_loss'})
                position = None
                continue
            
            # EOD
            if df.iloc[i]['hour'] >= 16 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'eod'})
                    position = None
    
    if len(trades) == 0:
        print(f"0 trades")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    total_pnl = trades_df['pnl_net'].sum()
    
    print(f"✓ {total_trades} trades | {win_rate:.1f}% win | {total_pnl:+.2f}% total")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl
    }
