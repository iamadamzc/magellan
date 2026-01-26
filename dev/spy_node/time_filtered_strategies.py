"""
TIME-FILTERED SEPARATE STRATEGIES
- SPY: LONG-only, 0.25%/0.25% TP/SL, Last Hour Only (15:00+)
- QQQ: LONG-only, 20-min time-based, Last Hour Only (15:00+)

Records all trades for further analysis.
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

# DISTINCT OPTIMAL PARAMETERS
SPY_CONFIG = {
    'rsi_period': 10, 
    'vol_window': 10, 
    'rsi_weight': 0.6,
    'exit_type': 'target',  # Take profit / Stop loss
    'take_profit': 0.25,
    'stop_loss': 0.25,
    'max_hold': 60,
}

QQQ_CONFIG = {
    'rsi_period': 10, 
    'vol_window': 20, 
    'rsi_weight': 0.5,
    'exit_type': 'time',  # Time-based exit
    'horizon': 20,
}

# TIME FILTERS (from analysis)
TRADING_START_HOUR = 15  # Only trade from 3:00 PM onwards
TRADING_END_HOUR = 19    # Up to 7:00 PM (extended hours)


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


def run_spy_strategy() -> pd.DataFrame:
    """SPY: LONG-only with target-based exits and time filter."""
    symbol = 'SPY'
    config = SPY_CONFIG
    
    log(f"{symbol}: Loading data...")
    df = load_data(symbol)
    log(f"{symbol}: Loaded {len(df):,} bars")
    
    log(f"{symbol}: Calculating features...")
    df = calculate_features(df, config['rsi_period'], config['vol_window'])
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    trading_days = df['date'].unique()
    log(f"{symbol}: {len(trading_days)} trading days")
    
    rsi_weight = config['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    take_profit = config['take_profit']
    stop_loss = config['stop_loss']
    max_hold = config['max_hold']
    
    trades = []
    skipped_time = 0
    equity = 100000.0
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_data = df.loc[df['date'].isin(is_days), ['rsi', 'volume_zscore', 'close', 'hour']].copy()
        oos_data = df.loc[df['date'] == oos_day, ['rsi', 'volume_zscore', 'close', 'hour']].copy()
        
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
        
        while i < len(indices) - 1:
            entry_idx = indices[i]
            entry_hour = oos_data.loc[entry_idx, 'hour']
            
            # TIME FILTER: Only trade during last hours
            if entry_hour < TRADING_START_HOUR or entry_hour > TRADING_END_HOUR:
                skipped_time += 1
                i += 1
                continue
            
            alpha_val = oos_alpha.loc[entry_idx]
            
            if alpha_val > threshold:
                entry_price = oos_data.loc[entry_idx, 'close']
                target_price = entry_price * (1 + take_profit / 100)
                stop_price = entry_price * (1 - stop_loss / 100)
                
                exit_idx = None
                exit_price = None
                exit_reason = None
                
                for j in range(i + 1, min(i + max_hold + 1, len(indices))):
                    bar_idx = indices[j]
                    bar_price = oos_data.loc[bar_idx, 'close']
                    
                    if bar_price >= target_price:
                        exit_idx = bar_idx
                        exit_price = target_price
                        exit_reason = 'TP'
                        break
                    
                    if bar_price <= stop_price:
                        exit_idx = bar_idx
                        exit_price = stop_price
                        exit_reason = 'SL'
                        break
                
                if exit_idx is None and i + max_hold < len(indices):
                    exit_idx = indices[i + max_hold]
                    exit_price = oos_data.loc[exit_idx, 'close']
                    exit_reason = 'TIMEOUT'
                
                if exit_idx is not None:
                    pnl_pct = (exit_price - entry_price) / entry_price * 100
                    pnl_dollars = equity * (pnl_pct / 100)
                    equity += pnl_dollars
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': str(entry_idx),
                        'exit_time': str(exit_idx),
                        'entry_hour': entry_hour,
                        'signal': 'LONG',
                        'entry_price': round(entry_price, 4),
                        'exit_price': round(exit_price, 4),
                        'pnl_pct': round(pnl_pct, 6),
                        'pnl_dollars': round(pnl_dollars, 2),
                        'equity_after': round(equity, 2),
                        'correct': 1 if pnl_pct > 0 else 0,
                        'exit_reason': exit_reason
                    })
                    
                    exit_loc = indices.index(exit_idx)
                    i = exit_loc + 1
                    continue
            
            i += 1
    
    log(f"{symbol}: Complete - {len(trades):,} trades, Skipped (time): {skipped_time:,}, Final equity: ${equity:,.2f}")
    return pd.DataFrame(trades)


def run_qqq_strategy() -> pd.DataFrame:
    """QQQ: LONG-only with time-based exits and time filter."""
    symbol = 'QQQ'
    config = QQQ_CONFIG
    
    log(f"{symbol}: Loading data...")
    df = load_data(symbol)
    log(f"{symbol}: Loaded {len(df):,} bars")
    
    log(f"{symbol}: Calculating features...")
    df = calculate_features(df, config['rsi_period'], config['vol_window'])
    df['date'] = df.index.date
    df['hour'] = df.index.hour
    trading_days = df['date'].unique()
    log(f"{symbol}: {len(trading_days)} trading days")
    
    rsi_weight = config['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    horizon = config['horizon']
    
    trades = []
    skipped_time = 0
    equity = 100000.0
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        is_data = df.loc[df['date'].isin(is_days), ['rsi', 'volume_zscore', 'close', 'hour']].copy()
        oos_data = df.loc[df['date'] == oos_day, ['rsi', 'volume_zscore', 'close', 'hour']].copy()
        
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
            entry_hour = oos_data.loc[entry_idx, 'hour']
            
            # TIME FILTER: Only trade during last hours
            if entry_hour < TRADING_START_HOUR or entry_hour > TRADING_END_HOUR:
                skipped_time += 1
                i += horizon
                continue
            
            alpha_val = oos_alpha.loc[entry_idx]
            
            if alpha_val > threshold:
                entry_price = oos_data.loc[entry_idx, 'close']
                exit_price = oos_data.loc[exit_idx, 'close']
                
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                pnl_dollars = equity * (pnl_pct / 100)
                equity += pnl_dollars
                
                trades.append({
                    'symbol': symbol,
                    'entry_time': str(entry_idx),
                    'exit_time': str(exit_idx),
                    'entry_hour': entry_hour,
                    'signal': 'LONG',
                    'entry_price': round(entry_price, 4),
                    'exit_price': round(exit_price, 4),
                    'pnl_pct': round(pnl_pct, 6),
                    'pnl_dollars': round(pnl_dollars, 2),
                    'equity_after': round(equity, 2),
                    'correct': 1 if pnl_pct > 0 else 0,
                    'exit_reason': 'TIME'
                })
            
            i += horizon
    
    log(f"{symbol}: Complete - {len(trades):,} trades, Skipped (time): {skipped_time:,}, Final equity: ${equity:,.2f}")
    return pd.DataFrame(trades)


def main():
    print("=" * 80)
    print("TIME-FILTERED SEPARATE STRATEGIES")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Time Filter: Only trade hours {TRADING_START_HOUR}:00 - {TRADING_END_HOUR}:00")
    print("=" * 80)
    
    print("\nSPY Strategy:")
    print(f"  RSI={SPY_CONFIG['rsi_period']}, Vol={SPY_CONFIG['vol_window']}, Weight={SPY_CONFIG['rsi_weight']}")
    print(f"  Exit: Target-based (TP={SPY_CONFIG['take_profit']}%, SL={SPY_CONFIG['stop_loss']}%)")
    
    print("\nQQQ Strategy:")
    print(f"  RSI={QQQ_CONFIG['rsi_period']}, Vol={QQQ_CONFIG['vol_window']}, Weight={QQQ_CONFIG['rsi_weight']}")
    print(f"  Exit: Time-based ({QQQ_CONFIG['horizon']} min hold)")
    
    print("=" * 80 + "\n")
    
    all_trades = []
    
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(run_spy_strategy): 'SPY',
            executor.submit(run_qqq_strategy): 'QQQ'
        }
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                trades_df = future.result()
                all_trades.append(trades_df)
            except Exception as e:
                log(f"{symbol}: ERROR - {e}")
                import traceback
                traceback.print_exc()
    
    # Save each separately
    for df in all_trades:
        if len(df) > 0:
            symbol = df['symbol'].iloc[0]
            output_file = os.path.join(OUTPUT_DIR, f"{symbol.lower()}_time_filtered_trades.csv")
            df.to_csv(output_file, index=False)
            log(f"Saved {len(df):,} {symbol} trades to {symbol.lower()}_time_filtered_trades.csv")
    
    # Also save combined
    combined = pd.concat(all_trades, ignore_index=True)
    combined.to_csv(os.path.join(OUTPUT_DIR, "time_filtered_trades_combined.csv"), index=False)
    
    print("\n" + "=" * 80)
    print("TIME-FILTERED RESULTS")
    print("=" * 80)
    
    # Comparison baselines
    baselines = {
        'SPY': {'unfiltered': 17.38, 'trades': 17556},  # Target-based without time filter
        'QQQ': {'unfiltered': 32.49, 'trades': 21758},  # Time-based without time filter
    }
    
    for df in all_trades:
        if len(df) > 0:
            symbol = df['symbol'].iloc[0]
            final_eq = df['equity_after'].iloc[-1]
            hr = df['correct'].mean() * 100
            total_return = (final_eq - 100000) / 1000
            
            baseline = baselines[symbol]
            
            print(f"\n{symbol}:")
            print(f"  Trades: {len(df):,} (vs {baseline['trades']:,} unfiltered)")
            print(f"  Hit Rate: {hr:.1f}%")
            print(f"  Final Equity: ${final_eq:,.2f}")
            print(f"  Total Return: {total_return:.2f}% (vs {baseline['unfiltered']:.2f}% unfiltered)")
            print(f"  Change: {total_return - baseline['unfiltered']:+.2f}%")
            
            if 'exit_reason' in df.columns:
                counts = df['exit_reason'].value_counts()
                print(f"  Exit Types: {dict(counts)}")
    
    print("=" * 80)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
