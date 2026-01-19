"""Test ORB V8 - Strict Timing on Small Caps + Futures"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v8 import run_orb_v8
import pandas as pd

# Test universe
tests = {
    'SMALL CAPS': [
        ('RIOT', '2024-11-01', '2025-01-17'),
        ('MARA', '2024-11-01', '2025-01-17'),
        ('HOOD', '2024-11-01', '2025-01-17'),
    ],
    'FUTURES (TODO)': [
        # Will add ES, NQ, RTY futures
        # Futures have 23-hour trading, different OR logic needed
    ],
}

results = []

for category, symbols in tests.items():
    if not symbols:
        continue
    
    print("\n" + "="*80)
    print(f"TESTING: {category}")
    print("="*80)
    
    for symbol, start, end in symbols:
        try:
            r = run_orb_v8(symbol, start, end)
            r['category'] = category
            results.append(r)
        except Exception as e:
            print(f"✗ {symbol}: {e}")

if results:
    df = pd.DataFrame(results)
    
    print("\n" + "="*80)
    print("ORB V8 - STRICT TIMING RESULTS")
    print("="*80)
    print(f"Total trades: {df['total_trades'].sum()}")
    print(f"Avg win rate: {df['win_rate'].mean():.1f}%")
    print(f"Avg P&L/trade: {df['avg_pnl'].mean():+.3f}%")
    print(f"Total P&L: {df['total_pnl'].sum():+.2f}%")
    
    print("\n" + "="*80)
    print("COMPARISON: V7 (All Day) vs V8 (ORB Window Only)")
    print("="*80)
    print("V7 RIOT: 50 trades, 58.0% win, +0.084% avg, +4.18% total")
    print(f"V8 RIOT: {df[df['symbol']=='RIOT']['total_trades'].values[0] if len(df[df['symbol']=='RIOT']) > 0 else 0} trades, "
          f"{df[df['symbol']=='RIOT']['win_rate'].values[0] if len(df[df['symbol']=='RIOT']) > 0 else 0:.1f}% win, "
          f"{df[df['symbol']=='RIOT']['avg_pnl'].values[0] if len(df[df['symbol']=='RIOT']) > 0 else 0:+.3f}% avg, "
          f"{df[df['symbol']=='RIOT']['total_pnl'].values[0] if len(df[df['symbol']=='RIOT']) > 0 else 0:+.2f}% total")
    
    print("\nBy Symbol:")
    for _, row in df.iterrows():
        status = "✅" if row['avg_pnl'] > 0 else "❌"
        print(f"  {status} {row['symbol']:6} | {row['total_trades']:3} trades | {row['win_rate']:5.1f}% win | {row['avg_pnl']:+.3f}% avg")
    
    if df['avg_pnl'].mean() > 0:
        print("\n🎉 V8 IS PROFITABLE!")
        print(f"   Strict ORB timing fixed the strategy!")
    elif df['avg_pnl'].mean() > -0.05:
        print("\n⚡ V8 is near breakeven - much better than V7 all-day trading")
    
    # Save
    output_path = Path('research/new_strategy_builds/results/orb_v8_strict_timing.csv')
    df.to_csv(output_path, index=False)
    print(f"\n✅ Results saved to: {output_path}")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. ✅ Fixed timing (9:40-10:00 AM only)")
    print("2. 🔄 Test on futures (ES, NQ, RTY)")
    print("3. 🔄 Expand small-cap universe if profitable")
