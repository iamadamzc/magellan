import pandas as pd

df = pd.read_csv('results/options/earnings_straddles_trades.csv')

print("="*70)
print("EARNINGS STRADDLES - FINAL RESULTS")
print("="*70)

total_pnl = df['pnl'].sum()
total_return = (total_pnl / 100000) * 100
win_rate = (df['pnl'] > 0).mean() * 100
avg_win = df[df['pnl'] > 0]['pnl_pct'].mean()
avg_loss = df[df['pnl'] < 0]['pnl_pct'].mean()
avg_move = df['price_move_pct'].mean()

print(f"\n📊 Performance:")
print(f"  Total Return: {total_return:+.2f}%")
print(f"  Trades: {len(df)}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Avg Win: {avg_win:+.2f}%")
print(f"  Avg Loss: {avg_loss:+.2f}%")
print(f"  Avg Price Move: {avg_move:.2f}%")

print(f"\n✅ Success Criteria:")
print(f"  Return > 0%: {'✅ PASS' if total_return > 0 else '❌ FAIL'} ({total_return:+.2f}%)")
print(f"  Win Rate > 55%: {'✅ PASS' if win_rate > 55 else '❌ FAIL'} ({win_rate:.1f}%)")

print("\n" + "="*70)
print("COMPARISON TO PREMIUM SELLING")
print("="*70)

print(f"\nPremium Selling (SPY 2024-2025):")
print(f"  Return: +686%/year")
print(f"  Win Rate: 71%")
print(f"  Trades: 10-11/year")

print(f"\nEarnings Straddles (NVDA 2024-2025):")
print(f"  Return: {total_return:+.2f}% over 2 years ({total_return/2:+.2f}%/year)")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Trades: {len(df)} over 2 years ({len(df)/2:.0f}/year)")

if total_return > 100:
    print("\n✅ Earnings straddles are PROFITABLE!")
    print("✅ Can be used as complementary strategy to premium selling")
else:
    print("\n⚠️ Earnings straddles underperformed premium selling")
    print("Recommend focusing on premium selling only")

print("="*70)
