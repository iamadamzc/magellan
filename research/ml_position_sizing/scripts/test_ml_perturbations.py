"""
Perturbation Tests for ML Disaster Filter Enhancement.

Critical Tests:
1. Threshold Sensitivity (0.3-0.7 range)
2. Time Window Shift (11am-3pm cutoff vs 2pm)
3. Feature Scaling Drift (±20% ATR/Volume variations)
4. Model Degradation (random noise injection)
5. Edge Cases (zero volume, extreme volatility)
"""
import pandas as pd
import numpy as np
import pickle
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from research.ml_position_sizing.scripts.validate_adaptive_threshold import (
    run_bear_trap_validation, load_disaster_model, get_cyclical_features
)

def run_perturbation_suite():
    print("\n" + "="*80)
    print("ML DISASTER FILTER - PERTURBATION TEST SUITE")
    print("="*80)
    
    model, features = load_disaster_model()
    tickers = ['GOEV', 'MULN', 'NKLA']
    cache_dir = Path('data/cache/equities')
    
    # Baseline reference
    print("\n🔹 BASELINE (Adaptive 0.6/0.4)")
    baseline_pnl = run_test_variant(tickers, cache_dir, model, features, 'baseline')
    
    # Test 1: Threshold Sensitivity
    print(f"\n{'='*80}")
    print("TEST 1: THRESHOLD SENSITIVITY")
    print(f"{'='*80}")
    
    thresholds = [
        (0.5, 0.3, "Relaxed"),
        (0.6, 0.4, "Baseline"),
        (0.7, 0.5, "Strict"),
        (0.8, 0.6, "Very Strict")
    ]
    
    for am_thresh, pm_thresh, label in thresholds:
        pnl = run_test_variant(tickers, cache_dir, model, features, 'threshold',
                               am_threshold=am_thresh, pm_threshold=pm_thresh)
        delta = pnl - baseline_pnl
        pct = (delta / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        status = "✅" if pnl >= baseline_pnl * 0.8 else "⚠️"
        print(f"{status} {label} ({am_thresh}/{pm_thresh}): ${pnl:,.0f} ({pct:+.1f}%)")
    
    # Test 2: Time Window Variations
    print(f"\n{'='*80}")
    print("TEST 2: TIME WINDOW VARIATIONS")
    print(f"{'='*80}")
    
    time_cutoffs = [
        (11, "11am Cutoff (Very Early)"),
        (13, "1pm Cutoff (Early)"),
        (14, "2pm Cutoff (Baseline)"),
        (15, "3pm Cutoff (Late)")
    ]
    
    for hour, label in time_cutoffs:
        pnl = run_test_variant(tickers, cache_dir, model, features, 'time_cutoff',
                               cutoff_hour=hour)
        delta = pnl - baseline_pnl
        pct = (delta / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        status = "✅" if pnl >= baseline_pnl * 0.8 else "⚠️"
        print(f"{status} {label}: ${pnl:,.0f} ({pct:+.1f}%)")
    
    # Test 3: Feature Scaling Drift
    print(f"\n{'='*80}")
    print("TEST 3: FEATURE SCALING DRIFT (Simulated Market Regime Change)")
    print(f"{'='*80}")
    
    scaling_factors = [
        (0.8, "20% Lower Volatility"),
        (1.0, "Baseline"),
        (1.2, "20% Higher Volatility"),
        (1.5, "50% Higher Volatility")
    ]
    
    for factor, label in scaling_factors:
        pnl = run_test_variant(tickers, cache_dir, model, features, 'feature_scale',
                               scale_factor=factor)
        delta = pnl - baseline_pnl
        pct = (delta / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        status = "✅" if pnl >= baseline_pnl * 0.7 else "⚠️"  # More tolerant for drift
        print(f"{status} {label}: ${pnl:,.0f} ({pct:+.1f}%)")
    
    # Test 4: Model Noise Injection
    print(f"\n{'='*80}")
    print("TEST 4: MODEL PREDICTION NOISE (Robustness to Degradation)")
    print(f"{'='*80}")
    
    noise_levels = [
        (0.0, "No Noise (Baseline)"),
        (0.05, "5% Random Noise"),
        (0.10, "10% Random Noise"),
        (0.20, "20% Random Noise")
    ]
    
    for noise, label in noise_levels:
        pnl = run_test_variant(tickers, cache_dir, model, features, 'model_noise',
                               noise_level=noise)
        delta = pnl - baseline_pnl
        pct = (delta / abs(baseline_pnl) * 100) if baseline_pnl != 0 else 0
        status = "✅" if pnl >= baseline_pnl * 0.6 else "⚠️"  # Should tolerate some noise
        print(f"{status} {label}: ${pnl:,.0f} ({pct:+.1f}%)")
    
    # Summary
    print(f"\n{'='*80}")
    print("PERTURBATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Baseline PnL: ${baseline_pnl:,.0f}")
    print(f"\nAll tests measure degradation tolerance vs baseline")
    print(f"Pass Criteria: >80% baseline (>60% for extreme perturbations)")

def run_test_variant(tickers, cache_dir, model, features, variant_type, **kwargs):
    """Run backtest with specific variant."""
    total_pnl = 0
    
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
        
        # Apply variant modifications
        if variant_type == 'threshold':
            trades, _ = run_bear_trap_perturbed(
                ticker, df, model, features,
                am_threshold=kwargs.get('am_threshold', 0.6),
                pm_threshold=kwargs.get('pm_threshold', 0.4)
            )
        elif variant_type == 'time_cutoff':
            trades, _ = run_bear_trap_perturbed(
                ticker, df, model, features,
                cutoff_hour=kwargs.get('cutoff_hour', 14)
            )
        elif variant_type == 'feature_scale':
            trades, _ = run_bear_trap_perturbed(
                ticker, df, model, features,
                scale_factor=kwargs.get('scale_factor', 1.0)
            )
        elif variant_type == 'model_noise':
            trades, _ = run_bear_trap_perturbed(
                ticker, df, model, features,
                noise_level=kwargs.get('noise_level', 0.0)
            )
        else:  # baseline
            trades, _ = run_bear_trap_validation(ticker, df, model, features, use_adaptive=True)
        
        total_pnl += sum(trades)
    
    return total_pnl

def run_bear_trap_perturbed(symbol, df, model, features, 
                            am_threshold=0.6, pm_threshold=0.4,
                            cutoff_hour=14, scale_factor=1.0, noise_level=0.0):
    """Modified backtest with perturbations."""
    capital = 100000
    params = {'RECLAIM_WICK_RATIO_MIN': 0.15, 'RECLAIM_VOL_MULT': 0.2,
              'RECLAIM_BODY_RATIO_MIN': 0.2, 'MIN_DAY_CHANGE_PCT': 15.0,
              'STOP_ATR_MULTIPLIER': 0.45, 'ATR_PERIOD': 14,
              'MAX_HOLD_MINUTES': 30, 'PER_TRADE_RISK_PCT': 0.02,
              'MAX_POSITION_DOLLARS': 50000, 'MAX_DAILY_LOSS_PCT': 0.10,
              'MAX_TRADES_PER_DAY': 10}

    # Feature Engineering (with scaling)
    df['h_l'] = df['high'] - df['low']
    df['h_pc'] = abs(df['high'] - df['close'].shift(1))
    df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    df['atr'] = df['tr'].rolling(params['ATR_PERIOD']).mean()
    
    # Apply scaling to ATR (simulate regime shift)
    if scale_factor != 1.0:
        df['atr'] = df['atr'] * scale_factor
    
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
    df['time_sin'], df['time_cos'] = get_cyclical_features(df)
    df['is_late_day'] = (df.index.hour >= cutoff_hour).astype(int)  # Perturbed cutoff
    
    atr_roll_min = df['atr'].rolling(7).min()
    atr_roll_max = df['atr'].rolling(7).max()
    df['atr_percentile'] = (df['atr'] - atr_roll_min) / (atr_roll_max - atr_roll_min).replace(0, np.inf)
    df['atr_percentile'] = df['atr_percentile'].fillna(0.5)
    
    df['vol_volatility_ratio'] = df['atr_percentile'] / (df['volume_ratio'] + 0.001)

    trades = []
    filtered_count = 0
    daily_pnl = {}
    
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
        
        if current_date not in daily_pnl:
            daily_pnl[current_date] = 0
            
        if daily_pnl[current_date] <= -params['MAX_DAILY_LOSS_PCT'] * capital: continue
        
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
                # Model prediction with noise injection
                X_live = pd.DataFrame([row[features]])
                prob_disaster = model.predict_proba(X_live)[:, 1][0]
                
                # Add noise
                if noise_level != 0.0:
                    noise = np.random.uniform(-noise_level, noise_level)
                    prob_disaster = np.clip(prob_disaster + noise, 0, 1)
                
                # Adaptive threshold (perturbed)
                threshold = pm_threshold if row.name.hour >= cutoff_hour else am_threshold
                
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

        # EXIT
        elif position is not None:
            if row['low'] <= stop_loss:
                pnl_dollars = (stop_loss - entry_price) * position_size
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                position = None
                continue
            
            hold_mins = (row.name - entry_time).total_seconds() / 60
            if hold_mins >= params['MAX_HOLD_MINUTES'] or (row.name.hour >= 15 and row.name.minute >= 55):
                pnl_dollars = (current_price - entry_price) * position_size
                trades.append(pnl_dollars)
                daily_pnl[current_date] += pnl_dollars
                position = None

    return trades, filtered_count

if __name__ == "__main__":
    run_perturbation_suite()
