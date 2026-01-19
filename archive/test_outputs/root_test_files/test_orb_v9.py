"""Test ORB V9 - OR=5 vs OR=10 Comparison"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from research.new_strategy_builds.strategies.orb_v9 import run_orb_v9

print("="*80)
print("ORB V9 - OR=5 vs OR=10 COMPARISON (RIOT)")
print("="*80)

result_or5 = run_orb_v9('RIOT', '2024-11-01', '2025-01-17', or_minutes=5)
result_or10 = run_orb_v9('RIOT', '2024-11-01', '2025-01-17', or_minutes=10)

print("\n" + "="*80)
print("RESULTS")
print("="*80)

metrics = [
    ('Total Trades', 'total_trades', ''),
    ('Win Rate', 'win_rate', '%'),
    ('Avg P&L', 'avg_pnl', '%'),
    ('Avg Win', 'avg_win', '%'),
    ('% Reached 0.25R', 'pct_reached_025r', '%'),
    ('% Reached 0.50R', 'pct_reached_050r', '%'),
    ('Avg MAE', 'avg_mae', 'R'),
    ('Avg MFE', 'avg_mfe', 'R'),
]

print(f"\n{'Metric':<20} | {'OR=5':>12} | {'OR=10':>12} | {'Winner':>10}")
print("-" * 80)

for metric_name, key, unit in metrics:
    val5 = result_or5[key]
    val10 = result_or10[key]
    
    # Determine winner
    if key in ['total_trades', 'win_rate', 'avg_pnl', 'avg_win', 'pct_reached_025r', 'pct_reached_050r', 'avg_mfe']:
        winner = "OR=5" if val5 > val10 else "OR=10" if val10 > val5 else "TIE"
    elif key == 'avg_mae':
        winner = "OR=10" if val10 > val5 else "OR=5" if val5 > val10 else "TIE"
    else:
        winner = ""
    
    if unit == '%':
        print(f"{metric_name:<20} | {val5:>11.1f}% | {val10:>11.1f}% | {winner:>10}")
    elif unit == 'R':
        print(f"{metric_name:<20} | {val5:>11.2f}R | {val10:>11.2f}R | {winner:>10}")
    else:
        print(f"{metric_name:<20} | {val5:>12.0f} | {val10:>12.0f} | {winner:>10}")

print("\n" + "="*80)
print("VERDICT")
print("="*80)

if result_or5['avg_mfe'] > result_or10['avg_mfe'] and result_or5['avg_mae'] <= result_or10['avg_mae']:
    print("✅ OR=5 WINS: Increases early MFE without blowing up MAE")
    print("   Use 5-minute opening range")
elif result_or10['avg_mfe'] > result_or5['avg_mfe'] or result_or5['avg_mae'] > result_or10['avg_mae'] * 1.2:
    print("✅ OR=10 WINS: OR=5 becomes a fakeout festival")
    print("   Stick to 10-minute opening range")
else:
    print("⚡ CLOSE CALL: Marginal difference")
    print(f"   OR=5: {result_or5['avg_mfe']:.2f}R MFE, {result_or5['avg_mae']:.2f}R MAE")
    print(f"   OR=10: {result_or10['avg_mfe']:.2f}R MFE, {result_or10['avg_mae']:.2f}R MAE")
