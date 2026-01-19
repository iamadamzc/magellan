"""
ORB V7 - Gem_Ni's Barbell Stack (No FTA)
-----------------------------------------
Based on Gem_Ni's analysis: "Get the baseline. No corrupted data."

KEY CHANGES FROM V6:
1. ✅ REMOVE FTA (get natural drift)
2. ✅ NO scaling at 0.25R (friction trap - Gem's critical insight)
3. ✅ Barbell scaling:
   - @ 0.5R: Move stop to breakeven (zero risk)
   - @ 1.3R: Scale 50% (bank the win)
   - Trail 50% remainder (catch the trend)

HYPOTHESIS:
- Win rate: 50-55% (natural, not forced)
- Avg P&L: -0.05% to +0.05% (near breakeven or profitable)
- We'll see what the strategy WANTS to do

Gem's Rule: "Never scale before 0.5R minimum, ideally 1.0R"
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

def run_orb_v7(symbol, start, end):
    """
    ORB V7 - Barbell Stack (No FTA)
    
    The "Control Group" test to see natural strategy behavior
    """
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'BREAKEVEN_TRIGGER_R': 0.5,    # Move to BE at 0.5R
        'SCALE_13R_PCT': 0.50,         # Take 50% at 1.3R
        'TRAIL_ATR': 0.6,              # Trail remainder
        'MIN_PRICE': 3.0,
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
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    df['above_vwap'] = df['close'] > df['vwap']
    
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    position_size = 1.0
    highest_price = 0
    breakout_seen = False
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
        
        if df.iloc[i]['minutes_since_open'] <= params['OR_MINUTES']:
            continue
        
        # Entry (pullback entry from V5)
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
                    entry_time = current_time
                    entry_price = current_price
                    stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                    highest_price = current_price
                    breakout_seen = False
                    moved_to_be = False
        
        # Position management
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
            
            # BREAKEVEN TRIGGER @ 0.5R (Gem's Barbell)
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price  # Move to breakeven
                moved_to_be = True
            
            # SCALE @ 1.3R (Bank the win)
            if current_r >= 1.3 and position == 1.0:
                pnl_pct = (risk * 1.3) / entry_price * 100 * params['SCALE_13R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 1.3, 'type': 'scale_13r'})
                position -= params['SCALE_13R_PCT']
            
            # TRAILING STOP (after breakeven)
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP-LOSS SOFT STOP (after moved to BE)
            if moved_to_be and current_price < current_vwap:
                # Exit if VWAP lost
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'vwap_loss'})
                position = None
                continue
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'eod'})
                    position = None
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'sharpe': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_net'].mean()
    total_pnl = trades_df['pnl_net'].sum()
    sharpe = (avg_pnl / trades_df['pnl_net'].std() * np.sqrt(252)) if trades_df['pnl_net'].std() > 0 else 0
    
    exit_counts = trades_df['type'].value_counts().to_dict()
    
    print(f"✓ {symbol}: {total_trades} trades | {win_rate:.1f}% win | {avg_pnl:+.3f}% avg | {total_pnl:+.2f}% total")
    print(f"  Exits: {exit_counts}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'total_pnl': total_pnl,
        'sharpe': sharpe,
        'exit_counts': exit_counts
    }
