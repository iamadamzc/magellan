"""
ORB V9 - Expert Refinements (OR=5 vs OR=10 Comparison)
-------------------------------------------------------
Based on expert feedback:

1. Test OR=5 vs OR=10 (9:30-9:35 vs 9:30-9:40)
2. Entry window: 9:35-10:15 (40 min)
3. Prior day context (PDH/PDL/PDC)
4. PDH collision filter (skip if OR high within 0.25 ATR of PDH)
5. Track MAE (Max Adverse Excursion) and MFE (Max Favorable Excursion)

Comparison metrics:
- Win rate
- Avg win
- % reaching 0.25R and 0.5R
- MAE (how ugly trades get)
- MFE (how good trades get)
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

def run_orb_v9(symbol, start, end, or_minutes=10):
    """
    ORB V9 - Expert refinements
    
    or_minutes: 5 or 10 (for comparison)
    """
    
    params = {
        'OR_MINUTES': or_minutes,
        'ENTRY_WINDOW_START': or_minutes,  # Right after OR
        'ENTRY_WINDOW_END': 45,            # 10:15 AM (45 min after open)
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'SCALE_13R_PCT': 0.50,
        'TRAIL_ATR': 0.6,
        'MIN_PRICE': 3.0,
        'PDH_COLLISION_ATR': 0.25,  # Skip if OR high within 0.25 ATR of PDH
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
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    
    # Track trades with MAE/MFE
    trades = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    lowest_price = 999999
    breakout_seen = False
    moved_to_be = False
    
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
        
        if minutes_since_open <= params['OR_MINUTES']:
            continue
        
        # Entry logic
        if position is None:
            # Entry window check
            if minutes_since_open < params['ENTRY_WINDOW_START'] or minutes_since_open > params['ENTRY_WINDOW_END']:
                breakout_seen = False
                continue
            
            if df.iloc[i]['breakout'] and not breakout_seen:
                breakout_seen = True
            
            if breakout_seen:
                # PDH collision filter
                if not pd.isna(current_pdh):
                    distance_to_pdh = abs(current_or_high - current_pdh)
                    if distance_to_pdh < params['PDH_COLLISION_ATR'] * current_atr:
                        # Skip - OR high too close to PDH
                        breakout_seen = False
                        continue
                
                pullback_zone_low = current_or_high - (params['PULLBACK_ATR'] * current_atr)
                pullback_zone_high = current_or_high + (params['PULLBACK_ATR'] * current_atr)
                in_pullback = (current_low <= pullback_zone_high) and (current_high >= pullback_zone_low)
                
                if (in_pullback and 
                    current_price > current_or_high and
                    current_price > current_vwap and
                    df.iloc[i]['volume_spike'] >= params['VOL_MULT'] and
                    current_price >= params['MIN_PRICE']):
                    
                    position = 1.0
                    entry_time = current_time
                    entry_price = current_price
                    stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                    highest_price = current_price
                    lowest_price = current_price
                    breakout_seen = False
                    moved_to_be = False
        
        # Position management
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # Track MAE/MFE
            if current_high > highest_price:
                highest_price = current_high
            if current_low < lowest_price:
                lowest_price = current_low
            
            # Hard stop
            if current_low <= stop_loss:
                mae = (lowest_price - entry_price) / risk if risk > 0 else 0
                mfe = (highest_price - entry_price) / risk if risk > 0 else 0
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'r': -1.0,
                    'type': 'stop',
                    'mae': mae,
                    'mfe': mfe,
                    'reached_025r': mfe >= 0.25,
                    'reached_050r': mfe >= 0.50,
                })
                position = None
                continue
            
            # Breakeven at 0.5R
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            # Scale at 1.3R
            if current_r >= 1.3 and position == 1.0:
                pnl_pct = (risk * 1.3) / entry_price * 100 * params['SCALE_13R_PCT']
                mae = (lowest_price - entry_price) / risk if risk > 0 else 0
                mfe = (highest_price - entry_price) / risk if risk > 0 else 0
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'r': 1.3,
                    'type': 'scale_13r',
                    'mae': mae,
                    'mfe': mfe,
                    'reached_025r': True,
                    'reached_050r': True,
                })
                position -= params['SCALE_13R_PCT']
            
            # Trailing stop
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP-loss soft stop
            if moved_to_be and current_price < current_vwap:
                mae = (lowest_price - entry_price) / risk if risk > 0 else 0
                mfe = (highest_price - entry_price) / risk if risk > 0 else 0
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'r': current_r,
                    'type': 'vwap_loss',
                    'mae': mae,
                    'mfe': mfe,
                    'reached_025r': mfe >= 0.25,
                    'reached_050r': mfe >= 0.50,
                })
                position = None
                continue
            
            # EOD exit
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                if position > 0:
                    mae = (lowest_price - entry_price) / risk if risk > 0 else 0
                    mfe = (highest_price - entry_price) / risk if risk > 0 else 0
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    
                    trades.append({
                        'pnl_pct': pnl_pct,
                        'r': current_r,
                        'type': 'eod',
                        'mae': mae,
                        'mfe': mfe,
                        'reached_025r': mfe >= 0.25,
                        'reached_050r': mfe >= 0.50,
                    })
                    position = None
    
    if len(trades) == 0:
        return {
            'or_minutes': or_minutes,
            'total_trades': 0,
            'win_rate': 0,
            'avg_pnl': 0,
            'avg_win': 0,
            'pct_reached_025r': 0,
            'pct_reached_050r': 0,
            'avg_mae': 0,
            'avg_mfe': 0,
        }
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    winners = trades_df[trades_df['pnl_net'] > 0]
    
    return {
        'or_minutes': or_minutes,
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_net'] > 0).sum() / len(trades_df) * 100,
        'avg_pnl': trades_df['pnl_net'].mean(),
        'avg_win': winners['pnl_net'].mean() if len(winners) > 0 else 0,
        'pct_reached_025r': trades_df['reached_025r'].sum() / len(trades_df) * 100,
        'pct_reached_050r': trades_df['reached_050r'].sum() / len(trades_df) * 100,
        'avg_mae': trades_df['mae'].mean(),
        'avg_mfe': trades_df['mfe'].mean(),
    }

# Test OR=5 vs OR=10 on RIOT
print("="*80)
print("ORB V9 - OR=5 vs OR=10 COMPARISON (RIOT)")
print("="*80)

result_or5 = run_orb_v9('RIOT', '2024-11-01', '2025-01-17', or_minutes=5)
result_or10 = run_orb_v9('RIOT', '2024-11-01', '2025-01-17', or_minutes=10)

print("\n" + "="*80)
print("RESULTS")
print("="*80)

metrics = [
    ('Total Trades', 'total_trades', ''),
    ('Win Rate', 'win_rate', '%'),
    ('Avg P&L', 'avg_pnl', '%'),
    ('Avg Win', 'avg_win', '%'),
    ('% Reached 0.25R', 'pct_reached_025r', '%'),
    ('% Reached 0.50R', 'pct_reached_050r', '%'),
    ('Avg MAE', 'avg_mae', 'R'),
    ('Avg MFE', 'avg_mfe', 'R'),
]

print(f"\n{'Metric':<20} | {'OR=5':>12} | {'OR=10':>12} | {'Winner':>10}")
print("-" * 80)

for metric_name, key, unit in metrics:
    val5 = result_or5[key]
    val10 = result_or10[key]
    
    # Determine winner
    if key in ['total_trades', 'win_rate', 'avg_pnl', 'avg_win', 'pct_reached_025r', 'pct_reached_050r', 'avg_mfe']:
        winner = "OR=5" if val5 > val10 else "OR=10" if val10 > val5 else "TIE"
    elif key == 'avg_mae':
        winner = "OR=10" if val10 > val5 else "OR=5" if val5 > val10 else "TIE"  # Lower MAE is better
    else:
        winner = ""
    
    if unit == '%':
        print(f"{metric_name:<20} | {val5:>11.1f}% | {val10:>11.1f}% | {winner:>10}")
    elif unit == 'R':
        print(f"{metric_name:<20} | {val5:>11.2f}R | {val10:>11.2f}R | {winner:>10}")
    else:
        print(f"{metric_name:<20} | {val5:>12.0f} | {val10:>12.0f} | {winner:>10}")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

if result_or5['avg_mfe'] > result_or10['avg_mfe'] and result_or5['avg_mae'] <= result_or10['avg_mae']:
    print("✅ OR=5 WINS: Increases early MFE without blowing up MAE")
    print("   Use 5-minute opening range")
elif result_or10['avg_mfe'] > result_or5['avg_mfe'] or result_or5['avg_mae'] > result_or10['avg_mae'] * 1.2:
    print("✅ OR=10 WINS: OR=5 becomes a fakeout festival")
    print("   Stick to 10-minute opening range")
else:
    print("⚡ CLOSE CALL: Marginal difference")
    print(f"   OR=5: {result_or5['avg_mfe']:.2f}R MFE, {result_or5['avg_mae']:.2f}R MAE")
    print(f"   OR=10: {result_or10['avg_mfe']:.2f}R MFE, {result_or10['avg_mae']:.2f}R MAE")
