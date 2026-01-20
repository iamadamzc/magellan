"""
True Simulation Backtest for Bear Trap (2024 Baseline Cohort)
Evaluates Performance with active ML Filtering in the loop.

Cohort: GOEV, MULN, NKLA
Year: 2024
Data: Local Cache (1-min Intraday)
Model: bear_trap_enhanced_xgb.pkl
"""
import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path
from datetime import datetime

# Adjust path to find src
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def load_model():
    model_path = Path('research/ml_position_sizing/models/bear_trap_enhanced_xgb.pkl')
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
    print(f"Loaded ML Model: {data.get('description', 'Unknown')}")
    return data['model']

# Cyclical time feature helper
def get_cyclical_features(df):
    minutes = df.index.hour * 60 + df.index.minute
    day_minutes = 1440
    return np.sin(2 * np.pi * minutes / day_minutes), np.cos(2 * np.pi * minutes / day_minutes)

def run_bear_trap_ml(symbol, df, model, use_ml=True):

    """
    Bear Trap Strategy Engine with ML Injection.
    """
    capital = 100000
    params = {
        'RECLAIM_WICK_RATIO_MIN': 0.15,
        'RECLAIM_VOL_MULT': 0.2,
        'RECLAIM_BODY_RATIO_MIN': 0.2,
        'MIN_DAY_CHANGE_PCT': 15.0,
        'SUPPORT_MODE': 'session_low',
        'STOP_ATR_MULTIPLIER': 0.45,
        'ATR_PERIOD': 14,
        'SCALE_TP1_PCT': 40,
        'SCALE_TP2_PCT': 30,
        'RUNNER_PCT': 30,
        'MAX_HOLD_MINUTES': 30,
        'PER_TRADE_RISK_PCT': 0.02,
        'MAX_POSITION_DOLLARS': 50000,
        'MAX_DAILY_LOSS_PCT': 0.10,
        'MAX_TRADES_PER_DAY': 10,
    }

    # --- Feature Engineering for Strategy ---
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(params['ATR_PERIOD']).mean()
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    # Session Low Accumulator (No Lookahead)
    df['date_only'] = df.index.date
    # Fix: session_low/high should be per-symbol logic, but here we process 1 ticker dataframe at a time.
    # Groupby date_only is correct.
    df['session_low'] = df.groupby('date_only')['low'].cummin()
    df['session_high'] = df.groupby('date_only')['high'].cummax()
    df['session_open'] = df.groupby('date_only')['open'].transform('first')
    
    # Fix: replace 0 session_open to avoid div by zero
    df['session_open'] = df['session_open'].replace(0, np.nan)
    df['day_change_pct'] = ((df['close'] - df['session_open']) / df['session_open']) * 100

    
    # Candle metrics
    df['candle_range'] = df['high'] - df['low']
    df['candle_body'] = abs(df['close'] - df['open'])
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    df['body_ratio'] = df['candle_body'] / df['candle_range'].replace(0, np.inf)

    # --- ML Specific Features ---
    if use_ml:
        df['time_sin'], df['time_cos'] = get_cyclical_features(df)
        
        # FIX: ATR Percentile is LOCAL 20-period Min-Max (Stochastic ATR)
        # BUT: Extraction script calculated ATR on a 20-bar slice with 14-bar warmup.
        # This leaves only 7 valid ATR values (indices 14-20).
        # So effective min/max lookback was 7 bars.
        atr_roll_min = df['atr'].rolling(7).min()
        atr_roll_max = df['atr'].rolling(7).max()
        df['atr_percentile'] = (df['atr'] - atr_roll_min) / (atr_roll_max - atr_roll_min).replace(0, np.inf)
        df['atr_percentile'] = df['atr_percentile'].fillna(0.5) 
        # If max == min, replace(0, inf) makes it 0. Which is technically correct (no range).
        # Actually max-min=0 means flat ATR. 
        
        df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)
        
        ml_features = ['time_sin', 'time_cos', 'volume_ratio', 'day_change_pct', 'atr_percentile', 'vol_volatility_ratio']
    
    # --- Simulation Loop ---
    trades = []
    daily_pnl = {}
    daily_trades = {}
    
    position = None
    entry_price = None
    stop_loss = None
    position_size = 0
    highest_price = 0
    entry_time = None
    support_level = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']): continue
        
        # Pull Row Data
        row = df.iloc[i]
        current_date = row['date_only']
        current_time_idx = row.name # DatetimeIndex
        current_price = row['close']
        
        # Init Day
        if current_date not in daily_pnl:
            daily_pnl[current_date] = 0
            daily_trades[current_date] = 0
            
        # Risk Gates
        if daily_pnl[current_date] <= -params['MAX_DAILY_LOSS_PCT'] * capital: continue
        if daily_trades[current_date] >= params['MAX_TRADES_PER_DAY']: continue
        
        # ENTRY
        if position is None:
            # Baseline Filter: Down 15%
            if row['day_change_pct'] >= -params['MIN_DAY_CHANGE_PCT']: continue
            
            # Reclaim Logic
            is_reclaim = (
                row['close'] > row['session_low'] and
                row['wick_ratio'] >= params['RECLAIM_WICK_RATIO_MIN'] and
                row['body_ratio'] >= params['RECLAIM_BODY_RATIO_MIN'] and
                row['volume_ratio'] >= (1 + params['RECLAIM_VOL_MULT'])
            )
            
            if is_reclaim:
                # ML GATE
                if use_ml:
                    # Predict live
                    # Reshape for single prediction
                    X_live = pd.DataFrame([row[ml_features]])
                    prob = model.predict_proba(X_live)[:, 1][0]
                    if prob < 0.50:
                        # DEBUG: If this would have been a winner, why did we reject?
                        # Approximate "Winner" check: look ahead (cheating just for debug print)
                        # We can't easily look ahead here without complex logic.
                        # Instead, print features for ALL rejections if strict debug mode on.
                        # Let's just print features for first 5 rejections of MULN to see values.
                        if symbol == 'MULN': 
                             # Print rejections to debug why winners are killed
                             print(f"REJECT: Time={row.name} Prob={prob:.2f} ATR%={row['atr_percentile']:.2f}")
                        continue # REJECTED BY ML
                
                if params.get('DEBUG_MULN') and symbol == 'MULN':
                     print(f"ACCEPTED: Features={row[ml_features].to_dict()}")
                
                # Sizing
                support_level = row['session_low']
                stop_distance = support_level - (params['STOP_ATR_MULTIPLIER'] * row['atr'])
                risk_per_share = current_price - stop_distance
                
                # CHECK: If we are here, we passed ML or ML is off.
                # If we are verifying ML (use_ml=True) and we are about to take a trade
                # We want to know if we inadvertently kept LOSERS.
                
                if risk_per_share <= 0: continue
                
                risk_dollars = capital * params['PER_TRADE_RISK_PCT']
                shares = int(risk_dollars / risk_per_share)
                position_dollars = shares * current_price
                if position_dollars > params['MAX_POSITION_DOLLARS']:
                    shares = int(params['MAX_POSITION_DOLLARS'] / current_price)
                
                if shares > 0:
                    position = 1.0
                    position_size = shares
                    entry_price = current_price
                    stop_loss = stop_distance
                    highest_price = current_price
                    entry_time = current_time_idx
        
        # EXIT
        elif position is not None:
            # Update High
            if row['high'] > highest_price: highest_price = row['high']
            
            # Stop Loss
            if row['low'] <= stop_loss:
                pnl_dollars = (stop_loss - entry_price) * position_size * position
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1
                position = None
                continue
            
            # TP1 (40% at mid range)
            mid_range = entry_price + ((row['session_high'] - entry_price) * 0.5)
            if row['high'] >= mid_range and position == 1.0:
                scale_qty = params['SCALE_TP1_PCT'] / 100
                pnl_dollars = (mid_range - entry_price) * position_size * scale_qty
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                capital += pnl_dollars
                position -= scale_qty
            
            # TP2 (30% at HOD)
            if row['high'] >= row['session_high'] and position >= (params['SCALE_TP2_PCT']/100):
                scale_qty = params['SCALE_TP2_PCT'] / 100
                pnl_dollars = (row['session_high'] - entry_price) * position_size * scale_qty
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                capital += pnl_dollars
                position -= scale_qty
                stop_loss = support_level # Move stop to breakeven/support
            
            # Time Stop (30 mins)
            hold_mins = (current_time_idx - entry_time).total_seconds() / 60
            if hold_mins >= params['MAX_HOLD_MINUTES']:
                pnl_dollars = (current_price - entry_price) * position_size * position
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1
                position = None
                continue
                
            # EOD Stop
            if row.name.hour >= 15 and row.name.minute >= 55:
                pnl_dollars = (current_price - entry_price) * position_size * position
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1
                position = None
                continue

    return trades

