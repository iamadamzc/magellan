"""
Bear Trap - ML with Entry-Only Features (No Data Leakage)

Uses retrained model with ONLY entry-time features.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Load entry-only model
MODEL_PATH = Path(__file__).parent / 'models' / 'bear_trap_entry_only_classifier.pkl'
with open(MODEL_PATH, 'rb') as f:
    model_data = pickle.load(f)
    MODEL = model_data['model']
    FEATURES = model_data['features']

print(f"✓ Loaded entry-only ML model with features: {FEATURES}")

def classify_regime(row, df_minute, entry_idx):
    """Classify using ONLY entry-time features"""
    
    # Feature 1: Time score (late session)
    time_score = 1 if row.name.hour >= 15 else 0
    
    # Feature 2: Is midweek
    is_midweek = 1 if 1 <= row.name.dayofweek <= 3 else 0
    
    # Feature 3: High volume
    high_volume = 1 if row.get('volume_ratio', 1.0) > 2.0 else 0
    
    # Feature 4: Big drop
    session_data = df_minute[df_minute.index.date == row.name.date()]
    if len(session_data) > 0:
        session_open = session_data['open'].iloc[0]
        day_change = ((row['close'] - session_open) / session_open) * 100
        big_drop = 1 if day_change < -20 else 0
    else:
        big_drop = 0
    
    # Feature 5: High volatility (placeholder - we don't have ATR percentile at entry)
    high_volatility = 0
    
    # Create feature vector
    features = pd.DataFrame([[time_score, is_midweek, high_volume, big_drop, high_volatility]], 
                           columns=FEATURES)
    
    # Predict
    prediction = MODEL.predict(features)[0]
    return prediction

def run_bear_trap_entry_only(symbol, start, end):
    """Bear Trap with entry-only ML model"""
    print(f"\nTesting {symbol} - Entry-Only ML [{start} to {end}]")
    
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        print(f"0 trades (no data)")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_r': 0}
    
    # Setup
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    
    # ATR
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    
    # Session metrics (NO LOOKAHEAD)
    df['session_low'] = df.groupby('date')['low'].cummin()
    df['session_high'] = df.groupby('date')['high'].cummax()
    df['session_open'] = df.groupby('date')['open'].transform('first')
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
    ml_skipped = 0
    position = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']):
            continue
        
        current_price = df.iloc[i]['close']
        current_low = df.iloc[i]['low']
        current_atr = df.iloc[i]['atr']
        session_low = df.iloc[i]['session_low']
        day_change = df.iloc[i]['day_change_pct']
        
        if position is None:
            if day_change <= -15:
                is_reclaim = (
                    df.iloc[i]['close'] > session_low and
                    df.iloc[i]['wick_ratio'] >= 0.15 and
                    df.iloc[i]['body_ratio'] >= 0.2 and
                    df.iloc[i]['volume_ratio'] >= 1.2
                )
                
                if is_reclaim:
                    # ML FILTER (entry-only features)
                    regime = classify_regime(df.iloc[i], df, i)
                    
                    if regime == 'NO_ADD':
                        ml_skipped += 1
                        continue
                    
                    # Take trade
                    position = 1
                    entry_idx = i
                    entry_price = current_price
                    stop_loss = session_low - (0.45 * current_atr)
        
        elif position == 1:
            bars_held = i - entry_idx
            if bars_held >= 30 or current_low <= stop_loss:
                exit_price = stop_loss if current_low <= stop_loss else current_price
                
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                risk = entry_price - stop_loss
                r_multiple = (exit_price - entry_price) / risk if risk > 0 else 0
                
                trades.append({'pnl_pct': pnl_pct, 'r': r_multiple})
                position = None
    
    if len(trades) == 0:
        print(f"0 trades (ML skipped {ml_skipped})")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_r': 0, 'ml_skipped': ml_skipped}
    
    trades_df = pd.DataFrame(trades)
    trades_df['pnl_net'] = trades_df['pnl_pct'] - 0.125
    
    total_trades = len(trades_df)
    win_rate = (trades_df['pnl_net'] > 0).sum() / total_trades * 100
    total_pnl = trades_df['pnl_net'].sum()
    avg_r = trades_df['r'].mean()
    
    print(f"✓ {total_trades} trades | {win_rate:.1f}% win | {total_pnl:+.2f}% total | Avg R: {avg_r:+.2f} | ML skipped: {ml_skipped}")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_r': avg_r,
        'ml_skipped': ml_skipped
    }

if __name__ == "__main__":
    symbols = ['AMC', 'MULN', 'NKLA']
    start = '2024-01-01'
    end = '2024-12-31'
    
    print("="*80)
    print("BEAR TRAP - ENTRY-ONLY ML MODEL")
    print("="*80)
    print(f"Period: {start} to {end}\n")
    
    results = []
    for symbol in symbols:
        result = run_bear_trap_entry_only(symbol, start, end)
        results.append(result)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    df_results = pd.DataFrame(results)
    total_trades = df_results['total_trades'].sum()
    avg_win_rate = df_results['win_rate'].mean()
    total_pnl = df_results['total_pnl'].sum()
    avg_r = df_results['avg_r'].mean()
    total_skipped = df_results['ml_skipped'].sum()
    
    print(f"\nTotal trades: {total_trades}")
    print(f"ML skipped: {total_skipped}")
    print(f"Avg win rate: {avg_win_rate:.1f}%")
    print(f"Total P&L: {total_pnl:+.2f}%")
    print(f"Avg R: {avg_r:+.2f}")
    
    print(f"\nBaseline (no filter): 543 trades, 43.5% WR, +0.15R")
    print(f"Entry-only ML: {total_trades} trades, {avg_win_rate:.1f}% WR, {avg_r:+.2f}R")
