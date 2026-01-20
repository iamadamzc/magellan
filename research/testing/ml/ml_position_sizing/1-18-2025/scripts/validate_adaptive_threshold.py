"""
Final Validation: Adaptive Threshold Disaster Filter
Clean simulation to confirm +166% improvement.

Strategy: ML threshold 0.6 before 2pm, 0.4 after 2pm
Expected: ~$53k vs $20k baseline
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

def run_bear_trap_validation(symbol, df, model, features, use_adaptive=False):
    """Bear Trap with optional adaptive threshold."""
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
    if use_adaptive:
        df['time_sin'], df['time_cos'] = get_cyclical_features(df)
        df['is_late_day'] = (df.index.hour >= 14).astype(int)
        
        atr_roll_min = df['atr'].rolling(7).min()
        atr_roll_max = df['atr'].rolling(7).max()
        df['atr_percentile'] = (df['atr'] - atr_roll_min) / (atr_roll_max - atr_roll_min).replace(0, np.inf)
        df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
        
        df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)

    trades = []
    filtered_count = 0
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
                # ADAPTIVE DISASTER FILTER
                if use_adaptive:
                    X_live = pd.DataFrame([row[features]])
                    prob_disaster = model.predict_proba(X_live)[:, 1][0]
                    
                    # Adaptive threshold based on time
                    threshold = 0.4 if current_hour >= 14 else 0.6
                    
                    if prob_disaster >= threshold:
                        filtered_count += 1
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

    return trades, filtered_count

def main():
    tickers = ['GOEV', 'MULN', 'NKLA']
    cache_dir = Path('data/cache/equities')
    
    print("\n" + "="*80)
    print("ADAPTIVE THRESHOLD DISASTER FILTER - FINAL VALIDATION")
    print("="*80)
    print("\nStrategy: ML Threshold 0.6 (AM) / 0.4 (PM)")
    print("Expected Improvement: +166% vs Baseline\n")
    
    model, features = load_disaster_model()
    
    # Run Baseline
    print("="*80)
    print("BASELINE (No Filter)")
    print("="*80)
    
    baseline_results = {}
    baseline_total_pnl = 0
    baseline_total_trades = 0
    
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
        
        trades, _ = run_bear_trap_validation(ticker, df.copy(), model, features, use_adaptive=False)
        pnl = sum(trades)
        baseline_results[ticker] = {'pnl': pnl, 'trades': len(trades)}
        baseline_total_pnl += pnl
        baseline_total_trades += len(trades)
        
        print(f"{ticker:6} | PnL: ${pnl:>10,.0f} | Trades: {len(trades):>3}")
    
    print(f"{'─'*80}")
    print(f"{'TOTAL':6} | PnL: ${baseline_total_pnl:>10,.0f} | Trades: {baseline_total_trades:>3}")
    
    # Run Adaptive
    print(f"\n{'='*80}")
    print("ADAPTIVE THRESHOLD (0.6 AM / 0.4 PM)")
    print("="*80)
    
    adaptive_results = {}
    adaptive_total_pnl = 0
    adaptive_total_trades = 0
    adaptive_total_filtered = 0
    
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
        
        trades, filtered = run_bear_trap_validation(ticker, df.copy(), model, features, use_adaptive=True)
        pnl = sum(trades)
        adaptive_results[ticker] = {'pnl': pnl, 'trades': len(trades), 'filtered': filtered}
        adaptive_total_pnl += pnl
        adaptive_total_trades += len(trades)
        adaptive_total_filtered += filtered
        
        improvement = pnl - baseline_results[ticker]['pnl']
        print(f"{ticker:6} | PnL: ${pnl:>10,.0f} | Trades: {len(trades):>3} | Filtered: {filtered:>3} | Δ: ${improvement:>+9,.0f}")
    
    print(f"{'─'*80}")
    total_improvement = adaptive_total_pnl - baseline_total_pnl
    pct_improvement = (total_improvement / abs(baseline_total_pnl) * 100) if baseline_total_pnl != 0 else 0
    print(f"{'TOTAL':6} | PnL: ${adaptive_total_pnl:>10,.0f} | Trades: {adaptive_total_trades:>3} | Filtered: {adaptive_total_filtered:>3} | Δ: ${total_improvement:>+9,.0f}")
    
    # Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Baseline PnL:      ${baseline_total_pnl:>10,.0f}  ({baseline_total_trades} trades)")
    print(f"Adaptive PnL:      ${adaptive_total_pnl:>10,.0f}  ({adaptive_total_trades} trades, {adaptive_total_filtered} filtered)")
    print(f"{'─'*80}")
    print(f"Improvement:       ${total_improvement:>+10,.0f}  ({pct_improvement:+.1f}%)")
    print(f"{'='*80}")
    
    if pct_improvement >= 150:
        print("\n✅ VALIDATION PASSED: Exceeded +150% improvement target")
    elif pct_improvement >= 100:
        print("\n✅ VALIDATION PASSED: Exceeded +100% improvement target")
    elif pct_improvement >= 50:
        print("\n⚠️  VALIDATION MARGINAL: Exceeded +50% but below +100% target")
    else:
        print("\n❌ VALIDATION FAILED: Did not meet +50% improvement threshold")

if __name__ == "__main__":
    main()
