"""
TIMEFRAME PIVOT: 5-MINUTE VALIDATION
- Hypothesis: Resampling to 5-min bars will capture larger moves, increasing Avg Trade > Spread.
- Logic: Same RSI+VolZ strategy, but on 5-min aggregated data.
- Slippage: 5bps
- Spread Cost Analysis Included.
"""

import os
import pandas as pd
import numpy as np
import multiprocessing

CACHE_DIR = r"a:\1\Magellan\data\cache\equities"
START_DATE = "2022-01-01"
END_DATE = "2026-01-24"

# 5 Basis Points Slippage
SLIPPAGE_BPS = 5
SLIPPAGE_FACTOR = SLIPPAGE_BPS / 10000.0

# Adjusted Config for 5-Min (RSI period length means 5x time now 10*5 = 50mins)
# We keep parameters same to test 'Scalability' or we could adjust?
# Let's keep parameters same first. RSI(10) on 5min = 50 minutes of lookback vs 10 mins.
CONFIG = {
    'rsi_period': 10, 
    'vol_window': 20, 
    'rsi_weight': 0.6,
    'exit_type': 'target',
    'take_profit': 0.40,  # Increased TP for higher timeframe volatility
    'stop_loss': 0.40,    # Increased SL
    'max_hold': 12,       # 12 bars * 5 min = 60 mins (Same duration)
}

TRADING_START_HOUR = 15
TRADING_END_HOUR = 19

def load_and_resample(symbol: str) -> pd.DataFrame:
    filepath = os.path.join(CACHE_DIR, f"{symbol}_1min_20220101_20260124.parquet")
    df = pd.read_parquet(filepath, columns=['timestamp', 'close', 'volume'])
    if 'timestamp' in df.columns: df.set_index('timestamp', inplace=True)
    df = df.loc[START_DATE:END_DATE]
    
    # RESAMPLE TO 5-MIN
    # Logic: Close is last close, Volume is sum
    df_5m = df.resample('5min').agg({
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    return df_5m

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

def run_5min_test(symbol: str):
    print(f"Running 5-Minute Validation for {symbol}...")
    df = load_and_resample(symbol)
    df = calculate_features(df, CONFIG['rsi_period'], CONFIG['vol_window'])
    
    df['date_only'] = df.index.date
    df['hour'] = df.index.hour
    
    rsi_weight = CONFIG['rsi_weight']
    vol_weight = 1.0 - rsi_weight
    
    trades = []
    
    # Simple rolling alpha calc
    # To simulate 'In Sample' median, we can just use a rolling median of the signal itself
    # for simplicity in this pivot test.
    # Alpha Signal
    rsi_min, rsi_max = df['rsi'].rolling(500).min(), df['rsi'].rolling(500).max()
    vol_min, vol_max = df['volume_zscore'].rolling(500).min(), df['volume_zscore'].rolling(500).max()
    
    # Normalize
    rsi_norm = (df['rsi'] - rsi_min) / (rsi_max - rsi_min)
    vol_norm = (df['volume_zscore'] - vol_min) / (vol_max - vol_min)
    alpha = rsi_weight * rsi_norm + vol_weight * vol_norm
    threshold = alpha.rolling(500).median()
    
    indices = df.index.tolist()
    i = 500 # Warmup
    
    while i < len(indices) - 1:
        idx = indices[i]
        
        # Time Filter
        if df.loc[idx, 'hour'] < TRADING_START_HOUR or df.loc[idx, 'hour'] > TRADING_END_HOUR:
            i += 1; continue
            
        # Signal
        if alpha.iloc[i] > threshold.iloc[i]:
            entry_price = df.loc[idx, 'close']
            entry_w_slip = entry_price * (1 + SLIPPAGE_FACTOR)
            
            # EXIT LOGIC
            tp = entry_w_slip * (1 + CONFIG['take_profit']/100)
            sl = entry_w_slip * (1 - CONFIG['stop_loss']/100)
            
            exit_price = None
            jump_idx = None
            exit_reason = None
            
            end_scan = min(i + CONFIG['max_hold'] + 1, len(indices))
            for j in range(i+1, end_scan):
                p = df.loc[indices[j], 'close']
                if p >= tp: exit_price = tp; jump_idx = j; exit_reason = 'TP'; break
                if p <= sl: exit_price = sl; jump_idx = j; exit_reason = 'SL'; break
            
            if not exit_price:
                if i + CONFIG['max_hold'] < len(indices):
                    exit_price = df.loc[indices[i+CONFIG['max_hold']], 'close']
                    jump_idx = i+CONFIG['max_hold']; exit_reason = 'TIMEOUT'
                else:
                    exit_price = df.loc[indices[-1], 'close']
                    jump_idx = len(indices)-1; exit_reason = 'EOD'
            
            exit_w_slip = exit_price * (1 - SLIPPAGE_FACTOR)
            
            # Calc
            gross_pnl = 100000 * ((exit_price - entry_price)/entry_price)
            net_pnl = 100000 * ((exit_w_slip - entry_w_slip)/entry_w_slip)
            
            # Spread Cost (Shares * $0.02)
            shares = 100000 / entry_price
            spread_cost = shares * 0.02 
            
            trades.append({
                'net_pnl': net_pnl,
                'gross_pnl': gross_pnl,
                'spread_cost': spread_cost
            })
            
            i = jump_idx + 1
        else:
            i += 1
            
    return pd.DataFrame(trades)

def main():
    print("="*60)
    print("5-MINUTE TIMEFRAME PIVOT TEST")
    print(f"Goal: Increase Avg Trade Size > Spread Cost")
    print(f"Slippage: {SLIPPAGE_BPS}bps | Spread: $0.02/share")
    print("="*60)
    
    for sym in ['SPY', 'QQQ']:
        df = run_5min_test(sym)
        if df.empty:
            print(f"{sym}: No trades.")
            continue
            
        avg_gross = df['gross_pnl'].mean()
        avg_net = df['net_pnl'].mean() - df['spread_cost'].mean() # Apply spread logic to net
        win_rate = (df['net_pnl'] > df['spread_cost']).mean() * 100
        
        print(f"\n{sym} (5-MIN Results):")
        print(f"  Trades:           {len(df):,}")
        print(f"  Avg GROSS:        ${avg_gross:.2f}")
        print(f"  Avg SPREAD Cost:  ${df['spread_cost'].mean():.2f}")
        print(f"  Avg NET (Final):  ${avg_net:.2f}")
        print(f"  Win Rate:         {win_rate:.1f}%")
        
        if avg_net > 0:
            print("  RESULT: VIABLE CANDIDATE ✅")
        else:
            print("  RESULT: STILL INSOLVENT ❌")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
