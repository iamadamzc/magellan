"""
Test Disaster Filter Model in True Simulation.

Tests multiple rejection thresholds to find optimal balance.
"""
import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def load_disaster_model():
    model_path = Path('research/ml_position_sizing/models/bear_trap_disaster_filter.pkl')
    with open(model_path, 'rb') as f:
        data = pickle.load(f)
    print(f"Loaded: {data.get('description', 'Unknown')}")
    print(f"  AUC: {data.get('auc', 0):.4f}")
    print(f"  Disaster Recall: {data.get('disaster_recall', 0)*100:.1f}%")
    return data['model'], data['features']

def get_cyclical_features(df):
    minutes = df.index.hour * 60 + df.index.minute
    day_minutes = 1440
    return np.sin(2 * np.pi * minutes / day_minutes), np.cos(2 * np.pi * minutes / day_minutes)

def run_bear_trap_disaster_filter(symbol, df, model, features, disaster_threshold=0.7, use_filter=True):
    """Bear Trap with Disaster Filter."""
    capital = 100000
    params = {
        'RECLAIM_WICK_RATIO_MIN': 0.15,
        'RECLAIM_VOL_MULT': 0.2,
        'RECLAIM_BODY_RATIO_MIN': 0.2,
        'MIN_DAY_CHANGE_PCT': 15.0,
        'STOP_ATR_MULTIPLIER': 0.45,
        'ATR_PERIOD': 14,
        'MAX_HOLD_MINUTES': 30,
        'PER_TRADE_RISK_PCT': 0.02,
        'MAX_POSITION_DOLLARS': 50000,
        'MAX_DAILY_LOSS_PCT': 0.10,
        'MAX_TRADES_PER_DAY': 10,
    }

    # Feature Engineering
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(params['ATR_PERIOD']).mean()
    
    df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    
    df['date_only'] = df.index.date
    df['session_low'] = df.groupby('date_only')['low'].cummin()
    df['session_high'] = df.groupby('date_only')['high'].cummax()
    df['session_open'] = df.groupby('date_only')['open'].transform('first')
    df['session_open'] = df['session_open'].replace(0, np.nan)
    df['day_change_pct'] = ((df['close'] - df['session_open']) / df['session_open']) * 100
    
    df['candle_range'] = df['high'] - df['low']
    df['candle_body'] = abs(df['close'] - df['open'])
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    df['body_ratio'] = df['candle_body'] / df['candle_range'].replace(0, np.inf)

    # ML Features
    if use_filter:
        df['time_sin'], df['time_cos'] = get_cyclical_features(df)
        df['is_late_day'] = (df.index.hour >= 14).astype(int)
        
        # Match training: 7-period lookback
        atr_roll_min = df['atr'].rolling(7).min()
        atr_roll_max = df['atr'].rolling(7).max()
        df['atr_percentile'] = (df['atr'] - atr_roll_min) / (atr_roll_max - atr_roll_min).replace(0, np.inf)
        df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
        
        df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)

    trades = []
    rejections = []
    daily_pnl = {}
    daily_trades = {}
    
    position = None
    entry_price = None
    stop_loss = None
    position_size = 0
    entry_time = None
    support_level = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']): continue
        
        row = df.iloc[i]
        current_date = row['date_only']
        current_price = row['close']
        
        if current_date not in daily_pnl:
            daily_pnl[current_date] = 0
            daily_trades[current_date] = 0
            
        if daily_pnl[current_date] <= -params['MAX_DAILY_LOSS_PCT'] * capital: continue
        if daily_trades[current_date] >= params['MAX_TRADES_PER_DAY']: continue
        
        # ENTRY
        if position is None:
            if row['day_change_pct'] >= -params['MIN_DAY_CHANGE_PCT']: continue
            
            is_reclaim = (
                row['close'] > row['session_low'] and
                row['wick_ratio'] >= params['RECLAIM_WICK_RATIO_MIN'] and
                row['body_ratio'] >= params['RECLAIM_BODY_RATIO_MIN'] and
                row['volume_ratio'] >= (1 + params['RECLAIM_VOL_MULT'])
            )
            
            if is_reclaim:
                # DISASTER FILTER
                if use_filter:
                    X_live = pd.DataFrame([row[features]])
                    prob_disaster = model.predict_proba(X_live)[:, 1][0]
                    
                    if prob_disaster >= disaster_threshold:
                        rejections.append({'prob_disaster': prob_disaster, 'time': row.name})
                        continue  # SKIP this trade
                
                # Sizing
                support_level = row['session_low']
                stop_distance = support_level - (params['STOP_ATR_MULTIPLIER'] * row['atr'])
                risk_per_share = current_price - stop_distance
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
                    entry_time = row.name
        
        # EXIT (simplified for PnL tracking)
        elif position is not None:
            if row['low'] <= stop_loss:
                pnl_dollars = (stop_loss - entry_price) * position_size * position
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1
                position = None
                continue
            
            hold_mins = (row.name - entry_time).total_seconds() / 60
            if hold_mins >= params['MAX_HOLD_MINUTES'] or (row.name.hour >= 15 and row.name.minute >= 55):
                pnl_dollars = (current_price - entry_price) * position_size * position
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                daily_trades[current_date] += 1
                position = None

    return trades, rejections

