"""
Full Backtest with Trade-Level Data
- 675 parameter combinations (225 per symbol)
- 2-year period (2024-01-01 to 2025-12-31)
- Parallel execution across SPY, QQQ, IWM
- Every trade logged with entry/exit/P&L
- Real-time progress tracking
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import itertools

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
OUTPUT_DIR = r"a:\1\Magellan\test\spy_node"

# Date range: 2 years
START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

# Parameter grid (same as 15-hour test)
RSI_PERIODS = [10, 14, 20]
VOL_WINDOWS = [10, 20, 30]
RSI_WEIGHTS = [0.4, 0.5, 0.6, 0.7, 0.8]
HORIZONS = [5, 10, 15, 20, 30]

# Total combos per symbol: 3 * 3 * 5 * 5 = 225
SYMBOLS = ['SPY', 'QQQ', 'IWM']


def log_progress(msg: str):
    """Thread-safe progress logging."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"{timestamp} - {msg}\n"
    with open(os.path.join(OUTPUT_DIR, "full_backtest_progress.txt"), "a") as f:
        f.write(line)
        f.flush()
    print(line.strip())


def load_data(symbol: str) -> pd.DataFrame:
    """Load cached 1-minute data for a symbol."""
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath)
    df = df.loc[START_DATE:END_DATE]
    return df


def calculate_features(df: pd.DataFrame, rsi_period: int, vol_window: int) -> pd.DataFrame:
    """Calculate RSI and Volume Z-Score with given parameters."""
    df = df.copy()
    
    # Log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0
    df.loc[avg_gain == 0, 'rsi'] = 0.0
    
    # Volume Z-Score
    vol_mean = df['volume'].rolling(window=vol_window).mean()
    vol_std = df['volume'].rolling(window=vol_window).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    # Drop warmup
    df = df.iloc[max(rsi_period, vol_window):]
    
    return df


