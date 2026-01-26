"""
VWAP Reclaim V2 - Expert-Corrected Implementation
--------------------------------------------------
Based on red team analysis (Chad_G, Dee_S, Gem_Ni, Marina_G)

KEY FIXES from V1:
1. Stock must be UP 15-20% on day (not just any VWAP cross)
2. Volume confirmation on BOTH flush AND reclaim
3. Absorption wick requirement (35-45% of candle)
4. Trend filter (no fading in strong downtrends)
5. Time-of-day adjustments
6. Proper scaling out (40% at 1R, 30% at 2R, 30% runner)

Core Thesis (from experts):
"VWAP acts as liquidity magnet. Flushes below VWAP in STRONG names 
represent forced selling, not trend failure. Reclaim = smart money accumulation."
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
    df['cumulative_tp_volume'] = df['tp_volume'].cumsum()
    df['cumulative_volume'] = df['volume'].cumsum()
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

def run_backtest_v2(symbol, start, end, params=None):
    """
    VWAP Reclaim V2 - Expert-corrected implementation
    
    Entry Requirements (ALL must be true):
    1. Stock up 15-20% on day (MIN_DAY_CHANGE_PCT)
    2. Flush below VWAP (0.8-1.2 ATR deviation)
    3. Absorption wick (35-45% of candle)
    4. Volume spike on flush (1.4-1.8× average)
    5. Reclaim VWAP with volume (1.4-1.8× average)
    6. Hold above VWAP for 1-2 bars
    
    Exit:
    - Stop: Below flush low - 0.45 ATR
    - TP1 (40%): 1R
    - TP2 (30%): 2R
    - Runner (30%): Trail at VWAP
    - Time: 30 min (25 min after 14:30)
    """
    
    if params is None:
        params = {
            'MIN_DAY_CHANGE_PCT': 15.0,      # Expert: 15-20%
            'FLUSH_DEV_ATR': 1.0,             # Expert: 0.8-1.2
            'WICK_RATIO_MIN': 0.40,           # Expert: 0.35-0.45
            'FLUSH_VOL_MULT': 1.6,            # Expert: 1.4-1.8
            'RECLAIM_VOL_MULT': 1.6,          # Expert: 1.4-1.8 (NEW!)
            'STOP_ATR': 0.45,                 # Expert: 0.35-0.6
            'HOLD_BARS': 2,                   # Expert: 1-3
            'MAX_HOLD_MINUTES': 30,           # Expert: 25-35
            'SCALE_1R_PCT': 0.40,             # Expert: 40-50%
            'SCALE_2R_PCT': 0.30,             # Expert: 25-35%
        }
    
    print(f"Testing {symbol} ({start} to {end})...")
    
    # Load data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    # Calculate features
    df['date'] = df.index.date
    df['time'] = df.index.time
    df['prev_day_close'] = df.groupby('date')['close'].transform('first').shift(1)
    df['day_change_pct'] = ((df['close'] - df['prev_day_close']) / df['prev_day_close'] * 100)
    
    # Candle metrics
    df['candle_range'] = df['high'] - df['low']
    df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    
    # Volume metrics
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Flush detection
    df['flush_deviation'] = (df['vwap'] - df['low']) / df['atr']
    
    # Entry conditions
    # 1. Stock up on day (CRITICAL!)
    condition_up = df['day_change_pct'] >= params['MIN_DAY_CHANGE_PCT']
    
    # 2. Flush below VWAP with volume
    condition_flush = (df['flush_deviation'] >= params['FLUSH_DEV_ATR']) & \
                     (df['volume_spike'] >= params['FLUSH_VOL_MULT'])
    
    # 3. Absorption wick
    condition_wick = df['wick_ratio'] >= params['WICK_RATIO_MIN']
    
    # 4. Reclaim VWAP with volume (NEW!)
    df['above_vwap'] = (df['close'] > df['vwap']).astype(int)
    df['reclaim'] = (df['above_vwap'] == 1) & (df['above_vwap'].shift(1) == 0)
    condition_reclaim_vol = df['reclaim'] & (df['volume_spike'] >= params['RECLAIM_VOL_MULT'])
    
    # 5. Hold above VWAP
    df['bars_above_vwap'] = df['above_vwap'].rolling(params['HOLD_BARS']).sum()
    condition_hold = df['bars_above_vwap'] >= params['HOLD_BARS']
    
    # 6. Trend filter (NEW!) - Don't fade in strong downtrends
    condition_trend = df['day_change_pct'] > -3.0  # Not down >3% on day
    
    # Combined entry (must have seen flush recently)
    df['flush_signal'] = condition_flush & condition_wick
    df['flush_recent'] = df['flush_signal'].rolling(10).max()  # Flush in last 10 bars
    
    entry_signal = (condition_up & df['flush_recent'] & condition_reclaim_vol & 
                   condition_hold & condition_trend)
    
    # Track trades
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    position_size = 1.0
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        # Entry
        if position is None and entry_signal.iloc[i]:
            position = 1.0
            entry_time = current_time
            entry_price = current_price
            
            # Find flush low from recent bars
            flush_low = df.iloc[max(0, i-10):i]['low'].min()
            stop_loss = flush_low - (params['STOP_ATR'] * current_atr)
            
            # Adjust max hold time for late day (Dee_S recommendation)
            if current_hour >= 14 and current_minute >= 30:
                max_hold = params['MAX_HOLD_MINUTES'] * 0.5  # 50% reduction
            else:
                max_hold = params['MAX_HOLD_MINUTES']
        
        # Exit management
        elif position is not None and position > 0:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            
            # Calculate R-multiples
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Stop loss
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'stop',
                    'r_multiple': -1.0
                })
                position = None
                continue
            
            # Scale out at 1R (40%)
            if current_r >= 1.0 and position == 1.0:
                scale_pnl = (entry_price * 1.01 - entry_price) / entry_price * 100 * params['SCALE_1R_PCT']
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_1r',
                    'r_multiple': 1.0
                })
                position -= params['SCALE_1R_PCT']
            
            # Scale out at 2R (30%)
            if current_r >= 2.0 and position >= 0.6:
                scale_pnl = (entry_price * 1.02 - entry_price) / entry_price * 100 * params['SCALE_2R_PCT']
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_2r',
                    'r_multiple': 2.0
                })
                position -= params['SCALE_2R_PCT']
            
            # VWAP trail (runner exits if breaks below VWAP)
            if current_low < df.iloc[i]['vwap'] and position > 0:
                pnl_pct = (df.iloc[i]['vwap'] - entry_price) / entry_price * 100 * position
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'vwap_trail',
                    'r_multiple': current_r
                })
                position = None
                continue
            
            # Time stop
            if time_in_position >= max_hold and position > 0:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
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
            'sharpe': 0,
            'avg_hold': 0
        }
    
    trades_df = pd.DataFrame(trades)
    friction_bps = 12.5
    trades_df['pnl_after_friction'] = trades_df['pnl_pct'] - (friction_bps / 100)
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_after_friction'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_after_friction'].mean()
    total_pnl = trades_df['pnl_after_friction'].sum()
    sharpe = (avg_pnl / trades_df['pnl_after_friction'].std() * np.sqrt(252)) if trades_df['pnl_after_friction'].std() > 0 else 0
    avg_hold = trades_df['hold_minutes'].mean()
    
    print(f"✓ {symbol}: {total_trades} trades | Win Rate: {win_rate:.1f}% | Avg P&L: {avg_pnl:+.2f}% | Sharpe: {sharpe:.2f}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'total_pnl': total_pnl,
        'sharpe': sharpe,
        'avg_hold': avg_hold
    }

if __name__ == '__main__':
    # Test on RIOT Recent
    result = run_backtest_v2('RIOT', '2024-11-01', '2025-01-17')
    
    print("\n" + "="*80)
    print("VWAP RECLAIM V2 - EXPERT-CORRECTED")
    print("="*80)
    print(f"Symbol: {result['symbol']}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Avg P&L: {result['avg_pnl']:+.2f}%")
    print(f"Total P&L: {result['total_pnl']:+.2f}%")
    print(f"Sharpe: {result['sharpe']:.2f}")
    print(f"Avg Hold: {result['avg_hold']:.1f} min")
