"""
Strategy Tuning Analysis
Tests multiple parameter combinations to find optimal configuration.
Uses cached 4-year 1-minute data for SPY, QQQ, IWM.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import itertools

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"

def load_cached_1min_bars(symbol: str) -> pd.DataFrame:
    """Load cached 1-minute bar parquet file."""
    filename = f"{symbol}_1min_20220101_20260124.parquet"
    filepath = os.path.join(CACHE_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No cached data found: {filepath}")
    return pd.read_parquet(filepath)


def calculate_features(df: pd.DataFrame, rsi_period: int = 14, vol_window: int = 20) -> pd.DataFrame:
    """Calculate RSI and Volume Z-Score with configurable periods."""
    df = df.copy()
    
    # Log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # RSI with configurable period
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0
    df.loc[avg_gain == 0, 'rsi'] = 0.0
    
    # Volume Z-Score with configurable window
    vol_mean = df['volume'].rolling(window=vol_window).mean()
    vol_std = df['volume'].rolling(window=vol_window).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    return df


def normalize_features(df: pd.DataFrame, feature_cols: list) -> dict:
    """Normalize features to 0-1 range."""
    normalized = {}
    for col in feature_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            normalized[col] = (df[col] - col_min) / col_range
        else:
            normalized[col] = pd.Series(0.5, index=df.index)
    return normalized


def run_backtest(
    df: pd.DataFrame,
    rsi_weight: float,
    forward_horizon: int,
    in_sample_days: int = 3
) -> dict:
    """Run walk-forward backtest with given parameters."""
    
    vol_weight = 1.0 - rsi_weight
    feature_cols = ['rsi', 'volume_zscore']
    
    # Group by trading day
    df = df.copy()
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    
    equity = 100000.0
    results = []
    
    for day_idx in range(in_sample_days, len(trading_days)):
        # In-sample: previous N days
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_mask = df['date'].isin(is_days)
        oos_mask = df['date'] == oos_day
        
        is_data = df.loc[is_mask, feature_cols + ['log_return']].copy()
        oos_data = df.loc[oos_mask, feature_cols + ['log_return']].copy()
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue
        
        # Normalize and calculate alpha
        is_norm = normalize_features(is_data, feature_cols)
        is_alpha = rsi_weight * is_norm['rsi'] + vol_weight * is_norm['volume_zscore']
        threshold = is_alpha.median()
        
        oos_norm = normalize_features(oos_data, feature_cols)
        oos_alpha = rsi_weight * oos_norm['rsi'] + vol_weight * oos_norm['volume_zscore']
        
        # Generate signals
        signal = np.where(oos_alpha > threshold, 1, -1)
        
        # Forward returns
        oos_data = oos_data.copy()
        oos_data['forward_return'] = oos_data['log_return'].shift(-forward_horizon)
        oos_data['signal'] = signal
        valid = oos_data.dropna()
        
        if len(valid) < 30:
            continue
        
        # Metrics
        correct = (valid['signal'] * valid['forward_return']) > 0
        hit_rate = correct.mean()
        
        position_returns = valid['signal'] * valid['forward_return']
        period_return = (1 + position_returns).prod() - 1
        equity = equity * (1 + period_return)
        
        results.append({
            'date': oos_day,
            'hit_rate': hit_rate,
            'period_return': period_return,
            'equity': equity
        })
    
    if not results:
        return {'total_return': 0, 'avg_hit_rate': 0, 'sharpe': 0}
    
    total_return = ((equity - 100000) / 100000) * 100
    avg_hr = np.mean([r['hit_rate'] for r in results])
    
    # Calculate Sharpe (annualized)
    daily_returns = [r['period_return'] for r in results]
    if len(daily_returns) > 10 and np.std(daily_returns) > 0:
        sharpe = (np.mean(daily_returns) * 252) / (np.std(daily_returns) * np.sqrt(252))
    else:
        sharpe = 0
    
    return {
        'total_return': total_return,
        'avg_hit_rate': avg_hr,
        'sharpe': sharpe,
        'final_equity': equity,
        'num_days': len(results)
    }


def run_parameter_grid_search():
    """Run grid search over parameter space."""
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    # Parameter grid
    rsi_weights = [0.4, 0.5, 0.6, 0.7, 0.8]
    forward_horizons = [5, 10, 15, 20, 30]
    rsi_periods = [10, 14, 20]
    vol_windows = [10, 20, 30]
    
    print("=" * 90)
    print("STRATEGY PARAMETER TUNING")
    print("4-Year Backtest (2022-2026) | 1-Minute Bars")
    print("=" * 90)
    
    all_results = []
    
    for symbol in symbols:
        print(f"\n{'='*90}")
        print(f"SYMBOL: {symbol}")
        print("=" * 90)
        
        # Load data
        print(f"Loading data...")
        df = load_cached_1min_bars(symbol)
        print(f"Loaded {len(df):,} bars")
        
        symbol_results = []
        
        # Test each combination
        total_combos = len(rsi_weights) * len(forward_horizons) * len(rsi_periods) * len(vol_windows)
        print(f"Testing {total_combos} parameter combinations...")
        
        combo_num = 0
        best_sharpe = -999
        best_params = {}
        
        for rsi_period in rsi_periods:
            for vol_window in vol_windows:
                # Calculate features once per period combo
                feature_df = calculate_features(df, rsi_period=rsi_period, vol_window=vol_window)
                feature_df = feature_df.iloc[max(rsi_period, vol_window):]  # Warmup
                
                for rsi_wt in rsi_weights:
                    for horizon in forward_horizons:
                        combo_num += 1
                        
                        result = run_backtest(
                            feature_df,
                            rsi_weight=rsi_wt,
                            forward_horizon=horizon
                        )
                        
                        result['symbol'] = symbol
                        result['rsi_period'] = rsi_period
                        result['vol_window'] = vol_window
                        result['rsi_weight'] = rsi_wt
                        result['vol_weight'] = 1.0 - rsi_wt
                        result['horizon'] = horizon
                        
                        symbol_results.append(result)
                        
                        if result['sharpe'] > best_sharpe:
                            best_sharpe = result['sharpe']
                            best_params = result
                        
                        # Progress
                        if combo_num % 25 == 0:
                            print(f"  Progress: {combo_num}/{total_combos} ({100*combo_num/total_combos:.0f}%)")
        
        # Best for this symbol
        print(f"\n[{symbol}] BEST PARAMETERS (by Sharpe):")
        print(f"  RSI Period: {best_params.get('rsi_period')}")
        print(f"  Vol Window: {best_params.get('vol_window')}")
        print(f"  RSI Weight: {best_params.get('rsi_weight')}")
        print(f"  Horizon: {best_params.get('horizon')} min")
        print(f"  Sharpe: {best_params.get('sharpe'):.3f}")
        print(f"  Return: {best_params.get('total_return'):.2f}%")
        print(f"  Hit Rate: {best_params.get('avg_hit_rate')*100:.1f}%")
        
        all_results.extend(symbol_results)
    
    # Convert to DataFrame for analysis
    results_df = pd.DataFrame(all_results)
    
    # Save results
    results_df.to_csv('tuning_results.csv', index=False)
    print(f"\nResults saved to tuning_results.csv")
    
    # Aggregate best by symbol
    print("\n" + "=" * 90)
    print("OPTIMAL PARAMETERS BY SYMBOL")
    print("=" * 90)
    
    for symbol in symbols:
        sym_df = results_df[results_df['symbol'] == symbol]
        best_row = sym_df.loc[sym_df['sharpe'].idxmax()]
        
        print(f"\n{symbol}:")
        print(f"  RSI Period: {int(best_row['rsi_period'])}")
        print(f"  Vol Window: {int(best_row['vol_window'])}")
        print(f"  RSI Weight: {best_row['rsi_weight']:.1f}")
        print(f"  Horizon: {int(best_row['horizon'])} min")
        print(f"  Sharpe: {best_row['sharpe']:.3f}")
        print(f"  Return: {best_row['total_return']:.2f}%")
        print(f"  Hit Rate: {best_row['avg_hit_rate']*100:.1f}%")
    
    # Find universal best parameters (average across symbols)
    print("\n" + "=" * 90)
    print("UNIVERSAL OPTIMAL PARAMETERS")
    print("=" * 90)
    
    grouped = results_df.groupby(['rsi_period', 'vol_window', 'rsi_weight', 'horizon']).agg({
        'sharpe': 'mean',
        'total_return': 'mean',
        'avg_hit_rate': 'mean'
    }).reset_index()
    
    best_universal = grouped.loc[grouped['sharpe'].idxmax()]
    
    print(f"\nBest Average Parameters (across all symbols):")
    print(f"  RSI Period: {int(best_universal['rsi_period'])}")
    print(f"  Vol Window: {int(best_universal['vol_window'])}")
    print(f"  RSI Weight: {best_universal['rsi_weight']:.1f}")
    print(f"  Horizon: {int(best_universal['horizon'])} min")
    print(f"  Avg Sharpe: {best_universal['sharpe']:.3f}")
    print(f"  Avg Return: {best_universal['total_return']:.2f}%")
    print(f"  Avg Hit Rate: {best_universal['avg_hit_rate']*100:.1f}%")
    
    print("=" * 90)
    
    return results_df


if __name__ == '__main__':
    run_parameter_grid_search()
