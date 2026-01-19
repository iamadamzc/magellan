"""
SEQUENTIAL TWEAKS TEST
V23: Baseline (Trail 1.0, Stop 0.4, Vol 1.8x)
V24: Wider trail (1.2 ATR)
V25: V24 + Tighter stop (0.35 ATR)
V26: V25 + Higher volume (2.0x)
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v23_all_day import run_orb_v23_all_day
from research.new_strategy_builds.strategies.orb_tweaked import run_orb_tweaked

commodities = [
    ('ES', 'S&P 500'),
    ('HG', 'Copper'),
    ('NG', 'Natural Gas'),
    ('KC', 'Coffee'),
    ('SB', 'Sugar'),
]

print("\n" + "="*80)
print("SEQUENTIAL TWEAKS - Pushing ES/HG Over the Hump")
print("="*80)

all_results = []

for symbol, name in commodities:
    print(f"\n{'='*80}")
    print(f"{symbol} ({name})")
    print(f"{'='*80}")
    
    # V23 Baseline
    print("\nV23 (Baseline):")
    v23 = run_orb_v23_all_day(symbol, '2024-01-01', '2024-12-31')
    
    # V24: Wider trail
    print("\nV24 (Wider Trail 1.2 ATR):")
    v24 = run_orb_tweaked(symbol, '2024-01-01', '2024-12-31', 
                          trail_atr=1.2, stop_atr=0.4, vol_mult=1.8, version="V24")
    
    # V25: V24 + Tighter stop
    print("\nV25 (V24 + Tighter Stop 0.35 ATR):")
    v25 = run_orb_tweaked(symbol, '2024-01-01', '2024-12-31',
                          trail_atr=1.2, stop_atr=0.35, vol_mult=1.8, version="V25")
    
    # V26: V25 + Higher volume
    print("\nV26 (V25 + Higher Volume 2.0x):")
    v26 = run_orb_tweaked(symbol, '2024-01-01', '2024-12-31',
                          trail_atr=1.2, stop_atr=0.35, vol_mult=2.0, version="V26")
    
    all_results.append({
        'symbol': symbol,
        'name': name,
        'v23_pnl': v23['total_pnl'],
        'v23_trades': v23['total_trades'],
        'v24_pnl': v24['total_pnl'],
        'v24_trades': v24['total_trades'],
        'v25_pnl': v25['total_pnl'],
        'v25_trades': v25['total_trades'],
        'v26_pnl': v26['total_pnl'],
        'v26_trades': v26['total_trades'],
    })
    
    print(f"\n📊 PROGRESSION:")
    print(f"V23: {v23['total_pnl']:+.2f}% ({v23['total_trades']} trades)")
    print(f"V24: {v24['total_pnl']:+.2f}% ({v24['total_trades']} trades) [{v24['total_pnl']-v23['total_pnl']:+.2f}%]")
    print(f"V25: {v25['total_pnl']:+.2f}% ({v25['total_trades']} trades) [{v25['total_pnl']-v24['total_pnl']:+.2f}%]")
    print(f"V26: {v26['total_pnl']:+.2f}% ({v26['total_trades']} trades) [{v26['total_pnl']-v25['total_pnl']:+.2f}%]")

# Summary
import pandas as pd
df = pd.DataFrame(all_results)

print(f"\n{'='*80}")
print("FINAL COMPARISON - ALL VERSIONS")
print(f"{'='*80}")
print(f"\n{'Symbol':<8} {'V23':>10} {'V24':>10} {'V25':>10} {'V26':>10} {'Best':>6}")
print("─"*80)

for _, row in df.iterrows():
    versions = [row['v23_pnl'], row['v24_pnl'], row['v25_pnl'], row['v26_pnl']]
    best_idx = versions.index(max(versions))
    best_ver = ['V23', 'V24', 'V25', 'V26'][best_idx]
    
    print(f"{row['symbol']:<8} {row['v23_pnl']:>9.2f}% {row['v24_pnl']:>9.2f}% {row['v25_pnl']:>9.2f}% {row['v26_pnl']:>9.2f}% {best_ver:>6}")

print(f"\n{'='*80}")
print("KEY QUESTIONS")
print(f"{'='*80}")

# Did ES/HG become profitable?
es_row = df[df['symbol'] == 'ES'].iloc[0]
hg_row = df[df['symbol'] == 'HG'].iloc[0]

print(f"\n1. Did ES become profitable?")
if max(es_row['v24_pnl'], es_row['v25_pnl'], es_row['v26_pnl']) > 0:
    best_es = max(es_row['v24_pnl'], es_row['v25_pnl'], es_row['v26_pnl'])
    best_ver = ['V24', 'V25', 'V26'][[es_row['v24_pnl'], es_row['v25_pnl'], es_row['v26_pnl']].index(best_es)]
    print(f"   ✅ YES! {best_ver}: {best_es:+.2f}%")
else:
    print(f"   ❌ No, still losing")

print(f"\n2. Did HG become profitable?")
if max(hg_row['v24_pnl'], hg_row['v25_pnl'], hg_row['v26_pnl']) > 0:
    best_hg = max(hg_row['v24_pnl'], hg_row['v25_pnl'], hg_row['v26_pnl'])
    best_ver = ['V24', 'V25', 'V26'][[hg_row['v24_pnl'], hg_row['v25_pnl'], hg_row['v26_pnl']].index(best_hg)]
    print(f"   ✅ YES! {best_ver}: {best_hg:+.2f}%")
else:
    print(f"   ❌ No, still losing")

print(f"\n3. Did tweaks hurt the winners (NG, KC, SB)?")
winners = df[df['symbol'].isin(['NG', 'KC', 'SB'])]
for _, w in winners.iterrows():
    best_new = max(w['v24_pnl'], w['v25_pnl'], w['v26_pnl'])
    if best_new > w['v23_pnl']:
        print(f"   📈 {w['symbol']}: Improved! {w['v23_pnl']:+.2f}% → {best_new:+.2f}%")
    elif best_new < w['v23_pnl'] * 0.9:  # More than 10% worse
        print(f"   📉 {w['symbol']}: Hurt significantly! {w['v23_pnl']:+.2f}% → {best_new:+.2f}%")
    else:
        print(f"   = {w['symbol']}: Roughly same ({w['v23_pnl']:+.2f}% → {best_new:+.2f}%)")

print(f"\n{'='*80}\n")
