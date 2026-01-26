"""
Daily Trading Strategy Candidate Analysis
Analyzes SPY, QQQ, and major stocks for intraday trading potential
"""

import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path('../../data/cache/equities')

def analyze_intraday_characteristics(ticker, sample_days=30):
    """Analyze intraday trading metrics."""
    
    # Load recent 1-min data
    files = sorted(list(data_dir.glob(f'{ticker}_1min_*.parquet')))
    if not files:
        return None
    
    df = pd.read_parquet(files[-1])  # Most recent file
    df.index = pd.to_datetime(df.index)
    
    # Take last N days
    recent = df.tail(sample_days * 390)  # ~390 1-min bars per day
    
    if len(recent) < 100:
        return None
    
    # Calculate metrics
    recent['returns'] = recent['close'].pct_change()
    recent['range'] = (recent['high'] - recent['low']) / recent['close']
    
    # Daily stats
    recent['date'] = recent.index.date
    daily_stats = recent.groupby('date').agg({
        'close': ['first', 'last', 'min', 'max'],
        'volume': 'sum',
        'range': 'mean'
    })
    
    daily_stats['daily_range'] = (daily_stats[('close', 'max')] - daily_stats[('close', 'min')]) / daily_stats[('close', 'first')]
    daily_stats['daily_return'] = (daily_stats[('close', 'last')] - daily_stats[('close', 'first')]) / daily_stats[('close', 'first')]
    
    avg_daily_range = daily_stats['daily_range'].mean() * 100
    avg_daily_volume = daily_stats[('volume', 'sum')].mean()
    volatility = recent['returns'].std() * np.sqrt(390)  # Annualized intraday vol
    
    # Count big intraday moves (good for scalping)
    recent['abs_return'] = recent['returns'].abs()
    big_moves_per_day = (recent.groupby('date')['abs_return'].apply(lambda x: (x > 0.002).sum()).mean())
    
    return {
        'ticker': ticker,
        'avg_daily_range_pct': avg_daily_range,
        'avg_daily_volume': avg_daily_volume / 1e6,  # In millions
        'intraday_volatility': volatility,
        'big_moves_per_day': big_moves_per_day,
        'sample_days': len(daily_stats)
    }


print("=" * 80)
print("DAILY TRADING STRATEGY - CANDIDATE ANALYSIS")
print("=" * 80)
print("\nAnalyzing intraday characteristics for top liquid assets...")
print()

candidates = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AMD']
results = []

for ticker in candidates:
    print(f"Analyzing {ticker}...")
    result = analyze_intraday_characteristics(ticker)
    if result:
        results.append(result)

# Display results
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

results_df = pd.DataFrame(results)
results_df = results_df.sort_values('big_moves_per_day', ascending=False)

print("\nRanked by Trading Opportunities (big moves/day):")
print(results_df.to_string(index=False))

print("\n" + "-" * 80)
print("INTERPRETATION:")
print("-" * 80)

best = results_df.iloc[0]
print(f"\nBEST CANDIDATE: {best['ticker']}")
print(f"  Average daily range: {best['avg_daily_range_pct']:.2f}%")
print(f"  Big moves per day: {best['big_moves_per_day']:.0f}")
print(f"  Avg volume: {best['avg_daily_volume']:.0f}M shares/day")
print(f"  Intraday volatility: {best['intraday_volatility']:.2f}")

print("\nWHY THIS MATTERS:")
print("  - More big moves = more trading opportunities")
print("  - Higher volume = tighter spreads, less slippage")
print("  - Higher volatility = larger profit potential per trade")

# Recommendation
print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if best['ticker'] in ['SPY', 'QQQ']:
    print(f"\n{best['ticker']} is IDEAL for daily trading:")
    print("  ✅ Extremely liquid (tight spreads)")
    print("  ✅ Consistent intraday patterns")
    print("  ✅ No single-stock risk")
    print("  ✅ Options available for hedging")
    print("  ✅ Futures alternative (ES/NQ) available")
else:
    print(f"\n{best['ticker']} has HIGH potential for daily trading:")
    print("  ✅ High volatility = larger moves")
    print("  ✅ Plenty of trading opportunities")
    print("  ⚠️ Higher risk (single stock)")
    print("  ⚠️ May have wider spreads than SPY/QQQ")

print()
