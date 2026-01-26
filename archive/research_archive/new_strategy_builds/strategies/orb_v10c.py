"""
ORB V10C - Aggressive Breakout (Minimal Filters)
-------------------------------------------------
V10B diagnostic: ALL trades exited via FTA. Strategy too conservative.

RADICAL SIMPLIFICATION:
- Remove: Pullback requirement ✓ (already gone)
- Remove: VWAP filter (was killing setups)
- Remove: FTA exit (was killing ALL trades)
- Remove: PDH collision filter (too restrictive)
- Keep: Volume 1.2x (relaxed further)
- Keep: Breakeven + scaling exits
- Keep: Hard stop at OR low

This is the "nuclear option" - test if ANY edge exists in pure ORB breakouts.
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

def run_orb_v10c(symbol, start, end):
    """ORB V10C - Aggressive breakout, minimal filters"""
    
    params = {
        'OR_MINUTES': 10,
        'ENTRY_WINDOW_START': 10,
        'ENTRY_WINDOW_END': 60,
        'VOL_MULT': 1.2,            # RELAXED to 1.2x
        'MIN_PRICE': 3.0,
        # REMOVED: PDH_COLLISION_ATR
        # REMOVED: FTA_MINUTES, FTA_THRESHOLD_R
        'SCALE_025R_PCT': 0.25,
        'SCALE_050R_PCT': 0.25,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'TARGET_13R': 1.3,
        'TRAIL_ATR': 0.6,
        'HARD_STOP_ATR': 0.75,
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
    
    # Calculate OR
    or_mask = df['minutes_since_open'] <= params['OR_MINUTES']
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) > 0:
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    # Track trades
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    lowest_price = 999999
    moved_to_be = False
    scaled_025r = False
    scaled_050r = False
    
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
        
        # Entry logic (MINIMAL FILTERS)
        if position is None:
            if minutes_since_open < params['ENTRY_WINDOW_START'] or minutes_since_open > params['ENTRY_WINDOW_END']:
                continue
            
            # ONLY 2 filters: breakout + volume
            breakout = current_price > current_or_high
            volume_ok = volume_spike >= params['VOL_MULT']
            price_ok = current_price >= params['MIN_PRICE']
            
            if breakout and volume_ok and price_ok:
                position = 1.0
                entry_time = current_time
                entry_price = current_price
                stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                highest_price = current_price
                lowest_price = current_price
                moved_to_be = False
                scaled_025r = False
                scaled_050r = False
        
        # Position management (NO FTA)
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            if current_low < lowest_price:
                lowest_price = current_low
            
            mae = (lowest_price - entry_price) / risk if risk > 0 else 0
            mfe = (highest_price - entry_price) / risk if risk > 0 else 0
            time_in_trade = (current_time - entry_time).total_seconds() / 60
            
            # Hard stop
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
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
            
            # Scale 25% @ 0.25R
            if current_r >= 0.25 and not scaled_025r:
                pnl_pct = (risk * 0.25) / entry_price * 100 * params['SCALE_025R_PCT']
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': 0.25,
                    'type': 'scale_025r',
                    'mae': mae,
                    'mfe': mfe,
                })
                position -= params['SCALE_025R_PCT']
                scaled_025r = True
            
            # Scale 25% @ 0.5R + Breakeven
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not scaled_050r:
                pnl_pct = (risk * 0.5) / entry_price * 100 * params['SCALE_050R_PCT']
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': 0.5,
                    'type': 'scale_050r',
                    'mae': mae,
                    'mfe': mfe,
                })
                position -= params['SCALE_050R_PCT']
                stop_loss = entry_price
                moved_to_be = True
                scaled_050r = True
            
            # Target @ 1.3R
            if current_r >= params['TARGET_13R'] and position > 0:
                pnl_pct = (risk * params['TARGET_13R']) / entry_price * 100 * position
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'r': params['TARGET_13R'],
                    'type': 'target_13r',
                    'mae': mae,
                    'mfe': mfe,
                })
                position = None
                continue
            
            # Trailing stop (after moved to BE)
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP loss (after moved to BE)
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
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
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
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

if __name__ == '__main__':
    result = run_orb_v10c('RIOT', '2024-11-01', '2024-11-30')
    print(f"RIOT: {len(result)} trades")