def run_simulation():
    tickers = ['GOEV', 'MULN', 'NKLA']
    cache_dir = Path('data/cache/equities')
    
    print("\nStarting True Simulation (Engine Replay)...")
    model = load_model()
    
    total_baseline_pnl = 0
    total_ml_pnl = 0
    
    for ticker in tickers:
        print(f"\nProcessing {ticker}...")
        # Find 2024 Parquet
        # Try specific 1min 2024 file or 2022-2025 combined
        files = list(cache_dir.glob(f"{ticker}_1min_*.parquet"))
        file_path = None
        # Prefer specific 2024 range if exists
        for f in files:
            if "20240101_20241231" in f.name:
                file_path = f
                break
        
        if not file_path:
            # Fallback to wider range
            for f in files:
                 if "20220101_20251231" in f.name:
                     file_path = f
                     break
                     
        if not file_path:
            print(f"No cache file found for {ticker}")
            continue
            
        print(f"Loading {file_path.name}")
        df = pd.read_parquet(file_path)
        
        # Filter for 2024
        df = df[df.index.year == 2024].copy()
        if len(df) == 0:
            print("No 2024 data in file.")
            continue
            
        # Run Baseline
        print(" -> Running Baseline...")
        trades_base = run_bear_trap_ml(ticker, df.copy(), model, use_ml=False)
        pnl_base = sum(trades_base)
        total_baseline_pnl += pnl_base
        print(f"    Baseline PnL: ${pnl_base:,.2f} ({len(trades_base)} fills/scales)")
        
        # Run ML
        print(" -> Running ML Enhanced...")
        trades_ml = run_bear_trap_ml(ticker, df.copy(), model, use_ml=True)
        pnl_ml = sum(trades_ml)
        total_ml_pnl += pnl_ml
        print(f"    ML PnL:       ${pnl_ml:,.2f} ({len(trades_ml)} fills/scales)")

    print("\n" + "="*40)
    print("FINAL SIMULATION RESULTS (2024)")
    print("="*40)
    print(f"Baseline Total PnL: ${total_baseline_pnl:+,.2f}")
    print(f"ML Enhanced PnL:    ${total_ml_pnl:+,.2f}")
    
    diff = total_ml_pnl - total_baseline_pnl
    print(f"Net Difference:     ${diff:+,.2f}")

if __name__ == "__main__":
    run_simulation()
