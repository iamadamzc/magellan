import pandas as pd

# Load both datasets
s1 = pd.read_csv('results/options/spy_baseline_trades.csv')
s3 = pd.read_csv('results/options/spy_system3_trades.csv')

print("="*70)
print("SYSTEM 1 vs SYSTEM 3 COMPARISON")
print("="*70)

print("\nSystem 1 Baseline (RSI 58/42):")
print(f"  Trades: {len(s1)}")
print(f"  Win Rate: {(s1['pnl'] > 0).mean()*100:.1f}%")
s1_hold = (pd.to_datetime(s1['exit_date']) - pd.to_datetime(s1['entry_date'])).dt.days
print(f"  Avg Hold: {s1_hold.mean():.1f} days")
print(f"  Avg P&L%: {s1['pnl_pct'].mean():.2f}%")

print("\nSystem 3 (RSI 65/35):")
print(f"  Trades: {len(s3)}")
print(f"  Win Rate: {(s3['pnl'] > 0).mean()*100:.1f}%")
s3_hold = (pd.to_datetime(s3['exit_date']) - pd.to_datetime(s3['entry_date'])).dt.days
print(f"  Avg Hold: {s3_hold.mean():.1f} days")
print(f"  Avg P&L%: {s3['pnl_pct'].mean():.2f}%")

print("\n" + "="*70)
print("SYSTEM 3 ANALYSIS")
print("="*70)

print("\nExit Reasons:")
print(s3['reason'].value_counts())

print("\n\nPerformance by Exit Reason:")
for reason in s3['reason'].unique():
    subset = s3[s3['reason'] == reason]
    print(f"\n{reason}:")
    print(f"  Count: {len(subset)}")
    print(f"  Win Rate: {(subset['pnl'] > 0).mean()*100:.1f}%")
    print(f"  Avg P&L%: {subset['pnl_pct'].mean():.2f}%")
    print(f"  Avg Hold: {((pd.to_datetime(subset['exit_date']) - pd.to_datetime(subset['entry_date'])).dt.days).mean():.1f} days")

print("\n" + "="* 70)
print("DIAGNOSIS")
print("="*70)
print("\nProblem: System 3 performed WORSE than System 1")
print(f"  System 1: {len(s1)} trades, {(s1['pnl'] > 0).mean()*100:.1f}% win rate")
print(f"  System 3: {len(s3)} trades, {(s3['pnl'] > 0).mean()*100:.1f}% win rate")
print("\nRoot Causes:")
print("  1. Win rate DECREASED (42.9% vs 28.1%) - still below 50% target")
print("  2. Fewer but LARGER losses (avg loss -26.2% vs -15% for S1)")
print("  3. Long holding periods allow theta decay to accumulate")
print("  4. Signal changes causing premature exits at losses")
