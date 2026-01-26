"""
Bear Trap Strategy - ML-Enhanced Version (Using Trained Model)

Uses the trained sklearn model to classify regimes.
Skips NO_ADD trades entirely.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import pickle

# Path resolution
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Load trained model
MODEL_PATH = Path(__file__).parent / 'models' / 'bear_trap_regime_classifier.pkl'
with open(MODEL_PATH, 'rb') as f:
    model_data = pickle.load(f)
    MODEL = model_data['model']
    FEATURES = model_data['features']

print(f"✓ Loaded ML model with features: {FEATURES}")

def classify_regime(row, df_minute, entry_idx):
    """
    Classify trade regime using trained ML model.
    
    Returns: 'ADD_ALLOWED', 'ADD_NEUTRAL', or 'NO_ADD'
    """
    # Calculate features (same as training)
    
    # Feature 1: Time score (late session = 1)
    entry_hour = row.name.hour
    time_score = 1 if entry_hour >= 15 else 0
    
    # Feature 2: Momentum score (fast reclaim = 2)
    # Use max_profit as proxy for reclaim speed
    # (In real-time, we'd calculate actual reclaim speed)
    # For now, use a simple heuristic based on recent price action
    lookback = min(30, entry_idx)
    if lookback > 0:
        recent_data = df_minute.iloc[entry_idx-lookback:entry_idx+1]
        price_change = (row['close'] - recent_data['low'].min()) / recent_data['low'].min() * 100
        bars_since_low = lookback
        reclaim_speed = price_change / bars_since_low if bars_since_low > 0 else 0
        momentum_score = 2 if reclaim_speed > 0.5 else 0
    else:
        momentum_score = 0
    
    # Feature 3: Volume score (high volume = 1)
    vol_score = 1 if row.get('volume_ratio', 1.0) > 2.0 else 0
    
    # Create feature vector
    features = pd.DataFrame([[time_score, momentum_score, vol_score]], columns=FEATURES)
    
    # Predict
    prediction = MODEL.predict(features)[0]
    
    return prediction

def run_bear_trap_ml(symbol, start, end):
    """
    Run Bear Trap with trained ML model.
    Skips NO_ADD trades entirely.
    """
    print(f"\nTesting {symbol} - ML-Enhanced Bear Trap [{start} to {end}]")
    
    # Fetch 1-minute data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        print(f"0 trades (no data)")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0, 'avg_r': 0}
    
    # Add time features
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute
    
    # Calculate ATR
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
        
        # Entry logic
        if position is None:
            if day_change <= -15:
                is_reclaim = (
                    df.iloc[i]['close'] > session_low and
                    df.iloc[i]['wick_ratio'] >= 0.15 and
                    df.iloc[i]['body_ratio'] >= 0.2 and
                    df.iloc[i]['volume_ratio'] >= 1.2
                )
                
                if is_reclaim:
                    # ML FILTER
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
                
                trades.append({
                    'pnl_pct': pnl_pct,
                    'r': r_multiple,
                    'type': 'stop' if current_low <= stop_loss else 'time'
                })
                
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
    print("BEAR TRAP - ML-ENHANCED (Trained Model)")
    print("="*80)
    print(f"Period: {start} to {end}\n")
    
    results = []
    for symbol in symbols:
        result = run_bear_trap_ml(symbol, start, end)
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
