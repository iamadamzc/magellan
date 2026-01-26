"""
FAST Take Profit / Stop Loss Backtest
- PARALLEL execution (SPY and QQQ simultaneously)
- SYMMETRIC targets (TP=SL to avoid asymmetric losses)
- FAST combinations: 4 combos per symbol = 8 total (~7-10 minutes)
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

OPTIMAL_PARAMS = {
    'SPY': {'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.6},
    'QQQ': {'rsi_period': 10, 'vol_window': 20, 'rsi_weight': 0.5},
}

# SYMMETRIC targets only (TP = SL)
TARGET_COMBOS = [
    (0.1, 0.1),
    (0.15, 0.15),
    (0.2, 0.2),
    (0.25, 0.25),
]
MAX_HOLD = 60


def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    line = f"{ts} - {msg}\n"
    with open(os.path.join(OUTPUT_DIR, "target_progress.txt"), "a") as f:
        f.write(line)
        f.flush()
    print(line.strip())


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


def run_symbol_target_tests(symbol: str) -> list:
    """Run all target combinations for one symbol."""
    log(f"{symbol}: Starting")
    
    params = OPTIMAL_PARAMS[symbol]
    rsi_weight = params['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    
    df = load_data(symbol)
    log(f"{symbol}: Loaded {len(df):,} bars")
    
    df = calculate_features(df, params['rsi_period'], params['vol_window'])
    df['date'] = df.index.date
    trading_days = df['date'].unique()
    
    results = []
    
    for take_profit, stop_loss in TARGET_COMBOS:
        log(f"{symbol}: Testing TP={take_profit}% SL={stop_loss}%")
        
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
                
                if alpha_val > threshold:
                    entry_price = oos_data.loc[entry_idx, 'close']
                    target_price = entry_price * (1 + take_profit / 100)
                    stop_price = entry_price * (1 - stop_loss / 100)
                    
                    exit_idx = None
                    exit_price = None
                    exit_reason = None
                    
                    for j in range(i + 1, min(i + MAX_HOLD + 1, len(indices))):
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
                        
                        exit_loc = indices.index(exit_idx)
                        i = exit_loc + 1
                        continue
                
                i += 1
        
        if trades:
            trades_df = pd.DataFrame(trades)
            result = {
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
            }
        else:
            result = {
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
            }
        
        results.append(result)
        log(f"{symbol} TP={take_profit}% SL={stop_loss}%: Return={result['total_return']:.2f}%, HR={result['hit_rate']:.1f}%")
    
    log(f"{symbol}: Complete")
    return results


def main():
    with open(os.path.join(OUTPUT_DIR, "target_progress.txt"), "w") as f:
        f.write(f"=== STARTED: {datetime.now()} ===\n\n")
    
    print("=" * 70)
    print("FAST TAKE PROFIT / STOP LOSS BACKTEST")
    print(f"Period: {START_DATE} to {END_DATE}")
    print("Symbols: SPY, QQQ (PARALLEL)")
    print(f"Combinations: {len(TARGET_COMBOS)} per symbol = {len(TARGET_COMBOS)*2} total")
    print("=" * 70 + "\n")
    
    all_results = []
    
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(run_symbol_target_tests, sym): sym for sym in OPTIMAL_PARAMS.keys()}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                log(f"{symbol}: ERROR - {e}")
    
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(OUTPUT_DIR, "target_results_fast.csv"), index=False)
    
    print("\n" + "=" * 70)
    print("BEST CONFIGURATIONS")
    print("=" * 70)
    
    time_based = {'SPY': 9.39, 'QQQ': 32.49}
    
    for symbol in OPTIMAL_PARAMS.keys():
        sym_df = results_df[results_df['symbol'] == symbol]
        best = sym_df.loc[sym_df['total_return'].idxmax()]
        
        print(f"\n{symbol}:")
        print(f"  BEST: TP={best['take_profit']}% SL={best['stop_loss']}%")
        print(f"  Return: {best['total_return']:.2f}% (vs {time_based[symbol]:.2f}% time-based)")
        print(f"  Hit Rate: {best['hit_rate']:.1f}%")
        print(f"  Trades: {int(best['total_trades'])}")
        print(f"  TP: {int(best['tp_exits'])} | SL: {int(best['sl_exits'])} | Timeout: {int(best['timeout_exits'])}")
    
    print("=" * 70)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
