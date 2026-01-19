"""V12 - LET WINNERS RUN (Remove VWAP loss, wider trail)"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd()))
import pandas as pd; import numpy as np; from src.data_cache import cache

def calc_vwap(df):
    df['tp']=(df['high']+df['low']+df['close'])/3; df['tpv']=df['tp']*df['volume']; df['d']=df.index.date
    df['cv']=df.groupby('d')['volume'].cumsum(); df['ctpv']=df.groupby('d')['tpv'].cumsum()
    df['vwap']=df['ctpv']/df['cv']; return df

def calc_atr(df):
    df['hl']=df['high']-df['low']; df['hpc']=abs(df['high']-df['close'].shift(1))
    df['lpc']=abs(df['low']-df['close'].shift(1)); df['tr']=df[['hl','hpc','lpc']].max(axis=1)
    df['atr']=df['tr'].rolling(14).mean(); return df

def run_v12(sym):
    df=cache.get_or_fetch_equity(sym,'1min','2024-11-01','2025-01-17')
    df=calc_vwap(df); df=calc_atr(df); df['d']=df.index.date; df['h']=df.index.hour
    df['m']=df.index.minute; df['mso']=(df['h']-9)*60+(df['m']-30)
    df['va']=df['volume'].rolling(20).mean(); df['vs']=df['volume']/df['va'].replace(0,np.inf)
    df['oh']=np.nan; df['ol']=np.nan
    for date in df['d'].unique():
        dm=df['d']==date; od=df[dm&(df['mso']<=10)]
        if len(od)>0: df.loc[dm,'oh']=od['high'].max(); df.loc[dm,'ol']=od['low'].min()
    df['bo']=(df['close']>df['oh'])&(df['vs']>=1.8)
    trades=[]; pos=None; ep=None; sl=None; hp=0; bs=False; mbe=False
    for i in range(len(df)):
        if pd.isna(df.iloc[i]['atr']) or pd.isna(df.iloc[i]['oh']): continue
        cp,cl,ch=df.iloc[i]['close'],df.iloc[i]['low'],df.iloc[i]['high']
        atr,orh,orl,vw=df.iloc[i]['atr'],df.iloc[i]['oh'],df.iloc[i]['ol'],df.iloc[i]['vwap']
        mso=df.iloc[i]['mso']
        if mso<=10: continue
        if pos is None:
            if df.iloc[i]['bo'] and not bs: bs=True
            if bs:
                pbl=orh-(0.15*atr); pbh=orh+(0.15*atr); in_pb=(cl<=pbh)and(ch>=pbl)
                if in_pb and cp>orh and cp>vw and df.iloc[i]['vs']>=1.8 and cp>=3.0:
                    pos=1.0; ep=cp; sl=orl-(0.4*atr); hp=cp; bs=False; mbe=False
        elif pos>0:
            risk=ep-sl; r=(cp-ep)/risk if risk>0 else 0
            if ch>hp: hp=ch
            if cl<=sl: trades.append({'pnl':(sl-ep)/ep*100*pos,'t':'stop'}); pos=None; continue
            if r>=0.5 and not mbe: sl=ep; mbe=True
            if r>=0.7 and pos==1.0: trades.append({'pnl':(risk*0.7)/ep*100*0.5,'t':'scale'}); pos-=0.5
            # CHANGE 1: Wider trail (1.0 ATR instead of 0.6)
            if mbe: sl=max(sl,hp-(1.0*atr))
            # CHANGE 2: NO VWAP LOSS - Removed!
            # EOD only
            if df.iloc[i]['h']>=15 and df.iloc[i]['m']>=55 and pos>0:
                trades.append({'pnl':(cp-ep)/ep*100*pos,'t':'eod'}); pos=None
    if not trades: return None
    tdf=pd.DataFrame(trades); tdf['net']=tdf['pnl']-0.125
    return {'sym':sym,'tr':len(tdf),'win':(tdf.net>0).sum()/len(tdf)*100,'tot':tdf.net.sum()}

print("="*70); print("V12 - LET WINNERS RUN (No VWAP loss, 1.0 ATR trail)"); print("="*70)
syms=['RIOT','PLTR','NVDA','COIN','SOFI','MARA']; results=[]
for s in syms:
    try:
        r=run_v12(s)
        if r: results.append(r); print(f"{s}: {r['tr']} trades | {r['win']:.1f}% win | {r['tot']:+.2f}%")
    except Exception as e: print(f"{s}: ERROR")

if results:
    rdf=pd.DataFrame(results); print(f"\n{'='*70}"); print("RESULTS"); print("="*70)
    print(f"Total: {rdf.tot.sum():+.2f}% | Profitable: {len(rdf[rdf.tot>0])}/{len(rdf)}")
    print(f"Avg win rate: {rdf.win.mean():.1f}%")
