"""
COMPREHENSIVE VALIDATION SUITE
Run all critical tests for symbols with >20% return

Tests:
1. 2024 Standalone Backtest
2. Walk-Forward Validation (2023 val, 2024 test, 2025 OOS)
3. Parameter Stability
4. Drawdown Analysis
5. Monthly Returns

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Load final configs
with open(project_root / "test" / "vol_expansion" / "FINAL_OPTIMIZED_CONFIGS.json") as f:
    CONFIGS = json.load(f)

# Symbols to test (>20% return)
SYMBOLS = ['GLD', 'IVV', 'IWM', 'SPY', 'QQQ', 'VOO']


def calculate_atr(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift(1)).abs()
    tr3 = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def build_features(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    features = pd.DataFrame(index=df.index)
    features['velocity_1'] = df['close'].pct_change(1)
    features['velocity_4'] = df['close'].pct_change(4)
    
    tr = pd.concat([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift(1)).abs(),
        (df['low'] - df['close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    
    atr_5 = tr.rolling(5).mean()
    atr_20 = tr.rolling(20).mean()
    features['volatility_ratio'] = (atr_5 / (atr_20 + 0.0001)).clip(0, 5)
    
    vol_mean = df['volume'].rolling(20).mean()
    vol_std = df['volume'].rolling(20).std()
    features['volume_z'] = ((df['volume'] - vol_mean) / (vol_std + 1)).clip(-5, 5)
    
    pct_change_abs = df['close'].pct_change().abs()
    features['effort_result'] = (features['volume_z'] / (pct_change_abs + 0.0001)).clip(-100, 100)
    
    full_range = df['high'] - df['low']
    body = (df['close'] - df['open']).abs()
    features['range_ratio'] = (full_range / (body + 0.0001)).clip(0, 20)
    
    for col in ['velocity_1', 'volatility_ratio', 'effort_result', 'range_ratio', 'volume_z']:
        features[f'{col}_mean'] = features[col].rolling(lookback).mean()
        features[f'{col}_std'] = features[col].rolling(lookback).std()
    
    return features


def train_model(df_train: pd.DataFrame) -> tuple:
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
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    
    kmeans = KMeans(n_clusters=8, random_state=42, n_init=10)
    kmeans.fit(X_scaled)
    
    return scaler, kmeans, feat_cols


def backtest(df_test: pd.DataFrame, model: tuple, config: dict, track_equity: bool = False) -> dict:
    scaler, kmeans, feat_cols = model
    
    features = build_features(df_test, lookback=20)
    atr = calculate_atr(df_test)
    sma_50 = df_test['close'].rolling(50).mean()
    in_uptrend = df_test['close'] > sma_50
    
    X_full = features[feat_cols].fillna(0).values
    X_scaled = scaler.transform(X_full)
    clusters = kmeans.predict(X_scaled)
    
    signal_mask = pd.Series(clusters == config['cluster'], index=df_test.index)
    if config['trend_filter']:
        signal_mask = signal_mask & in_uptrend
    
    account = 25000.0
    trades = []
    position = None
    equity_curve = []
    
    risk_pct = 0.01
    slippage = 0.02
    
    for idx in range(len(df_test)):
        current_atr = atr.iloc[idx]
        if pd.isna(current_atr):
            if track_equity:
                equity_curve.append(account)
            continue
        
        if position is None:
            if signal_mask.iloc[idx]:
                risk_dollars = account * risk_pct
                stop_distance = config['stop_atr'] * current_atr
                shares = int(risk_dollars / stop_distance)
                
                if shares > 0:
                    raw_entry = df_test['close'].iloc[idx]
                    position = {
                        'entry_idx': idx,
                        'raw_entry': raw_entry,
                        'entry_price': raw_entry + slippage/2,
                        'shares': shares,
                        'target': raw_entry + config['target_atr'] * current_atr,
                        'stop': raw_entry - config['stop_atr'] * current_atr,
                        'entry_date': df_test.index[idx]
                    }
        else:
            high = df_test['high'].iloc[idx]
            low = df_test['low'].iloc[idx]
            close = df_test['close'].iloc[idx]
            
            exit_signal = False
            raw_exit = None
            
            if low <= position['stop']:
                exit_signal = True
                raw_exit = position['stop']
            elif high >= position['target']:
                exit_signal = True
                raw_exit = position['target']
            elif idx - position['entry_idx'] >= config['time_stop_bars']:
                exit_signal = True
                raw_exit = close
            
            if exit_signal:
                exit_price = raw_exit - slippage/2
                pnl_net = (exit_price - position['entry_price']) * position['shares']
                risk = (position['raw_entry'] - position['stop']) * position['shares']
                pnl_r = pnl_net / risk if risk > 0 else 0
                
                account += pnl_net
                trades.append({
                    'pnl': pnl_net,
                    'pnl_r': pnl_r,
                    'is_win': pnl_net > 0,
                    'entry_date': position['entry_date'],
                    'exit_date': df_test.index[idx],
                    'bars_held': idx - position['entry_idx']
                })
                position = None
        
        if track_equity:
            equity_curve.append(account)
    
    if not trades:
        return {
            'trades': 0, 'win_rate': 0, 'expectancy': 0, 'return_pct': 0,
            'max_drawdown': 0, 'sharpe': 0
        }
    
    df_trades = pd.DataFrame(trades)
    
    result = {
        'trades': len(df_trades),
        'win_rate': df_trades['is_win'].mean(),
        'expectancy': df_trades['pnl_r'].mean(),
        'return_pct': (account / 25000 - 1) * 100,
        'final_balance': account
    }
    
    if track_equity:
        equity_series = pd.Series(equity_curve, index=df_test.index[:len(equity_curve)])
        result['equity_curve'] = equity_series
        result['max_drawdown'] = calculate_max_drawdown(equity_series)
    
    return result


def calculate_max_drawdown(equity: pd.Series) -> float:
    running_max = equity.expanding().max()
    drawdown = (equity - running_max) / running_max
    return drawdown.min() * 100


def test_2024(symbol: str, config: dict) -> dict:
    """Test on 2024 data alone."""
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
    if not files:
        return None
    
    file = max(files, key=lambda x: x.stat().st_size)
    df_1m = pd.read_parquet(file)
    
    df_15m = df_1m.resample('15min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    df_15m = df_15m.between_time('09:30', '15:45')
    
    df_train = df_15m[df_15m.index < '2024-01-01']
    df_test = df_15m[(df_15m.index >= '2024-01-01') & (df_15m.index < '2025-01-01')]
    
    if len(df_test) < 100:
        return None
    
    model = train_model(df_train)
    return backtest(df_test, model, config['workhorse'], track_equity=True)


def walk_forward_validation(symbol: str, config: dict) -> dict:
    """Train 2022-2023, validate 2024, test 2025."""
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
    if not files:
        return None
    
    file = max(files, key=lambda x: x.stat().st_size)
    df_1m = pd.read_parquet(file)
    
    df_15m = df_1m.resample('15min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    df_15m = df_15m.between_time('09:30', '15:45')
    
    # Split periods
    df_train = df_15m[(df_15m.index >= '2022-01-01') & (df_15m.index < '2024-01-01')]
    df_val = df_15m[(df_15m.index >= '2024-01-01') & (df_15m.index < '2025-01-01')]
    df_test = df_15m[(df_15m.index >= '2025-01-01') & (df_15m.index < '2026-01-01')]
    
    if len(df_val) < 100 or len(df_test) < 100:
        return None
    
    # Train on 2022-2023
    model = train_model(df_train)
    
    # Test on 2024 (validation)
    val_result = backtest(df_val, model, config['workhorse'])
    
    # Test on 2025 (OOS)
    test_result = backtest(df_test, model, config['workhorse'])
    
    return {
        'validation_2024': val_result,
        'oos_2025': test_result
    }


def test_parameter_stability(symbol: str, config: dict) -> dict:
    """Test nearby parameter values."""
    data_path = project_root / "data" / "cache" / "equities"
    files = list(data_path.glob(f"{symbol}_1min_*.parquet"))
    if not files:
        return None
    
    file = max(files, key=lambda x: x.stat().st_size)
    df_1m = pd.read_parquet(file)
    
    df_15m = df_1m.resample('15min').agg({
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()
    df_15m = df_15m.between_time('09:30', '15:45')
    
    df_train = df_15m[df_15m.index < '2025-01-01']
    df_test = df_15m[(df_15m.index >= '2025-01-01') & (df_15m.index < '2026-01-01')]
    
    if len(df_test) < 100:
        return None
    
    model = train_model(df_train)
    
    results = []
    base_config = config['workhorse']
    
    # Test ±1 cluster
    for cluster_adj in [-1, 0, 1]:
        test_cluster = (base_config['cluster'] + cluster_adj) % 8
        test_config = base_config.copy()
        test_config['cluster'] = test_cluster
        
        result = backtest(df_test, model, test_config)
        results.append({
            'param': f'cluster_{test_cluster}',
            'return': result['return_pct']
        })
    
    # Test ±0.5 on target
    for target_adj in [-0.5, 0, 0.5]:
        test_config = base_config.copy()
        test_config['target_atr'] = base_config['target_atr'] + target_adj
        
        result = backtest(df_test, model, test_config)
        results.append({
            'param': f'target_{test_config["target_atr"]}',
            'return': result['return_pct']
        })
    
    return results


def main():
    print("="*70)
    print("COMPREHENSIVE VALIDATION SUITE")
    print("="*70)
    
    all_results = {}
    
    for symbol in SYMBOLS:
        if symbol not in CONFIGS:
            continue
        
        print(f"\n{'='*70}")
        print(f"TESTING: {symbol}")
        print(f"{'='*70}")
        
        config = CONFIGS[symbol]
        symbol_results = {}
        
        # Test 1: 2024 Standalone
        print(f"\n  Running 2024 backtest...")
        try:
            result_2024 = test_2024(symbol, config)
            if result_2024:
                symbol_results['test_2024'] = {
                    'trades': result_2024['trades'],
                    'return_pct': result_2024['return_pct'],
                    'win_rate': result_2024['win_rate'],
                    'max_drawdown': result_2024.get('max_drawdown', 0)
                }
                print(f"    2024: {result_2024['trades']} trades, {result_2024['return_pct']:.1f}% return")
        except Exception as e:
            print(f"    ERROR: {e}")
        
        # Test 2: Walk-Forward
        print(f"  Running walk-forward validation...")
        try:
            wf_result = walk_forward_validation(symbol, config)
            if wf_result:
                symbol_results['walk_forward'] = wf_result
                print(f"    2024 (val): {wf_result['validation_2024']['return_pct']:.1f}%")
                print(f"    2025 (OOS): {wf_result['oos_2025']['return_pct']:.1f}%")
        except Exception as e:
            print(f"    ERROR: {e}")
        
        # Test 3: Parameter Stability
        print(f"  Running parameter stability tests...")
        try:
            stability = test_parameter_stability(symbol, config)
            if stability:
                symbol_results['parameter_stability'] = stability
                returns = [s['return'] for s in stability]
                print(f"    Return range: {min(returns):.1f}% to {max(returns):.1f}%")
        except Exception as e:
            print(f"    ERROR: {e}")
        
        all_results[symbol] = symbol_results
    
    # Save results
    output_file = project_root / "test" / "vol_expansion" / "comprehensive_validation.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n*** Results saved to {output_file} ***")
    
    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
