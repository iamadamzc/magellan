"""
Deep Analysis of 2024 Backtest Results

Goal: Understand WHY the strategy failed in 2024 and identify tuning opportunities

Analysis Areas:
1. Monthly performance patterns - which months worked vs failed?
2. Trade distribution - when do wins vs losses cluster?
3. Market regime analysis - trending vs ranging vs volatile periods
4. Entry/exit quality - are we entering at good times?
5. Parameter sensitivity - what if we adjust thresholds?

Load the detailed results and find patterns
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime

# Load full year results
with open('full_year_backtest_results.json', 'r') as f:
    results = json.load(f)

data_2024 = results['2024']

print("="*80)
print("DEEP DIVE ANALYSIS - 2024 RESULTS")
print("="*80)

# 1. Monthly Performance Analysis
print("\n" + "="*80)
print("1. MONTHLY PERFORMANCE PATTERNS")
print("="*80)

monthly = data_2024['monthly_breakdown']

print(f"\n{'Month':<10s} | {'Trades':>7s} | {'Return':>8s} | {'Win%':>6s} | {'Avg/Trade':>11s} | {'Status':>10s}")
print("-" * 80)

for month in sorted(monthly.keys()):
    m_data = monthly[month]
    avg_per_trade = m_data['return'] / m_data['trades'] if m_data['trades'] > 0 else 0
    
    status = "✅" if m_data['return'] > 0 else "❌"
    
    print(f"{month:<10s} | {m_data['trades']:>7d} | {m_data['return']:>7.2f}% | {m_data['win_rate']:>5.1f}% | {avg_per_trade:>10.3f}% | {status:>10s}")

# Identify best and worst months
monthly_items = [(m, d['return']) for m, d in monthly.items()]
best_months = sorted(monthly_items, key=lambda x: x[1], reverse=True)[:3]
worst_months = sorted(monthly_items, key=lambda x: x[1])[:3]

print(f"\n🏆 Best 3 Months:")
for month, ret in best_months:
    print(f"   {month}: {ret:+.2f}% (Win Rate: {monthly[month]['win_rate']:.1f}%)")

print(f"\n💀 Worst 3 Months:")
for month, ret in worst_months:
    print(f"   {month}: {ret:+.2f}% (Win Rate: {monthly[month]['win_rate']:.1f}%)")

# 2. Win Rate Analysis
print(f"\n{'='*80}")
print("2. WIN RATE DISTRIBUTION")
print(f"{'='*80}")

win_rates = [m['win_rate'] for m in monthly.values()]
high_wr_months = [m for m, data in monthly.items() if data['win_rate'] >= 50]
low_wr_months = [m for m, data in monthly.items() if data['win_rate'] < 35]

print(f"\nMonths with Win Rate >= 50%: {len(high_wr_months)}/12")
for month in high_wr_months:
    print(f"   {month}: {monthly[month]['win_rate']:.1f}% ({monthly[month]['trades']} trades, {monthly[month]['return']:+.2f}%)")

print(f"\nMonths with Win Rate < 35%: {len(low_wr_months)}/12")
for month in low_wr_months:
    print(f"   {month}: {monthly[month]['win_rate']:.1f}% ({monthly[month]['trades']} trades, {monthly[month]['return']:+.2f}%)")

# 3. Trade Frequency Analysis
print(f"\n{'='*80}")
print("3. TRADE FREQUENCY PATTERNS")
print(f"{'='*80}")

trade_counts = [(m, data['trades']) for m, data in monthly.items()]
high_freq = sorted(trade_counts, key=lambda x: x[1], reverse=True)[:3]
low_freq = sorted(trade_counts, key=lambda x: x[1])[:3]

print(f"\nHighest Frequency Months:")
for month, count in high_freq:
    trades_per_day = count / 21  # Approx 21 trading days per month
    print(f"   {month}: {count} trades ({trades_per_day:.1f}/day) - Return: {monthly[month]['return']:+.2f}%")

print(f"\nLowest Frequency Months:")
for month, count in low_freq:
    trades_per_day = count / 21
    print(f"   {month}: {count} trades ({trades_per_day:.1f}/day) - Return: {monthly[month]['return']:+.2f}%")

# 4. Correlation Analysis
print(f"\n{'='*80}")
print("4. FREQUENCY vs PERFORMANCE CORRELATION")
print(f"{'='*80}")

freq_data = []
for month, data in monthly.items():
    freq_data.append({
        'month': month,
        'trades': data['trades'],
        'return': data['return'],
        'win_rate': data['win_rate']
    })

df_corr = pd.DataFrame(freq_data)
corr_freq_return = df_corr['trades'].corr(df_corr['return'])
corr_wr_return = df_corr['win_rate'].corr(df_corr['return'])

print(f"\nCorrelation between Trade Frequency and Return: {corr_freq_return:.3f}")
print(f"Correlation between Win Rate and Return: {corr_wr_return:.3f}")

if corr_freq_return < -0.3:
    print("\n⚠️  **NEGATIVE correlation** - More trades = worse returns (overtrading!)")
elif corr_freq_return > 0.3:
    print("\n✅ Positive correlation - More trades = better returns")
else:
    print("\n⚠️  Weak correlation - Frequency doesn't predict performance")

# 5. Key Insights
print(f"\n{'='*80}")
print("5. KEY INSIGHTS & TUNING OPPORTUNITIES")
print(f"{'='*80}")

insights = []

# Insight 1: High-frequency months
high_freq_months = [m for m, d in monthly.items() if d['trades'] > 40]
if high_freq_months:
    avg_return_high_freq = np.mean([monthly[m]['return'] for m in high_freq_months])
    insights.append({
        'title': 'High-Frequency Months Perform WORSE',
        'data': f"Months with >40 trades: {len(high_freq_months)}",
        'metric': f"Avg return: {avg_return_high_freq:.2f}%",
        'action': 'INCREASE threshold to reduce trade frequency'
    })

# Insight 2: Low win rate months
if len(low_wr_months) > 6:  # More than half the year
    insights.append({
        'title': 'Win Rate Too Low Most Months',
        'data': f"{len(low_wr_months)}/12 months below 35% win rate",
        'metric': 'Overall: 36.3% win rate',
        'action': 'Add stricter filters (volatility, volume, momentum)'
    })

# Insight 3: June was breakeven
june_data = monthly.get('2024-06')
if june_data and abs(june_data['return']) < 0.1:
    insights.append({
        'title': 'June Was Breakeven (50% Win Rate)',
        'data': f"12 trades, 0.00% return, 50% win rate",
        'metric': 'Only profitable month conditions',
        'action': 'Study June market conditions and replicate filters'
    })

# Insight 4: August surge
aug_data = monthly.get('2024-08')
if aug_data and aug_data['trades'] > 60:
    insights.append({
        'title': 'August Had Excessive Trades (82)',
        'data': f"82 trades = 3.9/day (highest frequency)",
        'metric': f"Return: {aug_data['return']:.2f}% (losing)",
        'action': 'Avoid volatile/choppy periods - add regime filter'
    })

# Print insights
for idx, insight in enumerate(insights, 1):
    print(f"\n{idx}. {insight['title']}")
    print(f"   Data: {insight['data']}")
    print(f"   Metric: {insight['metric']}")
    print(f"   💡 Action: {insight['action']}")

# 6. Proposed Tuning Parameters
print(f"\n{'='*80}")
print("6. PROPOSED TUNING PARAMETERS")
print(f"{'='*80}")

proposals = []

# Proposal 1: Increase threshold
current_thresh = 0.45
proposals.append({
    'param': 'VWAP Threshold',
    'current': f'{current_thresh}%',
    'proposed': '0.60-0.75%',
    'rationale': 'Reduce trades from 1.43/day to <0.5/day',
    'expected_impact': 'Lower frequency, higher signal quality'
})

# Proposal 2: Volatility filter
proposals.append({
    'param': 'Volatility Filter',
    'current': 'None',
    'proposed': 'ATR > 0.5%',
    'rationale': 'Only trade in volatile periods (avoid August choppy)',
    'expected_impact': 'Filter out low-quality ranging markets'
})

# Proposal 3: Profit target
proposals.append({
    'param': 'Profit Target',
    'current': '0.30%',
    'proposed': '0.40-0.50%',
    'rationale': 'Larger targets = better R/R to overcome friction',
    'expected_impact': 'Lower win rate but profitable trades'
})

# Proposal 4: Stop loss
proposals.append({
    'param': 'Stop Loss',
    'current': 'None (time-based only)',
    'proposed': '0.20% hard stop',
    'rationale': 'Worst trade was -0.805% - need downside protection',
    'expected_impact': 'Limit catastrophic losses'
})

print(f"\n{'Parameter':<20s} | {'Current':<15s} | {'Proposed':<15s} | {'Rationale':<50s}")
print("-" * 110)
for p in proposals:
    print(f"{p['param']:<20s} | {p['current']:<15s} | {p['proposed']:<15s} | {p['rationale']:<50s}")

# 7. Recommended Test
print(f"\n{'='*80}")
print("7. RECOMMENDED NEXT TEST")
print(f"{'='*80}")

print("""
Test Configuration V2:
---------------------
✅ VWAP Threshold: 0.60% (vs 0.45% current)
✅ Profit Target: 0.40% (vs 0.30% current)
✅ Stop Loss: 0.20% (NEW)
✅ Hold Time: 20 minutes (vs 15 min)
✅ Time Filter: Avoid 12-2 PM (keep)
✅ Volatility Filter: ATR > 0.5% (NEW)
✅ Volume Filter: Volume spike >2x (NEW)

Expected Impact:
- Reduce trades: 361 → ~100-150/year
- Improve win rate: 36.3% → 45-50%+
- Better R/R: Avg win/loss ratio improves
- Lower friction: 14.8% → 4-6%

Hypothesis: Stricter filters + larger targets = profitability
""")

print(f"\n{'='*80}")
print("Would you like me to backtest this V2 configuration on 2024?")
print(f"{'='*80}")
