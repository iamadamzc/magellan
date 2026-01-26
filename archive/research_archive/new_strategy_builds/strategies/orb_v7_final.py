"""ORB V7-FINAL - V7 with closer targets"""
import pandas as pd, numpy as np; from pathlib import Path; import sys
project_root = Path(__file__).resolve().parent.parent.parent; sys.path.insert(0, str(project_root))
from dotenv import load_dotenv; load_dotenv(); from src.data_cache import cache

def calculate_vwap(df):
    df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3; df['tp_volume'] = df['typical_price'] * df['volume']; df['date'] = df.index.date
    df['cumulative_tp_volume'] = df.groupby('date')['tp_volume'].cumsum(); df['cumulative_volume'] = df.groupby('date')['volume'].cumsum()
    df['vwap'] = df['cumulative_tp_volume'] / df['cumulative_volume']; return df

def calculate_atr(df, period=14):
    df['h_l'] = df['high'] - df['low']; df['h_pc'] = abs(df['high'] - df['close'].shift(1)); df['l_pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1); df['atr'] = df['tr'].rolling(period).mean(); return df

def run_orb(symbol, start, end):
    df = cache.get_or_fetch_equity(symbol, '1min', start, end); df = calculate_vwap(df); df = calculate_atr(df)
    df['date'] = df.index.date; df['hour'], df['minute'] = df.index.hour, df.index.minute
    df['minutes_since_open'] = (df['hour'] - 9) * 60 + (df['minute'] - 30); df['avg_volume_20'] = df['volume'].rolling(20).mean()
    df['volume_spike'] = df['volume'] / df['avg_volume_20'].replace(0, np.inf)
    or_mask = df['minutes_since_open'] <= 10; df['or_high'] = np.nan; df['or_low'] = np.nan
    for date in df['date'].unique():
        date_mask = df['date'] == date; or_data = df[date_mask & or_mask]
        if len(or_data) > 0: df.loc[date_mask, 'or_high'] = or_data['high'].max(); df.loc[date_mask, 'or_low'] = or_data['low'].min()
    df['breakout'] = (df['close'] > df['or_high']) & (df['volume_spike'] >= 1.5)
    trades, position, entry_price, stop_loss, highest_price, breakout_seen, moved_to_be = [], None, None, None, 0, False, False
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['or_high']): continue
        cp, cl, ch, ca, orh, orl, vwap, mso = df.iloc[i]['close'], df.iloc[i]['low'], df.iloc[i]['high'], df.iloc[i]['atr'], df.iloc[i]['or_high'], df.iloc[i]['or_low'], df.iloc[i]['vwap'], df.iloc[i]['minutes_since_open']
        if mso <= 10: continue
        if position is None:
            if df.iloc[i]['breakout'] and not breakout_seen: breakout_seen = True
            if breakout_seen:
                pbl, pbh = orh - (0.15 * ca), orh + (0.15 * ca); in_pb = (cl <= pbh) and (ch >= pbl)
                if in_pb and cp > orh and cp > vwap and df.iloc[i]['volume_spike'] >= 1.5 and cp >= 3.0:
                    position, entry_price, stop_loss, highest_price, breakout_seen, moved_to_be = 1.0, cp, orl - (0.4 * ca), cp, False, False
        elif position > 0:
            risk = entry_price - stop_loss; cr = (cp - entry_price) / risk if risk > 0 else 0
            if ch > highest_price: highest_price = ch
            if cl <= stop_loss: trades.append({'symbol': symbol, 'pnl_pct': (stop_loss - entry_price) / entry_price * 100 * position, 'type': 'stop'}); position = None; continue
            if cr >= 0.5 and not moved_to_be: stop_loss, moved_to_be = entry_price, True
            if cr >= 0.7 and position == 1.0: trades.append({'symbol': symbol, 'pnl_pct': (risk * 0.7) / entry_price * 100 * 0.5, 'type': 'scale_07r'}); position -= 0.5
            if moved_to_be: stop_loss = max(stop_loss, highest_price - (0.6 * ca))
            if moved_to_be and cp < vwap: trades.append({'symbol': symbol, 'pnl_pct': (cp - entry_price) / entry_price * 100 * position, 'type': 'vwap_loss'}); position = None; continue
            if df.iloc[i]['hour'] >= 15 and df.iloc[i]['minute'] >= 55 and position > 0: trades.append({'symbol': symbol, 'pnl_pct': (cp - entry_price) / entry_price * 100 * position, 'type': 'eod'}); position = None
    return trades
