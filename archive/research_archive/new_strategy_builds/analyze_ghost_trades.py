"""
Ghost Trade Analysis - Gem_Ni's Post-Exit Analysis
---------------------------------------------------
Analyzes V6's FTA exits to determine if they were:
- MISSED_WIN: Would have hit target (FTA killed alpha)
- SAVED_LOSS: Would have hit stop (FTA saved money)
- NO_RESULT: Neither (zombie trade)

Decision Matrix:
- If MISSED_WIN > 20%: FTA is burning alpha. Kill it.
- If SAVED_LOSS > MISSED_WIN: FTA is valid. Keep it.
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

def analyze_ghost_trades(symbol, start, end):
    """
    Run V6 strategy and track what happens AFTER FTA exits
    
    For each FTA exit, simulate what would have happened if we held:
    - Check max/min price in next 30 minutes
    - Did it hit 1.0R target?
    - Did it hit -1.0R stop?
    - Neither? (zombie)
    """
    
    print(f"\nAnalyzing {symbol} ghost trades...")
    
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
    or_mask = df['minutes_since_open'] <= 10
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        or_data = df[date_mask & or_mask]
        if len(or_data) > 0:
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= 1.8)
    
    # Track FTA exits and their ghost outcomes
    fta_exits = []
    position = None
    entry_time = None
    entry_price = None
    stop_loss = None
    entry_idx = None
    breakout_seen = False
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_time = df.index[i]
        current_price = df.iloc[i]['close']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_or_low = df.iloc[i]['or_low']
        current_vwap = df.iloc[i]['vwap']
        
        if df.iloc[i]['minutes_since_open'] <= 10:
            continue
        
        # Entry (V6 logic)
        if position is None:
            if df.iloc[i]['breakout'] and not breakout_seen:
                breakout_seen = True
            
            if breakout_seen:
                pullback_zone_low = current_or_high - (0.15 * current_atr)
                pullback_zone_high = current_or_high + (0.15 * current_atr)
                in_pullback = (df.iloc[i]['low'] <= pullback_zone_high) and (df.iloc[i]['high'] >= pullback_zone_low)
                
                if (in_pullback and current_price > current_or_high and 
                    current_price > current_vwap and df.iloc[i]['volume_spike'] >= 1.8):
                    
                    position = 1.0
                    entry_time = current_time
                    entry_price = current_price
                    stop_loss = current_or_low - (0.4 * current_atr)
                    entry_idx = i
                    breakout_seen = False
        
        # FTA exit detection
        elif position is not None:
            time_in_position = (current_time - entry_time).total_seconds() / 60
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            # FTA: 5 min / 0.3R
            if time_in_position >= 5 and current_r < 0.3:
                # Record FTA exit
                fta_exit = {
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'stop_loss': stop_loss,
                    'entry_idx': entry_idx,
                    'exit_idx': i,
                    'risk': risk,
                }
                
                # Analyze next 30 minutes
                future_window = df.iloc[i:min(i+30, len(df))]
                if len(future_window) > 0:
                    max_price = future_window['high'].max()
                    min_price = future_window['low'].min()
                    
                    # Calculate R-multiples
                    max_r = (max_price - entry_price) / risk if risk > 0 else 0
                    min_r = (min_price - entry_price) / risk if risk > 0 else 0
                    
                    # Determine outcome
                    hit_target = max_r >= 1.0  # Would have hit 1R
                    hit_stop = min_price <= stop_loss  # Would have hit stop
                    
                    if hit_target and not hit_stop:
                        outcome = 'MISSED_WIN'
                    elif hit_stop and not hit_target:
                        outcome = 'SAVED_LOSS'
                    elif hit_target and hit_stop:
                        # Check which came first
                        for j in range(len(future_window)):
                            if future_window.iloc[j]['high'] >= entry_price + risk:
                                outcome = 'MISSED_WIN'
                                break
                            if future_window.iloc[j]['low'] <= stop_loss:
                                outcome = 'SAVED_LOSS'
                                break
                    else:
                        outcome = 'ZOMBIE'
                    
                    fta_exit['outcome'] = outcome
                    fta_exit['max_r_after'] = max_r
                    fta_exit['min_r_after'] = min_r
                    fta_exits.append(fta_exit)
                
                position = None
            
            # Also exit on stop or EOD to continue simulation
            elif df.iloc[i]['low'] <= stop_loss or (df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55):
                position = None
    
    return pd.DataFrame(fta_exits)

# Run analysis
symbols = ['RIOT', 'MARA', 'AMC']
all_results = []

for symbol in symbols:
    result = analyze_ghost_trades(symbol, '2024-11-01', '2025-01-17')
    all_results.append(result)

# Combine results
combined = pd.concat(all_results, ignore_index=True)

print("\n" + "="*80)
print("GHOST TRADE ANALYSIS - V6 FTA EXITS")
print("="*80)

if len(combined) > 0:
    print(f"\nTotal FTA exits analyzed: {len(combined)}")
    
    # Outcome distribution
    outcome_counts = combined['outcome'].value_counts()
    outcome_pct = combined['outcome'].value_counts(normalize=True) * 100
    
    print("\n" + "="*80)
    print("OUTCOME DISTRIBUTION")
    print("="*80)
    for outcome in ['MISSED_WIN', 'SAVED_LOSS', 'ZOMBIE']:
        count = outcome_counts.get(outcome, 0)
        pct = outcome_pct.get(outcome, 0)
        print(f"{outcome:15} {count:4} ({pct:5.1f}%)")
    
    # By symbol
    print("\n" + "="*80)
    print("BY SYMBOL")
    print("="*80)
    for symbol in symbols:
        symbol_data = combined[combined['symbol'] == symbol]
        if len(symbol_data) > 0:
            print(f"\n{symbol}:")
            for outcome in ['MISSED_WIN', 'SAVED_LOSS', 'ZOMBIE']:
                count = (symbol_data['outcome'] == outcome).sum()
                pct = count / len(symbol_data) * 100
                print(f"  {outcome:15} {count:4} ({pct:5.1f}%)")
    
    # Decision
    print("\n" + "="*80)
    print("DECISION MATRIX (Gem_Ni)")
    print("="*80)
    
    missed_win_pct = outcome_pct.get('MISSED_WIN', 0)
    saved_loss_pct = outcome_pct.get('SAVED_LOSS', 0)
    
    print(f"MISSED_WIN: {missed_win_pct:.1f}%")
    print(f"SAVED_LOSS: {saved_loss_pct:.1f}%")
    
    if missed_win_pct > 20:
        print("\n⚠️ VERDICT: FTA is burning alpha. KILL IT.")
        print("   (MISSED_WIN > 20%)")
    elif saved_loss_pct > missed_win_pct:
        print("\n✅ VERDICT: FTA is valid. KEEP IT (or refine).")
        print("   (SAVED_LOSS > MISSED_WIN)")
    else:
        print("\n⚡ VERDICT: FTA is marginal. Consider Test 3 (tightening trigger).")
    
    # Save results
    output_path = Path('research/new_strategy_builds/results/ghost_trade_analysis.csv')
    combined.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to: {output_path}")
else:
    print("No FTA exits found to analyze")
