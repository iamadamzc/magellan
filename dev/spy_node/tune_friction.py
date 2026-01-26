"""
FRICTION TUNING: THRESHOLD OPTIMIZATION
- Goal: Find a signal threshold where Avg Trade > Friction Cost
- Slippage: 5bps ($50/side approx) -> We need Avg Trade >> $100
- Sweeping Alpha Percentiles: 50% to 99%
"""

import os
import pandas as pd
import numpy as np
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
START_DATE = "2022-01-01"
END_DATE = "2026-01-24"

# 5 Basis Points Slippage (0.05%)
SLIPPAGE_BPS = 5
SLIPPAGE_FACTOR = SLIPPAGE_BPS / 10000.0

# Base Configs
SPY_CONFIG = {
    'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.6,
    'exit_type': 'target', 'take_profit': 0.25, 'stop_loss': 0.25, 'max_hold': 60
}

QQQ_CONFIG = {
    'rsi_period': 10, 'vol_window': 20, 'rsi_weight': 0.5,
    'exit_type': 'time', 'horizon': 20
}

TRADING_START_HOUR = 15
TRADING_END_HOUR = 19

def load_data(symbol: str) -> pd.DataFrame:
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath, columns=['timestamp', 'close', 'volume'])
    if 'timestamp' in df.columns:
        df.set_index('timestamp', inplace=True)
    return df.loc[START_DATE:END_DATE]

def calculate_features(df: pd.DataFrame, rsi_period: int, vol_window: int) -> pd.DataFrame:
    df = df.copy()
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

def run_threshold_test(symbol: str, config: dict, percentile: float):
    df = load_data(symbol)
    df = calculate_features(df, config['rsi_period'], config['vol_window'])
    
    df['date_only'] = df.index.date
    df['hour'] = df.index.hour
    trading_days = df['date_only'].unique()
    
    rsi_weight = config['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    
    equity = 100000.0
    trades = []
    
    in_sample_days = 3
    
    for day_idx in range(in_sample_days, len(trading_days)):
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        day_mask = df['date_only'] == oos_day
        oos_data = df.loc[day_mask].copy()
        
        # Optimization: Don't re-slice IS data every time if percentile is static, 
        # but here we are inside the loop. 
        # To be fast, we just need the stats.
        
        is_mask = df['date_only'].isin(is_days)
        is_data = df.loc[is_mask]
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue

        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        
        # Calculate Threshold
        is_rsi_norm = (is_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)
        is_vol_norm = (is_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6)
        is_alpha = rsi_weight * is_rsi_norm + vol_weight * is_vol_norm
        
        # KEY CHANGE: Using variable percentile
        threshold = is_alpha.quantile(percentile)
        
        oos_rsi_norm = (oos_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)
        oos_vol_norm = (oos_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6)
        oos_alpha = rsi_weight * oos_rsi_norm + vol_weight * oos_vol_norm
        
        indices = oos_data.index.tolist()
        i = 0
        
        while i < len(indices) - 1:
            idx = indices[i]
            hour = oos_data.loc[idx, 'hour']
            
            if hour < TRADING_START_HOUR or hour > TRADING_END_HOUR:
                i += 1
                continue
                
            if oos_alpha.loc[idx] > threshold:
                entry_price = oos_data.loc[idx, 'close']
                entry_w_slip = entry_price * (1 + SLIPPAGE_FACTOR)
                
                exit_price = None
                exit_reason = None
                jump_idx = None
                
                if config['exit_type'] == 'target':
                    tp = entry_w_slip * (1 + config['take_profit']/100)
                    sl = entry_w_slip * (1 - config['stop_loss']/100)
                    end_scan = min(i + config['max_hold'] + 1, len(indices))
                    
                    for j in range(i+1, end_scan):
                        p = oos_data.loc[indices[j], 'close']
                        if p >= tp:
                            exit_price = tp # Limit fill assumption
                            exit_reason = 'TP'
                            jump_idx = j
                            break
                        if p <= sl:
                            exit_price = sl # Stop fill assumption
                            exit_reason = 'SL'
                            jump_idx = j
                            break
                    
                    if not exit_price:
                        if i + config['max_hold'] < len(indices):
                            exit_price = oos_data.loc[indices[i+config['max_hold']], 'close']
                            exit_reason = 'TIMEOUT'
                            jump_idx = i + config['max_hold']
                        else:
                            exit_price = oos_data.loc[indices[-1], 'close']
                            exit_reason = 'EOD'
                            jump_idx = len(indices) - 1
                            
                else: # Time based
                    horizon = config['horizon']
                    if i + horizon < len(indices):
                        exit_price = oos_data.loc[indices[i+horizon], 'close']
                        exit_reason = 'TIME'
                        jump_idx = i + horizon
                    else:
                        exit_price = oos_data.loc[indices[-1], 'close']
                        exit_reason = 'EOD'
                        jump_idx = len(indices) - 1
                
                exit_w_slip = exit_price * (1 - SLIPPAGE_FACTOR)
                
                pnl = (exit_w_slip - entry_w_slip) / entry_w_slip * 100
                dollars = 100000 * (pnl/100) # Fixed capital for expectancy calc
                trades.append(dollars)
                
                # Move loop
                i = jump_idx + 1
            else:
                i += 1
                
    if not trades:
        return {'percentile': percentile, 'trades': 0, 'acc_return': 0, 'avg_trade': 0, 'win_rate': 0}
        
    trades = np.array(trades)
    return {
        'percentile': percentile,
        'trades': len(trades),
        'acc_return': np.sum(trades),
        'avg_trade': np.mean(trades),
        'win_rate': np.mean(trades > 0) * 100
    }

def main():
    print("="*70)
    print(f"HIGH FRICTION FILTER TUNING (Slippage: {SLIPPAGE_BPS}bps)")
    print("Optimization Target: Maximize Net Expectancy")
    print("="*70)
    
    percentiles = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98, 0.99]
    
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {}
        for p in percentiles:
            futures[executor.submit(run_threshold_test, 'SPY', SPY_CONFIG, p)] = ('SPY', p)
            futures[executor.submit(run_threshold_test, 'QQQ', QQQ_CONFIG, p)] = ('QQQ', p)
            
        results = {'SPY': [], 'QQQ': []}
        
        for future in as_completed(futures):
            sym, p = futures[future]
            try:
                res = future.result()
                results[sym].append(res)
                print(f"Finished {sym} @ {int(p*100)}%")
            except Exception as e:
                print(f"Error {sym} {p}: {e}")
                import traceback
                traceback.print_exc()

    # Report
    for sym in ['SPY', 'QQQ']:
        print(f"\n{sym} RESULTS (Sorted by Avg Trade Net):")
        print(f"{'Pct':<5} | {'Trades':<6} | {'WinRate':<7} | {'Net Return':<12} | {'Avg Net Trade':<13}")
        print("-" * 55)
        
        # Sort by Avg Trade
        sorted_res = sorted(results[sym], key=lambda x: x['avg_trade'], reverse=True)
        
        for r in sorted_res:
            print(f"{r['percentile']:.2f}  | {r['trades']:<6} | {r['win_rate']:>5.1f}%  | ${r['acc_return']:>10,.0f} | ${r['avg_trade']:>10.2f}")
            
if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
