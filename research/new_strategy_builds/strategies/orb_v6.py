"""
ORB V6 - Chad_G's Data-Aligned Scaling
---------------------------------------
Based on Chad_G's reconciliation of expert opinions

KEY INSIGHT: "Optimize distribution shape under friction"
- Most trades reach 0.3-0.6R (not 1R+)
- Edge is win rate + impulse (not long runners)
- Need to monetize where price ACTUALLY goes

SCALING STRATEGY (Front-Loaded Asymmetric):
- 25-30% at +0.25R (monetize impulse)
- 25-30% at +0.5R (reduce net loss on failures)
- Trail remainder (upside alive without depending on it)

STOP MANAGEMENT (Dynamic):
- After +0.25R: Tighten to entry - 0.15 ATR
- After +0.5R: Allow VWAP-loss exit before hard stop
- Hard stop (0.4 ATR): Emergency only

FAILURE-TO-ADVANCE:
- If no +0.3R within 5 minutes: Exit at market
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

def run_orb_v6(symbol, start, end):
    """
    ORB V6 - Data-Aligned Scaling
    
    Changes from V5:
    - Scale at 0.25R and 0.5R (not 0.5R and 1.0R)
    - Dynamic stop tightening (not fixed)
    - VWAP-loss soft stop
    - Failure-to-advance exit (5 min / 0.3R)
    """
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,          # Emergency only
        'SCALE_025R_PCT': 0.30,        # 30% at 0.25R
        'SCALE_050R_PCT': 0.30,        # 30% at 0.5R
        'TRAIL_ATR': 0.6,              # Trail remainder
        'FTA_TIME_MINUTES': 5,         # Failure-to-advance time
        'FTA_MIN_PROFIT_R': 0.3,       # Minimum profit to avoid FTA exit
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
    
    # Entry signal tracking
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
    vwap_at_entry = 0
    bars_in_trade = 0
    
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
        
        # Entry logic (pullback entry from V5)
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
                    vwap_at_entry = current_vwap
                    breakout_seen = False
                    bars_in_trade = 0
        
        # Position management
        elif position is not None and position > 0:
            bars_in_trade += 1
            time_in_position = (current_time - entry_time).total_seconds() / 60
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            # FAILURE-TO-ADVANCE EXIT (Chad_G #1 priority)
            if time_in_position >= params['FTA_TIME_MINUTES'] and current_r < params['FTA_MIN_PROFIT_R']:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'fta'})
                position = None
                continue
            
            # VWAP-LOSS SOFT STOP (after +0.5R)
            if current_r >= 0.5 and current_price < current_vwap:
                # Check if VWAP reclaimed within 2 bars
                if bars_in_trade >= 2:
                    lookback = df.iloc[max(0, i-2):i]
                    if not (lookback['close'] > lookback['vwap']).any():
                        pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                        trades.append({'pnl_pct': pnl_pct, 'r': current_r, 'type': 'vwap_loss'})
                        position = None
                        continue
            
            # HARD STOP (emergency only)
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'r': -1.0, 'type': 'stop'})
                position = None
                continue
            
            # SCALE at 0.25R (monetize impulse)
            if current_r >= 0.25 and position == 1.0:
                pnl_pct = (risk * 0.25) / entry_price * 100 * params['SCALE_025R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 0.25, 'type': 'scale_025r'})
                position -= params['SCALE_025R_PCT']
                # Tighten stop to entry - 0.15 ATR
                stop_loss = max(stop_loss, entry_price - (0.15 * current_atr))
            
            # SCALE at 0.5R (reduce net loss on failures)
            if current_r >= 0.5 and position >= 0.7:
                pnl_pct = (risk * 0.5) / entry_price * 100 * params['SCALE_050R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'r': 0.5, 'type': 'scale_050r'})
                position -= params['SCALE_050R_PCT']
            
            # TRAILING STOP (remainder)
            if current_r >= 0.5:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
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
