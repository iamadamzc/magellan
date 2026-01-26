import pandas as pd

df = pd.read_csv('results/options/premium_selling_trades.csv')

print("="*70)
print("PREMIUM SELLING TRADE ANALYSIS")
print("="*70)

print(f"\nTotal Trades: {len(df)}")
print(f"Winners: {(df['pnl'] > 0).sum()}")
print(f"Losers: {(df['pnl'] < 0).sum()}")

print("\nExit Reasons:")
print(df['reason'].value_counts())

print("\n" + "="*70)
print("BY EXIT REASON")
print("="*70)

for reason in df['reason'].unique():
    subset = df[df['reason'] == reason]
    print(f"\n{reason}: {len(subset)} trades")
    print(f"  Win Rate: {(subset['pnl'] > 0).mean()*100:.1f}%")
    print(f"  Avg P&L: {subset['pnl_pct'].mean():+.2f}%")
    print(f"  Avg Hold: {subset['hold_days'].mean():.1f} days")

print("\n" + "="*70)
print("ALL TRADES")
print("="*70)

for idx, trade in df.iterrows():
    print(f"\n{trade['entry_date'][:10]}: SELL {trade['type'].upper()}")
    print(f"  P&L: {trade['pnl_pct']:+.1f}%")
    print(f"  Exit: {trade['reason']} ({trade['hold_days']} days)")
    print(f"  Premium: ${trade['premium_collected']:.0f} → Buyback: ${trade['buyback_cost']:.0f}")
