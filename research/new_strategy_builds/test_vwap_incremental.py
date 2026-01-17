"""
VWAP Reclaim - Incremental Filter Analysis
-------------------------------------------
Tests VWAP Reclaim with progressively more filters to understand impact.

Versions tested:
1. Baseline: Just VWAP reclaim (price > VWAP after being below)
2. +Day Change: Add requirement that stock is up on day
3. +Flush: Add requirement for meaningful flush below VWAP
4. +Wick: Add absorption wick requirement
5. +Volume: Add volume spike requirement
6. Full: All filters (original strategy)

Goal: Identify which filters add value vs just reduce frequency.
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

def test_version(df, version_name, filters):
    """Test a specific filter combination"""
    
    # Start with all True
    entry_signal = pd.Series([True] * len(df), index=df.index)
    
    # Apply filters based on version
    if 'reclaim' in filters:
        # Basic VWAP reclaim: was below, now above
        df['above_vwap'] = (df['close'] > df['vwap']).astype(int)
        df['was_below'] = (df['close'].shift(1) <= df['vwap'].shift(1))
        entry_signal = entry_signal & (df['above_vwap'] == 1) & df['was_below']
    
    if 'day_change' in filters:
        entry_signal = entry_signal & (df['day_change_pct'] >= filters['day_change'])
    
    if 'flush' in filters:
        entry_signal = entry_signal & (df['flush_deviation'] >= filters['flush'])
    
    if 'wick' in filters:
        entry_signal = entry_signal & (df['wick_ratio'] >= filters['wick'])
    
    if 'volume' in filters:
        entry_signal = entry_signal & (df['volume_spike'] >= filters['volume'])
    
    # Simple position management
    trades = []
    position = None
    entry_time = None
    entry_price = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        
        # Entry
        if position is None and entry_signal.iloc[i]:
            position = 1
            entry_time = current_time
            entry_price = current_price
            stop_loss = entry_price - (0.5 * current_atr)  # Simple ATR stop
        
        # Exit management
        elif position is not None:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            
            # Stop loss
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'stop'
                })
                position = None
                continue
            
            # Time stop (30 min)
            if time_in_position >= 30:
                pnl_pct = (current_price - entry_price) / entry_price * 100
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'time'
                })
                position = None
                continue
            
            # Take profit at 2% gain
            if current_high >= entry_price * 1.02:
                pnl_pct = 2.0
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'pnl_pct': pnl_pct,
                    'hold_minutes': time_in_position,
                    'exit_reason': 'profit'
                })
                position = None
    
    # Calculate metrics
    if len(trades) == 0:
        return {
            'version': version_name,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'sharpe': 0
        }
    
    trades_df = pd.DataFrame(trades)
    friction_bps = 12.5
    trades_df['pnl_after_friction'] = trades_df['pnl_pct'] - (friction_bps / 100)
    
    return {
        'version': version_name,
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_after_friction'] > 0).sum() / len(trades_df) * 100,
        'avg_pnl': trades_df['pnl_after_friction'].mean(),
        'total_pnl': trades_df['pnl_after_friction'].sum(),
        'sharpe': (trades_df['pnl_after_friction'].mean() / trades_df['pnl_after_friction'].std() * np.sqrt(252)) if trades_df['pnl_after_friction'].std() > 0 else 0
    }

def run_incremental_test(symbol, start, end):
    """Run all versions on a single symbol/period"""
    
    print(f"\nTesting {symbol} ({start} to {end})")
    print("="*80)
    
    # Load data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    # Calculate features
    df['date'] = df.index.date
    df['prev_day_close'] = df.groupby('date')['close'].transform('first').shift(1)
    df['day_change_pct'] = ((df['close'] - df['prev_day_close']) / df['prev_day_close'] * 100)
    
    df['candle_range'] = df['high'] - df['low']
    df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    
    df['flush_deviation'] = (df['vwap'] - df['low']) / df['atr']
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Test versions
    versions = [
        ('V1_Baseline', {'reclaim': True}),
        ('V2_+DayChange', {'reclaim': True, 'day_change': 8.0}),
        ('V3_+Flush', {'reclaim': True, 'day_change': 8.0, 'flush': 0.6}),
        ('V4_+Wick', {'reclaim': True, 'day_change': 8.0, 'flush': 0.6, 'wick': 0.30}),
        ('V5_+Volume', {'reclaim': True, 'day_change': 8.0, 'flush': 0.6, 'wick': 0.30, 'volume': 1.4}),
    ]
    
    results = []
    for version_name, filters in versions:
        result = test_version(df, version_name, filters)
        result['symbol'] = symbol
        result['period'] = f"{start}_{end}"
        results.append(result)
        
        print(f"{version_name:20} | Trades: {result['total_trades']:4} | Win%: {result['win_rate']:5.1f} | Avg: {result['avg_pnl']:+6.2f}% | Sharpe: {result['sharpe']:5.2f}")
    
    return results

def main():
    print("="*80)
    print("VWAP RECLAIM - INCREMENTAL FILTER ANALYSIS")
    print("="*80)
    
    # Test on RIOT Recent period first
    all_results = []
    
    test_cases = [
        ('RIOT', '2024-11-01', '2025-01-17'),
        ('RIOT', '2025-04-01', '2025-06-30'),
        ('MARA', '2024-11-01', '2025-01-17'),
    ]
    
    for symbol, start, end in test_cases:
        results = run_incremental_test(symbol, start, end)
        all_results.extend(results)
    
    # Save results
    results_df = pd.DataFrame(all_results)
    output_path = Path('research/new_strategy_builds/results/vwap_incremental_analysis.csv')
    results_df.to_csv(output_path, index=False)
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"Results saved to: {output_path}")
    
    # Summary by version
    print("\n" + "="*80)
    print("SUMMARY BY VERSION (Across all tests)")
    print("="*80)
    
    summary = results_df.groupby('version').agg({
        'total_trades': 'sum',
        'win_rate': 'mean',
        'avg_pnl': 'mean',
        'sharpe': 'mean'
    }).round(2)
    
    print(summary.to_string())
    
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    print("Compare V1 (baseline) with each subsequent version to see:")
    print("- How much each filter reduces trade frequency")
    print("- Whether the filter improves win rate or Sharpe")
    print("- The trade-off between frequency and quality")

if __name__ == '__main__':
    main()
