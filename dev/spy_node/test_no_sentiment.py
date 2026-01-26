"""
Comparative Backtest: Original (with fake sentiment) vs No-Sentiment
Tests the 15-day rolling walk-forward with sentiment removed.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Load environment from .env file manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Map common .env variable names to what Alpaca SDK expects
if 'ALPACA_API_KEY' in os.environ and 'APCA_API_KEY_ID' not in os.environ:
    os.environ['APCA_API_KEY_ID'] = os.environ['ALPACA_API_KEY']
if 'ALPACA_SECRET_KEY' in os.environ and 'APCA_API_SECRET_KEY' not in os.environ:
    os.environ['APCA_API_SECRET_KEY'] = os.environ['ALPACA_SECRET_KEY']
if 'APCA_API_BASE_URL' not in os.environ:
    os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets'

from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer, add_technical_indicators, merge_news_pit
from src.discovery import trim_warmup_period
from src.pnl_tracker import simulate_portfolio, calculate_max_drawdown


def get_trading_days(end_date: datetime, num_days: int) -> list:
    """Get list of trading days going backwards from end_date."""
    trading_days = []
    current = end_date
    while len(trading_days) < num_days:
        if current.weekday() < 5:
            trading_days.append(current)
        current -= timedelta(days=1)
    return list(reversed(trading_days))


def calculate_alpha_two_factor(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Calculate alpha score using only RSI and Volume Z-Score.
    Normalizes each factor to 0-1 range.
    """
    feature_cols = list(weights.keys())
    normalized = {}
    
    for col in feature_cols:
        col_min = df[col].min()
        col_max = df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            normalized[col] = (df[col] - col_min) / col_range
        else:
            normalized[col] = pd.Series(0.5, index=df.index)
    
    alpha_score = sum(weights[col] * normalized[col] for col in feature_cols)
    return alpha_score


def optimize_two_factor_weights(df: pd.DataFrame, horizon: int = 15) -> dict:
    """
    Grid search for optimal RSI/Volume weights (no sentiment).
    """
    feature_cols = ['rsi_14', 'volume_zscore']
    
    working_df = df[feature_cols + ['log_return']].copy()
    working_df['forward_return'] = working_df['log_return'].shift(-horizon)
    working_df = working_df.dropna()
    
    if len(working_df) < 50:
        return {'rsi_14': 0.6, 'volume_zscore': 0.4}, 0.5
    
    # Normalize features
    normalized = {}
    for col in feature_cols:
        col_min = working_df[col].min()
        col_max = working_df[col].max()
        col_range = col_max - col_min
        if col_range > 0:
            normalized[col] = (working_df[col] - col_min) / col_range
        else:
            normalized[col] = pd.Series(0.5, index=working_df.index)
    
    # Grid search: RSI weight from 0.3 to 0.9
    best_hr = 0
    best_weights = {'rsi_14': 0.6, 'volume_zscore': 0.4}
    
    for rsi_wt in np.arange(0.3, 0.95, 0.1):
        vol_wt = round(1.0 - rsi_wt, 2)
        
        alpha = rsi_wt * normalized['rsi_14'] + vol_wt * normalized['volume_zscore']
        median_alpha = alpha.median()
        signal = np.where(alpha > median_alpha, 1, -1)
        correct = (signal * working_df['forward_return'].values) > 0
        hr = correct.mean()
        
        if hr > best_hr:
            best_hr = hr
            best_weights = {'rsi_14': round(rsi_wt, 2), 'volume_zscore': round(vol_wt, 2)}
    
    return best_weights, best_hr


