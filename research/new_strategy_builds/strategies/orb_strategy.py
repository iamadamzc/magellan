"""
Opening Range Breakout (ORB) Strategy
--------------------------------------
Based on expert consensus (Chad_G, Dee_S, Gem_Ni, Marina_G)

Core Thesis:
"Directional momentum established in first minutes of trading by breaking 
through opening range resistance with volume confirmation."

Entry:
- Price breaks above Opening Range High (ORH) or Pre-Market High (PMH)
- Volume spike 1.8-2.5× average on breakout
- Price above VWAP
- Spread and liquidity gates satisfied

Exit:
- Stop: Below breakout level - 0.4 ATR
- TP1 (45%): 1R
- TP2 (30%): 2R  
- Runner (25%): Trail below higher lows
- Time: 20 minutes if stalls

Expert Parameters (Dee_S Synthesis):
- OR_MINUTES: 5 (first 5 minutes)
- VOL_MULT: 2.0× average
- STOP_ATR: 0.4× ATR
- TRAIL_ACTIVATE: 1.5R
- MAX_HOLD: 20 minutes
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

def run_orb_backtest(symbol, start, end, params=None):
    """
    Opening Range Breakout Strategy
    
    Entry: Break of OR high with volume, above VWAP
    Exit: Stop at OR low - 0.4 ATR, scale at 1R/2R, trail runner
    """
    
    if params is None:
        params = {
            'OR_MINUTES': 5,           # First 5 minutes define OR
            'VOL_MULT': 2.0,           # Volume spike on breakout
            'STOP_ATR': 0.4,           # Stop below OR low
            'TRAIL_ACTIVATE_R': 1.5,   # Start trailing at 1.5R
            'MAX_HOLD_MINUTES': 20,    # Time stop
            'SCALE_1R_PCT': 0.45,      # 45% at 1R
            'SCALE_2R_PCT': 0.30,      # 30% at 2R
            'MIN_RVOL': 2.5,           # Minimum relative volume
        }
    
    print(f"Testing {symbol} ({start} to {end})...")
    
    # Load data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    # Add time features
    df['date'] = df.index.date
    df['time'] = df.index.time
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    
    # Calculate volume metrics
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate Opening Range for each day
    df['or_high'] = df.groupby('date').apply(
        lambda x: x[x['minutes_since_open'] <= params['OR_MINUTES']]['high'].max()
    ).reindex(df['date']).values
    
    df['or_low'] = df.groupby('date').apply(
        lambda x: x[x['minutes_since_open'] <= params['OR_MINUTES']]['low'].min()
    ).reindex(df['date']).values
    
    # Entry conditions
    condition_breakout = df['close'] > df['or_high']
    condition_volume = df['volume_spike'] >= params['VOL_MULT']
    condition_vwap = df['close'] > df['vwap']
    condition_time = df['minutes_since_open'] > params['OR_MINUTES']  # After OR period
    
    entry_signal = condition_breakout & condition_volume & condition_vwap & condition_time
    
    # Track trades
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    or_low = None
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
            or_low = current_or_low
            stop_loss = or_low - (params['STOP_ATR'] * current_atr)
        
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
            
            # Scale at 1R (45%)
            if current_r >= 1.0 and position == 1.0:
                scale_pnl = risk / entry_price * 100 * params['SCALE_1R_PCT']
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_1r',
                    'r_multiple': 1.0
                })
                position -= params['SCALE_1R_PCT']
            
            # Scale at 2R (30%)
            if current_r >= 2.0 and position >= 0.55:
                scale_pnl = (risk * 2) / entry_price * 100 * params['SCALE_2R_PCT']
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': scale_pnl,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'scale_2r',
                    'r_multiple': 2.0
                })
                position -= params['SCALE_2R_PCT']
            
            # Trailing stop (after 1.5R, trail below higher lows)
            if current_r >= params['TRAIL_ACTIVATE_R']:
                # Simple trail: move stop to breakeven + 0.5R
                stop_loss = max(stop_loss, entry_price + (risk * 0.5))
            
            # Time stop
            if time_in_position >= params['MAX_HOLD_MINUTES'] and position > 0:
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
    # Quick test
    result = run_orb_backtest('RIOT', '2024-11-01', '2025-01-17')
    
    print("\n" + "="*80)
    print("OPENING RANGE BREAKOUT - TEST RESULTS")
    print("="*80)
    print(f"Symbol: {result['symbol']}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Avg P&L: {result['avg_pnl']:+.2f}%")
    print(f"Total P&L: {result['total_pnl']:+.2f}%")
    print(f"Sharpe: {result['sharpe']:.2f}")
    print(f"Avg Hold: {result['avg_hold']:.1f} min")
