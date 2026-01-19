"""
ORB V4 - With Proper Risk Management
-------------------------------------
FIXES:
1. Proper trailing stop (trails below higher lows, not just breakeven)
2. Pyramiding (1 add allowed after 0.8R profit)
3. Dynamic stop tightening
4. Better R-multiple targets

Expert specs (Chad_G, Dee_S):
- Pyramid: 1 add max, only after net risk reduction
- Trail: Below higher lows OR ATR-based
- Scale: 40% at 1R, 30% at 2R, 30% runner
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

def run_orb_v4(symbol, start, end):
    """ORB V4 - Proper risk management"""
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.5,
        'STOP_ATR': 0.6,
        'MIN_PRICE': 3.0,
        'TRAIL_ATR': 0.8,          # Trail distance in ATR
        'PYRAMID_MIN_R': 0.8,      # Add after 0.8R profit
        'PYRAMID_MAX_ADDS': 1,     # Max 1 add
        'MAX_HOLD_MINUTES': 30,
        'SCALE_1R_PCT': 0.40,
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
    adds_made = 0
    highest_price = 0
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_low = df.iloc[i]['or_low']
        
        # Entry
        if position is None and entry_signal.iloc[i]:
            position = 1.0
            entry_time = current_time
            entry_price = current_price
            stop_loss = current_or_low - (params['STOP_ATR'] * current_atr)
            adds_made = 0
            highest_price = current_price
        
        # Position management
        elif position is not None and position > 0:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Track highest price for trailing
            if current_high > highest_price:
                highest_price = current_high
            
            # Stop loss
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0, 'type': 'stop'})
                position = None
                continue
            
            # Pyramiding (add to winner)
            if (current_r >= params['PYRAMID_MIN_R'] and 
                adds_made < params['PYRAMID_MAX_ADDS'] and 
                position == 1.0):  # Only add to full position
                
                # Add 50% more, but move stop to reduce net risk
                add_size = 0.5
                new_position = position + add_size
                
                # Move stop to breakeven on original position
                stop_loss = entry_price
                
                # Record the add
                adds_made += 1
                position = new_position
                print(f"  → Pyramid add at {current_r:.2f}R, new size: {position:.2f}")
            
            # Scale at 1R
            if current_r >= 1.0 and position >= 1.0:
                scale_amount = min(params['SCALE_1R_PCT'], position)
                pnl_pct = risk / entry_price * 100 * scale_amount
                trades.append({'pnl_pct': pnl_pct, 'r': 1.0, 'type': 'scale_1r'})
                position -= scale_amount
            
            # Scale at 2R
            if current_r >= 2.0 and position >= 0.5:
                scale_amount = min(params['SCALE_2R_PCT'], position)
                pnl_pct = (risk * 2) / entry_price * 100 * scale_amount
                trades.append({'pnl_pct': pnl_pct, 'r': 2.0, 'type': 'scale_2r'})
                position -= scale_amount
            
            # Proper trailing stop (trail below highest price)
            if current_r >= 1.0:
                # Trail at TRAIL_ATR below highest price
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # Time stop
            if time_in_position >= params['MAX_HOLD_MINUTES'] and position > 0:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'time'})
                position = None
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'sharpe': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125  # Friction
    
    # Calculate metrics
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_net'].mean()
    total_pnl = trades_df['pnl_net'].sum()
    sharpe = (avg_pnl / trades_df['pnl_net'].std() * np.sqrt(252)) if trades_df['pnl_net'].std() > 0 else 0
    
    # Count exit types
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
