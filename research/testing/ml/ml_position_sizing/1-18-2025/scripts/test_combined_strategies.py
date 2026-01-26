"""
Test Combined Time + ML Filtering Strategies.

Strategies to test:
1. Baseline (no filter)
2. ML 0.5 (Phase 1 winner)
3. Skip after 2pm (simple time filter)
4. ML 0.5 + Skip after 2pm (combined)
5. Adaptive: ML 0.6 before 2pm, ML 0.4 after 2pm
6. Adaptive: ML 0.6 before 2pm, ML 0.3 after 2pm
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
    return data['model'], data['features']

def get_cyclical_features(df):
    minutes = df.index.hour * 60 + df.index.minute
    day_minutes = 1440
    return np.sin(2 * np.pi * minutes / day_minutes), np.cos(2 * np.pi * minutes / day_minutes)

def run_bear_trap_adaptive(symbol, df, model, features, strategy='baseline'):
    """
    Bear Trap with Adaptive Filtering.
    
    Strategies:
    - 'baseline': No filter
    - 'ml_05': ML threshold 0.5
    - 'time_2pm': Skip all trades after 2pm
    - 'ml_05_time': ML 0.5 + skip after 2pm
    - 'adaptive_1': ML 0.6 before 2pm, 0.4 after 2pm
    - 'adaptive_2': ML 0.6 before 2pm, 0.3 after 2pm
    """
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
    df['wick_ratio'] = df['lower_wick'] / df['candle_range'].replace(0, np.inf)
    df['body_ratio'] = df['candle_body'] / df['candle_range'].replace(0, np.inf)

    # ML Features
    if strategy != 'baseline' and strategy != 'time_2pm':
        df['time_sin'], df['time_cos'] = get_cyclical_features(df)
        df['is_late_day'] = (df.index.hour >= 14).astype(int)
        
        atr_roll_min = df['atr'].rolling(7).min()
        atr_roll_max = df['atr'].rolling(7).max()
        df['atr_percentile'] = (df['atr'] - atr_roll_min) / (atr_roll_max - atr_roll_min).replace(0, np.inf)
        df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
        
        df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)

    trades = []
    rejections = {'time': 0, 'ml': 0}
    daily_pnl = {}
    daily_trades = {}
    
    position = None
    entry_price = None
    stop_loss = None
    position_size = 0
    entry_time = None
    
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']): continue
        
        row = df.iloc[i]
        current_date = row['date_only']
        current_price = row['close']
        current_hour = row.name.hour
        
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
                # STRATEGY-SPECIFIC FILTERING
                skip = False
                
                if strategy == 'time_2pm':
                    if current_hour >= 14:
                        rejections['time'] += 1
                        skip = True
                
                elif strategy == 'ml_05':
                    X_live = pd.DataFrame([row[features]])
                    prob_disaster = model.predict_proba(X_live)[:, 1][0]
                    if prob_disaster >= 0.5:
                        rejections['ml'] += 1
                        skip = True
                
                elif strategy == 'ml_05_time':
                    # Time filter first
                    if current_hour >= 14:
                        rejections['time'] += 1
                        skip = True
                    else:
                        # ML filter
                        X_live = pd.DataFrame([row[features]])
                        prob_disaster = model.predict_proba(X_live)[:, 1][0]
                        if prob_disaster >= 0.5:
                            rejections['ml'] += 1
                            skip = True
                
                elif strategy == 'adaptive_1':
                    X_live = pd.DataFrame([row[features]])
                    prob_disaster = model.predict_proba(X_live)[:, 1][0]
                    threshold = 0.4 if current_hour >= 14 else 0.6
                    if prob_disaster >= threshold:
                        rejections['ml'] += 1
                        skip = True
                
                elif strategy == 'adaptive_2':
                    X_live = pd.DataFrame([row[features]])
                    prob_disaster = model.predict_proba(X_live)[:, 1][0]
                    threshold = 0.3 if current_hour >= 14 else 0.6
                    if prob_disaster >= threshold:
                        rejections['ml'] += 1
                        skip = True
                
                if skip:
                    continue
                
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
        
        # EXIT (simplified)
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

def run_combined_test():
    tickers = ['GOEV', 'MULN', 'NKLA']
    cache_dir = Path('data/cache/equities')
    
    print("\n" + "="*80)
    print("COMBINED TIME + ML FILTERING TEST")
    print("="*80)
    
    model, features = load_disaster_model()
    
    strategies = [
        ('baseline', 'Baseline (No Filter)'),
        ('ml_05', 'ML Filter 0.5'),
        ('time_2pm', 'Skip After 2pm'),
        ('ml_05_time', 'ML 0.5 + Skip After 2pm'),
        ('adaptive_1', 'Adaptive (0.6 AM / 0.4 PM)'),
        ('adaptive_2', 'Adaptive (0.6 AM / 0.3 PM)'),
    ]
    
    results = {}
    
    for strategy_id, strategy_name in strategies:
        print(f"\n{'='*80}")
        print(f"Testing: {strategy_name}")
        print(f"{'='*80}")
        
        total_pnl = 0
        total_trades = 0
        total_time_rejects = 0
        total_ml_rejects = 0
        
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
            
            trades, rejections = run_bear_trap_adaptive(ticker, df.copy(), model, features, strategy_id)
            pnl = sum(trades)
            total_pnl += pnl
            total_trades += len(trades)
            total_time_rejects += rejections['time']
            total_ml_rejects += rejections['ml']
            
            print(f"  {ticker}: ${pnl:>8,.0f} | {len(trades):>3} trades | ML:{rejections['ml']:>2} Time:{rejections['time']:>2}")
        
        results[strategy_id] = {
            'name': strategy_name,
            'pnl': total_pnl,
            'trades': total_trades,
            'ml_rejects': total_ml_rejects,
            'time_rejects': total_time_rejects
        }
        
        total_rejects = total_ml_rejects + total_time_rejects
        print(f"\n  TOTAL: ${total_pnl:>+8,.0f} | {total_trades} trades | {total_rejects} rejected (ML:{total_ml_rejects} Time:{total_time_rejects})")
    
    # Summary Table
    baseline_pnl = results['baseline']['pnl']
    
    print(f"\n{'='*80}")
    print("FINAL COMPARISON")
    print(f"{'='*80}")
    print(f"{'Strategy':<30} {'PnL':<15} {'Trades':<8} {'Rejected':<12} {'vs Baseline'}")
    print(f"{'-'*80}")
    
    for strategy_id, _ in strategies:
        r = results[strategy_id]
        improvement = r['pnl'] - baseline_pnl
        pct = (improvement / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        total_rejects = r['ml_rejects'] + r['time_rejects']
        
        print(f"{r['name']:<30} ${r['pnl']:>+12,.0f} {r['trades']:>7}  {total_rejects:>11}  {improvement:>+8,.0f} ({pct:>+5.1f}%)")
    
    # Winner announcement
    best_strategy = max(results.items(), key=lambda x: x[1]['pnl'])
    print(f"\n{'='*80}")
    print(f"🏆 WINNER: {best_strategy[1]['name']}")
    print(f"   PnL: ${best_strategy[1]['pnl']:+,.0f}")
    print(f"   Improvement: {((best_strategy[1]['pnl'] - baseline_pnl) / abs(baseline_pnl) * 100):+.1f}%")
    print(f"{'='*80}")

if __name__ == "__main__":
    run_combined_test()
