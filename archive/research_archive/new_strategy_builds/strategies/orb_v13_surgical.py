"""
ORB V13 "SURGICAL" - Expert Consensus Version
-----------------------------------------------
Based on synthesis of 3 expert consultations (Chad G, Dee S, Gem Ni)

KEY CHANGES FROM V7 (THE CRITICAL FIXES):
1. ✅ REMOVED: VWAP loss exit (right-tail killer)
2. ✅ REMOVED: Breakeven @ 0.5R (whipsaw generator)
3. ✅ NEW: Breakeven @ 1.0R with -0.05R offset (room to breathe)
4. ✅ NEW: Asymmetric scaling (30% @ 1.2R, 30% @ 2.0R)
5. ✅ NEW: Wider trail (0.8 ATR vs 0.6 ATR)
6. ✅ NEW: Time stop @ 45 minutes if not +0.25R
7. ✅ NEW: Minimum OR range filter (0.3 ATR - volatility expansion)

HYPOTHESIS:
- Win rate: 40-50% (down from 59%, acceptable)
- Avg Win: 1.2-1.8R (up from 0.5R, CRITICAL)
- Avg Loss: 1.0R (unchanged)
- Expectancy: +0.10R to +0.20R per trade (vs -0.215R in V7)
- Monthly Return: 1.5-2.5% per symbol after friction

Expert Consensus:
- "Exit asymmetry + friction was the whole problem" - Chad G
- "Strategy has edge but needs surgery, not optimization" - Dee S
- "Restore convexity to the right tail" - Gem Ni
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
from datetime import time

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

def run_orb_v13_surgical(symbol, start, end):
    """
    ORB V13 SURGICAL - Expert Consensus Implementation
    
    The definitive test: Did exit asymmetry cause the paradox?
    """
    
    params = {
        # OR DEFINITION (unchanged)
        'OR_MINUTES': 10,
        
        # ENTRY FILTERS (unchanged from V7, will tune in V14)
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'MIN_PRICE': 3.0,
        
        # NEW: Volatility Expansion Filter (Chad G)
        'MIN_OR_RANGE_ATR': 0.30,  # OR must be >= 0.3 ATR to trade
        
        # STOP LOSS (slightly tighter per Gem Ni)
        'HARD_STOP_ATR': 0.30,  # Was 0.4 in V7
        
        # **CRITICAL EXIT CHANGES** (All 3 experts agreed)
        'ENABLE_VWAP_LOSS': False,  # ❌ REMOVED (was True in V7)
        'BREAKEVEN_TRIGGER_R': 1.0,  # ✅ Was 0.5R (moved to 1.0R)
        'BREAKEVEN_OFFSET': -0.05,   # ✅ NEW: -0.05R not 0.0R (room to breathe)
        
        # ASYMMETRIC SCALING (Dee S + Chad G consensus)
        'PROFIT_TARGET_1': 1.2,      # Take 30% at 1.2R
        'PROFIT_TARGET_1_SIZE': 0.30,
        'PROFIT_TARGET_2': 2.0,      # Take 30% at 2.0R
        'PROFIT_TARGET_2_SIZE': 0.30,
        # Remaining 40% trails
        
        # TRAILING STOP (Wider per consensus)
        'TRAIL_ATR': 0.8,  # Was 0.6 in V7
        
        # TIME STOP (Chad + Dee consensus)
        'TIME_STOP_MINUTES': 45,     # Exit if not +0.25R after 45min
        'TIME_STOP_MIN_R': 0.25,
    }
    
    print(f"\n{'='*60}")
    print(f"Testing {symbol} with ORB V13 SURGICAL")
    print(f"Period: {start} to {end}")
    print(f"{'='*60}")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        print(f"❌ No data for {symbol}")
        return None
    
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
    df['or_range'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) > 0:
            or_high = or_data['high'].max()
            or_low = or_data['low'].min()
            or_range = or_high - or_low
            df.loc[date_mask, 'or_high'] = or_high
            df.loc[date_mask, 'or_low'] = or_low
            df.loc[date_mask, 'or_range'] = or_range
    
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
    moved_to_be = False
    scaled_at_12r = False
    scaled_at_20r = False
    
    # MAE/MFE tracking (Chad G's diagnostic framework)
    max_adverse_excursion = 0
    max_favorable_excursion = 0
    
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
        current_or_range = df.iloc[i]['or_range']
        current_vwap = df.iloc[i]['vwap']
        
        # Skip OR period
        if df.iloc[i]['minutes_since_open'] <= params['OR_MINUTES']:
            continue
        
        # Entry Logic
        if position is None:
            # NEW: Volatility Expansion Filter (only trade if OR is big enough)
            if current_or_range < (params['MIN_OR_RANGE_ATR'] * current_atr):
                breakout_seen = False  # Reset for next bar
                continue
            
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
                    breakout_seen = False
                    moved_to_be = False
                    scaled_at_12r = False
                    scaled_at_20r = False
                    max_adverse_excursion = 0
                    max_favorable_excursion = 0
        
        # Position Management
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Track MAE/MFE (diagnostic)
            mae = (current_low - entry_price) / risk if risk > 0 else 0
            mfe = (current_high - entry_price) / risk if risk > 0 else 0
            max_adverse_excursion = min(max_adverse_excursion, mae)
            max_favorable_excursion = max(max_favorable_excursion, mfe)
            
            if current_high > highest_price:
                highest_price = current_high
            
            minutes_in_trade = (current_time - entry_time).seconds / 60
            
            # HARD STOP
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({
                    'pnl_pct': pnl_pct, 
                    'r': -1.0, 
                    'type': 'stop',
                    'mae': max_adverse_excursion,
                    'mfe': max_favorable_excursion,
                    'minutes_in_trade': minutes_in_trade
                })
                position = None
                continue
            
            # ✅ NEW: BREAKEVEN @ 1.0R with -0.05R offset (not 0.5R)
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price + (params['BREAKEVEN_OFFSET'] * risk)  # -0.05R
                moved_to_be = True
            
            # ✅ NEW: SCALE #1 @ 1.2R (30%)
            if current_r >= params['PROFIT_TARGET_1'] and not scaled_at_12r:
                pnl_pct = (risk * params['PROFIT_TARGET_1']) / entry_price * 100 * params['PROFIT_TARGET_1_SIZE']
                trades.append({
                    'pnl_pct': pnl_pct, 
                    'r': params['PROFIT_TARGET_1'], 
                    'type': 'scale_12r',
                    'mae': max_adverse_excursion,
                    'mfe': max_favorable_excursion,
                    'minutes_in_trade': minutes_in_trade
                })
                position -= params['PROFIT_TARGET_1_SIZE']
                scaled_at_12r = True
            
            # ✅ NEW: SCALE #2 @ 2.0R (30%)
            if current_r >= params['PROFIT_TARGET_2'] and not scaled_at_20r:
                pnl_pct = (risk * params['PROFIT_TARGET_2']) / entry_price * 100 * params['PROFIT_TARGET_2_SIZE']
                trades.append({
                    'pnl_pct': pnl_pct, 
                    'r': params['PROFIT_TARGET_2'], 
                    'type': 'scale_20r',
                    'mae': max_adverse_excursion,
                    'mfe': max_favorable_excursion,
                    'minutes_in_trade': minutes_in_trade
                })
                position -= params['PROFIT_TARGET_2_SIZE']
                scaled_at_20r = True
            
            # ✅ WIDER TRAILING STOP (0.8 ATR, only after BE)
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # ❌ VWAP LOSS EXIT REMOVED (was killing winners)
            # (Keeping code commented for reference)
            # if params['ENABLE_VWAP_LOSS'] and moved_to_be and current_price < current_vwap:
            #     # This was the right-tail killer
            #     pass
            
            # ✅ NEW: TIME STOP (Chad + Dee consensus)
            if (minutes_in_trade >= params['TIME_STOP_MINUTES'] and 
                current_r < params['TIME_STOP_MIN_R']):
                # If trade hasn't reached +0.25R after 45 min, exit
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({
                    'pnl_pct': pnl_pct, 
                    'r': current_r, 
                    'type': 'time_stop',
                    'mae': max_adverse_excursion,
                    'mfe': max_favorable_excursion,
                    'minutes_in_trade': minutes_in_trade
                })
                position = None
                continue
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({
                        'pnl_pct': pnl_pct, 
                        'r': current_r, 
                        'type': 'eod',
                        'mae': max_adverse_excursion,
                        'mfe': max_favorable_excursion,
                        'minutes_in_trade': minutes_in_trade
                    })
                    position = None
    
    if len(trades) == 0:
        print(f"⚠️  No trades generated for {symbol}")
        return {
            'symbol': symbol, 
            'total_trades': 0, 
            'win_rate': 0, 
            'avg_pnl': 0, 
            'total_pnl': 0, 
            'sharpe': 0,
            'avg_winner_r': 0,
            'avg_loser_r': 0,
            'expectancy_r': 0
        }
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125  # Friction
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_net'].mean()
    total_pnl = trades_df['pnl_net'].sum()
    sharpe = (avg_pnl / trades_df['pnl_net'].std() * np.sqrt(252)) if trades_df['pnl_net'].std() > 0 else 0
    
    # R-Multiple Analysis (THE KEY METRICS)
    winners = trades_df[trades_df['pnl_net'] > 0]
    losers = trades_df[trades_df['pnl_net'] <= 0]
    
    avg_winner_r = winners['r'].mean() if len(winners) > 0 else 0
    avg_loser_r = losers['r'].mean() if len(losers) > 0 else 0
    
    # Expectancy in R
    win_pct = len(winners) / total_trades if total_trades > 0 else 0
    expectancy_r = (win_pct * avg_winner_r) - ((1 - win_pct) * abs(avg_loser_r))
    
    exit_counts = trades_df['type'].value_counts().to_dict()
    
    print(f"\n{'─'*60}")
    print(f"📊 RESULTS FOR {symbol}")
    print(f"{'─'*60}")
    print(f"Total Trades:    {total_trades}")
    print(f"Win Rate:        {win_rate:.1f}%")
    print(f"Avg P&L:         {avg_pnl:+.3f}%")
    print(f"Total P&L:       {total_pnl:+.2f}%")
    print(f"Sharpe Ratio:    {sharpe:.2f}")
    print(f"\n💡 R-MULTIPLE ANALYSIS (The Truth):")
    print(f"Avg Winner:      {avg_winner_r:+.2f}R")
    print(f"Avg Loser:       {avg_loser_r:+.2f}R")
    print(f"Expectancy:      {expectancy_r:+.3f}R per trade")
    print(f"\n🚪 Exit Distribution:")
    for exit_type, count in exit_counts.items():
        print(f"  {exit_type:12s}: {count:3d} ({count/total_trades*100:.1f}%)")
    print(f"{'='*60}\n")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'total_pnl': total_pnl,
        'sharpe': sharpe,
        'avg_winner_r': avg_winner_r,
        'avg_loser_r': avg_loser_r,
        'expectancy_r': expectancy_r,
        'exit_counts': exit_counts,
        'trades': trades_df  # Return full trades for analysis
    }
