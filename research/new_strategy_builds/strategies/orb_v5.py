"""
ORB V5 - Expert Consensus Implementation
-----------------------------------------
Based on unanimous recommendations from Chad_G, Dee_S, and Gem_Ni

CRITICAL FIXES (All 3 Experts Agree):
1. ✅ REMOVE time stop (96.7% of exits - killing winners)
2. ✅ Wait for pullback entry (stop chasing breakouts)
3. ✅ Scale earlier at 0.5R (targets too far)
4. ✅ Add VWAP filter (avoid trap breakouts)
5. ✅ Tighter stop (0.4 ATR middle ground)

Expected Impact: +12-21% win rate improvement
Target: 48-52% win rate (from 40.8%)
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

def run_orb_v5(symbol, start, end):
    """
    ORB V5 - Expert Consensus
    
    Key Changes from V4:
    - NO time stop (let winners run!)
    - Pullback entry (wait for retest)
    - Scale at 0.5R and 1.0R (not 1R and 2R)
    - VWAP filter (only long above VWAP)
    - Tighter stop (0.4 ATR)
    - No pyramiding (simplify)
    """
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,           # Tighter (Dee_S)
        'STOP_ATR': 0.4,           # Middle ground (0.35-0.5)
        'PULLBACK_ATR': 0.15,      # Wait for pullback (Chad_G)
        'MIN_CONSOLIDATION': 2,    # Bars above OR high
        'TRAIL_ATR': 0.6,          # Tighter trail (Dee_S)
        'SCALE_05R_PCT': 0.50,     # 50% at 0.5R
        'SCALE_10R_PCT': 0.30,     # 30% at 1.0R
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
    
    # Track breakouts and pullbacks
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    df['above_vwap'] = df['close'] > df['vwap']
    
    # Entry signal: Breakout happened, then pullback to OR high, then reclaim
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    position_size = 1.0
    highest_price = 0
    
    # State tracking
    breakout_seen = False
    breakout_high = 0
    
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
        
        # After OR period
        if df.iloc[i]['minutes_since_open'] <= params['OR_MINUTES']:
            continue
        
        # Entry logic: Pullback entry
        if position is None:
            # Detect breakout
            if df.iloc[i]['breakout'] and not breakout_seen:
                breakout_seen = True
                breakout_high = current_high
            
            # Wait for pullback after breakout
            if breakout_seen:
                # Check if price pulled back to OR high ± PULLBACK_ATR
                pullback_zone_low = current_or_high - (params['PULLBACK_ATR'] * current_atr)
                pullback_zone_high = current_or_high + (params['PULLBACK_ATR'] * current_atr)
                
                in_pullback_zone = (current_low <= pullback_zone_high) and (current_high >= pullback_zone_low)
                
                # Entry: Reclaim above OR high with volume, above VWAP
                if (in_pullback_zone and 
                    current_price > current_or_high and
                    current_price > current_vwap and
                    df.iloc[i]['volume_spike'] >= params['VOL_MULT'] and
                    current_price >= params['MIN_PRICE']):
                    
                    # Enter
                    position = 1.0
                    entry_time = current_time
                    entry_price = current_price
                    stop_loss = current_or_low - (params['STOP_ATR'] * current_atr)
                    highest_price = current_price
                    breakout_seen = False  # Reset for next trade
        
        # Position management
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Track highest
            if current_high > highest_price:
                highest_price = current_high
            
            # Stop loss
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0, 'type': 'stop'})
                position = None
                continue
            
            # Scale at 0.5R (NEW!)
            if current_r >= 0.5 and position == 1.0:
                pnl_pct = (risk * 0.5) / entry_price * 100 * params['SCALE_05R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 0.5, 'type': 'scale_05r'})
                position -= params['SCALE_05R_PCT']
            
            # Scale at 1.0R
            if current_r >= 1.0 and position >= 0.5:
                pnl_pct = risk / entry_price * 100 * params['SCALE_10R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 1.0, 'type': 'scale_10r'})
                position -= params['SCALE_10R_PCT']
            
            # Trailing stop (start at 0.5R)
            if current_r >= 0.5:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # NO TIME STOP! Let winners run!
            # Only exit via stop loss or end of day
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                # End of day exit
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'eod'})
                    position = None
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'sharpe': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125  # Friction
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_net'].mean()
    total_pnl = trades_df['pnl_net'].sum()
    sharpe = (avg_pnl / trades_df['pnl_net'].std() * np.sqrt(252)) if trades_df['pnl_net'].std() > 0 else 0
    
    # Exit breakdown
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
