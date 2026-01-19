"""V7 on 5-min bars - Quick Test"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import pandas as pd
import numpy as np
from src.data_cache import cache

def calc_vwap(df):
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['tpv'] = df['tp'] * df['volume']
    df['d'] = df.index.date
    df['cv'] = df.groupby('d')['volume'].cumsum()
    df['ctpv'] = df.groupby('d')['tpv'].cumsum()
    df['vwap'] = df['ctpv'] / df['cv']
    return df

def calc_atr(df):
    df['hl'] = df['high'] - df['low']
    df['hpc'] = abs(df['high'] - df['close'].shift(1))
    df['lpc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['hl', 'hpc', 'lpc']].max(axis=1)
    df['atr'] = df['tr'].rolling(14).mean()
    return df

print("Fetching 5-min data...")
df = cache.get_or_fetch_equity('RIOT', '5min', '2024-11-01', '2025-01-17')
df = calc_vwap(df)
df = calc_atr(df)

df['d'] = df.index.date
df['vol_avg'] = df['volume'].rolling(4).mean()
df['vol_spike'] = df['volume'] / df['vol_avg'].replace(0, np.inf)

# Calculate OR (first 2 bars = 10 min)
df['or_h'] = np.nan
df['or_l'] = np.nan
for date in df['d'].unique():
    date_data = df[df['d'] == date]
    if len(date_data) >= 2:
        df.loc[df['d'] == date, 'or_h'] = date_data.iloc[:2]['high'].max()
        df.loc[df['d'] == date, 'or_l'] = date_data.iloc[:2]['low'].min()

df['bo'] = (df['close'] > df['or_h']) & (df['vol_spike'] >= 1.8)

trades = []
pos, ep, sl, hp, bo_seen, moved_be = None, None, None, 0, False, False
bar_in_day = 0

for i in range(len(df)):
    if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_h']):
        continue
    
    if i == 0 or df.iloc[i]['d'] != df.iloc[i-1]['d']:
        bar_in_day = 0
    else:
        bar_in_day += 1
    
    if bar_in_day < 2:
        continue
    
    cp, cl, ch = df.iloc[i]['close'], df.iloc[i]['low'], df.iloc[i]['high']
    atr, orh, orl, vwap = df.iloc[i]['atr'], df.iloc[i]['or_h'], df.iloc[i]['or_l'], df.iloc[i]['vwap']
    
    if pos is None:
        if df.iloc[i]['bo'] and not bo_seen:
            bo_seen = True
        if bo_seen:
            pb_l, pb_h = orh - (0.15 * atr), orh + (0.15 * atr)
            in_pb = (cl <= pb_h) and (ch >= pb_l)
            if in_pb and cp > orh and cp > vwap and df.iloc[i]['vol_spike'] >= 1.8 and cp >= 3.0:
                pos, ep, sl, hp, bo_seen, moved_be = 1.0, cp, orl - (0.4 * atr), cp, False, False
    elif pos > 0:
        risk = ep - sl
        r = (cp - ep) / risk if risk > 0 else 0
        if ch > hp:
            hp = ch
        if cl <= sl:
            trades.append({'pnl': (sl - ep) / ep * 100 * pos, 'type': 'stop'})
            pos = None
            continue
        if r >= 0.5 and not moved_be:
            sl, moved_be = ep, True
        if r >= 1.3 and pos == 1.0:
            trades.append({'pnl': (risk * 1.3) / ep * 100 * 0.5, 'type': 'scale'})
            pos -= 0.5
        if moved_be:
            sl = max(sl, hp - (0.6 * atr))
        if moved_be and cp < vwap:
            trades.append({'pnl': (cp - ep) / ep * 100 * pos, 'type': 'vwap'})
            pos = None
            continue
        if (i == len(df) - 1) or (i < len(df) - 1 and df.iloc[i+1]['d'] != df.iloc[i]['d']):
            if pos > 0:
                trades.append({'pnl': (cp - ep) / ep * 100 * pos, 'type': 'eod'})
                pos = None

tdf = pd.DataFrame(trades) if trades else None

print("\n" + "="*60)
print("V7 on 5-MIN BARS - RIOT")
print("="*60)
print(f"Trades: {len(tdf) if tdf is not None else 0}")
if tdf is not None:
    tdf['net'] = tdf['pnl'] - 0.125
    print(f"Win rate: {(tdf.net > 0).sum() / len(tdf) * 100:.1f}%")
    print(f"Avg P&L: {tdf.net.mean():+.3f}%")
    print(f"Total P&L: {tdf.net.sum():+.2f}%")
    print(f"\nExit breakdown:")
    for t in tdf.type.unique():
        print(f"  {t}: {len(tdf[tdf.type == t])}")

print("\n" + "="*60)
print("COMPARISON")
print("="*60)
print("V7-1min: 50 trades | 58% win | +4.18%")
if tdf is not None:
    print(f"V7-5min: {len(tdf)} trades | {(tdf.net>0).sum()/len(tdf)*100:.1f}% win | {tdf.net.sum():+.2f}%")
