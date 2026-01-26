"""
Leverage Analysis for Gold Bull Market
Shows what's achievable with different leverage levels
"""

# Gold bull market: Jan 2024 to now
gold_start = 2073.4
gold_end = 4341.1
gold_return = (gold_end / gold_start - 1) * 100

print("=" * 50)
print("GOLD LEVERAGED RETURN ANALYSIS")
print("=" * 50)
print(f"Jan 2024 price: ${gold_start:.2f}")
print(f"Current price:  ${gold_end:.2f}")
print(f"Unleveraged:    {gold_return:.1f}%")
print("=" * 50)

# Leveraged returns (Jan 2024 to now = ~390 trading days)
trading_days = 390
capital = 20000

print(f"\nStarting Capital: ${capital:,}")
print(f"Trading Days: {trading_days}")
print("-" * 50)
print(f"{'Leverage':<10} {'Return':<12} {'Total P&L':<15} {'Daily P&L'}")
print("-" * 50)

for lev in [1, 2, 3, 5, 8, 10]:
    lev_return = gold_return * lev
    final = capital * (1 + lev_return / 100)
    total_pnl = final - capital
    daily_pnl = total_pnl / trading_days
    marker = " ✅" if daily_pnl >= 200 else ""
    print(
        f"{lev}x{'':<8} {lev_return:>6.1f}%      ${total_pnl:>10,.0f}      ${daily_pnl:>6.2f}{marker}"
    )

print("-" * 50)
print("\n✅ = Meets $200/day target")
print("\nNote: This is idealized buy-and-hold with perfect timing.")
print("Real trading will have drawdowns and timing risks.")
