"""
Strategy E: VWAP Reclaim / Washout Reversal
--------------------------------------------
Type: Mean Reversion → Momentum Shift
Tier: Core / Highest Consensus
Market: Small-cap ($1-$20), high RVOL, intraday movers

Core Thesis:
VWAP acts as liquidity magnet. Flushes below VWAP in strong names represent 
forced selling, not trend failure. Reclaim = smart money accumulation.

Entry Logic:
1. Stock up on day (>= 15%)
2. Flush below VWAP (>= 0.8 ATR deviation)
3. Absorption wick (>= 40% of candle range)
4. Volume spike (>= 1.6x average)
5. Reclaim VWAP and hold for 2 bars

Exit Rules:
- Stop Loss: Flush low - (0.45 × ATR)
- TP1 (40%): VWAP → Mid-range
- TP2 (30%): High of Day (HOD)
- Runner (30%): Trail at VWAP
- Time Stop: 30 minutes

Based on expert synthesis (Chad_G, Dee_S, Gem_Ni) + independent machine analysis
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

def calculate_vwap(df):
    """Calculate VWAP (Volume Weighted Average Price)"""
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['cumulative_tp_volume'] = df['tp_volume'].cumsum()
    df['cumulative_volume'] = df['volume'].cumsum()
    df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']
    return df

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df

def run_backtest(symbol, start_date, end_date, params=None):
    """
    Run backtest for VWAP Reclaim strategy
    
    Parameters (with defaults from spec):
    - MIN_DAY_CHANGE_PCT: 15% (stock must be up on day)
    - FLUSH_DEV_ATR: 0.8 (flush deviation in ATR units)
    - WICK_RATIO_MIN: 0.40 (absorption wick threshold)
    - FLUSH_VOL_MULT: 1.6 (volume spike multiplier)
    - STOP_LOSS_ATR: 0.45 (stop loss in ATR units)
    - HOLD_BARS: 2 (bars to hold above VWAP before entry)
    - MAX_HOLD_MINUTES: 30 (maximum hold time)
    - SCALE_TP1_PCT: 0.40 (40% position at TP1)
    - SCALE_TP2_PCT: 0.30 (30% position at TP2)
    """
    
    # Default parameters from spec
    if params is None:
        params = {
            'MIN_DAY_CHANGE_PCT': 15.0,
            'FLUSH_DEV_ATR': 0.8,
            'WICK_RATIO_MIN': 0.40,
            'FLUSH_VOL_MULT': 1.6,
            'STOP_LOSS_ATR': 0.45,
            'HOLD_BARS': 2,
            'MAX_HOLD_MINUTES': 30,
            'SCALE_TP1_PCT': 0.40,
            'SCALE_TP2_PCT': 0.30,
            'MIN_DOLLAR_VOLUME': 250000,  # Liquidity gate
            'MAX_SPREAD_BPS': 35,  # Spread gate
        }
    
    print(f"Testing {symbol} ({start_date} to {end_date})...")
    
    # Fetch 1-minute data
    df = cache.get_or_fetch_equity(symbol, '1min', start_date, end_date)
    
    if len(df) < 100:
        raise ValueError(f"Insufficient data: {len(df)} bars")
    
    # Calculate VWAP
    df = calculate_vwap(df)
    
    # Calculate ATR
    df = calculate_atr(df, period=14)
    
    # Calculate day change (from previous day close)
    df['date'] = df.index.date
    df['prev_day_close'] = df.groupby('date')['close'].transform('first').shift(1)
    df['day_change_pct'] = ((df['close'] - df['prev_day_close']) / df['prev_day_close'] * 100)
    
    # Calculate candle metrics
    df['candle_range'] = df['high'] - df['low']
    df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    
    # Calculate volume metrics
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate dollar volume
    df['dollar_volume'] = df['close'] * df['volume']
    
    # High of Day (HOD)
    df['hod'] = df.groupby('date')['high'].transform('max')
    
    # Entry conditions
    # 1. Stock up on day
    condition_up = df['day_change_pct'] >= params['MIN_DAY_CHANGE_PCT']
    
    # 2. Flush below VWAP
    df['flush_deviation'] = (df['vwap'] - df['low']) / df['atr']
    condition_flush = df['flush_deviation'] >= params['FLUSH_DEV_ATR']
    
    # 3. Absorption wick
    condition_wick = df['wick_ratio'] >= params['WICK_RATIO_MIN']
    
    # 4. Volume spike
    condition_volume = df['volume_spike'] >= params['FLUSH_VOL_MULT']
    
    # 5. Reclaim VWAP
    df['above_vwap'] = (df['close'] > df['vwap']).astype(int)
    df['bars_above_vwap'] = df['above_vwap'].rolling(params['HOLD_BARS']).sum()
    condition_reclaim = df['bars_above_vwap'] >= params['HOLD_BARS']
    
    # Liquidity gate
    condition_liquidity = df['dollar_volume'] > params['MIN_DOLLAR_VOLUME']
    
    # Combined entry signal
    entry_signal = (condition_up & condition_flush & condition_wick & 
                   condition_volume & condition_reclaim & condition_liquidity)
    
    # Track trades
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    flush_low = None
    
    for i in range(len(df)):
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_high = df.iloc[i]['high']
        current_low = df.iloc[i]['low']
        current_atr = df.iloc[i]['atr']
        current_hod = df.iloc[i]['hod']
        
        if pd.isna(current_atr):
            continue
        
        # Check for entry
        if position is None and entry_signal.iloc[i]:
            # Enter position
            position = 1.0  # Full position
            entry_time = current_time
            entry_price = current_price
            flush_low = df.iloc[i-params['HOLD_BARS']]['low']  # Low from flush candle
            stop_loss = flush_low - (params['STOP_LOSS_ATR'] * current_atr)
            
        # Manage position
        elif position is not None:
            # Calculate time in position
            time_in_position = (current_time - entry_time).total_seconds() / 60
            
            # Check stop loss
            if current_low <= stop_loss:
                # Stopped out
                pnl_pct = (stop_loss - entry_price) / entry_price * 100
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': stop_loss,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'stop_loss'
                })
                position = None
                continue
            
            # Check time stop
            if time_in_position >= params['MAX_HOLD_MINUTES']:
                # Time stop
                pnl_pct = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'time_stop'
                })
                position = None
                continue
            
            # Simplified exit logic (no partial scaling for now)
            # Exit at HOD or VWAP trail
            if current_high >= current_hod * 0.99:  # Near HOD
                # Take profit at HOD
                exit_price = current_hod * 0.99
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'take_profit_hod'
                })
                position = None
    
    # Calculate performance metrics
    if len(trades) == 0:
        return {
            'symbol': symbol,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl_pct': 0,
            'total_pnl_pct': 0,
            'sharpe': 0,
            'avg_hold_minutes': 0
        }
    
    trades_df = pd.DataFrame(trades)
    
    # Apply friction (10-15 bps for small-cap scalping)
    friction_bps = 12.5  # Middle of range
    trades_df['pnl_pct_after_friction'] = trades_df['pnl_pct'] - (friction_bps / 100)
    
    # Metrics
    total_trades = len(trades_df)
    winning_trades = (trades_df['pnl_pct_after_friction'] > 0).sum()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    avg_pnl_pct = trades_df['pnl_pct_after_friction'].mean()
    total_pnl_pct = trades_df['pnl_pct_after_friction'].sum()
    
    # Sharpe ratio (annualized for intraday)
    if trades_df['pnl_pct_after_friction'].std() > 0:
        sharpe = (avg_pnl_pct / trades_df['pnl_pct_after_friction'].std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    avg_hold_minutes = trades_df['hold_minutes'].mean()
    
    print(f"✓ {symbol}: {total_trades} trades | Win Rate: {win_rate:.1f}% | Avg P&L: {avg_pnl_pct:+.2f}% | Sharpe: {sharpe:.2f}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl_pct': avg_pnl_pct,
        'total_pnl_pct': total_pnl_pct,
        'sharpe': sharpe,
        'avg_hold_minutes': avg_hold_minutes
    }

if __name__ == '__main__':
    # Test on a single asset
    import argparse
    
    parser = argparse.ArgumentParser(description='VWAP Reclaim Strategy')
    parser.add_argument('--symbol', type=str, default='RIOT', help='Symbol to test')
    parser.add_argument('--start', type=str, default='2024-11-01', help='Start date')
    parser.add_argument('--end', type=str, default='2025-01-17', help='End date')
    
    args = parser.parse_args()
    
    result = run_backtest(args.symbol, args.start, args.end)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Symbol: {result['symbol']}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Avg P&L: {result['avg_pnl_pct']:+.2f}%")
    print(f"Total P&L: {result['total_pnl_pct']:+.2f}%")
    print(f"Sharpe Ratio: {result['sharpe']:.2f}")
    print(f"Avg Hold Time: {result['avg_hold_minutes']:.1f} minutes")
