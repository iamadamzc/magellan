"""Test ORB V10 - Simplified Entry, Sophisticated Exits"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v10 import run_orb_v10

print("="*80)
print("ORB V10 - VALIDATION TEST")
print("="*80)
print("\nTesting on RIOT (Nov 2024 - Jan 2025)")
print("Expected: 15-25 trades, 52-58% win rate, +0.08-0.15% avg P&L")
print("="*80)

result = run_orb_v10('RIOT', '2024-11-01', '2025-01-17')

print(f"\n{'Metric':<20} | {'Value':>12} | {'Target':>12} | {'Status':>10}")
print("-" * 80)

metrics = [
    ('Total Trades', result['total_trades'], '15-25', 15 <= result['total_trades'] <= 25),
    ('Win Rate', f"{result['win_rate']:.1f}%", '52-58%', 52 <= result['win_rate'] <= 58),
    ('Avg P&L', f"{result['avg_pnl']:+.3f}%", '+0.08-0.15%', 0.08 <= result['avg_pnl'] <= 0.15),
    ('Sharpe', f"{result['sharpe']:.2f}", '0.8-1.2', 0.8 <= result['sharpe'] <= 1.2),
]

for metric_name, value, target, passed in metrics:
    status = "✅ PASS" if passed else "⚠️ REVIEW"
    print(f"{metric_name:<20} | {str(value):>12} | {target:>12} | {status:>10}")

print("\n" + "="*80)
print("EXIT BREAKDOWN")
print("="*80)

if result['total_trades'] > 0:
    for exit_type, count in result['exit_breakdown'].items():
        pct = count / result['total_trades'] * 100
        print(f"{exit_type:<15}: {count:>3} ({pct:>5.1f}%)")
    
    print("\n" + "="*80)
    print("DETAILED METRICS")
    print("="*80)
    print(f"Avg Win:  {result['avg_win']:+.3f}%")
    print(f"Avg Loss: {result['avg_loss']:+.3f}%")
    print(f"Avg MAE:  {result['avg_mae']:.2f}R")
    print(f"Avg MFE:  {result['avg_mfe']:.2f}R")
    
    print("\n" + "="*80)
    print("SAMPLE TRADES (First 10)")
    print("="*80)
    print(result['trades_df'][['entry_time', 'pnl_pct', 'r', 'type', 'mae', 'mfe', 'time_in_trade']].head(10).to_string(index=False))
    
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    
    if result['total_trades'] == 0:
        print("❌ FAILED: Still 0 trades. Need to relax filters further.")
    elif result['total_trades'] < 10:
        print("⚠️ WARNING: Too few trades. Consider relaxing filters.")
    elif result['avg_pnl'] < 0:
        print("⚠️ WARNING: Negative expectancy. Review exit logic.")
    elif result['avg_pnl'] > 0 and result['sharpe'] > 0.5:
        print("✅ SUCCESS: Positive expectancy achieved!")
        print(f"   Avg P&L: {result['avg_pnl']:+.3f}%")
        print(f"   Sharpe: {result['sharpe']:.2f}")
        print("\n   Next steps:")
        print("   1. Test on full momentum universe (9 symbols)")
        print("   2. Run walk-forward analysis")
        print("   3. Generate deployment configs")
    else:
        print("⚠️ MARGINAL: Positive but weak. Consider further tuning.")
else:
    print("❌ FAILED: 0 trades. Filters still too restrictive.")
    print("\nDiagnostic steps:")
    print("1. Check if data is available for RIOT in Nov-Jan period")
    print("2. Review entry conditions in orb_v10.py")
    print("3. Consider relaxing volume threshold further (1.5x → 1.3x)")
