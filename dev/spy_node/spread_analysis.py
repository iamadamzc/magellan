"""
SPREAD COST ANALYSIS
- Quantifies the impact of the "Bid-Ask Spread" on the strategy's edge.
- Assumption: SPY/QQQ have a tight $0.01 spread.
- We assume 'Market Orders' which cross the spread (Pay Ask, Sell Bid).
- Cost = (Shares * $0.01) on Entry + (Shares * $0.01) on Exit = Shares * $0.02.
"""

import os
import pandas as pd
import numpy as np
import multiprocessing

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
START_DATE = "2022-01-01"
END_DATE = "2026-01-24"

# CONFIG PARTIALS (Matching the "Profitable" Specs)
SPY_CONFIG = {'rsi_period': 10, 'vol_window': 10, 'rsi_weight': 0.6, 'exit_type': 'target', 'take_profit': 0.25, 'stop_loss': 0.25, 'max_hold': 60}
QQQ_CONFIG = {'rsi_period': 10, 'vol_window': 20, 'rsi_weight': 0.5, 'exit_type': 'time', 'horizon': 20}
TRADING_START_HOUR = 15
TRADING_END_HOUR = 19

def load_data(symbol: str) -> pd.DataFrame:
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath, columns=['timestamp', 'close', 'volume'])
    if 'timestamp' in df.columns: df.set_index('timestamp', inplace=True)
    return df.loc[START_DATE:END_DATE]

def calculate_features(df, rsi_period, vol_window):
    df = df.copy()
    delta = df['close'].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    df['rsi'] = 100 - (100 / (1 + rs))
    df.loc[avg_loss == 0, 'rsi'] = 100.0; df.loc[avg_gain == 0, 'rsi'] = 0.0
    vol_mean = df['volume'].rolling(window=vol_window).mean()
    vol_std = df['volume'].rolling(window=vol_window).std()
    df['volume_zscore'] = (df['volume'] - vol_mean) / vol_std.replace(0, np.inf)
    df.loc[vol_std == 0, 'volume_zscore'] = 0.0
    return df.iloc[max(rsi_period, vol_window):]

