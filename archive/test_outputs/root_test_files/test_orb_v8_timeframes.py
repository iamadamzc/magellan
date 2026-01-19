"""
ORB Multi-Timeframe Test
-------------------------
Test SAME V8 logic on different bar sizes:
- 1min (current)
- 5min (likely better)
- 15min (swing style)

Will reveal optimal tempo for ORB strategy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from src.data_cache import cache

def calculate_vwap(df):
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
    df['tp_volume'] = df['typical_price'] * df['volume']
    df['trading_date'] = df.index.date
    df['cumulative_tp_volume'] = df.groupby('trading_date')['tp_volume'].cumsum()
    df['cumulative_volume'] = df.groupby('trading_date')['volume'].cumsum()
    df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']
    return df

def calculate_atr(df, period=14):
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df

def run_orb_v8_timeframe(symbol, start, end, timeframe='1min'):
    """V8 strategy on different timeframes"""
    
    # Adjust OR periods based on timeframe
    if timeframe == '1min':
        or_bars = 10  # 10 min = 10 bars
        vol_window = 20
    elif timeframe == '5min':
        or_bars = 2   # 10 min = 2 bars
        vol_window = 4
    elif timeframe == '15min':
        or_bars = 1   # 15 min = 1 bar (OR is first bar)
        vol_window = 4
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    
    params = {
        'OR_BARS': or_bars,
        'VOL_MULT': 1.8,
        'HARD_STOP_ATR': 0.4,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'SCALE_07R_PCT': 0.50,
        'TRAIL_ATR': 0.6,
        'MIN_PRICE': 3.0,
    }
    
    # Fetch data
    df = cache.get_or_fetch_equity(symbol, timeframe, start, end)
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['trading_date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    df['avg_volume'] = df['volume'].rolling(vol_window).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume'].replace(0, np.inf)
    
    # Calculate OR for each day
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['trading_date'].unique():
        date_mask = df['trading_date'] == date
        date_data = df[date_mask]
        if len(date_data) >= or_bars:
            or_data = date_data.iloc[:or_bars]
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    
    trades = []
    position = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    moved_to_be = False
    bar_in_day = 0
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        # Track bar number in day
        if i == 0 or df.iloc[i]['trading_date'] != df.iloc[i-1]['trading_date']:
            bar_in_day = 0
        else:
            bar_in_day += 1
        
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_or_low = df.iloc[i]['or_low']
        current_vwap = df.iloc[i]['vwap']
        
        # Skip OR period
        if bar_in_day < or_bars:
            continue
        
        # Entry: breakout + volume + VWAP
        if position is None:
            if (df.iloc[i]['breakout'] and
                current_price > current_vwap and
                current_price >= params['MIN_PRICE']):
                
                position = 1.0
                entry_price = current_price
                stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                highest_price = current_price
                moved_to_be = False
        
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            # Hard stop
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'type': 'stop'})
                position = None
                continue
            
            # Breakeven
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            # Scale at 0.7R
            if current_r >= 0.7 and position == 1.0:
                pnl_pct = (risk * 0.7) / entry_price * 100 * params['SCALE_07R_PCT']
                trades.append({'pnl_pct': pnl_pct, 'type': 'scale_07r'})
                position -= params['SCALE_07R_PCT']
            
            # Trail
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            # VWAP loss
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'pnl_pct': pnl_pct, 'type': 'vwap_loss'})
                position = None
                continue
            
            # EOD (last bar of day)
            if i == len(df) - 1 or (i < len(df) - 1 and df.iloc[i+1]['trading_date'] != df.iloc[i]['trading_date']):
                if position > 0:
                    pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                    trades.append({'pnl_pct': pnl_pct, 'type': 'eod'})
                    position = None
    
    if len(trades) == 0:
        return None
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    return {
        'symbol': symbol,
        'timeframe': timeframe,
        'total_trades': len(trades_df),
        'win_rate': (trades_df['pnl_net'] > 0).sum() / len(trades_df) * 100,
        'avg_pnl': trades_df['pnl_net'].mean(),
        'total_pnl': trades_df['pnl_net'].sum(),
    }

# Test symbols
TEST_SYMBOLS = ['RIOT', 'PLTR', 'NVDA', 'MARA', 'COIN']
TIMEFRAMES = ['1min', '5min', '15min']

print("="*80)
print("MULTI-TIMEFRAME ORB V8 TEST")
print("="*80)
print(f"Testing {len(TEST_SYMBOLS)} symbols on {len(TIMEFRAMES)} timeframes")
print("="*80)

results = []
for symbol in TEST_SYMBOLS:
    print(f"\n{symbol}:")
    for tf in TIMEFRAMES:
        try:
            result = run_orb_v8_timeframe(symbol, '2024-11-01', '2025-01-17', tf)
            if result:
                results.append(result)
                print(f"  {tf:>5}: {result['total_trades']:>3} trades | {result['win_rate']:>5.1f}% win | {result['total_pnl']:>+7.2f}%")
        except Exception as e:
            print(f"  {tf:>5}: Error - {str(e)[:50]}")

# Analysis
if results:
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("TIMEFRAME COMPARISON")
    print("="*80)
    
    for tf in TIMEFRAMES:
        tf_data = df[df['timeframe'] == tf]
        if len(tf_data) > 0:
            print(f"\n{tf}:")
            print(f"  Avg trades: {tf_data['total_trades'].mean():.1f}")
            print(f"  Avg win rate: {tf_data['win_rate'].mean():.1f}%")
            print(f"  Avg P&L: {tf_data['total_pnl'].mean():+.2f}%")
            print(f"  Best symbol: {tf_data.nlargest(1, 'total_pnl')['symbol'].iloc[0]} ({tf_data['total_pnl'].max():+.2f}%)")
    
    df.to_csv('research/new_strategy_builds/results/orb_v8_timeframe_test.csv', index=False)
    print(f"\n✅ Saved to: orb_v8_timeframe_test.csv")
    
    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    best_tf = df.groupby('timeframe')['total_pnl'].mean().idxmax()
    print(f"Best timeframe: {best_tf}")
    print(f"Avg P&L: {df[df['timeframe'] == best_tf]['total_pnl'].mean():+.2f}%")
