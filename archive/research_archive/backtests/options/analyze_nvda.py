import pandas as pd

nvda = pd.read_csv('results/options/nvda_system4_trades.csv')

print("="*70)
print("NVDA SYSTEM 4 DEEP DIVE")
print("="*70)

print(f"\nTotal Trades: {len(nvda)}")
print(f"Wins: {(nvda['pnl'] > 0).sum()}")
print(f"Losses: {(nvda['pnl'] < 0).sum()}")

print("\nExit Reasons:")
print(nvda['reason'].value_counts())

print("\n" + "="*70)
print("BY EXIT REASON")
print("="*70)

for reason in nvda['reason'].unique():
    subset = nvda[nvda['reason'] == reason]
    hold_days = (pd.to_datetime(subset['exit_date']) - pd.to_datetime(subset['entry_date'])).dt.days
    print(f"\n{reason}:")
    print(f"  Count: {len(subset)}")
    print(f"  Win Rate: {(subset['pnl'] > 0).mean()*100:.1f}%")
    print(f"  Avg P&L: {subset['pnl_pct'].mean():+.2f}%")
    print(f"  Avg Hold: {hold_days.mean():.1f} days")
    
    if len(subset) <= 5:
        print("  Individual trades:")
        for idx, trade in subset.iterrows():
            days = (pd.to_datetime(trade['exit_date']) - pd.to_datetime(trade['entry_date'])).days
            print(f"    {trade['entry_date'][:10]}: {trade['type'].upper()} ${trade['pnl_pct']:+.1f}% ({days}d)")

print("\n" + "="*70) 
print("THE SMOKING GUN")
print("="*70)

print("\nROLL trades (winners):")
roll_trades = nvda[nvda['reason'] == 'ROLL']
for idx, trade in roll_trades.iterrows():
    days = (pd.to_datetime(trade['exit_date']) - pd.to_datetime(trade['entry_date'])).days
    print(f"  {trade['entry_date'][:10]}: {trade['type'].upper()} ${trade['pnl_pct']:+.1f}% ({days}d)")

print("\nSIGNAL_FLIP trades (losers):")
flip_trades = nvda[nvda['reason'] == 'SIGNAL_FLIP']
for idx, trade in flip_trades.iterrows():
    days = (pd.to_datetime(trade['exit_date']) - pd.to_datetime(trade['entry_date'])).days
    print(f"  {trade['entry_date'][:10]}: {trade['type'].upper()} ${trade['pnl_pct']:+.1f}% ({days}d)")
