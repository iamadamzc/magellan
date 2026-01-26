"""
LONG-ONLY Backtest - 4 Years
Only takes positions when signal is LONG, skips SHORT signals.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
OUTPUT_DIR = r"a:\1\Magellan\test\spy_node"

START_DATE = "2022-01-01"
END_DATE = "2026-01-24"

# Using same optimal parameters
OPTIMAL_PARAMS = {
    'SPY': {'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.6, 'horizon': 20},
    'QQQ': {'rsi_period': 10, 'vol_window': 20, 'rsi_weight': 0.5, 'horizon': 20},
    'IWM': {'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.7, 'horizon': 20},
}


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"{ts} - {msg}")


def load_data(symbol: str) -> pd.DataFrame:
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath)
    return df.loc[START_DATE:END_DATE]


def calculate_features(df: pd.DataFrame, rsi_period: int, vol_window: int) -> pd.DataFrame:
    df = df.copy()
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0
    df.loc[avg_gain == 0, 'rsi'] = 0.0
    
    vol_mean = df['volume'].rolling(window=vol_window).mean()
    vol_std = df['volume'].rolling(window=vol_window).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    
    return df.iloc[max(rsi_period, vol_window):]


def run_long_only_backtest(symbol: str) -> pd.DataFrame:
    """Run LONG-only backtest - skip SHORT signals."""
    params = OPTIMAL_PARAMS[symbol]
    rsi_period = params['rsi_period']
    vol_window = params['vol_window']
    rsi_weight = params['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    horizon = params['horizon']
    
    log(f"{symbol}: Loading data...")
    df = load_data(symbol)
    log(f"{symbol}: Loaded {len(df):,} bars")
    
    df = calculate_features(df, rsi_period, vol_window)
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    log(f"{symbol}: {len(trading_days)} trading days")
    
    trades = []
    equity = 100000.0
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_data = df.loc[df['date'].isin(is_days), ['rsi', 'volume_zscore', 'close']].copy()
        oos_data = df.loc[df['date'] == oos_day, ['rsi', 'volume_zscore', 'close']].copy()
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue
        
        # Normalize
        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        rsi_range = max(rsi_max - rsi_min, 1e-6)
        vol_range = max(vol_max - vol_min, 1e-6)
        
        is_rsi_norm = (is_data['rsi'] - rsi_min) / rsi_range
        is_vol_norm = (is_data['volume_zscore'] - vol_min) / vol_range
        is_alpha = rsi_weight * is_rsi_norm + vol_weight * is_vol_norm
        threshold = is_alpha.median()
        
        oos_rsi_norm = (oos_data['rsi'] - rsi_min) / rsi_range
        oos_vol_norm = (oos_data['volume_zscore'] - vol_min) / vol_range
        oos_alpha = rsi_weight * oos_rsi_norm + vol_weight * oos_vol_norm
        
        indices = oos_data.index.tolist()
        i = 0
        while i + horizon < len(indices):
            entry_idx = indices[i]
            exit_idx = indices[i + horizon]
            
            alpha_val = oos_alpha.loc[entry_idx]
            
            # LONG-ONLY: Only trade if alpha > threshold (LONG signal)
            if alpha_val > threshold:
                signal = 1  # LONG
                
                entry_price = oos_data.loc[entry_idx, 'close']
                exit_price = oos_data.loc[exit_idx, 'close']
                
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                pnl_dollars = equity * (pnl_pct / 100)
                equity += pnl_dollars
                
                trades.append({
                    'symbol': symbol,
                    'entry_time': str(entry_idx),
                    'exit_time': str(exit_idx),
                    'signal': 'LONG',
                    'entry_price': round(entry_price, 4),
                    'exit_price': round(exit_price, 4),
                    'pnl_pct': round(pnl_pct, 6),
                    'pnl_dollars': round(pnl_dollars, 2),
                    'equity_after': round(equity, 2),
                    'correct': 1 if pnl_pct > 0 else 0
                })
            
            # Move to next potential trade
            i += horizon
    
    log(f"{symbol}: Complete - {len(trades):,} LONG trades, Final equity: ${equity:,.2f}")
    return pd.DataFrame(trades)


def main():
    print("=" * 70)
    print("LONG-ONLY BACKTEST")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("=" * 70)
    
    for sym, params in OPTIMAL_PARAMS.items():
        print(f"{sym}: RSI={params['rsi_period']}, Vol={params['vol_window']}, Weight={params['rsi_weight']}, Horizon={params['horizon']}")
    print("=" * 70 + "\n")
    
    all_trades = []
    
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_long_only_backtest, sym): sym for sym in OPTIMAL_PARAMS.keys()}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                trades_df = future.result()
                all_trades.append(trades_df)
            except Exception as e:
                log(f"{symbol}: ERROR - {e}")
    
    combined = pd.concat(all_trades, ignore_index=True)
    output_file = os.path.join(OUTPUT_DIR, "long_only_trades.csv")
    combined.to_csv(output_file, index=False)
    
    print("\n" + "=" * 70)
    print("LONG-ONLY RESULTS")
    print("=" * 70)
    print(f"Total trades saved: {len(combined):,}")
    
    for sym in OPTIMAL_PARAMS.keys():
        sym_df = combined[combined['symbol'] == sym]
        if len(sym_df) > 0:
            total_pnl = sym_df['pnl_dollars'].sum()
            final_eq = sym_df['equity_after'].iloc[-1]
            hr = sym_df['correct'].mean() * 100
            total_return = (final_eq - 100000) / 100000 * 100
            
            print(f"\n{sym}:")
            print(f"  Trades: {len(sym_df):,}")
            print(f"  Hit Rate: {hr:.1f}%")
            print(f"  Final Equity: ${final_eq:,.2f}")
            print(f"  Total Return: {total_return:.2f}%")
            print(f"  Avg P&L/trade: ${sym_df['pnl_dollars'].mean():.2f}")
    
    print("\n" + "=" * 70)
    print("COMPARISON: LONG-ONLY vs LONG+SHORT")
    print("=" * 70)
    
    # Load previous results for comparison
    prev_df = pd.read_csv(os.path.join(OUTPUT_DIR, "optimal_trades.csv"))
    
    for sym in OPTIMAL_PARAMS.keys():
        long_only = combined[combined['symbol'] == sym]
        both = prev_df[prev_df['symbol'] == sym]
        
        lo_return = (long_only['equity_after'].iloc[-1] - 100000) / 1000 if len(long_only) > 0 else 0
        both_return = (both['equity_after'].iloc[-1] - 100000) / 1000 if len(both) > 0 else 0
        
        print(f"\n{sym}:")
        print(f"  LONG-ONLY:   {lo_return:.2f}% return, {len(long_only):,} trades")
        print(f"  LONG+SHORT:  {both_return:.2f}% return, {len(both):,} trades")
        
        improvement = lo_return - both_return
        print(f"  Improvement: {improvement:+.2f}%")
    
    print("=" * 70)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
