"""
ORB V14 "CLOSER TARGETS" - Realistic Profit Taking
---------------------------------------------------
Based on V13b failure analysis: Profit targets at 1.2R/2.0R are too far.
RIOT doesn't move that far before reversing.

KEY CHANGES FROM V7:
1. Closer profit targets: 0.7R (30%), 1.3R (30%), trail 40%
2. Delay BE to 0.7R (from 0.5R) - give more room
3. Keep VWAP exit DISABLED (it wasn't triggering anyway)
4. Widen trail slightly: 0.7 ATR (from 0.6)

HYPOTHESIS: Most RIOT moves are 0.7R-1.5R, not 2.0R+
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

def run_orb_v14_closer_targets(symbol, start, end):
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'MIN_PRICE': 3.0,
        
        # NEW: Closer targets
        'BREAKEVEN_TRIGGER_R': 0.7,  # Was 0.5 in V7
        'PROFIT_TARGET_1': 0.7,      # Take 30% early
        'PROFIT_TARGET_1_SIZE': 0.30,
        'PROFIT_TARGET_2': 1.3,      # Keep V7's 1.3R
        'PROFIT_TARGET_2_SIZE': 0.30,
        'TRAIL_ATR': 0.7,            # Slightly wider
    }
    
    print(f"\nTesting {symbol} - V14 CLOSER TARGETS ({start} to {end})")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        return None
    
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
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    df['above_vwap'] = df['close'] > df['vwap']
    
    trades = []
    position = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    breakout_seen = False
    moved_to_be = False
    scaled_at_07r = False
    scaled_at_13r = False
    
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
        
        if df.iloc[i]['minutes_since_open'] <= params['OR_MINUTES']:
            continue
        
        if position is None:
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
                    scaled_at_07r = False
                    scaled_at_13r = False
        
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            # HARD STOP
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0, 'type': 'stop'})
                position = None
                continue
            
            # SCALE #1 @ 0.7R (NEW - earlier than V7)
            if current_r >= params['PROFIT_TARGET_1'] and not scaled_at_07r:
                pnl_pct = (risk * params['PROFIT_TARGET_1']) / entry_price * 100 * params['PROFIT_TARGET_1_SIZE']
                trades.append({'pnl_pct': pnl_pct, 'r': params['PROFIT_TARGET_1'], 'type': 'scale_07r'})
                position -= params['PROFIT_TARGET_1_SIZE']
                scaled_at_07r = True
            
            # BREAKEVEN @ 0.7R (after first scale)
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            # SCALE #2 @ 1.3R (V7 level)
            if current_r >= params['PROFIT_TARGET_2'] and not scaled_at_13r:
                pnl_pct = (risk * params['PROFIT_TARGET_2']) / entry_price * 100 * params['PROFIT_TARGET_2_SIZE']
                trades.append({'pnl_pct': pnl_pct, 'r': params['PROFIT_TARGET_2'], 'type': 'scale_13r'})
                position -= params['PROFIT_TARGET_2_SIZE']
                scaled_at_13r = True
            
            # TRAILING STOP (wider)
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # EOD
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'eod'})
                    position = None
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    total_pnl = trades_df['pnl_net'].sum()
    
    exit_counts = trades_df['type'].value_counts().to_dict()
    
    print(f"✓ {total_trades} trades | {win_rate:.1f}% win | {total_pnl:+.2f}% total")
    print(f"  Exits: {exit_counts}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'exit_counts': exit_counts
    }
