import pandas as pd

s4 = pd.read_csv('results/options/spy_system4_trades.csv')

print("System 4 Results:")
print(f"Total Trades: {len(s4)}")
print()

print("Exit Reasons:")
print(s4['reason'].value_counts())
print()

print("By Exit Reason:")
for reason in s4['reason'].unique():
    subset = s4[s4['reason'] == reason]
    hold_days = (pd.to_datetime(subset['exit_date']) - pd.to_datetime(subset['entry_date'])).dt.days
    print(f"\n{reason}: {len(subset)} trades")
    print(f"  Win Rate: {(subset['pnl'] > 0).mean()*100:.1f}%")
    print(f"  Avg P&L: {subset['pnl_pct'].mean():.2f}%")
    print(f"  Avg Hold: {hold_days.mean():.1f} days")

print("\n" +  "="*70)
print("CRITICAL INSIGHT")
print("="*70)
print("\nSystem 4 had SIGNAL_FLIP exits (call→put or put→call)")
print("These forced exits when trend completely reversed.")
print("\nThis means even 'hold-only' strategy can't work if we allow")
print("signal flips to close positions!")