def run_single_backtest(
    df: pd.DataFrame,
    symbol: str,
    rsi_period: int,
    vol_window: int,
    rsi_weight: float,
    horizon: int
) -> tuple:
    """
    Run a single parameter combo backtest with proper position management.
    Returns (trades_list, summary_dict)
    """
    vol_weight = 1.0 - rsi_weight
    
    # Group by trading day
    df = df.copy()
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    
    trades = []
    equity = 100000.0
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        # In-sample: previous 3 days
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_mask = df['date'].isin(is_days)
        oos_mask = df['date'] == oos_day
        
        is_data = df.loc[is_mask, ['rsi', 'volume_zscore', 'log_return', 'close']].copy()
        oos_data = df.loc[oos_mask, ['rsi', 'volume_zscore', 'log_return', 'close']].copy()
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue
        
        # Normalize in-sample features
        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        
        rsi_range = max(rsi_max - rsi_min, 1e-6)
        vol_range = max(vol_max - vol_min, 1e-6)
        
        is_rsi_norm = (is_data['rsi'] - rsi_min) / rsi_range
        is_vol_norm = (is_data['volume_zscore'] - vol_min) / vol_range
        is_alpha = rsi_weight * is_rsi_norm + vol_weight * is_vol_norm
        threshold = is_alpha.median()
        
        # OOS: Normalize and get signals
        oos_rsi_norm = (oos_data['rsi'] - rsi_min) / rsi_range
        oos_vol_norm = (oos_data['volume_zscore'] - vol_min) / vol_range
        oos_alpha = rsi_weight * oos_rsi_norm + vol_weight * oos_vol_norm
        
        # PROPER POSITION MANAGEMENT:
        # Trade at market open, hold for 'horizon' minutes, exit, repeat
        oos_indices = oos_data.index.tolist()
        i = 0
        while i + horizon < len(oos_indices):
            entry_idx = oos_indices[i]
            exit_idx = oos_indices[i + horizon]
            
            # Get signal at entry
            alpha_val = oos_alpha.loc[entry_idx]
            signal = 1 if alpha_val > threshold else -1
            
            entry_price = oos_data.loc[entry_idx, 'close']
            exit_price = oos_data.loc[exit_idx, 'close']
            
            # Calculate P&L
            if signal == 1:  # LONG
                pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:  # SHORT
                pnl_pct = (entry_price - exit_price) / entry_price * 100
            
            pnl_dollars = equity * (pnl_pct / 100)
            equity += pnl_dollars
            correct = 1 if pnl_pct > 0 else 0
            
            trades.append({
                'symbol': symbol,
                'rsi_period': rsi_period,
                'vol_window': vol_window,
                'rsi_weight': rsi_weight,
                'horizon': horizon,
                'entry_time': str(entry_idx),
                'exit_time': str(exit_idx),
                'signal': 'LONG' if signal == 1 else 'SHORT',
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'pnl_pct': round(pnl_pct, 6),
                'pnl_dollars': round(pnl_dollars, 2),
                'equity_after': round(equity, 2),
                'correct': correct
            })
            
            # Move to next trade (after exit)
            i += horizon
    
    # Summary
    if trades:
        total_return = ((equity - 100000) / 100000) * 100
        avg_hr = sum(t['correct'] for t in trades) / len(trades)
        
        # Sharpe (daily returns approximation)
        daily_pnl = {}
        for t in trades:
            day = t['entry_time'][:10]
            daily_pnl[day] = daily_pnl.get(day, 0) + t['pnl_dollars']
        if daily_pnl:
            returns = list(daily_pnl.values())
            if np.std(returns) > 0:
                sharpe = (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
            else:
                sharpe = 0
        else:
            sharpe = 0
    else:
        total_return = 0
        avg_hr = 0
        sharpe = 0
    
    summary = {
        'symbol': symbol,
        'rsi_period': rsi_period,
        'vol_window': vol_window,
        'rsi_weight': rsi_weight,
        'horizon': horizon,
        'total_return': total_return,
        'avg_hit_rate': avg_hr,
        'sharpe': sharpe,
        'final_equity': equity,
        'num_trades': len(trades)
    }
    
    return trades, summary


def run_symbol_backtest(symbol: str) -> tuple:
    """Run all 225 parameter combinations for one symbol."""
    log_progress(f"{symbol}: Starting backtest")
    
    # Load data
    df_raw = load_data(symbol)
    log_progress(f"{symbol}: Loaded {len(df_raw):,} bars ({START_DATE} to {END_DATE})")
    
    all_trades = []
    all_summaries = []
    
    # Generate all parameter combinations
    combos = list(itertools.product(RSI_PERIODS, VOL_WINDOWS, RSI_WEIGHTS, HORIZONS))
    total_combos = len(combos)
    
    log_progress(f"{symbol}: Testing {total_combos} parameter combinations")
    
    for combo_idx, (rsi_period, vol_window, rsi_weight, horizon) in enumerate(combos):
        # Calculate features for this RSI/Vol combo
        df = calculate_features(df_raw.copy(), rsi_period, vol_window)
        
        # Run backtest
        trades, summary = run_single_backtest(
            df, symbol, rsi_period, vol_window, rsi_weight, horizon
        )
        
        all_trades.extend(trades)
        all_summaries.append(summary)
        
        # Progress every 25 combos
        if (combo_idx + 1) % 25 == 0:
            log_progress(f"{symbol}: {combo_idx + 1}/{total_combos} ({100*(combo_idx+1)/total_combos:.0f}%)")
    
    log_progress(f"{symbol}: Complete - {len(all_trades):,} trades, {len(all_summaries)} summaries")
    
    return all_trades, all_summaries


def main():
    # Clear progress file
    progress_file = os.path.join(OUTPUT_DIR, "full_backtest_progress.txt")
    with open(progress_file, "w") as f:
        f.write(f"=== FULL BACKTEST STARTED: {datetime.now()} ===\n")
        f.write(f"Period: {START_DATE} to {END_DATE}\n")
        f.write(f"Symbols: {', '.join(SYMBOLS)}\n")
        f.write(f"Combinations per symbol: {len(RSI_PERIODS) * len(VOL_WINDOWS) * len(RSI_WEIGHTS) * len(HORIZONS)}\n")
        f.write("=" * 60 + "\n\n")
    
    log_progress("Starting parallel backtest across 3 symbols...")
    
    all_trades = []
    all_summaries = []
    
    # PARALLEL EXECUTION
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_symbol_backtest, sym): sym for sym in SYMBOLS}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                trades, summaries = future.result()
                all_trades.extend(trades)
                all_summaries.extend(summaries)
                log_progress(f"{symbol}: Received {len(trades):,} trades, {len(summaries)} summaries")
            except Exception as e:
                log_progress(f"{symbol}: ERROR - {e}")
    
    # Save trade-level data
    trades_df = pd.DataFrame(all_trades)
    trades_file = os.path.join(OUTPUT_DIR, "all_trades_full.csv")
    trades_df.to_csv(trades_file, index=False)
    log_progress(f"Saved {len(trades_df):,} trades to all_trades_full.csv")
    
    # Save summary data
    summary_df = pd.DataFrame(all_summaries)
    summary_file = os.path.join(OUTPUT_DIR, "all_summaries_full.csv")
    summary_df.to_csv(summary_file, index=False)
    log_progress(f"Saved {len(summary_df)} summaries to all_summaries_full.csv")
    
    # Print top results
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    print(f"Total Trades: {len(trades_df):,}")
    print(f"Total Summaries: {len(summary_df)}")
    
    for sym in SYMBOLS:
        sym_df = summary_df[summary_df['symbol'] == sym]
        if len(sym_df) > 0:
            best = sym_df.loc[sym_df['sharpe'].idxmax()]
            print(f"\n{sym} Best (by Sharpe):")
            print(f"  RSI={int(best['rsi_period'])}, Vol={int(best['vol_window'])}, Weight={best['rsi_weight']}, Horizon={int(best['horizon'])}")
            print(f"  Sharpe={best['sharpe']:.3f}, Return={best['total_return']:.2f}%, Trades={int(best['num_trades'])}")
    
    print("=" * 80)
    log_progress("=== BACKTEST COMPLETE ===")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
