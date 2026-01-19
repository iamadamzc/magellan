"""
ORB V7 for Futures/Commodities
--------------------------------
Same V7 logic, but uses FMP for futures data
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

def run_orb_v7_futures(symbol, start, end, timeframe='1hour'):
    """ORB V7 for futures/commodities"""
    
    params = {
        'OR_MINUTES': 10 if timeframe == '1min' else 1,  # 10 min for intraday, 1 hour for hourly
        'VOL_MULT': 1.8,
        'PULLBACK_ATR': 0.15,
        'HARD_STOP_ATR': 0.4,
        'BREAKEVEN_TRIGGER_R': 0.5,
        'SCALE_13R_PCT': 0.50,
        'TRAIL_ATR': 0.6,
        'MIN_PRICE': 0.0,  # No min price for futures
    }
    
    # Fetch futures data from FMP
    try:
        df = cache.get_or_fetch_futures(symbol, timeframe, start, end)
    except Exception as e:
        print(f"✗ {symbol}: Error fetching data - {e}")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'error': str(e)}
    
    if len(df) == 0:
        print(f"✗ {symbol}: No data returned")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0, 'error': 'No data'}
    
    df = calculate_vwap(df)
    df = calculate_atr(df)
    
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # For futures, calculate "minutes since 9:30 AM" but allow 24-hour trading
    # We'll use session start as the OR period
    df['minutes_since_start'] = np.arange(len(df))
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Calculate OR - first N periods of each day
    or_periods = params['OR_MINUTES']
    df['or_high'] = np.nan
    df['or_low'] = np.nan
    
    for date in df['date'].unique():
        date_mask = df['date'] == date
        date_data = df[date_mask]
        if len(date_data) >= or_periods:
            or_data = date_data.iloc[:or_periods]
            df.loc[date_mask, 'or_high'] = or_data['high'].max()
            df.loc[date_mask, 'or_low'] = or_data['low'].min()
    
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= params['VOL_MULT'])
    
    trades = []
    position = None
    entry_price = None
    stop_loss = None
    highest_price = 0
    breakout_seen = False
    moved_to_be = False
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']):
            continue
        
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_high = df.iloc[i]['high']
        current_atr = df.iloc[i]['atr']
        current_or_high = df.iloc[i]['or_high']
        current_or_low = df.iloc[i]['or_low']
        current_vwap = df.iloc[i]['vwap']
        
        # Skip OR period
        if i % 24 < or_periods:  # Approximate daily reset
            continue
        
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
                    df.iloc[i]['volume_spike'] >= params['VOL_MULT']):
                    
                    position = 1.0
                    entry_price = current_price
                    stop_loss = current_or_low - (params['HARD_STOP_ATR'] * current_atr)
                    highest_price = current_price
                    breakout_seen = False
                    moved_to_be = False
        
        elif position is not None and position > 0:
            risk = entry_price - stop_loss
            current_r = (current_price - entry_price) / risk if risk > 0 else 0
            
            if current_high > highest_price:
                highest_price = current_high
            
            if current_low <= stop_loss:
                pnl_pct = (stop_loss - entry_price) / entry_price * 100 * position
                trades.append({'symbol': symbol, 'pnl_pct': pnl_pct, 'type': 'stop'})
                position = None
                continue
            
            if current_r >= params['BREAKEVEN_TRIGGER_R'] and not moved_to_be:
                stop_loss = entry_price
                moved_to_be = True
            
            if current_r >= 1.3 and position == 1.0:
                pnl_pct = (risk * 1.3) / entry_price * 100 * params['SCALE_13R_PCT']
                trades.append({'symbol': symbol, 'pnl_pct': pnl_pct, 'type': 'scale_13r'})
                position -= params['SCALE_13R_PCT']
            
            if moved_to_be:
                trail_stop = highest_price - (params['TRAIL_ATR'] * current_atr)
                stop_loss = max(stop_loss, trail_stop)
            
            if moved_to_be and current_price < current_vwap:
                pnl_pct = (current_price - entry_price) / entry_price * 100 * position
                trades.append({'symbol': symbol, 'pnl_pct': pnl_pct, 'type': 'vwap_loss'})
                position = None
                continue
    
    if len(trades) == 0:
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    avg_pnl = trades_df['pnl_net'].mean()
    total_pnl = trades_df['pnl_net'].sum()
    
    print(f"✓ {symbol}: {total_trades} trades | {win_rate:.1f}% win | {avg_pnl:+.3f}% avg | {total_pnl:+.2f}% total")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'avg_pnl': avg_pnl,
        'total_pnl': total_pnl,
    }
