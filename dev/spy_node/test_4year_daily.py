"""
4-Year Backtest Using Cached Daily Data
Compares Original (with fake sentiment) vs No-Sentiment for SPY, QQQ, IWM
Period: 2022-01-01 to 2026-01-24
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Setup paths
CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
NEWS_DIR = r"a:\1\Magellan\data\cache\news"

def load_cached_daily_bars(symbol: str, start_year: int = 2022, end_year: int = 2025) -> pd.DataFrame:
    """Load and concatenate cached daily bar parquet files for a symbol."""
    all_data = []
    
    # Look for relevant parquet files
    for year_start in range(start_year, end_year + 1, 2):
        year_end = year_start + 1
        filename = f"{symbol}_1day_{year_start}0101_{year_end}1231.parquet"
        filepath = os.path.join(CACHE_DIR, filename)
        
        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            all_data.append(df)
            print(f"  Loaded: {filename} ({len(df)} bars)")
    
    # Also try the 2024-2025 file pattern
    for pattern in [
        f"{symbol}_1day_20240101_20251231.parquet",
        f"{symbol}_1day_20240601_20260118.parquet",
    ]:
        filepath = os.path.join(CACHE_DIR, pattern)
        if os.path.exists(filepath):
            df = pd.read_parquet(filepath)
            all_data.append(df)
            print(f"  Loaded: {pattern} ({len(df)} bars)")
    
    if not all_data:
        raise FileNotFoundError(f"No cached data found for {symbol}")
    
    # Concatenate and deduplicate
    combined = pd.concat(all_data)
    combined = combined[~combined.index.duplicated(keep='last')]
    combined = combined.sort_index()
    
    # Filter to date range
    start_date = f"{start_year}-01-01"
    end_date = "2026-01-24"
    combined = combined.loc[start_date:end_date]
    
    return combined


def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate RSI and Volume Z-Score for daily bars."""
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
    
    # Volume Z-Score (20-day)
    vol_mean = df['volume'].rolling(window=20).mean()
    vol_std = df['volume'].rolling(window=20).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    # Fake sentiment (article count proxy - simulated as random noise for comparison)
    # Since we don't have article count data, we simulate constant sentiment
    df['sentiment'] = 0.0  # This is what the real system was using anyway
    
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


def run_walk_forward_daily(
    df: pd.DataFrame,
    weights: dict,
    in_sample_days: int = 60,
    out_sample_days: int = 20,
    forward_horizon: int = 1
) -> dict:
    """
    Run rolling walk-forward backtest on daily bars.
    
    Args:
        df: DataFrame with features
        weights: Dict of feature weights
        in_sample_days: Days for in-sample optimization
        out_sample_days: Days for out-of-sample testing
        forward_horizon: Forward return horizon in days
    """
    feature_cols = list(weights.keys())
    
    # Prepare data
    working_df = df[feature_cols + ['log_return', 'close']].copy()
    working_df['forward_return'] = working_df['log_return'].shift(-forward_horizon)
    working_df = working_df.dropna()
    
    results = []
    equity = 100000.0
    window_size = in_sample_days + out_sample_days
    
    i = 0
    while i + window_size <= len(working_df):
        # In-sample window
        is_start = i
        is_end = i + in_sample_days
        oos_start = is_end
        oos_end = oos_start + out_sample_days
        
        is_data = working_df.iloc[is_start:is_end]
        oos_data = working_df.iloc[oos_start:oos_end]
        
        # Normalize features on in-sample
        is_norm = normalize_features(is_data, feature_cols)
        
        # Calculate in-sample alpha
        is_alpha = sum(weights[col] * is_norm[col] for col in feature_cols)
        threshold = is_alpha.median()
        
        # Normalize features on out-of-sample (using OOS stats - this is how the original does it)
        oos_norm = normalize_features(oos_data, feature_cols)
        oos_alpha = sum(weights[col] * oos_norm[col] for col in feature_cols)
        
        # Generate signals
        signal = np.where(oos_alpha > threshold, 1, -1)
        
        # Calculate OOS performance
        oos_returns = oos_data['forward_return'].values
        correct = (signal * oos_returns) > 0
        hit_rate = correct.mean()
        
        # Calculate P&L
        position_returns = signal * oos_returns
        cumulative_return = (1 + position_returns).prod() - 1
        period_pnl = equity * cumulative_return
        equity = equity * (1 + cumulative_return)
        
        results.append({
            'period_start': oos_data.index[0],
            'period_end': oos_data.index[-1],
            'hit_rate': hit_rate,
            'period_return': cumulative_return,
            'period_pnl': period_pnl,
            'ending_equity': equity
        })
        
        # Advance window
        i += out_sample_days
    
    return {
        'final_equity': equity,
        'total_return_pct': ((equity - 100000) / 100000) * 100,
        'results': results
    }


