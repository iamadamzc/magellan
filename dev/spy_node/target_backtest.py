"""
Take Profit / Stop Loss Backtest
- LONG-only on SPY and QQQ
- Tests various take profit / stop loss combinations
- Uses 1-minute bar data to simulate intra-bar exits
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

# SPY and QQQ only (removed IWM)
OPTIMAL_PARAMS = {
    'SPY': {'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.6},
    'QQQ': {'rsi_period': 10, 'vol_window': 20, 'rsi_weight': 0.5},
}

# Target/Stop combinations to test
TAKE_PROFITS = [0.1, 0.15, 0.2, 0.25, 0.3]  # % profit target
STOP_LOSSES = [0.1, 0.15, 0.2, 0.25, 0.3]   # % stop loss
MAX_HOLD = 60  # Max hold time in minutes (timeout)


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


def run_target_backtest(symbol: str, take_profit: float, stop_loss: float) -> dict:
    """Run backtest with take profit and stop loss."""
    params = OPTIMAL_PARAMS[symbol]
    rsi_weight = params['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    
    df = load_data(symbol)
    df = calculate_features(df, params['rsi_period'], params['vol_window'])
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    
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
        
        while i < len(indices) - 1:
            entry_idx = indices[i]
            alpha_val = oos_alpha.loc[entry_idx]
            
            # LONG-only
            if alpha_val > threshold:
                entry_price = oos_data.loc[entry_idx, 'close']
                target_price = entry_price * (1 + take_profit / 100)
                stop_price = entry_price * (1 - stop_loss / 100)
                
                # Simulate bar-by-bar to find exit
                exit_idx = None
                exit_price = None
                exit_reason = None
                
                for j in range(i + 1, min(i + MAX_HOLD + 1, len(indices))):
                    bar_idx = indices[j]
                    bar_price = oos_data.loc[bar_idx, 'close']
                    
                    # Check take profit
                    if bar_price >= target_price:
                        exit_idx = bar_idx
                        exit_price = target_price  # Assume filled at target
                        exit_reason = 'TP'
                        break
                    
                    # Check stop loss
                    if bar_price <= stop_price:
                        exit_idx = bar_idx
                        exit_price = stop_price  # Assume filled at stop
                        exit_reason = 'SL'
                        break
                
                # Timeout - exit at max hold
                if exit_idx is None and i + MAX_HOLD < len(indices):
                    exit_idx = indices[i + MAX_HOLD]
                    exit_price = oos_data.loc[exit_idx, 'close']
                    exit_reason = 'TIMEOUT'
                
                if exit_idx is not None:
                    pnl_pct = (exit_price - entry_price) / entry_price * 100
                    pnl_dollars = equity * (pnl_pct / 100)
                    equity += pnl_dollars
                    
                    trades.append({
                        'pnl_pct': pnl_pct,
                        'pnl_dollars': pnl_dollars,
                        'exit_reason': exit_reason,
                        'correct': 1 if pnl_pct > 0 else 0
                    })
                    
                    # Move to bar after exit
                    exit_loc = indices.index(exit_idx)
                    i = exit_loc + 1
                    continue
            
            i += 1
    
    if trades:
        trades_df = pd.DataFrame(trades)
        return {
            'symbol': symbol,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'total_trades': len(trades_df),
            'hit_rate': trades_df['correct'].mean() * 100,
            'total_return': (equity - 100000) / 1000,
            'final_equity': equity,
            'tp_exits': len(trades_df[trades_df['exit_reason'] == 'TP']),
            'sl_exits': len(trades_df[trades_df['exit_reason'] == 'SL']),
            'timeout_exits': len(trades_df[trades_df['exit_reason'] == 'TIMEOUT']),
            'avg_pnl': trades_df['pnl_dollars'].mean()
        }
    else:
        return {
            'symbol': symbol,
            'take_profit': take_profit,
            'stop_loss': stop_loss,
            'total_trades': 0,
            'hit_rate': 0,
            'total_return': 0,
            'final_equity': 100000,
            'tp_exits': 0,
            'sl_exits': 0,
            'timeout_exits': 0,
            'avg_pnl': 0
        }


def main():
    print("=" * 80)
    print("TAKE PROFIT / STOP LOSS BACKTEST")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("Symbols: SPY, QQQ (LONG-only)")
    print(f"Max Hold: {MAX_HOLD} minutes")
    print("=" * 80)
    
    all_results = []
    
    for symbol in OPTIMAL_PARAMS.keys():
        log(f"{symbol}: Loading data...")
        
        for tp in TAKE_PROFITS:
            for sl in STOP_LOSSES:
                result = run_target_backtest(symbol, tp, sl)
                all_results.append(result)
                log(f"{symbol} TP={tp}% SL={sl}%: Return={result['total_return']:.2f}%, HR={result['hit_rate']:.1f}%, Trades={result['total_trades']}")
    
    # Save results
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(OUTPUT_DIR, "target_backtest_results.csv"), index=False)
    
    # Find best for each symbol
    print("\n" + "=" * 80)
    print("BEST CONFIGURATIONS BY SYMBOL")
    print("=" * 80)
    
    for symbol in OPTIMAL_PARAMS.keys():
        sym_df = results_df[results_df['symbol'] == symbol]
        best = sym_df.loc[sym_df['total_return'].idxmax()]
        
        print(f"\n{symbol} BEST:")
        print(f"  Take Profit: {best['take_profit']}%")
        print(f"  Stop Loss: {best['stop_loss']}%")
        print(f"  Total Return: {best['total_return']:.2f}%")
        print(f"  Hit Rate: {best['hit_rate']:.1f}%")
        print(f"  Trades: {int(best['total_trades'])}")
        print(f"  TP Exits: {int(best['tp_exits'])} | SL Exits: {int(best['sl_exits'])} | Timeouts: {int(best['timeout_exits'])}")
    
    # Compare best target-based vs time-based
    print("\n" + "=" * 80)
    print("COMPARISON: TARGET-BASED vs TIME-BASED (20min hold)")
    print("=" * 80)
    
    time_based = {'SPY': 9.39, 'QQQ': 32.49}  # From long-only backtest
    
    for symbol in OPTIMAL_PARAMS.keys():
        sym_df = results_df[results_df['symbol'] == symbol]
        best = sym_df.loc[sym_df['total_return'].idxmax()]
        
        improvement = best['total_return'] - time_based[symbol]
        print(f"\n{symbol}:")
        print(f"  Time-based (20min): {time_based[symbol]:.2f}%")
        print(f"  Target-based (TP={best['take_profit']}%, SL={best['stop_loss']}%): {best['total_return']:.2f}%")
        print(f"  {'✅ Improvement' if improvement > 0 else '❌ Worse'}: {improvement:+.2f}%")
    
    print("=" * 80)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
