"""V7 on 5-min bars using FMP"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import pandas as pd
import numpy as np
import requests
import os

def fetch_5min_fmp(symbol, start, end):
    """Fetch 5min bars from FMP"""
    api_key = os.getenv('FMP_API_KEY')
    url = "https://financialmodelingprep.com/stable/historical-chart/5min"
    params = {
        'symbol': symbol,
        'from': start,
        'to': end,
        'apikey': api_key
    }
    
    print(f"Fetching {symbol} 5min from FMP...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    data = response.json()
    df = pd.DataFrame(data)
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        df = df[['open', 'high', 'low', 'close', 'volume']]
        return df
    else:
        raise ValueError("No data returned from FMP")

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

# Fetch data
df = fetch_5min_fmp('RIOT', '2024-11-01', '2025-01-17')
df = calc_vwap(df)
df = calc_atr(df)

df['d'] = df.index.date
df['vol_avg'] = df['volume'].rolling(4).mean()
df['vol_spike'] = df['volume'] / df['vol_avg'].replace(0, np.inf)

# OR = first 2 bars (10 min)
df['or_h'] = np.nan
df['or_l'] = np.nan
for date in df['d'].unique():
    date_data = df[df['d'] == date]
    if len(date_data) >= 2:
        df.loc[df['d'] == date, 'or_h'] = date_data.iloc[:2]['high'].max()
        df.loc[df['d'] == date, 'or_l'] = date_data.iloc[:2]['low'].min()

df['bo'] = (df['close'] > df['or_h']) & (df['vol_spike'] >= 1.8)

# V7 logic
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
    vs = df.iloc[i]['vol_spike']
    
    if pos is None:
        # Entry: breakout + pullback
        if df.iloc[i]['bo'] and not bo_seen:
            bo_seen = True
        if bo_seen:
            pb_l = orh - (0.15 * atr)
            pb_h = orh + (0.15 * atr)
            in_pb = (cl <= pb_h) and (ch >= pb_l)
            if in_pb and cp > orh and cp > vwap and vs >= 1.8 and cp >= 3.0:
                pos = 1.0
                ep = cp
                sl = orl - (0.4 * atr)
                hp = cp
                bo_seen = False
                moved_be = False
    
    elif pos > 0:
        risk = ep - sl
        r = (cp - ep) / risk if risk > 0 else 0
        if ch > hp:
            hp = ch
        
        # Stop
        if cl <= sl:
            trades.append({'pnl': (sl - ep) / ep * 100 * pos, 'type': 'stop'})
            pos = None
            continue
        
        # Breakeven @ 0.5R
        if r >= 0.5 and not moved_be:
            sl = ep
            moved_be = True
        
        # Scale @ 1.3R
        if r >= 1.3 and pos == 1.0:
            trades.append({'pnl': (risk * 1.3) / ep * 100 * 0.5, 'type': 'scale'})
            pos -= 0.5
        
        # Trail
        if moved_be:
            sl = max(sl, hp - (0.6 * atr))
        
        # VWAP loss
        if moved_be and cp < vwap:
            trades.append({'pnl': (cp - ep) / ep * 100 * pos, 'type': 'vwap'})
            pos = None
            continue
        
        # EOD
        if (i == len(df) - 1) or (i < len(df) - 1 and df.iloc[i+1]['d'] != df.iloc[i]['d']):
            if pos > 0:
                trades.append({'pnl': (cp - ep) / ep * 100 * pos, 'type': 'eod'})
                pos = None

tdf = pd.DataFrame(trades) if trades else None

print("\n" + "="*70)
print("V7 ON 5-MIN BARS - RIOT")
print("="*70)

if tdf is not None and len(tdf) > 0:
    tdf['net'] = tdf['pnl'] - 0.125
    print(f"Trades: {len(tdf)}")
    print(f"Win rate: {(tdf.net > 0).sum() / len(tdf) * 100:.1f}%")
    print(f"Avg P&L: {tdf.net.mean():+.3f}%")
    print(f"Total P&L: {tdf.net.sum():+.2f}%")
    
    print(f"\nExit breakdown:")
    for t in tdf.type.unique():
        count = len(tdf[tdf.type == t])
        avg = tdf[tdf.type == t].net.mean()
        print(f"  {t}: {count} ({avg:+.3f}%)")
    
    print("\n" + "="*70)
    print("COMPARISON TO 1-MIN")
    print("="*70)
    print(f"V7-1min: 50 trades | 58.0% win | +0.084% avg | +4.18% total")
    print(f"V7-5min: {len(tdf)} trades | {(tdf.net>0).sum()/len(tdf)*100:.1f}% win | {tdf.net.mean():+.3f}% avg | {tdf.net.sum():+.2f}% total")
    
    print("\n" + "="*70)
    print("VERDICT")
    print("="*70)
    
    if tdf.net.sum() > 4.18:
        print("✅ 5-MIN BETTER - Use this!")
    elif tdf.net.sum() > 0 and len(tdf) < 25:
        print("⚠️ 5-MIN CLEANER - Fewer trades, still profitable")
    elif len(tdf) < 25:
        print("⚠️ TRADE COUNT GOOD - But need to tune for profitability")
    else:
        print("❌ STICK WITH 1-MIN")
else:
    print("❌ NO TRADES on 5-min bars")