def run_comparative_4year_backtest():
    """Run 4-year comparative backtest for SPY, QQQ, IWM."""
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    print("=" * 80)
    print("4-YEAR COMPARATIVE BACKTEST: ORIGINAL vs NO-SENTIMENT")
    print("Period: 2022-01-01 to 2026-01-24 (Daily Bars)")
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
        print(f"\n[{symbol}] Loading cached daily bars...")
        try:
            df = load_cached_daily_bars(symbol)
            print(f"[{symbol}] Total bars loaded: {len(df)}")
            print(f"[{symbol}] Date range: {df.index[0]} to {df.index[-1]}")
        except FileNotFoundError as e:
            print(f"[{symbol}] ERROR: {e}")
            continue
        
        # Calculate features
        print(f"[{symbol}] Calculating features...")
        df = calculate_features(df)
        
        # Trim warmup period (first 20 days for RSI/Vol calculations)
        df = df.iloc[20:]
        print(f"[{symbol}] Bars after warmup: {len(df)}")
        
        # Run ORIGINAL strategy (with fake sentiment = 0.0)
        print(f"\n[{symbol}] Running ORIGINAL (RSI 40% / Vol 30% / Sent 30%)...")
        orig_result = run_walk_forward_daily(
            df, 
            original_weights,
            in_sample_days=60,
            out_sample_days=20,
            forward_horizon=1
        )
        
        # Run NO-SENTIMENT strategy
        print(f"[{symbol}] Running NO-SENTIMENT (RSI 60% / Vol 40%)...")
        ns_result = run_walk_forward_daily(
            df[['rsi_14', 'volume_zscore', 'log_return', 'close']].copy(),
            no_sent_weights,
            in_sample_days=60,
            out_sample_days=20,
            forward_horizon=1
        )
        
        # Calculate metrics
        orig_periods = orig_result['results']
        ns_periods = ns_result['results']
        
        orig_avg_hr = np.mean([r['hit_rate'] for r in orig_periods])
        ns_avg_hr = np.mean([r['hit_rate'] for r in ns_periods])
        
        orig_win_periods = sum(1 for r in orig_periods if r['period_pnl'] > 0)
        ns_win_periods = sum(1 for r in ns_periods if r['period_pnl'] > 0)
        
        # Print results
        print(f"\n[{symbol}] RESULTS COMPARISON")
        print("-" * 60)
        print(f"{'Metric':<30} {'ORIGINAL':>15} {'NO-SENTIMENT':>15}")
        print("-" * 60)
        print(f"{'Initial Capital':<30} ${'100,000.00':>14} ${'100,000.00':>14}")
        print(f"{'Final Equity':<30} ${orig_result['final_equity']:>14,.2f} ${ns_result['final_equity']:>14,.2f}")
        print(f"{'Total Return':<30} {orig_result['total_return_pct']:>14.2f}% {ns_result['total_return_pct']:>14.2f}%")
        print(f"{'Avg Hit Rate':<30} {orig_avg_hr*100:>14.1f}% {ns_avg_hr*100:>14.1f}%")
        print(f"{'Winning Periods':<30} {orig_win_periods:>15} {ns_win_periods:>15}")
        print(f"{'Total Periods':<30} {len(orig_periods):>15} {len(ns_periods):>15}")
        print("-" * 60)
        
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
            'winner': winner
        })
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY: 4-YEAR BACKTEST RESULTS")
    print("=" * 80)
    print(f"\n{'Symbol':<10} {'ORIGINAL Return':>18} {'NO-SENT Return':>18} {'Winner':>15}")
    print("-" * 70)
    for r in summary_results:
        print(f"{r['symbol']:<10} {r['orig_return']:>17.2f}% {r['ns_return']:>17.2f}% {r['winner']:>15}")
    
    print("=" * 80)
    
    # Overall verdict
    orig_wins = sum(1 for r in summary_results if r['winner'] == 'ORIGINAL')
    ns_wins = sum(1 for r in summary_results if r['winner'] == 'NO-SENTIMENT')
    
    print(f"\nOVERALL: ORIGINAL wins {orig_wins}/{len(summary_results)} | NO-SENTIMENT wins {ns_wins}/{len(summary_results)}")
    
    if ns_wins > orig_wins:
        print("\n[OK] RECOMMENDATION: Remove fake sentiment factor")
    elif orig_wins > ns_wins:
        print("\n[!!] FINDING: Fake sentiment (article count proxy) appears to add value")
    else:
        print("\n[--] FINDING: Results are mixed - further investigation needed")
    
    print("=" * 80)
    
    return summary_results


if __name__ == '__main__':
    run_comparative_4year_backtest()
