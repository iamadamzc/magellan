"""
ORB Strategy - Optimized Version
---------------------------------
Based on quant analysis of initial results + expert parameters

KEY CHANGES from V1:
1. Add gap size filter (2-8% minimum) - Gem_Ni spec
2. Add RVOL filter (2.5×) - Dee_S spec  
3. Widen stop to 0.5 ATR (less whipsaw on small caps)
4. Lower volume mult to 1.8× (catch more setups)
5. Extend OR period to 10 min (more stable range)
6. Add minimum OR range filter (avoid tight ranges)

Hypothesis: Current strategy has edge but filters are too strict.
Relaxing slightly should improve win rate while maintaining frequency.
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
    """Calculate VWAP"""
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    
    # Reset cumulative at start of each day
    df['date'] = df.index.date
    df['cumulative_tp_volume'] = df.groupby('date')['tp_volume'].cumsum()
    df['cumulative_volume'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']
    return df

def calculate_atr(df, period=14):
    """Calculate ATR"""
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df

def run_orb_optimized(symbol, start, end, params=None):
    """
    ORB Strategy - Optimized
    
    Entry: OR break + gap + volume + VWAP + RVOL
    Exit: Wider stop, scale at 1R/2R, trail runner
    """
    
    if params is None:
        params = {
            'OR_MINUTES': 10,          # Wider OR (was 5)
            'VOL_MULT': 1.8,           # Lower threshold (was 2.0)
            'STOP_ATR': 0.5,           # Wider stop (was 0.4)
            'MIN_GAP_PCT': 2.0,        # NEW: Minimum gap
            'MAX_GAP_PCT': 15.0,       # NEW: Max gap (avoid halts)
            'MIN_RVOL': 2.5,           # NEW: Relative volume
            'MIN_OR_RANGE_PCT': 0.5,   # NEW: Min OR range
            'TRAIL_ACTIVATE_R': 1.2,   # Earlier trail (was 1.5)
            'MAX_HOLD_MINUTES': 25,    # Longer hold (was 20)
            'SCALE_1R_PCT': 0.40,      # Less aggressive (was 0.45)
            'SCALE_2R_PCT': 0.30,
        }
    
    print(f"Testing {symbol} ({start} to {end})...")
    
    # Load data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    # Time features
    df['date'] = df.index.date
    df['time'] = df.index.time
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    
    # Volume metrics
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate daily metrics
    df['day_open'] = df.groupby('date')['open'].transform('first')
    df['prev_close'] = df.groupby('date')['close'].shift(1).fillna(method='ffill')
    df['gap_pct'] = ((df['day_open'] - df['prev_close']) / df['prev_close'] * 100).fillna(0)
    
    # Calculate OR high/low efficiently
    or_mask = df['minutes_since_open'] <= params['OR_MINUTES']
    df['or_high'] = df[or_mask].groupby('date')['high'].transform('max')
    df['or_low'] = df[or_mask].groupby('date')['low'].transform('min')
    
    # Forward fill OR values for the rest of the day
    df['or_high'] = df.groupby('date')['or_high'].fillna(method='ffill')
    df['or_low'] = df.groupby('date')['or_low'].fillna(method='ffill')
    
    # OR range
    df['or_range_pct'] = ((df['or_high'] - df['or_low']) / df['or_low'] * 100)
    
    # Daily volume (for RVOL)
    df['day_volume'] = df.groupby('date')['volume'].transform('sum')
    df['avg_day_volume'] = df['day_volume'].rolling(20).mean()
    df['rvol'] = df['day_volume'] / df['avg_day_volume']
    
    # Entry conditions
    condition_breakout = df['close'] > df['or_high']
    condition_volume = df['volume_spike'] >= params['VOL_MULT']
    condition_vwap = df['close'] > df['vwap']
    condition_time = df['minutes_since_open'] > params['OR_MINUTES']
    condition_gap = (df['gap_pct'] >= params['MIN_GAP_PCT']) & (df['gap_pct'] <= params['MAX_GAP_PCT'])
    condition_rvol = df['rvol'] >= params['MIN_RVOL']
    condition_or_range = df['or_range_pct'] >= params['MIN_OR_RANGE_PCT']
    
    entry_signal = (condition_breakout & condition_volume & condition_vwap & 
                   condition_time & condition_gap & condition_rvol & condition_or_range)
    
    # Track trades
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
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_low = df.iloc[i]['or_low']
        
        # Entry
        if position is None and entry_signal.iloc[i]:
            position = 1.0
            entry_time = current_time
            entry_price = current_price
            stop_loss = current_or_low - (params['STOP_ATR'] * current_atr)
        
        # Exit management
        elif position is not None and position > 0:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            
            # Calculate R
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Stop loss
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'stop',
                    'r_multiple': -1.0
                })
                position = None
                continue
            
            # Scale at 1R
            if current_r >= 1.0 and position == 1.0:
                scale_pnl = risk / entry_price * 100 * params['SCALE_1R_PCT']
                trades.append({
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_1r',
                    'r_multiple': 1.0
                })
                position -= params['SCALE_1R_PCT']
            
            # Scale at 2R
            if current_r >= 2.0 and position >= 0.6:
                scale_pnl = (risk * 2) / entry_price * 100 * params['SCALE_2R_PCT']
                trades.append({
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_2r',
                    'r_multiple': 2.0
                })
                position -= params['SCALE_2R_PCT']
            
            # Trailing stop
            if current_r >= params['TRAIL_ACTIVATE_R']:
                stop_loss = max(stop_loss, entry_price + (risk * 0.5))
            
            # Time stop
            if time_in_position >= params['MAX_HOLD_MINUTES'] and position > 0:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'time',
                    'r_multiple': current_r
                })
                position = None
    
    # Calculate metrics
    if len(trades) == 0:
        return {
            'symbol': symbol,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'total_pnl': 0,
            'sharpe': 0
        }
    
    trades_df = pd.DataFrame(trades)
    friction_bps = 12.5
    trades_df['pnl_after_friction'] = trades_df['pnl_pct'] - (friction_bps / 100)
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_after_friction'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_after_friction'].mean()
    total_pnl = trades_df['pnl_after_friction'].sum()
    sharpe = (avg_pnl / trades_df['pnl_after_friction'].std() * np.sqrt(252)) if trades_df['pnl_after_friction'].std() > 0 else 0
    
    print(f"✓ {symbol}: {total_trades} trades | Win%: {win_rate:.1f} | Avg: {avg_pnl:+.2f}% | Total: {total_pnl:+.2f}% | Sharpe: {sharpe:.2f}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'total_pnl': total_pnl,
        'sharpe': sharpe
    }
