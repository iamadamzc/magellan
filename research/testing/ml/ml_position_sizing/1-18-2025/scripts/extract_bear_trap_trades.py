"""
Extract Historical Bear Trap Trades for ML Training

This script runs Bear Trap strategy on historical data and saves ALL trades
with detailed metrics for regime labeling.

Output: CSV with each trade's entry, exit, path, and outcome
Purpose: Training data for ML regime classifier
"""
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Path: scripts/ -> ml_position_sizing/ -> research/ -> root (4 levels up)
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# Import Bear Trap strategy directly
# Don't use run_bear_trap - we'll implement inline for better control

from src.data_cache import cache

# Symbols to extract (Bear Trap validated symbols)
SYMBOLS = ['MULN', 'ONDS', 'NKLA', 'AMC', 'SENS', 'ACB', 'GOEV', 'BTCS', 'WKHS']

# Time periods
PERIODS = [
    ('2020-01-01', '2020-12-31'),
    ('2021-01-01', '2021-12-31'),
    ('2022-01-01', '2022-12-31'),
    ('2023-01-01', '2023-12-31'),
    ('2024-01-01', '2024-12-31'),
]

def calculate_regime_features_at_entry(df, entry_idx, symbol):
    """
    Calculate market regime features at trade entry
    
    These are the features ML will use to predict optimal scaling template
    """
    try:
        # Need at least 20 bars before entry for indicators
        if entry_idx < 20:
            return None
        
        # Get window before entry (no look-ahead!)
        window = df.iloc[max(0, entry_idx-20):entry_idx+1].copy()
        
        # Calculate ATR
        window['h_l'] = window['high'] - window['low']
        window['h_pc'] = abs(window['high'] - window['close'].shift(1))
        window['l_pc'] = abs(window['low'] - window['close'].shift(1))
        window['tr'] = window[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        window['atr'] = window['tr'].rolling(14).mean()
        
        current_atr = window['atr'].iloc[-1]
        atr_20 = window['atr'].rolling(20).mean().iloc[-1]
        
        # ATR percentile (where is current ATR in recent history?)
        atr_percentile = (current_atr - window['atr'].min()) / (window['atr'].max() - window['atr'].min())
        
        # Trend strength (simple: higher highs count)
        higher_highs = (window['high'] > window['high'].shift(1)).sum()
        trend_strength = higher_highs / len(window)
        
        # Volume regime
        avg_volume = window['volume'].rolling(20).mean().iloc[-1]
        current_volume = window['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Day change at entry
        session_open = window['open'].iloc[0]
        current_price = window['close'].iloc[-1]
        day_change_pct = ((current_price - session_open) / session_open) * 100
        
        return {
            'atr': current_atr,
            'atr_percentile': atr_percentile,
            'trend_strength': trend_strength,
            'volume_ratio': volume_ratio,
            'day_change_pct': day_change_pct,
        }
    
    except Exception as e:
        print(f"Error calculating features for {symbol}: {e}")
        return None

def extract_trades_from_period(symbol, start, end):
    """
    Run Bear Trap and extract individual trade details
    """
    print(f"\nExtracting {symbol} trades: {start} to {end}")
    
    try:
        # Fetch 1-minute data
        df = cache.get_or_fetch_equity(symbol, '1min', start, end)
        if df is None or len(df) == 0:
            print(f"  No data for {symbol}")
            return []
        
        # Run Bear Trap logic (simplified version for trade extraction)
        trades = run_bear_trap_with_details(df, symbol)
        
        print(f"  Found {len(trades)} trades")
        return trades
        
    except Exception as e:
        print(f"  Error: {e}")
        return []

def run_bear_trap_with_details(df, symbol):
    """
    Modified Bear Trap that captures detailed trade information
    
    Returns list of trade dictionaries with:
    - Entry/exit details
    - Path metrics (max favorable, max adverse)
    - Regime features at entry
    - Outcome labels
    """
    # Add time features
    df['date'] = df.index.date
    df['time'] = df.index.time
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # Calculate ATR
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # Session metrics (NO LOOKAHEAD - use cumulative)
    df['session_low'] = df.groupby('date')['low'].cummin()  # Running minimum
    df['session_high'] = df.groupby('date')['high'].cummax()  # Running maximum
    df['session_open'] = df.groupby('date')['open'].transform('first')  # First is OK
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
    position = None
    entry_idx = None
    entry_price = None
    stop_loss = None
    max_profit = 0
    max_loss = 0
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']):
            continue
        
        current_price = df.iloc[i]['close']
        current_high = df.iloc[i]['high']
        current_low = df.iloc[i]['low']
        current_atr = df.iloc[i]['atr']
        session_low = df.iloc[i]['session_low']
        day_change = df.iloc[i]['day_change_pct']
        
        # Entry logic (simplified)
        if position is None:
            if day_change <= -15:  # Down big
                is_reclaim = (
                    df.iloc[i]['close'] > session_low and
                    df.iloc[i]['wick_ratio'] >= 0.15 and
                    df.iloc[i]['body_ratio'] >= 0.2 and
                    df.iloc[i]['volume_ratio'] >= 1.2
                )
                
                if is_reclaim:
                    position = 1
                    entry_idx = i
                    entry_price = current_price
                    stop_loss = session_low - (0.45 * current_atr)
                    max_profit = 0
                    max_loss = 0
        
        # Position management
        elif position == 1:
            # Track max favorable/adverse excursion
            profit_pct = ((current_high - entry_price) / entry_price) * 100
            loss_pct = ((entry_price - current_low) / entry_price) * 100
            
            max_profit = max(max_profit, profit_pct)
            max_loss = max(max_loss, loss_pct)
            
            # Exit conditions (simplified - just 30 min time stop)
            bars_held = i - entry_idx
            if bars_held >= 30 or current_low <= stop_loss:
                # Trade complete - record it
                exit_price = stop_loss if current_low <= stop_loss else current_price
                
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                risk = entry_price - stop_loss
                r_multiple = (exit_price - entry_price) / risk if risk > 0 else 0
                
                # Calculate regime features at entry
                features = calculate_regime_features_at_entry(df, entry_idx, symbol)
                
                if features:
                    trade = {
                        'symbol': symbol,
                        'entry_date': df.index[entry_idx],
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'stop_loss': stop_loss,
                        'pnl_pct': pnl_pct,
                        'r_multiple': r_multiple,
                        'max_profit': max_profit,
                        'max_loss': max_loss,
                        'bars_held': bars_held,
                        'exit_reason': 'stop' if current_low <= stop_loss else 'time',
                        **features  # Add all regime features
                    }
                    trades.append(trade)
                
                position = None
    
    return trades

def main():
    print("="*80)
    print("BEAR TRAP HISTORICAL TRADE EXTRACTION")
    print("="*80)
    print("Purpose: Generate training data for ML regime classifier\n")
    
    all_trades = []
    
    for start, end in PERIODS:
        print(f"\n{'='*80}")
        print(f"Period: {start} to {end}")
        print(f"{'='*80}")
        
        for symbol in SYMBOLS:
            trades = extract_trades_from_period(symbol, start, end)
            all_trades.extend(trades)
    
    # Save to CSV
    if all_trades:
        df = pd.DataFrame(all_trades)
        output_path = Path('research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        print(f"\n{'='*80}")
        print(f"EXTRACTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total trades extracted: {len(all_trades)}")
        print(f"Saved to: {output_path}")
        print(f"\nNext step: Label these trades with regime using label_regime.py")
    else:
        print("\nNo trades found!")

if __name__ == "__main__":
    main()
