"""
ORB V10 - Simplified Entry, Sophisticated Exits
------------------------------------------------
Expert Quant Analysis: The problem is filter conjunction, not timing.

Key Changes from V9:
1. REMOVED: Pullback requirement (primary killer)
2. RELAXED: Volume threshold (1.8x → 1.5x)
3. ADDED: Failure-to-Advance (FTA) exit (5 min, 0.3R)
4. ADDED: Front-loaded scaling (25% @ 0.25R, 25% @ 0.5R)
5. WIDENED: Stop loss (0.4 ATR → 0.75 ATR)
6. EXTENDED: Entry window slightly (45 min → 60 min)

Expected Performance:
- Trades: 80-120 (vs V9's 0)
- Win Rate: 52-58%
- Avg P&L: +0.08% to +0.15%
- Sharpe: 0.8-1.2

Rationale:
V5 proved the edge exists (62% win rate). V9 over-corrected with too many filters.
V10 returns to V5's entry simplicity with V7's exit sophistication.
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

def run_orb_v10(symbol, start, end):
    """
    ORB V10 - Simplified entry, sophisticated exits
    
    Entry Logic (3 filters + 1 context):
    - Breakout above OR high
    - Volume spike >= 1.5x
    - Price > VWAP
    - NOT within 0.25 ATR of PDH (context filter)
    
    Exit Logic (4 tiers):
    - FTA: Exit if < 0.3R after 5 minutes
    - Scale 25% @ 0.25R
    - Scale 25% @ 0.5R (move to BE)
    - Trail remaining 50% to 1.3R or VWAP loss
    """
    
    params = {
        # Opening Range
        'OR_MINUTES': 10,
        
        # Entry Window
        'ENTRY_WINDOW_START': 10,   # 9:40 AM
        'ENTRY_WINDOW_END': 60,     # 10:30 AM (55 min window)
        
        # Entry Filters (SIMPLIFIED)
        'VOL_MULT': 1.5,            # Relaxed from 1.8
        'MIN_PRICE': 3.0,
        'PDH_COLLISION_ATR': 0.25,  # Context filter
        
        # Exit Logic (NEW)
        'FTA_MINUTES': 5,           # Failure-to-advance timeout
        'FTA_THRESHOLD_R': 0.3,     # Must reach 0.3R in 5 min
        
        'SCALE_025R_PCT': 0.25,     # Scale 25% at 0.25R
        'SCALE_050R_PCT': 0.25,     # Scale 25% at 0.5R
        'BREAKEVEN_TRIGGER_R': 0.5, # Move to BE at 0.5R
        
        'TARGET_13R': 1.3,          # Target for runner
        'TRAIL_ATR': 0.6,           # Trail stop
        
        # Stop Loss
        'HARD_STOP_ATR': 0.75,      # Widened from 0.4 (survive noise)
    }
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30)
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate prior day levels
    df['pdh'] = np.nan
    df['pdl'] = np.nan
    df['pdc'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        prev_date_data = df[df['date'] < date]
        
        if len(prev_date_data) > 0:
            prev_day = prev_date_data[prev_date_data['date'] == prev_date_data['date'].max()]
            if len(prev_day) > 0:
                df.loc[date_mask, 'pdh'] = prev_day['high'].max()
                df.loc[date_mask, 'pdl'] = prev_day['low'].min()
                df.loc[date_mask, 'pdc'] = prev_day['close'].iloc[-1]
    
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
    
    # Track trades with detailed metrics
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    lowest_price = 999999
    moved_to_be = False
    scaled_025r = False
    scaled_050r = False
    
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
        current_pdh = df.iloc[i]['pdh']
        minutes_since_open = df.iloc[i]['minutes_since_open']
        volume_spike = df.iloc[i]['volume_spike']
        
        if minutes_since_open <= params['OR_MINUTES']:
            continue
        
        # Entry logic (SIMPLIFIED)
        if position is None:
            # Entry window check
            if minutes_since_open < params['ENTRY_WINDOW_START'] or minutes_since_open > params['ENTRY_WINDOW_END']:
                continue
            
            # 3 core filters + 1 context filter
            breakout = current_price > current_or_high
            volume_ok = volume_spike >= params['VOL_MULT']
            above_vwap = current_price > current_vwap
            price_ok = current_price >= params['MIN_PRICE']
            
            # PDH collision filter (context, not hard requirement)
            pdh_collision = False
            if not pd.isna(current_pdh):
                distance_to_pdh = abs(current_or_high - current_pdh)
                if distance_to_pdh < params['PDH_COLLISION_ATR'] * current_atr:
                    pdh_collision = True
            
            # Entry condition
            if breakout and volume_ok and above_vwap and price_ok and not pdh_collision:
                position = 1.0
                entry_time = current_time
                entry_price = current_price
                stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                highest_price = current_price
                lowest_price = current_price
                moved_to_be = False
                scaled_025r = False
                scaled_050r = False
        
        # Position management
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Track MAE/MFE
            if current_high > highest_price:
                highest_price = current_high
            if current_low < lowest_price:
                lowest_price = current_low
            
            mae = (lowest_price - entry_price) / risk if risk > 0 else 0
            mfe = (highest_price - entry_price) / risk if risk > 0 else 0
            
            # Calculate time in trade
            time_in_trade = (current_time - entry_time).total_seconds() / 60
            
            # Tier 1: Failure-to-Advance (FTA) Exit
            if time_in_trade >= params['FTA_MINUTES'] and current_r < params['FTA_THRESHOLD_R']:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'r': current_r,
                    'type': 'fta',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position = None
                continue
            
            # Hard stop
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': stop_loss,
                    'pnl_pct': pnl_pct,
                    'r': -1.0,
                    'type': 'stop',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position = None
                continue
            
            # Tier 2: Scale 25% @ 0.25R
            if current_r >= 0.25 and not scaled_025r:
                pnl_pct = (risk * 0.25) / entry_price * 100 * params['SCALE_025R_PCT']
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': entry_price + (risk * 0.25),
                    'pnl_pct': pnl_pct,
                    'r': 0.25,
                    'type': 'scale_025r',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position -= params['SCALE_025R_PCT']
                scaled_025r = True
            
            # Tier 3: Scale 25% @ 0.5R + Move to Breakeven
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not scaled_050r:
                pnl_pct = (risk * 0.5) / entry_price * 100 * params['SCALE_050R_PCT']
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': entry_price + (risk * 0.5),
                    'pnl_pct': pnl_pct,
                    'r': 0.5,
                    'type': 'scale_050r',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position -= params['SCALE_050R_PCT']
                stop_loss = entry_price
                moved_to_be = True
                scaled_050r = True
            
            # Tier 4: Target @ 1.3R
            if current_r >= params['TARGET_13R'] and position > 0:
                pnl_pct = (risk * params['TARGET_13R']) / entry_price * 100 * position
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': entry_price + (risk * params['TARGET_13R']),
                    'pnl_pct': pnl_pct,
                    'r': params['TARGET_13R'],
                    'type': 'target_13r',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position = None
                continue
            
            # Trailing stop (after moved to BE)
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP-loss soft stop (after moved to BE)
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'r': current_r,
                    'type': 'vwap_loss',
                    'mae': mae,
                    'mfe': mfe,
                    'time_in_trade': time_in_trade,
                })
                position = None
                continue
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_pct': pnl_pct,
                        'r': current_r,
                        'type': 'eod',
                        'mae': mae,
                        'mfe': mfe,
                        'time_in_trade': time_in_trade,
                    })
                    position = None
    
    if len(trades) == 0:
        return {
            'symbol': symbol,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_mae': 0,
            'avg_mfe': 0,
            'sharpe': 0,
            'exit_breakdown': {},
        }
    
    trades_df = pd.DataFrame(trades)
    
    # Apply friction (spread + commission)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    winners = trades_df[trades_df['pnl_net'] > 0]
    losers = trades_df[trades_df['pnl_net'] <= 0]
    
    # Exit type breakdown
    exit_breakdown = trades_df['type'].value_counts().to_dict()
    
    return {
        'symbol': symbol,
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_net'] > 0).sum() / len(trades_df) * 100,
        'avg_pnl': trades_df['pnl_net'].mean(),
        'avg_win': winners['pnl_net'].mean() if len(winners) > 0 else 0,
        'avg_loss': losers['pnl_net'].mean() if len(losers) > 0 else 0,
        'avg_mae': trades_df['mae'].mean(),
        'avg_mfe': trades_df['mfe'].mean(),
        'sharpe': trades_df['pnl_net'].mean() / trades_df['pnl_net'].std() if trades_df['pnl_net'].std() > 0 else 0,
        'exit_breakdown': exit_breakdown,
        'trades_df': trades_df,
    }

if __name__ == '__main__':
    print("="*80)
    print("ORB V10 - SIMPLIFIED ENTRY, SOPHISTICATED EXITS")
    print("="*80)
    
    result = run_orb_v10('RIOT', '2024-11-01', '2025-01-17')
    
    print(f"\nSymbol: {result['symbol']}")
    print(f"Total Trades: {result['total_trades']}")
    print(f"Win Rate: {result['win_rate']:.1f}%")
    print(f"Avg P&L: {result['avg_pnl']:+.3f}%")
    print(f"Avg Win: {result['avg_win']:+.3f}%")
    print(f"Avg Loss: {result['avg_loss']:+.3f}%")
    print(f"Avg MAE: {result['avg_mae']:.2f}R")
    print(f"Avg MFE: {result['avg_mfe']:.2f}R")
    print(f"Sharpe: {result['sharpe']:.2f}")
    
    print("\nExit Breakdown:")
    for exit_type, count in result['exit_breakdown'].items():
        pct = count / result['total_trades'] * 100
        print(f"  {exit_type}: {count} ({pct:.1f}%)")
    
    if result['total_trades'] > 0:
        print("\n" + "="*80)
        print("SAMPLE TRADES (First 5)")
        print("="*80)
        print(result['trades_df'][['entry_time', 'exit_time', 'pnl_pct', 'r', 'type', 'mae', 'mfe']].head().to_string(index=False))
