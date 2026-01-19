"""
ORB V10 Diagnostic - Show filter rejection reasons
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent
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

def diagnose_orb_v10(symbol, start, end):
    """Diagnostic version showing filter rejection reasons"""
    
    params = {
        'OR_MINUTES': 10,
        'ENTRY_WINDOW_START': 10,
        'ENTRY_WINDOW_END': 60,
        'VOL_MULT': 1.5,
        'MIN_PRICE': 3.0,
        'PDH_COLLISION_ATR': 0.25,
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
    for date in df['date'].unique():
        date_mask = df['date'] == date
        prev_date_data = df[df['date'] < date]
        if len(prev_date_data) > 0:
            prev_day = prev_date_data[prev_date_data['date'] == prev_date_data['date'].max()]
            if len(prev_day) > 0:
                df.loc[date_mask, 'pdh'] = prev_day['high'].max()
    
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
    
    # Filter entry window
    entry_window = df[
        (df['minutes_since_open'] >= params['ENTRY_WINDOW_START']) &
        (df['minutes_since_open'] <= params['ENTRY_WINDOW_END']) &
        (~df['atr'].isna()) &
        (~df['or_high'].isna())
    ].copy()
    
    print(f"\n{'='*80}")
    print(f"ORB V10 DIAGNOSTIC - {symbol}")
    print(f"{'='*80}")
    print(f"Total bars in entry window: {len(entry_window)}")
    
    # Check each filter
    entry_window['breakout'] = entry_window['close'] > entry_window['or_high']
    entry_window['volume_ok'] = entry_window['volume_spike'] >= params['VOL_MULT']
    entry_window['above_vwap'] = entry_window['close'] > entry_window['vwap']
    entry_window['price_ok'] = entry_window['close'] >= params['MIN_PRICE']
    
    # PDH collision
    entry_window['pdh_collision'] = False
    for idx in entry_window.index:
        if not pd.isna(entry_window.loc[idx, 'pdh']):
            distance = abs(entry_window.loc[idx, 'or_high'] - entry_window.loc[idx, 'pdh'])
            if distance < params['PDH_COLLISION_ATR'] * entry_window.loc[idx, 'atr']:
                entry_window.loc[idx, 'pdh_collision'] = True
    
    print(f"\nFilter Pass Rates:")
    print(f"  Breakout (price > OR high):     {entry_window['breakout'].sum():>5} ({entry_window['breakout'].sum()/len(entry_window)*100:>5.1f}%)")
    print(f"  Volume (>= 1.5x avg):           {entry_window['volume_ok'].sum():>5} ({entry_window['volume_ok'].sum()/len(entry_window)*100:>5.1f}%)")
    print(f"  Above VWAP:                     {entry_window['above_vwap'].sum():>5} ({entry_window['above_vwap'].sum()/len(entry_window)*100:>5.1f}%)")
    print(f"  Price >= $3:                    {entry_window['price_ok'].sum():>5} ({entry_window['price_ok'].sum()/len(entry_window)*100:>5.1f}%)")
    print(f"  NOT PDH collision:              {(~entry_window['pdh_collision']).sum():>5} ({(~entry_window['pdh_collision']).sum()/len(entry_window)*100:>5.1f}%)")
    
    # Combined
    entry_window['all_filters'] = (
        entry_window['breakout'] &
        entry_window['volume_ok'] &
        entry_window['above_vwap'] &
        entry_window['price_ok'] &
        (~entry_window['pdh_collision'])
    )
    
    print(f"\n  ALL FILTERS PASS:               {entry_window['all_filters'].sum():>5} ({entry_window['all_filters'].sum()/len(entry_window)*100:>5.1f}%)")
    
    # Show rejection reasons for bars that almost passed
    almost = entry_window[
        (entry_window['breakout']) &
        (entry_window['volume_ok']) &
        (~entry_window['all_filters'])
    ]
    
    if len(almost) > 0:
        print(f"\nBars that had breakout + volume but failed other filters: {len(almost)}")
        print("  Rejection reasons:")
        print(f"    Below VWAP:      {(~almost['above_vwap']).sum()}")
        print(f"    Price < $3:      {(~almost['price_ok']).sum()}")
        print(f"    PDH collision:   {almost['pdh_collision'].sum()}")
    
    # Show sample of passing bars
    passing = entry_window[entry_window['all_filters']]
    if len(passing) > 0:
        print(f"\nSample of bars that PASSED all filters:")
        print(passing[['date', 'minutes_since_open', 'close', 'or_high', 'vwap', 'volume_spike']].head(10))
    
    # Analyze why win rate is low
    print(f"\n{'='*80}")
    print("VWAP ANALYSIS")
    print(f"{'='*80}")
    
    # Check if price tends to stay above VWAP after breakout
    breakouts = entry_window[entry_window['breakout']]
    if len(breakouts) > 0:
        print(f"Total breakouts: {len(breakouts)}")
        print(f"Breakouts above VWAP: {breakouts['above_vwap'].sum()} ({breakouts['above_vwap'].sum()/len(breakouts)*100:.1f}%)")
        print(f"Breakouts with volume: {breakouts['volume_ok'].sum()} ({breakouts['volume_ok'].sum()/len(breakouts)*100:.1f}%)")
        
        # Check what happens AFTER breakout
        print(f"\nWhat happens after breakout + volume?")
        good_breakouts = breakouts[breakouts['volume_ok']]
        if len(good_breakouts) > 0:
            print(f"  Above VWAP: {good_breakouts['above_vwap'].sum()} ({good_breakouts['above_vwap'].sum()/len(good_breakouts)*100:.1f}%)")

# Run diagnostic
diagnose_orb_v10('RIOT', '2024-11-01', '2024-11-30')