def run_comparative_backtest(days: int = 15, in_sample_days: int = 3):
    """
    Run rolling walk-forward backtest comparing:
    - Original: RSI 40% + Volume 30% + Sentiment 30%
    - No-Sentiment: RSI + Volume only (optimized)
    """
    print("\n" + "=" * 70)
    print("COMPARATIVE BACKTEST: Original vs No-Sentiment")
    print("=" * 70)
    
    symbol = 'SPY'
    initial_capital = 100000.0
    
    # Initialize clients
    alpaca_client = AlpacaDataClient()
    fmp_client = FMPDataClient()
    feature_engineer = FeatureEngineer()
    
    # Date range
    end_date = datetime.now() - timedelta(days=1)
    total_days_needed = days + in_sample_days
    trading_days = get_trading_days(end_date, total_days_needed)
    
    print(f"Symbol: {symbol}")
    print(f"Date Range: {trading_days[0].strftime('%Y-%m-%d')} to {trading_days[-1].strftime('%Y-%m-%d')}")
    print(f"Total Days: {len(trading_days)} | OOS Windows: {len(trading_days) - in_sample_days}")
    
    # Fetch all data
    start_str = trading_days[0].strftime('%Y-%m-%d')
    end_str = (trading_days[-1] + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"\n[DATA] Fetching {total_days_needed} days of 1-minute bars...")
    all_bars = alpaca_client.fetch_historical_bars(
        symbol=symbol, timeframe='1Min', start=start_str, end=end_str, feed='sip'
    )
    print(f"[DATA] Fetched {len(all_bars)} bars")
    
    # Fetch news (needed for original comparison)
    news_start = (trading_days[0] - timedelta(days=3)).strftime('%Y-%m-%d')
    print(f"[DATA] Fetching news from {news_start} to {end_str}...")
    news_list = fmp_client.fetch_historical_news(symbol, news_start, end_str)
    
    # Results containers
    original_results = []
    no_sent_results = []
    
    original_equity = initial_capital
    no_sent_equity = initial_capital
    
    num_windows = len(trading_days) - in_sample_days
    
    print(f"\n{'='*70}")
    print(f"{'Window':<8} {'Date':<12} {'ORIGINAL (w/ Sent)':<25} {'NO-SENTIMENT':<25}")
    print(f"{'':8} {'':12} {'HR%':>8} {'P&L':>14} {'HR%':>8} {'P&L':>14}")
    print("-" * 70)
    
    for window_idx in range(num_windows):
        is_start_idx = window_idx
        is_end_idx = window_idx + in_sample_days
        oos_idx = is_end_idx
        
        is_days = trading_days[is_start_idx:is_end_idx]
        oos_day = trading_days[oos_idx]
        
        # Extract bars
        is_start = is_days[0].strftime('%Y-%m-%d')
        is_end = (is_days[-1] + timedelta(days=1)).strftime('%Y-%m-%d')
        oos_start = oos_day.strftime('%Y-%m-%d')
        oos_end = (oos_day + timedelta(days=1)).strftime('%Y-%m-%d')
        
        is_mask = (all_bars.index >= is_start) & (all_bars.index < is_end)
        oos_mask = (all_bars.index >= oos_start) & (all_bars.index < oos_end)
        
        is_bars = all_bars.loc[is_mask].copy()
        oos_bars = all_bars.loc[oos_mask].copy()
        
        if len(is_bars) < 100 or len(oos_bars) < 50:
            continue
        
        # ============ ORIGINAL STRATEGY (with fake sentiment) ============
        # In-Sample features
        is_df_orig = is_bars.copy()
        is_df_orig['log_return'] = feature_engineer.calculate_log_return(is_df_orig)
        is_features_orig = merge_news_pit(is_df_orig, news_list, lookback_hours=4)
        add_technical_indicators(is_features_orig)
        is_features_orig = trim_warmup_period(is_features_orig, warmup_rows=20)
        
        # OOS features
        oos_df_orig = oos_bars.copy()
        oos_df_orig['log_return'] = feature_engineer.calculate_log_return(oos_df_orig)
        oos_features_orig = merge_news_pit(oos_df_orig, news_list, lookback_hours=4)
        add_technical_indicators(oos_features_orig)
        oos_features_orig = trim_warmup_period(oos_features_orig, warmup_rows=20)
        
        if len(is_features_orig) < 50 or len(oos_features_orig) < 30:
            continue
        
        # Original: Fixed 40/30/30 weights
        orig_weights = {'rsi_14': 0.4, 'volume_zscore': 0.3, 'sentiment': 0.3}
        
        # Calculate original alpha (IS)
        orig_cols = ['rsi_14', 'volume_zscore', 'sentiment']
        is_normalized = {}
        for col in orig_cols:
            col_min = is_features_orig[col].min()
            col_max = is_features_orig[col].max()
            rng = col_max - col_min
            is_normalized[col] = (is_features_orig[col] - col_min) / rng if rng > 0 else 0.5
        
        is_alpha_orig = sum(orig_weights[c] * is_normalized[c] for c in orig_cols)
        threshold_orig = is_alpha_orig.median()
        
        # OOS original
        oos_normalized = {}
        for col in orig_cols:
            col_min = oos_features_orig[col].min()
            col_max = oos_features_orig[col].max()
            rng = col_max - col_min
            oos_normalized[col] = (oos_features_orig[col] - col_min) / rng if rng > 0 else 0.5
        
        oos_alpha_orig = sum(orig_weights[c] * oos_normalized[c] for c in orig_cols)
        
        oos_sim_orig = oos_features_orig[['close', 'log_return']].copy()
        oos_sim_orig['signal'] = np.where(oos_alpha_orig > threshold_orig, 1, -1)
        
        # Hit rate
        oos_sim_orig['forward_return'] = oos_sim_orig['log_return'].shift(-15)
        oos_valid_orig = oos_sim_orig.dropna()
        if len(oos_valid_orig) > 0:
            correct_orig = (oos_valid_orig['signal'] * oos_valid_orig['forward_return']) > 0
            hr_orig = correct_orig.mean()
        else:
            hr_orig = 0.5
        
        # P&L
        pnl_orig = simulate_portfolio(oos_sim_orig.drop(columns=['forward_return']), 
                                       initial_capital=original_equity)
        original_equity = pnl_orig['final_equity']
        pnl_dollars_orig = pnl_orig['total_return_dollars']
        
        original_results.append({
            'date': oos_day.strftime('%Y-%m-%d'),
            'hit_rate': hr_orig,
            'pnl': pnl_dollars_orig,
            'equity': original_equity
        })
        
        # ============ NO-SENTIMENT STRATEGY ============
        # In-Sample features (no sentiment merge needed, just technicals)
        is_df_ns = is_bars.copy()
        is_df_ns['log_return'] = feature_engineer.calculate_log_return(is_df_ns)
        add_technical_indicators(is_df_ns)
        is_features_ns = trim_warmup_period(is_df_ns, warmup_rows=20)
        
        # OOS features
        oos_df_ns = oos_bars.copy()
        oos_df_ns['log_return'] = feature_engineer.calculate_log_return(oos_df_ns)
        add_technical_indicators(oos_df_ns)
        oos_features_ns = trim_warmup_period(oos_df_ns, warmup_rows=20)
        
        # Optimize 2-factor weights on IS
        best_weights_ns, is_hr_ns = optimize_two_factor_weights(is_features_ns, horizon=15)
        
        # Calculate OOS alpha
        is_alpha_ns = calculate_alpha_two_factor(is_features_ns, best_weights_ns)
        threshold_ns = is_alpha_ns.median()
        
        oos_alpha_ns = calculate_alpha_two_factor(oos_features_ns, best_weights_ns)
        
        oos_sim_ns = oos_features_ns[['close', 'log_return']].copy()
        oos_sim_ns['signal'] = np.where(oos_alpha_ns > threshold_ns, 1, -1)
        
        # Hit rate
        oos_sim_ns['forward_return'] = oos_sim_ns['log_return'].shift(-15)
        oos_valid_ns = oos_sim_ns.dropna()
        if len(oos_valid_ns) > 0:
            correct_ns = (oos_valid_ns['signal'] * oos_valid_ns['forward_return']) > 0
            hr_ns = correct_ns.mean()
        else:
            hr_ns = 0.5
        
        # P&L
        pnl_ns = simulate_portfolio(oos_sim_ns.drop(columns=['forward_return']), 
                                     initial_capital=no_sent_equity)
        no_sent_equity = pnl_ns['final_equity']
        pnl_dollars_ns = pnl_ns['total_return_dollars']
        
        no_sent_results.append({
            'date': oos_day.strftime('%Y-%m-%d'),
            'hit_rate': hr_ns,
            'pnl': pnl_dollars_ns,
            'equity': no_sent_equity,
            'weights': best_weights_ns
        })
        
        # Print row
        print(f"{window_idx+1:<8} {oos_day.strftime('%Y-%m-%d'):<12} "
              f"{hr_orig*100:>7.1f}% {pnl_dollars_orig:>+13,.2f} "
              f"{hr_ns*100:>7.1f}% {pnl_dollars_ns:>+13,.2f}")
    
    # ============ SUMMARY ============
    print("=" * 70)
    print("\n" + "=" * 70)
    print("COMPARATIVE SUMMARY")
    print("=" * 70)
    
    if original_results and no_sent_results:
        orig_total_pnl = sum(r['pnl'] for r in original_results)
        ns_total_pnl = sum(r['pnl'] for r in no_sent_results)
        
        orig_avg_hr = np.mean([r['hit_rate'] for r in original_results])
        ns_avg_hr = np.mean([r['hit_rate'] for r in no_sent_results])
        
        orig_win_days = sum(1 for r in original_results if r['pnl'] > 0)
        ns_win_days = sum(1 for r in no_sent_results if r['pnl'] > 0)
        
        orig_final = original_results[-1]['equity']
        ns_final = no_sent_results[-1]['equity']
        
        print(f"\n{'Metric':<30} {'ORIGINAL':>18} {'NO-SENTIMENT':>18}")
        print("-" * 70)
        print(f"{'Initial Capital':<30} ${initial_capital:>16,.2f} ${initial_capital:>16,.2f}")
        print(f"{'Final Equity':<30} ${orig_final:>16,.2f} ${ns_final:>16,.2f}")
        print(f"{'Total P&L':<30} ${orig_total_pnl:>+16,.2f} ${ns_total_pnl:>+16,.2f}")
        print(f"{'Return %':<30} {(orig_total_pnl/initial_capital)*100:>17.2f}% {(ns_total_pnl/initial_capital)*100:>17.2f}%")
        print(f"{'Avg Hit Rate':<30} {orig_avg_hr*100:>17.1f}% {ns_avg_hr*100:>17.1f}%")
        print(f"{'Winning Days':<30} {orig_win_days:>18} {ns_win_days:>18}")
        print(f"{'Total Days':<30} {len(original_results):>18} {len(no_sent_results):>18}")
        
        print("-" * 70)
        
        # Verdict
        diff = ns_total_pnl - orig_total_pnl
        if diff > 0:
            print(f"\n✅ NO-SENTIMENT outperforms by ${diff:+,.2f}")
        elif diff < 0:
            print(f"\n⚠️ ORIGINAL outperforms by ${-diff:,.2f}")
        else:
            print(f"\n➖ Results are equivalent")
        
        print("=" * 70)
    
    return original_results, no_sent_results


if __name__ == '__main__':
    run_comparative_backtest(days=15, in_sample_days=3)
