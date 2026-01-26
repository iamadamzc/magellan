"""
MULTI-SYMBOL 2025 OUT-OF-SAMPLE VALIDATION
Test both Sniper and Workhorse strategies across multiple symbols

Symbols: SPY, QQQ, IWM, IVV, VOO, GLD, TQQQ, SOXL
(Note: SLV data may not be available)

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
from typing import List, Dict
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


def train_workhorse_model(df_train: pd.DataFrame) -> tuple:
    """Train Workhorse model on pre-2025 data."""
    
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
    
    return scaler, kmeans, feat_cols


def run_symbol_backtest(symbol: str, df_test: pd.DataFrame, workhorse_model: tuple) -> dict:
    """Run backtest for a single symbol."""
    
    scaler, kmeans, feat_cols = workhorse_model
    
    # Build features
    features = build_features(df_test, lookback=20)
    
    # Calculate ATR and SMA
    atr = calculate_atr(df_test)
    sma_50 = df_test['close'].rolling(50).mean()
    in_uptrend = df_test['close'] > sma_50
    
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
    
    for idx in range(len(df_test)):
        bar_time = df_test.index[idx]
        current_price = df_test['close'].iloc[idx]
        
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
            high = df_test['high'].iloc[idx]
            low = df_test['low'].iloc[idx]
            close = df_test['close'].iloc[idx]
            
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
            high = df_test['high'].iloc[idx]
            low = df_test['low'].iloc[idx]
            close = df_test['close'].iloc[idx]
            
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
    
    # Calculate stats
    def calc_stats(trades, account):
        if not trades:
            return {
                'trades': 0,
                'win_rate': 0,
                'expectancy': 0,
                'final': account,
                'pnl': 0,
                'return_pct': 0
            }
        
        df_t = pd.DataFrame([{
            'pnl': t.pnl_dollars,
            'pnl_r': t.pnl_r,
            'is_win': t.is_win
        } for t in trades])
        
        return {
            'trades': len(df_t),
            'win_rate': df_t['is_win'].mean(),
            'expectancy': df_t['pnl_r'].mean(),
            'final': account,
            'pnl': df_t['pnl'].sum(),
            'return_pct': (account / 25000 - 1) * 100
        }
    
    sniper_stats = calc_stats(sniper_trades, sniper_account)
    workhorse_stats = calc_stats(workhorse_trades, workhorse_account)
    
    return {
        'symbol': symbol,
        'sniper': sniper_stats,
        'workhorse': workhorse_stats,
        'combined': {
            'final': sniper_account + workhorse_account,
            'pnl': sniper_stats['pnl'] + workhorse_stats['pnl'],
            'return_pct': ((sniper_account + workhorse_account) / 50000 - 1) * 100,
            'trades': sniper_stats['trades'] + workhorse_stats['trades']
        }
    }


def main():
    print("="*70)
    print("MULTI-SYMBOL 2025 OUT-OF-SAMPLE VALIDATION")
    print("="*70)
    
    symbols = ['SPY', 'QQQ', 'IWM', 'IVV', 'VOO', 'GLD', 'SLV', 'TQQQ', 'SOXL']
    
    all_results = {}
    
    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"PROCESSING: {symbol}")
        print(f"{'='*70}")
        
        try:
            # Load data
            data_path = project_root / "data" / "cache" / "equities"
            
            # Try to find the data file
            files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
            if not files:
                print(f"  ⚠️ No data found for {symbol}, skipping...")
                continue
            
            # Load largest file (likely has most data)
            file = max(files, key=lambda x: x.stat().st_size)
            df_1m = pd.read_parquet(file)
            
            print(f"  Loaded: {len(df_1m):,} 1-min bars")
            
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
            
            if len(df_test) < 100:
                print(f"  ⚠️ Insufficient 2025 data ({len(df_test)} bars), skipping...")
                continue
            
            print(f"  Training: {len(df_train):,} bars")
            print(f"  Testing (2025): {len(df_test):,} bars")
            
            # Train model on pre-2025 data
            print(f"  Training Workhorse model...")
            workhorse_model = train_workhorse_model(df_train)
            
            # Run backtest
            print(f"  Running backtest...")
            results = run_symbol_backtest(symbol, df_test, workhorse_model)
            
            all_results[symbol] = results
            
            # Print summary
            print(f"\n  RESULTS:")
            print(f"    Sniper:    {results['sniper']['trades']:3d} trades, {results['sniper']['return_pct']:6.1f}% return")
            print(f"    Workhorse: {results['workhorse']['trades']:3d} trades, {results['workhorse']['return_pct']:6.1f}% return")
            print(f"    Combined:  {results['combined']['trades']:3d} trades, {results['combined']['return_pct']:6.1f}% return")
            
        except Exception as e:
            print(f"  ❌ Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY - ALL SYMBOLS (2025 OOS)")
    print("="*70)
    
    print(f"\n{'Symbol':<8} {'Sniper':<25} {'Workhorse':<25} {'Combined':<20}")
    print(f"{'':8} {'Trades':>6} {'Return':>8} {'Expect':>8} {'Trades':>6} {'Return':>8} {'Expect':>8} {'Return':>10} {'Total':>8}")
    print("-"*100)
    
    for symbol, res in all_results.items():
        print(f"{symbol:<8} "
              f"{res['sniper']['trades']:>6} "
              f"{res['sniper']['return_pct']:>7.1f}% "
              f"{res['sniper']['expectancy']:>7.3f}R "
              f"{res['workhorse']['trades']:>6} "
              f"{res['workhorse']['return_pct']:>7.1f}% "
              f"{res['workhorse']['expectancy']:>7.3f}R "
              f"{res['combined']['return_pct']:>9.1f}% "
              f"{res['combined']['trades']:>7}")
    
    # Save results
    output_file = project_root / "test" / "vol_expansion" / "multi_symbol_2025_results.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n*** Results saved to {output_file} ***")
    
    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
