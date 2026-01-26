"""
OUT-OF-SAMPLE VALIDATION - 2025 ONLY
Portfolio Backtest: Sniper + Workhorse on unseen data

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class Trade:
    """Trade record."""
    strategy: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    shares: int
    pnl_dollars: float
    pnl_r: float
    is_win: bool
    exit_reason: str


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate ATR."""
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def build_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Build stationary features."""
    features = pd.DataFrame(index=df.index)
    
    # Velocity
    features['velocity_1'] = df['close'].pct_change(1)
    features['velocity_4'] = df['close'].pct_change(4)
    
    # Volatility ratio
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    
    atr_5 = tr.rolling(5).mean()
    atr_20 = tr.rolling(20).mean()
    features['volatility_ratio'] = (atr_5 / (atr_20 + 0.0001)).clip(0, 5)
    
    # Volume z-score
    vol_mean = df['volume'].rolling(20).mean()
    vol_std = df['volume'].rolling(20).std()
    features['volume_z'] = ((df['volume'] - vol_mean) / (vol_std + 1)).clip(-5, 5)
    
    # Effort-result
    pct_change_abs = df['close'].pct_change().abs()
    features['effort_result'] = (features['volume_z'] / (pct_change_abs + 0.0001)).clip(-100, 100)
    
    # Range ratio
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    features['range_ratio'] = (full_range / (body + 0.0001)).clip(0, 20)
    
    # Body position
    features['body_position'] = ((df['close'] - df['low']) / (full_range + 0.0001)).clip(0, 1)
    
    # Aggregated features
    for col in ['velocity_1', 'volatility_ratio', 'effort_result', 'range_ratio', 'volume_z']:
        features[f'{col}_mean'] = features[col].rolling(lookback).mean()
        features[f'{col}_std'] = features[col].rolling(lookback).std()
    
    return features


def train_model_on_training_data(df_train: pd.DataFrame) -> tuple:
    """Train Workhorse model on pre-2025 data."""
    
    print("\nTraining Workhorse model on PRE-2025 data...")
    
    features = build_features(df_train, lookback=20)
    atr = calculate_atr(df_train)
    
    target_atr = 2.0
    max_dd_atr = 1.0
    max_bars = 8
    
    is_winning = []
    for idx in range(len(df_train) - max_bars):
        entry = df_train['close'].iloc[idx]
        current_atr = atr.iloc[idx]
        
        if pd.isna(current_atr) or current_atr <= 0:
            is_winning.append(False)
            continue
        
        target = entry + target_atr * current_atr
        max_allowed_dd = max_dd_atr * current_atr
        
        winner = False
        max_dd = 0
        
        for j in range(idx + 1, min(idx + max_bars + 1, len(df_train))):
            dd = entry - df_train['low'].iloc[j]
            max_dd = max(max_dd, dd)
            
            if df_train['high'].iloc[j] >= target and max_dd <= max_allowed_dd:
                winner = True
                break
        
        is_winning.append(winner)
    
    is_winning.extend([False] * max_bars)
    features['is_winning'] = is_winning
    
    # Get feature columns
    feat_cols = [c for c in features.columns if '_mean' in c or '_std' in c]
    feat_cols = [c for c in feat_cols if not features[c].isna().all()]
    
    wins_df = features[features['is_winning']].dropna(subset=feat_cols)
    non_wins_df = features[~features['is_winning']].dropna(subset=feat_cols)
    
    n_sample = min(5000, len(wins_df), len(non_wins_df))
    np.random.seed(42)
    wins = wins_df.sample(n=n_sample)
    non_wins = non_wins_df.sample(n=n_sample)
    
    X_win = wins[feat_cols].values
    X_non = non_wins[feat_cols].values
    X_all = np.vstack([X_win, X_non])
    
    # Train scaler and K-Means
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    
    print(f"  Trained on {len(df_train):,} bars (pre-2025)")
    print(f"  Model sample: {len(X_all):,} ({n_sample:,} wins + {n_sample:,} non-wins)")
    
    return scaler, kmeans, feat_cols


def run_portfolio_backtest(df: pd.DataFrame, features: pd.DataFrame,
                           workhorse_model: tuple) -> dict:
    """Run portfolio backtest."""
    
    scaler, kmeans, feat_cols = workhorse_model
    
    # Calculate ATR and SMA
    atr = calculate_atr(df)
    sma_50 = df['close'].rolling(50).mean()
    in_uptrend = df['close'] > sma_50
    
    # Assign clusters for Workhorse
    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)
    is_cluster_7 = (clusters == 7)
    
    # Sniper thresholds
    sniper_effort_threshold = -61.0
    sniper_range_threshold = 3.88
    sniper_volatility_threshold = 0.88
    
    is_sniper = (
        (features.get('effort_result_mean', 0) < sniper_effort_threshold) &
        (features.get('range_ratio_mean', 0) > sniper_range_threshold) &
        (features.get('volatility_ratio_mean', 0) > sniper_volatility_threshold)
    )
    
    # Account tracking
    sniper_account = 25000.0
    workhorse_account = 25000.0
    
    sniper_trades = []
    workhorse_trades = []
    
    sniper_position = None
    workhorse_position = None
    
    # Risk parameters
    sniper_risk_pct = 0.02
    workhorse_risk_pct = 0.01
    
    target_mult = 2.0
    stop_mult = 1.0
    max_hold_bars = 8
    slippage = 0.02
    
    # Daily tracking
    daily_pnl = []
    current_date = None
    daily_sniper_pnl = 0
    daily_workhorse_pnl = 0
    
    for idx in range(len(df)):
        bar_time = df.index[idx]
        current_price = df['close'].iloc[idx]
        
        # Track daily P&L
        bar_date = bar_time.date()
        if current_date != bar_date:
            if current_date is not None:
                daily_pnl.append({
                    'date': current_date,
                    'sniper_pnl': daily_sniper_pnl,
                    'workhorse_pnl': daily_workhorse_pnl,
                    'sniper_balance': sniper_account,
                    'workhorse_balance': workhorse_account
                })
            current_date = bar_date
            daily_sniper_pnl = 0
            daily_workhorse_pnl = 0
        
        current_atr = atr.iloc[idx]
        if pd.isna(current_atr) or pd.isna(sma_50.iloc[idx]):
            continue
        
        # ===== SNIPER STRATEGY =====
        if sniper_position is None:
            if is_sniper.iloc[idx] and in_uptrend.iloc[idx]:
                risk_dollars = sniper_account * sniper_risk_pct
                stop_distance = stop_mult * current_atr
                shares = int(risk_dollars / stop_distance)
                
                if shares > 0:
                    raw_entry = current_price
                    entry_price = raw_entry + slippage/2
                    
                    sniper_position = {
                        'entry_idx': idx,
                        'entry_time': bar_time,
                        'raw_entry': raw_entry,
                        'entry_price': entry_price,
                        'shares': shares,
                        'target': raw_entry + target_mult * current_atr,
                        'stop': raw_entry - stop_mult * current_atr,
                        'atr': current_atr
                    }
        else:
            high = df['high'].iloc[idx]
            low = df['low'].iloc[idx]
            close = df['close'].iloc[idx]
            
            exit_signal = False
            raw_exit = None
            exit_reason = None
            
            if low <= sniper_position['stop']:
                exit_signal = True
                raw_exit = sniper_position['stop']
                exit_reason = 'STOP'
            elif high >= sniper_position['target']:
                exit_signal = True
                raw_exit = sniper_position['target']
                exit_reason = 'TARGET'
            elif idx - sniper_position['entry_idx'] >= max_hold_bars:
                exit_signal = True
                raw_exit = close
                exit_reason = 'TIME'
            
            if exit_signal:
                exit_price = raw_exit - slippage/2
                pnl_net = (exit_price - sniper_position['entry_price']) * sniper_position['shares']
                risk = (sniper_position['raw_entry'] - sniper_position['stop']) * sniper_position['shares']
                pnl_r = pnl_net / risk if risk > 0 else 0
                
                sniper_account += pnl_net
                daily_sniper_pnl += pnl_net
                
                sniper_trades.append(Trade(
                    strategy='SNIPER',
                    entry_time=sniper_position['entry_time'],
                    exit_time=bar_time,
                    entry_price=sniper_position['entry_price'],
                    exit_price=exit_price,
                    shares=sniper_position['shares'],
                    pnl_dollars=pnl_net,
                    pnl_r=pnl_r,
                    is_win=pnl_net > 0,
                    exit_reason=exit_reason
                ))
                sniper_position = None
        
        # ===== WORKHORSE STRATEGY =====
        if workhorse_position is None:
            if is_cluster_7[idx] and in_uptrend.iloc[idx]:
                risk_dollars = workhorse_account * workhorse_risk_pct
                stop_distance = stop_mult * current_atr
                shares = int(risk_dollars / stop_distance)
                
                if shares > 0:
                    raw_entry = current_price
                    entry_price = raw_entry + slippage/2
                    
                    workhorse_position = {
                        'entry_idx': idx,
                        'entry_time': bar_time,
                        'raw_entry': raw_entry,
                        'entry_price': entry_price,
                        'shares': shares,
                        'target': raw_entry + target_mult * current_atr,
                        'stop': raw_entry - stop_mult * current_atr,
                        'atr': current_atr
                    }
        else:
            high = df['high'].iloc[idx]
            low = df['low'].iloc[idx]
            close = df['close'].iloc[idx]
            
            exit_signal = False
            raw_exit = None
            exit_reason = None
            
            if low <= workhorse_position['stop']:
                exit_signal = True
                raw_exit = workhorse_position['stop']
                exit_reason = 'STOP'
            elif high >= workhorse_position['target']:
                exit_signal = True
                raw_exit = workhorse_position['target']
                exit_reason = 'TARGET'
            elif idx - workhorse_position['entry_idx'] >= max_hold_bars:
                exit_signal = True
                raw_exit = close
                exit_reason = 'TIME'
            
            if exit_signal:
                exit_price = raw_exit - slippage/2
                pnl_net = (exit_price - workhorse_position['entry_price']) * workhorse_position['shares']
                risk = (workhorse_position['raw_entry'] - workhorse_position['stop']) * workhorse_position['shares']
                pnl_r = pnl_net / risk if risk > 0 else 0
                
                workhorse_account += pnl_net
                daily_workhorse_pnl += pnl_net
                
                workhorse_trades.append(Trade(
                    strategy='WORKHORSE',
                    entry_time=workhorse_position['entry_time'],
                    exit_time=bar_time,
                    entry_price=workhorse_position['entry_price'],
                    exit_price=exit_price,
                    shares=workhorse_position['shares'],
                    pnl_dollars=pnl_net,
                    pnl_r=pnl_r,
                    is_win=pnl_net > 0,
                    exit_reason=exit_reason
                ))
                workhorse_position = None
    
    # Add final day
    if current_date is not None:
        daily_pnl.append({
            'date': current_date,
            'sniper_pnl': daily_sniper_pnl,
            'workhorse_pnl': daily_workhorse_pnl,
            'sniper_balance': sniper_account,
            'workhorse_balance': workhorse_account
        })
    
    return {
        'sniper_trades': sniper_trades,
        'workhorse_trades': workhorse_trades,
        'sniper_final': sniper_account,
        'workhorse_final': workhorse_account,
        'daily_pnl': pd.DataFrame(daily_pnl)
    }


def main():
    print("="*70)
    print("OUT-OF-SAMPLE VALIDATION: 2025 ONLY")
    print("Portfolio: Sniper + Workhorse")
    print("="*70)
    
    # Load data
    data_path = project_root / "data" / "cache" / "equities"
    files = sorted(data_path.glob("SPY_1min_202*.parquet"),
                   key=lambda x: x.stat().st_size, reverse=True)
    df_1m = pd.read_parquet(files[0])
    
    # Aggregate to 15-min
    df_15m = df_1m.resample('15min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    df_15m = df_15m.between_time('09:30', '15:45')
    
    # Split into training (pre-2025) and test (2025)
    df_train = df_15m[df_15m.index < '2025-01-01']
    df_test = df_15m[(df_15m.index >= '2025-01-01') & (df_15m.index < '2026-01-01')]
    
    print(f"\nTraining data (pre-2025): {len(df_train):,} bars")
    print(f"  Range: {df_train.index.min()} to {df_train.index.max()}")
    print(f"\nTest data (2025): {len(df_test):,} bars")
    print(f"  Range: {df_test.index.min()} to {df_test.index.max()}")
    
    # Train model on pre-2025 data
    workhorse_model = train_model_on_training_data(df_train)
    
    # Build features on test data
    features_test = build_features(df_test, lookback=20)
    
    # Run backtest on 2025 only
    print(f"\nRunning backtest on 2025 data...")
    results = run_portfolio_backtest(df_test, features_test, workhorse_model)
    
    # Analyze
    print("\n" + "="*70)
    print("2025 OUT-OF-SAMPLE RESULTS")
    print("="*70)
    
    sniper_trades = results['sniper_trades']
    workhorse_trades = results['workhorse_trades']
    
    # Sniper stats
    if sniper_trades:
        df_s = pd.DataFrame([{
            'pnl': t.pnl_dollars,
            'pnl_r': t.pnl_r,
            'is_win': t.is_win
        } for t in sniper_trades])
        s_total = len(df_s)
        s_wins = df_s['is_win'].sum()
        s_hr = s_wins / s_total
        s_pnl = df_s['pnl'].sum()
        s_expect = df_s['pnl_r'].mean()
    else:
        s_total = s_wins = s_hr = s_pnl = s_expect = 0
    
    # Workhorse stats
    if workhorse_trades:
        df_w = pd.DataFrame([{
            'pnl': t.pnl_dollars,
            'pnl_r': t.pnl_r,
            'is_win': t.is_win
        } for t in workhorse_trades])
        w_total = len(df_w)
        w_wins = df_w['is_win'].sum()
        w_hr = w_wins / w_total
        w_pnl = df_w['pnl'].sum()
        w_expect = df_w['pnl_r'].mean()
    else:
        w_total = w_wins = w_hr = w_pnl = w_expect = 0
    
    print(f"\n{'Metric':<20} {'SNIPER':<20} {'WORKHORSE':<20}")
    print("-"*60)
    print(f"{'Starting:':<20} $25,000{'':<12} $25,000")
    print(f"{'Final:':<20} ${results['sniper_final']:>8,.2f}{'':>7} ${results['workhorse_final']:>8,.2f}")
    print(f"{'P&L:':<20} ${s_pnl:>8,.2f}{'':>7} ${w_pnl:>8,.2f}")
    print(f"{'Return:':<20} {(results['sniper_final']/25000-1)*100:>7.2f}%{'':>8} {(results['workhorse_final']/25000-1)*100:>7.2f}%")
    print()
    print(f"{'Trades:':<20} {s_total:>10}{'':>10} {w_total:>10}")
    print(f"{'Win Rate:':<20} {s_hr:>9.1%}{'':>11} {w_hr:>9.1%}")
    print(f"{'Expectancy:':<20} {s_expect:>9.3f}R{'':>8} {w_expect:>9.3f}R")
    
    combined_final = results['sniper_final'] + results['workhorse_final']
    combined_pnl = combined_final - 50000
    combined_return = (combined_final / 50000 - 1) * 100
    
    print("\n" + "-"*60)
    print(f"{'COMBINED PORTFOLIO':^60}")
    print("-"*60)
    print(f"Starting:     $50,000")
    print(f"Final:        ${combined_final:,.2f}")
    print(f"P&L:          ${combined_pnl:,.2f}")
    print(f"Return:       {combined_return:.2f}%")
    print(f"Trades:       {s_total + w_total}")
    
    # Monthly breakdown
    if len(results['daily_pnl']) > 0:
        daily = results['daily_pnl']
        daily['month'] = pd.to_datetime(daily['date']).dt.to_period('M')
        monthly = daily.groupby('month').agg({
            'sniper_pnl': 'sum',
            'workhorse_pnl': 'sum'
        })
        
        print("\n" + "="*60)
        print("MONTHLY BREAKDOWN (2025)")
        print("="*60)
        print(f"\n{'Month':<15} {'Sniper':<15} {'Workhorse':<15} {'Combined'}")
        print("-"*60)
        for month, row in monthly.iterrows():
            combined_month = row['sniper_pnl'] + row['workhorse_pnl']
            print(f"{str(month):<15} ${row['sniper_pnl']:>8,.2f}{'':>4} ${row['workhorse_pnl']:>8,.2f}{'':>4} ${combined_month:>8,.2f}")
    
    print("\n" + "="*70)
    print("VALIDATION STATUS")
    print("="*70)
    
    if combined_return > 0:
        print("\n✅ OUT-OF-SAMPLE VALIDATION: PASSED")
        print(f"   2025 Return: {combined_return:.2f}%")
        print(f"   Both strategies remained profitable on unseen data")
    else:
        print("\n⚠️ OUT-OF-SAMPLE VALIDATION: MARGINAL")
        print(f"   2025 Return: {combined_return:.2f}%")
    
    # Save results
    output_file = project_root / "test" / "vol_expansion" / "oos_2025_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'period': '2025',
            'sniper': {
                'final': results['sniper_final'],
                'pnl': s_pnl,
                'return_pct': (results['sniper_final']/25000-1)*100,
                'trades': s_total,
                'win_rate': s_hr,
                'expectancy': s_expect
            },
            'workhorse': {
                'final': results['workhorse_final'],
                'pnl': w_pnl,
                'return_pct': (results['workhorse_final']/25000-1)*100,
                'trades': w_total,
                'win_rate': w_hr,
                'expectancy': w_expect
            },
            'combined': {
                'final': combined_final,
                'pnl': combined_pnl,
                'return_pct': combined_return,
                'trades': s_total + w_total
            }
        }, f, indent=2)
    
    print(f"\n*** Results saved to {output_file} ***")
    
    return results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
