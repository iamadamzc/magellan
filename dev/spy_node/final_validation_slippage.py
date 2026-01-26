"""
FINAL VALIDATION: SLIPPAGE COMPLIANCE TEST
- SPY & QQQ with 5bps Slippage per side (10bps round trip)
- Period: 2022-01-01 to 2026-01-24

Derived from time_filtered_strategies.py
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import multiprocessing

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
OUTPUT_DIR = r"a:\1\Magellan\test\spy_node"

START_DATE = "2022-01-01"
END_DATE = "2026-01-24"

# 5 Basis Points Slippage (0.05%)
SLIPPAGE_BPS = 5
SLIPPAGE_FACTOR = SLIPPAGE_BPS / 10000.0

SPY_CONFIG = {
    'rsi_period': 10, 
    'vol_window': 10, 
    'rsi_weight': 0.6,
    'exit_type': 'target',
    'take_profit': 0.25,
    'stop_loss': 0.25,
    'max_hold': 60,
}

QQQ_CONFIG = {
    'rsi_period': 10, 
    'vol_window': 20, 
    'rsi_weight': 0.5,
    'exit_type': 'time',
    'horizon': 20,
}

TRADING_START_HOUR = 15
TRADING_END_HOUR = 19

def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"{ts} - {msg}")

def load_data(symbol: str) -> pd.DataFrame:
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    # Optimize loading - schema has 'timestamp' not 'date'
    df = pd.read_parquet(filepath, columns=['timestamp', 'close', 'volume'])
    # Ensure datetime index
    if 'timestamp' in df.columns:
        df.set_index('timestamp', inplace=True)
    return df.loc[START_DATE:END_DATE]

def calculate_features(df: pd.DataFrame, rsi_period: int, vol_window: int) -> pd.DataFrame:
    df = df.copy()
    
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
    
    return df.iloc[max(rsi_period, vol_window):]

def run_strategy_logic(symbol: str, config: dict):
    """Run strategy logic for a single symbol with slippage."""
    log(f"{symbol}: Starting 5bps SLIPPAGE Test...")
    df = load_data(symbol)
    df = calculate_features(df, config['rsi_period'], config['vol_window'])
    
    df['date_only'] = df.index.date
    df['hour'] = df.index.hour
    trading_days = df['date_only'].unique()
    
    rsi_weight = config['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    
    trades = []
    equity = 100000.0
    in_sample_days = 3
    
    # Pre-calculate alpha for speed
    # We can't vectorise everything due to moving windows, but we can do the alpha calculation
    # actually the original code did daily loops. We'll stick to that for correctness with 'in-sample' logic.
    
    for day_idx in range(in_sample_days, len(trading_days)):
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        oos_day = trading_days[day_idx]
        
        # Use boolean indexing for speed
        day_mask = df['date_only'] == oos_day
        oos_data = df.loc[day_mask].copy()
        
        # We need IS stats. 
        # For speed: We can just use the global min/max of the previous 3 days window if we carefully slice
        # But to match original exactly, we follow the pattern
        is_mask = df['date_only'].isin(is_days)
        is_data = df.loc[is_mask]
        
        if len(is_data) < 100 or len(oos_data) < 50:
            continue

        # Feature normalization
        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        
        # Alpha Calculation
        # Normalized = (Value - Min) / (Max - Min)
        oos_rsi_norm = (oos_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)
        oos_vol_norm = (oos_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6)
        oos_alpha = rsi_weight * oos_rsi_norm + vol_weight * oos_vol_norm
        
        # Calculate Median Threshold from IS data
        is_rsi_norm = (is_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)
        is_vol_norm = (is_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6)
        threshold = (rsi_weight * is_rsi_norm + vol_weight * is_vol_norm).median()
        
        indices = oos_data.index.tolist()
        i = 0
        
        while i < len(indices) - 1:
            entry_idx = indices[i]
            entry_hour = oos_data.loc[entry_idx, 'hour']
            
            # 1. TIME FILTER
            if entry_hour < TRADING_START_HOUR or entry_hour > TRADING_END_HOUR:
                i += 1
                continue
            
            # 2. SIGNAL
            if oos_alpha.loc[entry_idx] > threshold:
                raw_entry_price = oos_data.loc[entry_idx, 'close']
                
                # APPLY SLIPPAGE ON ENTRY
                entry_price_with_slip = raw_entry_price * (1 + SLIPPAGE_FACTOR)
                
                exit_idx = None
                exit_price_raw = None
                exit_reason = None
                
                # SPY LOGIC (Targets)
                if config['exit_type'] == 'target':
                    # Targets depend on the FILLED price
                    target_price = entry_price_with_slip * (1 + config['take_profit'] / 100)
                    stop_price = entry_price_with_slip * (1 - config['stop_loss'] / 100)
                    max_hold = config['max_hold']
                    
                    search_end = min(i + max_hold + 1, len(indices))
                    for j in range(i + 1, search_end):
                        bar_idx = indices[j]
                        bar_price = oos_data.loc[bar_idx, 'close']
                        
                        if bar_price >= target_price:
                            exit_idx = bar_idx
                            exit_price_raw = bar_price # Realistically, we exit at limit, but lets use bar_price to be generous or target? 
                            # If it gaped up, we get better fill. If it just touched, we get target.
                            # Standard conservative backtest: use target price if touched.
                            exit_price_raw = target_price 
                            exit_reason = 'TP'
                            break
                        
                        if bar_price <= stop_price:
                            exit_idx = bar_idx
                            exit_price_raw = stop_price # Assuming stop filled at trigger
                            exit_reason = 'SL'
                            break
                    
                    # Timeout
                    if exit_idx is None:
                        if i + max_hold < len(indices):
                            exit_idx = indices[i + max_hold]
                            exit_price_raw = oos_data.loc[exit_idx, 'close']
                            exit_reason = 'TIMEOUT'
                        else:
                            # End of day close
                            exit_idx = indices[-1]
                            exit_price_raw = oos_data.loc[exit_idx, 'close']
                            exit_reason = 'EOD'
                            
                # QQQ LOGIC (Time-based)
                else:
                    horizon = config['horizon']
                    if i + horizon < len(indices):
                        exit_idx = indices[i + horizon]
                        exit_price_raw = oos_data.loc[exit_idx, 'close']
                        exit_reason = 'TIME'
                    else:
                        exit_idx = indices[-1]
                        exit_price_raw = oos_data.loc[exit_idx, 'close']
                        exit_reason = 'EOD'

                # APPLY SLIPPAGE ON EXIT
                # We pay slippage on the sell order
                exit_price_with_slip = exit_price_raw * (1 - SLIPPAGE_FACTOR)
                
                # Metrics
                pnl_pct = (exit_price_with_slip - entry_price_with_slip) / entry_price_with_slip * 100
                pnl_dollars = equity * (pnl_pct / 100)
                equity += pnl_dollars
                
                trades.append({
                    'symbol': symbol,
                    'pnl_dollars': pnl_dollars,
                    'equity': equity,
                    'exit_reason': exit_reason
                })
                
                # Advance index
                if exit_idx in indices:
                    i = indices.index(exit_idx) + 1
                else:
                    i += 1
            else:
                i += 1
                
    return pd.DataFrame(trades)

def main():
    print(f"Running Validation with {SLIPPAGE_BPS} bps Slippage per trade...")
    
    spy_df = run_strategy_logic('SPY', SPY_CONFIG)
    qqq_df = run_strategy_logic('QQQ', QQQ_CONFIG)
    
    print("\n" + "="*60)
    print(f"RESULTS (Slippage: {SLIPPAGE_BPS} bps / {SLIPPAGE_BPS/100:.2f}%)")
    print("="*60)
    
    for name, df in [('SPY', spy_df), ('QQQ', qqq_df)]:
        if len(df) == 0:
            print(f"{name}: No trades")
            continue
            
        final_eq = df['equity'].iloc[-1]
        total_ret = (final_eq - 100000) / 100000 * 100
        avg_trade = df['pnl_dollars'].mean()
        hit_rate = (df['pnl_dollars'] > 0).mean() * 100
        
        print(f"{name}:")
        print(f"  Final Equity: ${final_eq:,.2f}")
        print(f"  Total Return: {total_return_fmt(total_ret)}")
        print(f"  Hit Rate:     {hit_rate:.1f}%")
        print(f"  Avg Trade:    ${avg_trade:.2f}")
        print(f"  Trades:       {len(df):,}")
        print("-" * 30)

def total_return_fmt(val):
    return f"+{val:.2f}%" if val > 0 else f"{val:.2f}%"

if __name__ == "__main__":
    main()
