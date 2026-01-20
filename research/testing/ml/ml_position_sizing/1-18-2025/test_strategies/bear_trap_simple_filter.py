"""
Bear Trap - Simple Rule-Based Filter (No ML)

Uses Chad's insights without ML:
- Only trade late session (after 3pm)
- Require high volume (2x+ average)
- Fast reclaim (price moved >5% from session low in <30 bars)
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

def run_bear_trap_filtered(symbol, start, end):
    """Bear Trap with simple rule-based filter"""
    print(f"\nTesting {symbol} - Rule-Based Filter [{start} to {end}]")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        print(f"0 trades (no data)")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_r': 0}
    
    # Setup
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    
    # ATR
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # Session metrics (NO LOOKAHEAD)
    df['session_low'] = df.groupby('date')['low'].cummin()
    df['session_high'] = df.groupby('date')['high'].cummax()
    df['session_open'] = df.groupby('date')['open'].transform('first')
    df['day_change_pct'] = ((df['close'] - df['session_open']) / df['session_open']) * 100
    
    # Candle metrics
    df['candle_range'] = df['high'] - df['low']
    df['candle_body'] = abs(df['close'] - df['open'])
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    df['body_ratio'] = df['candle_body'] / df['candle_range'].replace(0, np.inf)
    
    # Volume
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    trades = []
    filtered_out = 0
    position = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']):
            continue
        
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_atr = df.iloc[i]['atr']
        session_low = df.iloc[i]['session_low']
        day_change = df.iloc[i]['day_change_pct']
        current_hour = df.iloc[i]['hour']
        
        if position is None:
            if day_change <= -15:
                is_reclaim = (
                    df.iloc[i]['close'] > session_low and
                    df.iloc[i]['wick_ratio'] >= 0.15 and
                    df.iloc[i]['body_ratio'] >= 0.2 and
                    df.iloc[i]['volume_ratio'] >= 1.2
                )
                
                if is_reclaim:
                    # SIMPLE FILTERS (Chad's insights)
                    
                    # Filter 1: Time of day (only late session)
                    if current_hour < 15:
                        filtered_out += 1
                        continue
                    
                    # Filter 2: Volume confirmation (high volume only)
                    if df.iloc[i]['volume_ratio'] < 2.0:
                        filtered_out += 1
                        continue
                    
                    # Filter 3: Fast reclaim (check recent price action)
                    lookback = min(30, i)
                    if lookback > 5:
                        recent_data = df.iloc[i-lookback:i+1]
                        recent_low = recent_data['low'].min()
                        price_move = (current_price - recent_low) / recent_low * 100
                        
                        # Require >5% move in <30 bars (fast reclaim)
                        if price_move < 5.0:
                            filtered_out += 1
                            continue
                    
                    # PASSED ALL FILTERS - Take trade
                    position = 1
                    entry_idx = i
                    entry_price = current_price
                    stop_loss = session_low - (0.45 * current_atr)
        
        elif position == 1:
            bars_held = i - entry_idx
            if bars_held >= 30 or current_low <= stop_loss:
                exit_price = stop_loss if current_low <= stop_loss else current_price
                
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                risk = entry_price - stop_loss
                r_multiple = (exit_price - entry_price) / risk if risk > 0 else 0
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'r': r_multiple,
                })
                
                position = None
    
    if len(trades) == 0:
        print(f"0 trades (filtered out {filtered_out})")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_r': 0, 'filtered': filtered_out}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    total_pnl = trades_df['pnl_net'].sum()
    avg_r = trades_df['r'].mean()
    
    print(f"✓ {total_trades} trades | {win_rate:.1f}% win | {total_pnl:+.2f}% total | Avg R: {avg_r:+.2f} | Filtered: {filtered_out}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_r': avg_r,
        'filtered': filtered_out
    }

if __name__ == "__main__":
    symbols = ['AMC', 'MULN', 'NKLA']
    start = '2024-01-01'
    end = '2024-12-31'
    
    print("="*80)
    print("BEAR TRAP - SIMPLE RULE-BASED FILTER")
    print("="*80)
    print("Filters: Late session (3pm+), High volume (2x+), Fast reclaim (>5% in <30 bars)")
    print(f"Period: {start} to {end}\n")
    
    results = []
    for symbol in symbols:
        result = run_bear_trap_filtered(symbol, start, end)
        results.append(result)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    df_results = pd.DataFrame(results)
    total_trades = df_results['total_trades'].sum()
    avg_win_rate = df_results['win_rate'].mean()
    total_pnl = df_results['total_pnl'].sum()
    avg_r = df_results['avg_r'].mean()
    total_filtered = df_results['filtered'].sum()
    
    print(f"\nTotal trades: {total_trades}")
    print(f"Filtered out: {total_filtered}")
    print(f"Avg win rate: {avg_win_rate:.1f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    print(f"Avg R: {avg_r:+.2f}")
    
    print(f"\nBaseline (no filter): 543 trades, 43.5% WR, +0.15R")
    print(f"Rule-based filter: {total_trades} trades, {avg_win_rate:.1f}% WR, {avg_r:+.2f}R")