def run_threshold_sweep():
    tickers = ['GOEV', 'MULN', 'NKLA']
    cache_dir = Path('data/cache/equities')
    
    print("\n" + "="*70)
    print("DISASTER FILTER THRESHOLD SWEEP")
    print("="*70)
    
    model, features = load_disaster_model()
    
    thresholds = [0.5, 0.6, 0.7, 0.8]
    results = {}
    
    for threshold in thresholds:
        print(f"\n{'='*70}")
        print(f"Testing Threshold: {threshold} (Reject if prob_disaster >= {threshold})")
        print(f"{'='*70}")
        
        total_pnl = 0
        total_trades = 0
        total_rejections = 0
        
        for ticker in tickers:
            files = list(cache_dir.glob(f"{ticker}_1min_*.parquet"))
            file_path = None
            for f in files:
                if "20240101_20241231" in f.name or "20220101_20251231" in f.name:
                    file_path = f
                    break
            
            if not file_path: continue
            
            df = pd.read_parquet(file_path)
            df = df[df.index.year == 2024].copy()
            if len(df) == 0: continue
            
            trades, rejections = run_bear_trap_disaster_filter(ticker, df.copy(), model, features, threshold, use_filter=True)
            pnl = sum(trades)
            total_pnl += pnl
            total_trades += len(trades)
            total_rejections += len(rejections)
            
            print(f"  {ticker}: ${pnl:>8,.0f} | {len(trades):>3} trades | {len(rejections):>3} rejected")
        
        results[threshold] = {
            'pnl': total_pnl,
            'trades': total_trades,
            'rejections': total_rejections
        }
        
        print(f"\n  TOTAL: ${total_pnl:>+8,.0f} from {total_trades} trades ({total_rejections} rejected)")
    
    # Baseline comparison
    print(f"\n{'='*70}")
    print("BASELINE (No Filter)")
    print(f"{'='*70}")
    
    baseline_pnl = 0
    baseline_trades = 0
    for ticker in tickers:
        files = list(cache_dir.glob(f"{ticker}_1min_*.parquet"))
        file_path = None
        for f in files:
            if "20240101_20241231" in f.name or "20220101_20251231" in f.name:
                file_path = f
                break
        
        if not file_path: continue
        
        df = pd.read_parquet(file_path)
        df = df[df.index.year == 2024].copy()
        if len(df) == 0: continue
        
        trades, _ = run_bear_trap_disaster_filter(ticker, df.copy(), model, features, 1.0, use_filter=False)
        pnl = sum(trades)
        baseline_pnl += pnl
        baseline_trades += len(trades)
        
        print(f"  {ticker}: ${pnl:>8,.0f} | {len(trades):>3} trades")
    
    print(f"\n  TOTAL: ${baseline_pnl:>+8,.0f} from {baseline_trades} trades")
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY COMPARISON")
    print(f"{'='*70}")
    print(f"{'Threshold':<12} {'PnL':<15} {'Trades':<10} {'Rejected':<12} {'vs Baseline'}")
    print(f"{'-'*70}")
    print(f"{'Baseline':<12} ${baseline_pnl:>+12,.0f} {baseline_trades:>9}  {'-':>11}  {'—'}")
    
    for threshold in sorted(results.keys()):
        r = results[threshold]
        improvement = r['pnl'] - baseline_pnl
        pct = (improvement / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        print(f"{threshold:<12.1f} ${r['pnl']:>+12,.0f} {r['trades']:>9}  {r['rejections']:>11}  {improvement:>+8,.0f} ({pct:>+5.1f}%)")

if __name__ == "__main__":
    run_threshold_sweep()
