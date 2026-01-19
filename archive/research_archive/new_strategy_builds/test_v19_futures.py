"""
V19 FUTURES TEST - Last Hope for ORB
Testing top futures with first-hour-only entry window
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v19_first_hour import run_orb_v19_first_hour

# Top futures candidates
futures = [
    'NG',   # Natural Gas - extreme volatility
    'GC',   # Gold - macro trending
    'CL',   # Crude Oil - worked before (+3.20%)
    'KC',   # Coffee - worked before (+4.83%)
    'SI',   # Silver - high beta to gold
    'HG',   # Copper - trends hard
]

print("\n" + "="*80)
print("V19 FUTURES TEST - The Last Hope for ORB")
print("Testing first-hour-only on futures (Full 2024)")
print("="*80)

results = []

for symbol in futures:
    print(f"\n{'='*80}")
    print(f"Testing: {symbol}")
    print(f"{'='*80}")
    
    try:
        result = run_orb_v19_first_hour(symbol, '2024-01-01', '2024-12-31')
        
        if result and result['total_trades'] > 0:
            results.append({
                'symbol': symbol,
                'total_pnl': result['total_pnl'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate']
            })
            
            status = "🎉 WINNER" if result['total_pnl'] > 0 else "❌ LOSER"
            print(f"\n{status}: {symbol} = {result['total_pnl']:+.2f}% ({result['total_trades']} trades, {result['win_rate']:.1f}% win)")
        else:
            print(f"⚠️  {symbol}: No trades")
            results.append({
                'symbol': symbol,
                'total_pnl': 0,
                'total_trades': 0,
                'win_rate': 0
            })
    
    except Exception as e:
        print(f"❌ Error testing {symbol}: {e}")

# Summary
if results:
    import pandas as pd
    df = pd.DataFrame(results)
    df_sorted = df.sort_values('total_pnl', ascending=False)
    
    print("\n" + "="*80)
    print("FUTURES RESULTS")
    print("="*80)
    print(f"\n{'Symbol':<10} {'P&L':>12} {'Trades':>10} {'Win%':>10} {'Status':<10}")
    print("─"*80)
    
    for _, row in df_sorted.iterrows():
        status = "✅ DEPLOY" if row['total_pnl'] > 0 else "❌ REJECT"
        print(f"{row['symbol']:<10} {row['total_pnl']:>11.2f}% {row['total_trades']:>10} {row['win_rate']:>9.1f}% {status:<10}")
    
    winners = df[df['total_pnl'] > 0]
    
    if len(winners) > 0:
        print(f"\n🎉 WINNERS FOUND: {len(winners)}/{len(df)}")
        for _, winner in winners.iterrows():
            print(f"   ✅ {winner['symbol']}: {winner['total_pnl']:+.2f}%")
        print(f"\n🚀 ORB WORKS ON FUTURES!")
    else:
        print(f"\n❌ No profitable futures. ORB is dead.")
        print(f"   Next: Test 5-minute bars")

print(f"\n{'='*80}\n")