def analyze_symbol(symbol, config):
    print(f"Analyzing {symbol}...")
    df = load_data(symbol)
    df = calculate_features(df, config['rsi_period'], config['vol_window'])
    df['date_only'] = df.index.date
    df['hour'] = df.index.hour
    
    rsi_weight = config['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    trading_days = df['date_only'].unique()
    in_sample_days = 3
    
    trades = []
    
    for day_idx in range(in_sample_days, len(trading_days)):
        oos_day = trading_days[day_idx]
        is_days = trading_days[day_idx-in_sample_days:day_idx]
        
        day_mask = df['date_only'] == oos_day
        oos_data = df.loc[day_mask].copy()
        
        # In-Sample Threshold stats
        is_data = df.loc[df['date_only'].isin(is_days)]
        if len(is_data) < 100 or len(oos_data) < 50: continue
            
        rsi_min, rsi_max = is_data['rsi'].min(), is_data['rsi'].max()
        vol_min, vol_max = is_data['volume_zscore'].min(), is_data['volume_zscore'].max()
        
        is_alpha = rsi_weight * ((is_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)) + \
                   vol_weight * ((is_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6))
        threshold = is_alpha.median()
        
        oos_alpha = rsi_weight * ((oos_data['rsi'] - rsi_min) / max(rsi_max - rsi_min, 1e-6)) + \
                    vol_weight * ((oos_data['volume_zscore'] - vol_min) / max(vol_max - vol_min, 1e-6))
        
        indices = oos_data.index.tolist()
        i = 0
        while i < len(indices) - 1:
            idx = indices[i]
            if oos_data.loc[idx, 'hour'] < TRADING_START_HOUR or oos_data.loc[idx, 'hour'] > TRADING_END_HOUR:
                i += 1; continue
                
            if oos_alpha.loc[idx] > threshold:
                entry_price = oos_data.loc[idx, 'close']
                exit_price = None
                jump_idx = None
                
                # Check Exit Logic
                if config['exit_type'] == 'target':
                    tp = entry_price * (1 + config['take_profit']/100)
                    sl = entry_price * (1 - config['stop_loss']/100)
                    end_scan = min(i + config['max_hold'] + 1, len(indices))
                    for j in range(i+1, end_scan):
                        p = oos_data.loc[indices[j], 'close']
                        if p >= tp: exit_price, jump_idx = tp, j; break
                        if p <= sl: exit_price, jump_idx = sl, j; break
                    if not exit_price:
                         if i + config['max_hold'] < len(indices):
                             exit_price, jump_idx = oos_data.loc[indices[i+config['max_hold']], 'close'], i+config['max_hold']
                         else:
                             exit_price, jump_idx = oos_data.loc[indices[-1], 'close'], len(indices)-1
                else: 
                     horizon = config['horizon']
                     if i + horizon < len(indices):
                         exit_price, jump_idx = oos_data.loc[indices[i+horizon], 'close'], i+horizon
                     else:
                         exit_price, jump_idx = oos_data.loc[indices[-1], 'close'], len(indices)-1
                
                # METRICS CALCULATION
                gross_pnl_pct = (exit_price - entry_price) / entry_price
                gross_dollar_pnl = 100000 * gross_pnl_pct
                
                # SPREAD COST CALC
                shares = 100000 / entry_price
                # 1 cent spread paid on Buy (Ask) and Sell (Bid) = $0.02 total per share
                # Note: If exit is TP/SL limit, maybe only pay half? 
                # Conservative: Pay spread on Entry (Market), Pay spread on Exit (Market or Stop). 
                # Limit limit exit might earn spread? Let's assume standard "Market Taker" for backtest reality.
                # Actually, Stop Loss is a market order. Take Profit is a limit. 
                # Let's assess "1 Cent Cost" per share as a Minimum baseline friction.
                spread_cost = shares * 0.02 
                
                trades.append({
                    'price': entry_price,
                    'gross_pnl': gross_dollar_pnl,
                    'spread_cost': spread_cost,
                    'net_pnl': gross_dollar_pnl - spread_cost
                })
                i = jump_idx + 1
            else:
                i += 1
                
    return pd.DataFrame(trades)

def main():
    print("="*80)
    print("SPREAD COST ANALYSIS (The 'Penny' Test)")
    print("Assuming strictly $0.01 Bid-Ask spread cost per side ($0.02/share round trip)")
    print("Capital: $100,000 per trade")
    print("="*80)
    
    for sym, cfg in [('SPY', SPY_CONFIG), ('QQQ', QQQ_CONFIG)]:
        df = analyze_symbol(sym, cfg)
        if df.empty:
            print(f"{sym}: No trades generated.")
            continue
            
        avg_gross = df['gross_pnl'].mean()
        avg_cost = df['spread_cost'].mean()
        avg_net = df['net_pnl'].mean()
        
        win_rate_gross = (df['gross_pnl'] > 0).mean() * 100
        win_rate_net = (df['net_pnl'] > 0).mean() * 100
        
        print(f"\n{sym} RESULTS ({len(df):,} trades):")
        print(f"  Avg Entry Price:    ${df['price'].mean():.2f}")
        print(f"  Avg Shares/Trade:   {int(100000 / df['price'].mean())}")
        print("-" * 40)
        print(f"  Avg GROSS Profit:   ${avg_gross:6.2f}  (Win Rate: {win_rate_gross:.1f}%)")
        print(f"  Avg SPREAD Cost:    ${avg_cost:6.2f}  (Impact of 1 cent spread)")
        print(f"  Avg NET Profit:     ${avg_net:6.2f}  (Win Rate: {win_rate_net:.1f}%)")
        print("-" * 40)
        
        ratio = avg_cost / avg_gross if avg_gross != 0 else 0
        print(f"  CRITICAL: Spread costs consume {ratio*100:.1f}% of your edge.")
        
        if avg_net < 0:
            print(f"  CONCLUSION: FAILED. The strategy cannot pay for the bid-ask spread.")
        else:
            print(f"  CONCLUSION: PASSED. Edge survives the spread.")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
