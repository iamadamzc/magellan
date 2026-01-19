"""
Friction Reality Check - Are We Overestimating?

Current assumption: 4.1 bps per round-trip trade
Breakdown:
- Slippage: 2.0 bps (67ms latency)
- Bid-Ask spread: 0.5 bps (SPY is 1 penny on $500 = 0.2 bps actually!)
- Commissions: 0.6 bps (might be lower with volume)
- Market impact: 1.0 bps (small size = minimal impact)

Let's recalculate with REALISTIC friction for small retail trader:
"""

print("="*80)
print("FRICTION REALITY CHECK")
print("="*80)

# SPY current price ~$500
spy_price = 500

# Bid-ask spread
spread_cents = 1  # 1 penny typical for SPY
spread_bps = (spread_cents / spy_price) * 10000
print(f"\n1. Bid-Ask Spread:")
print(f"   SPY @ ${spy_price}, spread = {spread_cents} cent")
print(f"   = {spread_bps:.2f} bps (NOT 0.5 bps!)")

# Slippage with 67ms latency
print(f"\n2. Slippage (67ms latency):")
print(f"   Market orders at 67ms: ~0.5-1.0 bps")
print(f"   Limit orders (patient): ~0.0 bps")
print(f"   Conservative estimate: 0.5 bps")

# Commissions
print(f"\n3. Commissions:")
print(f"   Interactive Brokers: $0.005/share, $1 min")
print(f"   100 shares @ $500 = $50,000 position")
print(f"   Round-trip: $0.005 * 100 * 2 = $1.00")
print(f"   = {(1.00 / 50000) * 10000:.2f} bps")
print(f"   ")
print(f"   OR with volume pricing:")
print(f"   $0.0035/share = $0.70 round-trip = 0.14 bps")

# Market impact
print(f"\n4. Market Impact:")
print(f"   100 shares in SPY (avg volume 80M/day)")
print(f"   = 0.000125% of daily volume")
print(f"   Impact: ~0.0 bps (negligible)")

# Total friction scenarios
print(f"\n{'='*80}")
print("TOTAL FRICTION ESTIMATES")
print(f"{'='*80}")

scenarios = [
    {
        'name': 'Current (Conservative)',
        'spread': 0.5,
        'slippage': 2.0,
        'commission': 0.6,
        'impact': 1.0,
    },
    {
        'name': 'Realistic (Market Orders)',
        'spread': 0.2,
        'slippage': 0.5,
        'commission': 0.2,
        'impact': 0.1,
    },
    {
        'name': 'Best Case (Limit Orders)',
        'spread': 0.0,  # Maker rebate
        'slippage': 0.0,
        'commission': 0.14,
        'impact': 0.0,
    },
    {
        'name': 'Worst Case (Fast Market)',
        'spread': 0.4,
        'slippage': 1.5,
        'commission': 0.2,
        'impact': 0.3,
    }
]

for scenario in scenarios:
    total = scenario['spread'] + scenario['slippage'] + scenario['commission'] + scenario['impact']
    print(f"\n{scenario['name']}:")
    print(f"  Spread:     {scenario['spread']:>5.2f} bps")
    print(f"  Slippage:   {scenario['slippage']:>5.2f} bps")
    print(f"  Commission: {scenario['commission']:>5.2f} bps")
    print(f"  Impact:     {scenario['impact']:>5.2f} bps")
    print(f"  TOTAL:      {total:>5.2f} bps ({total/100:.4f}%)")

print(f"\n{'='*80}")
print("IMPACT ON LIQUIDITY GRAB V2 (60% WIN RATE)")
print(f"{'='*80}")

# V2 Config 3 results
win_rate = 60.0
avg_win_gross = 0.042  # Before friction
avg_loss_gross = -0.249  # Before friction
trades_per_day = 0.2

print(f"\nOriginal results (4.1 bps friction):")
print(f"  Win rate: {win_rate}%")
print(f"  Avg win (gross): {avg_win_gross:.3f}%")
print(f"  Avg loss (gross): {avg_loss_gross:.3f}%")

for scenario in scenarios:
    friction_pct = (scenario['spread'] + scenario['slippage'] + scenario['commission'] + scenario['impact']) / 100
    
    # Recalculate with new friction
    avg_win_net = avg_win_gross - friction_pct
    avg_loss_net = avg_loss_gross - friction_pct
    
    expected_pnl = (win_rate/100 * avg_win_net) + ((100-win_rate)/100 * avg_loss_net)
    
    # Annual metrics
    trades_per_year = trades_per_day * 252
    annual_return = expected_pnl * trades_per_year
    annual_friction = friction_pct * trades_per_year
    
    print(f"\n{scenario['name']} ({friction_pct*100:.3f}% per trade):")
    print(f"  Avg win (net):  {avg_win_net:>7.3f}%")
    print(f"  Avg loss (net): {avg_loss_net:>7.3f}%")
    print(f"  Expected P&L:   {expected_pnl:>7.3f}% per trade")
    print(f"  Annual return:  {annual_return:>7.2f}% ({trades_per_year:.0f} trades)")
    print(f"  Annual friction:{annual_friction:>7.2f}%")
    
    if expected_pnl > 0:
        print(f"  ✅ PROFITABLE!")
    elif expected_pnl > -0.01:
        print(f"  ⚠️  Breakeven")
    else:
        print(f"  ❌ Losing")

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")
print(f"""
If we use REALISTIC friction (1.0 bps = 0.01%):
- Avg win: 0.042% - 0.01% = 0.032% net
- Avg loss: -0.249% - 0.01% = -0.259% net
- Expected: 60% * 0.032% + 40% * -0.259% = -0.084% per trade

Still negative BUT much closer!

If we use BEST CASE (0.14 bps with limit orders):
- Avg win: 0.042% - 0.0014% = 0.0406% net
- Avg loss: -0.249% - 0.0014% = -0.2504% net
- Expected: 60% * 0.0406% + 40% * -0.2504% = -0.076% per trade

STILL NEGATIVE!

The problem is NOT friction - it's that avg loss is 6x larger than avg win!
We need to either:
1. Increase avg win (let winners run longer)
2. Decrease avg loss (tighter stops)
3. Improve win rate even more (>70%)
""")

print(f"\nRECOMMENDATION:")
print(f"  Use 1.0 bps friction (realistic) instead of 4.1 bps")
print(f"  Focus on improving avg win / avg loss ratio")
print(f"  Target: Get avg win to at least 0.15% (4x current)")
