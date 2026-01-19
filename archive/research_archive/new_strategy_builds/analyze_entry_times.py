"""
Analyze Entry Times - When are we actually entering trades?
------------------------------------------------------------
Run V7 and log all entry times to see if we're trading during ORB window
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

def analyze_entry_times(symbol, start, end):
    """Run V7 logic but track entry times"""
    
    params = {
        'OR_MINUTES': 10,
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'MIN_PRICE': 3.0,
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
    
    # Track entries
    entries = []
    position = None
    breakout_seen = False
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_vwap = df.iloc[i]['vwap']
        minutes_since_open = df.iloc[i]['minutes_since_open']
        
        if minutes_since_open <= params['OR_MINUTES']:
            continue
        
        # Entry logic (V7)
        if position is None:
            if df.iloc[i]['breakout'] and not breakout_seen:
                breakout_seen = True
            
            if breakout_seen:
                pullback_zone_low = current_or_high - (params['PULLBACK_ATR'] * current_atr)
                pullback_zone_high = current_or_high + (params['PULLBACK_ATR'] * current_atr)
                in_pullback = (df.iloc[i]['low'] <= pullback_zone_high) and (df.iloc[i]['high'] >= pullback_zone_low)
                
                if (in_pullback and current_price > current_or_high and 
                    current_price > current_vwap and df.iloc[i]['volume_spike'] >= params['VOL_MULT'] and
                    current_price >= params['MIN_PRICE']):
                    
                    # ENTRY!
                    entries.append({
                        'symbol': symbol,
                        'entry_time': current_time,
                        'entry_hour': df.iloc[i]['hour'],
                        'entry_minute': df.iloc[i]['minute'],
                        'minutes_since_open': minutes_since_open,
                        'entry_price': current_price,
                    })
                    
                    position = 1.0
                    breakout_seen = False
        
        # Simple exit (just to reset position)
        elif position is not None:
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55:
                position = None
    
    return pd.DataFrame(entries)

# Test on RIOT
print("="*80)
print("ENTRY TIME ANALYSIS - RIOT")
print("="*80)

entries = analyze_entry_times('RIOT', '2024-11-01', '2025-01-17')

if len(entries) > 0:
    print(f"\nTotal entries: {len(entries)}")
    
    # Time distribution
    print("\n" + "="*80)
    print("ENTRY TIME DISTRIBUTION")
    print("="*80)
    
    # By hour
    print("\nBy Hour:")
    hour_dist = entries['entry_hour'].value_counts().sort_index()
    for hour, count in hour_dist.items():
        pct = count / len(entries) * 100
        bar = "█" * int(pct / 2)
        print(f"  {hour:02d}:00 | {count:3} ({pct:5.1f}%) {bar}")
    
    # By minutes since open
    print("\nBy Minutes Since Open:")
    bins = [0, 10, 20, 30, 60, 120, 180, 240, 300, 400]
    labels = ['0-10', '10-20', '20-30', '30-60', '60-120', '120-180', '180-240', '240-300', '300+']
    entries['time_bin'] = pd.cut(entries['minutes_since_open'], bins=bins, labels=labels)
    
    time_dist = entries['time_bin'].value_counts().sort_index()
    for bin_label, count in time_dist.items():
        pct = count / len(entries) * 100
        bar = "█" * int(pct / 2)
        print(f"  {bin_label:10} min | {count:3} ({pct:5.1f}%) {bar}")
    
    # ORB window analysis
    print("\n" + "="*80)
    print("ORB WINDOW ANALYSIS")
    print("="*80)
    
    orb_window = entries[entries['minutes_since_open'] <= 30]  # First 30 min
    non_orb = entries[entries['minutes_since_open'] > 30]
    
    print(f"\nEntries in ORB window (0-30 min): {len(orb_window)} ({len(orb_window)/len(entries)*100:.1f}%)")
    print(f"Entries outside ORB window (30+ min): {len(non_orb)} ({len(non_orb)/len(entries)*100:.1f}%)")
    
    # Ideal ORB window (10-30 min)
    ideal_orb = entries[(entries['minutes_since_open'] > 10) & (entries['minutes_since_open'] <= 30)]
    print(f"\nEntries in IDEAL ORB window (10-30 min): {len(ideal_orb)} ({len(ideal_orb)/len(entries)*100:.1f}%)")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if len(non_orb) / len(entries) > 0.5:
        print("⚠️ PROBLEM: Over 50% of entries are OUTSIDE the ORB window!")
        print("   We're trading random breakouts all day, not ORB setups.")
        print("\n   RECOMMENDATION: Restrict entries to 9:40-10:00 AM (10-30 min window)")
    else:
        print("✅ GOOD: Most entries are within ORB window")
    
    # Save
    output_path = Path('research/new_strategy_builds/results/entry_time_analysis.csv')
    entries.to_csv(output_path, index=False)
    print(f"\n✅ Full entry log saved to: {output_path}")
else:
    print("No entries found")
