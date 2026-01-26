"""
Proper Backtest with Trade-Level Logging
- Parallelized across symbols
- Progress file updated in real-time
- Every trade saved to CSV
- 6-month period: July 2024 - Dec 2024
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
OUTPUT_DIR = r"a:\1\Magellan\test\spy_node"

# Optimal parameters from tuning
RSI_PERIOD = 10
VOL_WINDOW = 10
RSI_WEIGHT = 0.7
VOL_WEIGHT = 0.3
FORWARD_HORIZON = 20

# Date range: 6 months
START_DATE = "2024-07-01"
END_DATE = "2024-12-31"


def log_progress(msg: str):
    """Write progress to file with flush."""
    with open(os.path.join(OUTPUT_DIR, "backtest_progress.txt"), "a") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        f.flush()


def load_and_filter_data(symbol: str) -> pd.DataFrame:
    """Load cached data and filter to date range."""
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath)
    df = df.loc[START_DATE:END_DATE]
    return df


def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate RSI and Volume Z-Score."""
    df = df.copy()
    
    # Log returns
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # RSI
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0
    df.loc[avg_gain == 0, 'rsi'] = 0.0
    
    # Volume Z-Score
    vol_mean = df['volume'].rolling(window=VOL_WINDOW).mean()
    vol_std = df['volume'].rolling(window=VOL_WINDOW).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    # Drop warmup
    df = df.iloc[max(RSI_PERIOD, VOL_WINDOW):]
    
    return df


def run_backtest_with_trades(symbol: str) -> pd.DataFrame:
    """Run backtest and return DataFrame of all trades."""
    log_progress(f"{symbol}: Starting backtest")
    
    # Load data
    df = load_and_filter_data(symbol)
    log_progress(f"{symbol}: Loaded {len(df):,} bars ({START_DATE} to {END_DATE})")
    
    # Calculate features
    df = calculate_features(df)
    log_progress(f"{symbol}: Features calculated, {len(df):,} bars after warmup")
    
    # Group by trading day
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    log_progress(f"{symbol}: {len(trading_days)} trading days")
    
    trades = []
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        # In-sample: previous 3 days
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_mask = df['date'].isin(is_days)
        oos_mask = df['date'] == oos_day
        
        is_data = df.loc[is_mask, ['rsi', 'volume_zscore', 'log_return']].copy()
        oos_data = df.loc[oos_mask, ['rsi', 'volume_zscore', 'log_return', 'close']].copy()
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue
        
        # Normalize in-sample
        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        
        rsi_range = rsi_max - rsi_min if rsi_max > rsi_min else 1
        vol_range = vol_max - vol_min if vol_max > vol_min else 1
        
        is_rsi_norm = (is_data['rsi'] - rsi_min) / rsi_range
        is_vol_norm = (is_data['volume_zscore'] - vol_min) / vol_range
        is_alpha = RSI_WEIGHT * is_rsi_norm + VOL_WEIGHT * is_vol_norm
        threshold = is_alpha.median()
        
        # OOS signals
        oos_rsi_norm = (oos_data['rsi'] - rsi_min) / rsi_range
        oos_vol_norm = (oos_data['volume_zscore'] - vol_min) / vol_range
        oos_alpha = RSI_WEIGHT * oos_rsi_norm + VOL_WEIGHT * oos_vol_norm
        
        signals = np.where(oos_alpha > threshold, 1, -1)
        
        # Forward returns
        oos_data = oos_data.copy()
        oos_data['forward_return'] = oos_data['log_return'].shift(-FORWARD_HORIZON)
        oos_data['signal'] = signals
        oos_data['exit_price'] = oos_data['close'].shift(-FORWARD_HORIZON)
        
        # Record each trade
        for idx, row in oos_data.dropna().iterrows():
            entry_time = idx
            exit_time = oos_data.index[oos_data.index.get_loc(idx) + FORWARD_HORIZON] if (oos_data.index.get_loc(idx) + FORWARD_HORIZON) < len(oos_data) else None
            
            if exit_time is None:
                continue
            
            entry_price = row['close']
            exit_price = row['exit_price']
            signal = int(row['signal'])
            
            if signal == 1:  # LONG
                pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:  # SHORT
                pnl_pct = (entry_price - exit_price) / entry_price * 100
            
            correct = 1 if pnl_pct > 0 else 0
            
            trades.append({
                'symbol': symbol,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'signal': 'LONG' if signal == 1 else 'SHORT',
                'entry_price': round(entry_price, 4),
                'exit_price': round(exit_price, 4),
                'pnl_pct': round(pnl_pct, 4),
                'pnl_dollars': round(pnl_pct * 1000, 2),  # Assuming $100k, 1% position
                'correct': correct,
                'rsi': round(row['rsi'], 2),
                'volume_zscore': round(row['volume_zscore'], 4),
                'alpha': round(oos_alpha.loc[idx], 4)
            })
        
        # Progress every 20 days
        if (day_idx - in_sample_days) % 20 == 0:
            log_progress(f"{symbol}: Day {day_idx-in_sample_days}/{len(trading_days)-in_sample_days}, {len(trades)} trades so far")
    
    log_progress(f"{symbol}: Complete - {len(trades)} total trades")
    return pd.DataFrame(trades)


def main():
    # Clear progress file
    progress_file = os.path.join(OUTPUT_DIR, "backtest_progress.txt")
    with open(progress_file, "w") as f:
        f.write(f"=== BACKTEST STARTED: {datetime.now()} ===\n")
        f.write(f"Period: {START_DATE} to {END_DATE}\n")
        f.write(f"Parameters: RSI={RSI_PERIOD}, Vol={VOL_WINDOW}, Weights={RSI_WEIGHT}/{VOL_WEIGHT}, Horizon={FORWARD_HORIZON}\n")
        f.write("=" * 60 + "\n")
    
    symbols = ['SPY', 'QQQ', 'IWM']
    
    log_progress("Starting parallel backtest across 3 symbols...")
    
    all_trades = []
    
    # Parallel execution
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_backtest_with_trades, sym): sym for sym in symbols}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                trades_df = future.result()
                all_trades.append(trades_df)
                log_progress(f"{symbol}: Received {len(trades_df)} trades from worker")
            except Exception as e:
                log_progress(f"{symbol}: ERROR - {e}")
    
    # Combine and save
    combined_trades = pd.concat(all_trades, ignore_index=True)
    trades_file = os.path.join(OUTPUT_DIR, "all_trades.csv")
    combined_trades.to_csv(trades_file, index=False)
    
    log_progress(f"=== COMPLETE: {len(combined_trades)} total trades saved to all_trades.csv ===")
    
    # Print summary
    print("\n" + "=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)
    print(f"Total trades: {len(combined_trades)}")
    print(f"Saved to: {trades_file}")
    
    for sym in symbols:
        sym_trades = combined_trades[combined_trades['symbol'] == sym]
        if len(sym_trades) > 0:
            print(f"\n{sym}:")
            print(f"  Trades: {len(sym_trades)}")
            print(f"  Hit Rate: {sym_trades['correct'].mean()*100:.1f}%")
            print(f"  Total P&L: ${sym_trades['pnl_dollars'].sum():,.2f}")
            print(f"  Avg P&L/trade: ${sym_trades['pnl_dollars'].mean():.2f}")
    
    print("=" * 70)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
