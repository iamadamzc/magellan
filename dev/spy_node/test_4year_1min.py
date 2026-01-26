"""
4-Year Backtest Using Cached 1-Minute Data
Compares Original (with fake sentiment) vs No-Sentiment for SPY, QQQ, IWM
Period: 2022-01-01 to 2026-01-24
Uses 15-minute forward return horizon (original strategy design)
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup paths
CACHE_DIR = r"a:\1\Magellan\data\cache\equities"

def load_cached_1min_bars(symbol: str) -> pd.DataFrame:
    """Load cached 1-minute bar parquet file for a symbol."""
    filename = f"{symbol}_1min_20220101_20260124.parquet"
    filepath = os.path.join(CACHE_DIR, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No cached 1-min data found: {filepath}")
    
    df = pd.read_parquet(filepath)
    print(f"  Loaded: {filename} ({len(df):,} bars)")
    return df


def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate RSI-14 and Volume Z-Score for 1-min bars."""
    df = df.copy()
    
    # Log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # RSI-14
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=14, adjust=False).mean()
    avg_loss = losses.ewm(span=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi_14'] = 100.0
    df.loc[avg_gain == 0, 'rsi_14'] = 0.0
    
    # Volume Z-Score (20-bar)
    vol_mean = df['volume'].rolling(window=20).mean()
    vol_std = df['volume'].rolling(window=20).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    # Fake sentiment (constant 0 - this is what the real system was using)
    df['sentiment'] = 0.0
    
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


def run_daily_walk_forward(
    df: pd.DataFrame,
    weights: dict,
    in_sample_bars: int = 3 * 390,  # 3 days of 1-min bars
    forward_horizon: int = 15  # 15-minute forward return
) -> dict:
    """
    Run daily walk-forward backtest on 1-minute bars.
    Process one trading day at a time for OOS.
    """
    feature_cols = list(weights.keys())
    
    # Group by trading day
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    
    results = []
    equity = 100000.0
    
    # Need at least 3 days for IS before starting OOS
    start_idx = 3
    
    for day_idx in range(start_idx, len(trading_days)):
        # In-sample: previous 3 days
        is_days = trading_days[day_idx-3:day_idx]
        oos_day = trading_days[day_idx]
        
        is_mask = df['date'].isin(is_days)
        oos_mask = df['date'] == oos_day
        
        is_data = df.loc[is_mask, feature_cols + ['log_return', 'close']].copy()
        oos_data = df.loc[oos_mask, feature_cols + ['log_return', 'close']].copy()
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue
        
        # Normalize features on in-sample
        is_norm = normalize_features(is_data, feature_cols)
        
        # Calculate in-sample alpha and threshold
        is_alpha = sum(weights[col] * is_norm[col] for col in feature_cols)
        threshold = is_alpha.median()
        
        # Normalize out-of-sample
        oos_norm = normalize_features(oos_data, feature_cols)
        oos_alpha = sum(weights[col] * oos_norm[col] for col in feature_cols)
        
        # Generate signals
        signal = np.where(oos_alpha > threshold, 1, -1)
        
        # Forward returns
        oos_data = oos_data.copy()
        oos_data['forward_return'] = oos_data['log_return'].shift(-forward_horizon)
        oos_data['signal'] = signal
        valid_data = oos_data.dropna()
        
        if len(valid_data) < 30:
            continue
        
        # Calculate metrics
        correct = (valid_data['signal'] * valid_data['forward_return']) > 0
        hit_rate = correct.mean()
        
        # Calculate P&L
        position_returns = valid_data['signal'] * valid_data['forward_return']
        cumulative_return = (1 + position_returns).prod() - 1
        period_pnl = equity * cumulative_return
        equity = equity * (1 + cumulative_return)
        
        results.append({
            'date': oos_day,
            'hit_rate': hit_rate,
            'period_return': cumulative_return,
            'period_pnl': period_pnl,
            'ending_equity': equity,
            'num_signals': len(valid_data)
        })
    
    return {
        'final_equity': equity,
        'total_return_pct': ((equity - 100000) / 100000) * 100,
        'results': results
    }


def run_comparative_4year_1min():
    """Run 4-year comparative backtest on 1-minute bars for SPY, QQQ, IWM."""
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    print("=" * 80)
    print("4-YEAR COMPARATIVE BACKTEST: ORIGINAL vs NO-SENTIMENT")
    print("Timeframe: 1-Minute Bars | Horizon: 15-min forward return")
    print("Period: 2022-01-01 to 2026-01-24")
    print("=" * 80)
    
    # Weight configurations
    original_weights = {'rsi_14': 0.4, 'volume_zscore': 0.3, 'sentiment': 0.3}
    no_sent_weights = {'rsi_14': 0.6, 'volume_zscore': 0.4}
    
    summary_results = []
    
    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"SYMBOL: {symbol}")
        print("=" * 80)
        
        # Load cached data
        print(f"\n[{symbol}] Loading cached 1-minute bars...")
        try:
            df = load_cached_1min_bars(symbol)
            print(f"[{symbol}] Date range: {df.index[0]} to {df.index[-1]}")
        except FileNotFoundError as e:
            print(f"[{symbol}] ERROR: {e}")
            continue
        
        # Calculate features
        print(f"[{symbol}] Calculating features...")
        df = calculate_features(df)
        
        # Trim warmup period
        df = df.iloc[20:]
        print(f"[{symbol}] Bars after warmup: {len(df):,}")
        
        # Run ORIGINAL strategy
        print(f"\n[{symbol}] Running ORIGINAL (RSI 40% / Vol 30% / Sent 30%)...")
        orig_result = run_daily_walk_forward(df, original_weights)
        
        # Run NO-SENTIMENT strategy
        print(f"[{symbol}] Running NO-SENTIMENT (RSI 60% / Vol 40%)...")
        ns_df = df[['rsi_14', 'volume_zscore', 'log_return', 'close']].copy()
        ns_df['date'] = df['date']
        ns_result = run_daily_walk_forward(ns_df, no_sent_weights)
        
        # Calculate metrics
        orig_periods = orig_result['results']
        ns_periods = ns_result['results']
        
        if not orig_periods or not ns_periods:
            print(f"[{symbol}] No valid periods - skipping")
            continue
        
        orig_avg_hr = np.mean([r['hit_rate'] for r in orig_periods])
        ns_avg_hr = np.mean([r['hit_rate'] for r in ns_periods])
        
        orig_win_days = sum(1 for r in orig_periods if r['period_pnl'] > 0)
        ns_win_days = sum(1 for r in ns_periods if r['period_pnl'] > 0)
        
        # Print results
        print(f"\n[{symbol}] RESULTS COMPARISON")
        print("-" * 70)
        print(f"{'Metric':<30} {'ORIGINAL':>18} {'NO-SENTIMENT':>18}")
        print("-" * 70)
        print(f"{'Initial Capital':<30} ${'100,000.00':>17} ${'100,000.00':>17}")
        print(f"{'Final Equity':<30} ${orig_result['final_equity']:>17,.2f} ${ns_result['final_equity']:>17,.2f}")
        print(f"{'Total Return':<30} {orig_result['total_return_pct']:>17.2f}% {ns_result['total_return_pct']:>17.2f}%")
        print(f"{'Avg Hit Rate':<30} {orig_avg_hr*100:>17.1f}% {ns_avg_hr*100:>17.1f}%")
        print(f"{'Winning Days':<30} {orig_win_days:>18} {ns_win_days:>18}")
        print(f"{'Total Days':<30} {len(orig_periods):>18} {len(ns_periods):>18}")
        print("-" * 70)
        
        # Determine winner
        diff = ns_result['total_return_pct'] - orig_result['total_return_pct']
        if diff > 0:
            winner = "NO-SENTIMENT"
            print(f"[OK] NO-SENTIMENT outperforms by {diff:.2f}%")
        else:
            winner = "ORIGINAL"
            print(f"[!!] ORIGINAL outperforms by {-diff:.2f}%")
        
        summary_results.append({
            'symbol': symbol,
            'orig_return': orig_result['total_return_pct'],
            'ns_return': ns_result['total_return_pct'],
            'orig_equity': orig_result['final_equity'],
            'ns_equity': ns_result['final_equity'],
            'orig_hr': orig_avg_hr,
            'ns_hr': ns_avg_hr,
            'winner': winner
        })
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: 4-YEAR BACKTEST RESULTS (1-MINUTE BARS)")
    print("=" * 80)
    print(f"\n{'Symbol':<10} {'ORIGINAL Return':>18} {'NO-SENT Return':>18} {'Winner':>15}")
    print("-" * 70)
    for r in summary_results:
        print(f"{r['symbol']:<10} {r['orig_return']:>+17.2f}% {r['ns_return']:>+17.2f}% {r['winner']:>15}")
    
    print("=" * 80)
    
    # Overall verdict
    orig_wins = sum(1 for r in summary_results if r['winner'] == 'ORIGINAL')
    ns_wins = sum(1 for r in summary_results if r['winner'] == 'NO-SENTIMENT')
    
    print(f"\nOVERALL: ORIGINAL wins {orig_wins}/{len(summary_results)} | NO-SENTIMENT wins {ns_wins}/{len(summary_results)}")
    
    if ns_wins > orig_wins:
        print("\n[OK] RECOMMENDATION: Remove fake sentiment factor")
    elif orig_wins > ns_wins:
        print("\n[!!] FINDING: Fake sentiment (constant proxy) appears to add value")
    else:
        print("\n[--] FINDING: Results are mixed - further investigation needed")
    
    # Additional stats
    print("\n" + "-" * 80)
    print("DETAILED STATISTICS")
    print("-" * 80)
    for r in summary_results:
        print(f"{r['symbol']}: Original HR={r['orig_hr']*100:.1f}%, No-Sent HR={r['ns_hr']*100:.1f}%")
    
    print("=" * 80)
    
    return summary_results


if __name__ == '__main__':
    run_comparative_4year_1min()
