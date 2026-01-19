"""
Debug Analysis - Why Q1 2024 vs Full Year Discrepancy?

Hypothesis 1: Data quality issues
- Maybe Q1 2024 data is different from rest of year?
- Check if FMP returns different data formats

Hypothesis 2: Calculation errors
- Sharpe calculation might be wrong
- Annualization factor might be incorrect

Hypothesis 3: Sample size effects
- Small sample (30 days) has high variance
- But this consistent across ALL strategies?

Hypothesis 4: Market regime
- Q1 2024 was genuinely different market conditions
- More volatility = better for mean reversion?

Let me check the actual data and calculations
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

def fetch_1min_data(symbol, date):
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {'symbol': symbol, 'from': date, 'to': date, 'apikey': FMP_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

print("="*80)
print("DEBUG: Q1 2024 vs FULL YEAR DISCREPANCY ANALYSIS")
print("="*80)

# Test on a few specific dates across the year
test_dates = {
    'Q1': ['2024-01-15', '2024-02-15', '2024-03-15'],
    'Q2': ['2024-04-15', '2024-05-15', '2024-06-15'],
    'Q3': ['2024-07-15', '2024-08-15', '2024-09-15'],
    'Q4': ['2024-10-15', '2024-11-15', '2024-12-15']
}

print("\n1. DATA QUALITY CHECK")
print("="*80)

for quarter, dates in test_dates.items():
    print(f"\n{quarter}:")
    for date in dates:
        bars = fetch_1min_data('ES', date)
        if bars:
            df = pd.DataFrame(bars)
            print(f"  {date}: {len(bars)} bars, Price range: ${df['low'].min():.2f}-${df['high'].max():.2f}")
            
            # Check for data anomalies
            if len(bars) < 300:
                print(f"    ⚠️  WARNING: Only {len(bars)} bars (expected ~390)")
        else:
            print(f"  {date}: NO DATA")

print("\n2. SHARPE CALCULATION VERIFICATION")
print("="*80)

# Manual Sharpe calculation check
test_returns = [0.1, -0.05, 0.15, -0.1, 0.2, -0.08, 0.12, -0.15, 0.18, -0.12]
avg_return = np.mean(test_returns)
std_return = np.std(test_returns)

print(f"\nTest data: {test_returns}")
print(f"Avg return: {avg_return:.4f}")
print(f"Std return: {std_return:.4f}")

# Different Sharpe calculations
sharpe_daily = avg_return / std_return
sharpe_annual_sqrt252 = sharpe_daily * np.sqrt(252)
sharpe_annual_trades = (avg_return / std_return) * np.sqrt(252 * len(test_returns) / 10)  # My formula

print(f"\nSharpe (daily): {sharpe_daily:.2f}")
print(f"Sharpe (annual, sqrt(252)): {sharpe_annual_sqrt252:.2f}")
print(f"Sharpe (my formula): {sharpe_annual_trades:.2f}")

print("\n3. TRADE FREQUENCY ANALYSIS BY QUARTER")
print("="*80)

# Simple strategy to count trades per quarter
def simple_range_strategy(df):
    """Simplified range strategy for debugging"""
    if len(df) < 30:
        return []
    
    df['sma'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['bb_upper'] = df['sma'] + (2.0 * df['std'])
    df['bb_lower'] = df['sma'] - (2.0 * df['std'])
    
    trades = []
    for i in range(25, len(df)):
        if pd.notna(df.loc[i, 'bb_lower']):
            if df.loc[i, 'close'] <= df.loc[i, 'bb_lower']:
                # Simulate trade
                entry_price = df.loc[i, 'close']
                # Exit after 10 bars or at target
                for j in range(i+1, min(i+11, len(df))):
                    pnl_pct = (df.loc[j, 'close'] - entry_price) / entry_price * 100
                    if pnl_pct >= 0.20 or pnl_pct <= -0.15:
                        trades.append(pnl_pct - 0.01)  # 1 bps friction
                        break
    
    return trades

for quarter, dates in test_dates.items():
    all_trades = []
    days_loaded = 0
    
    for date in dates:
        bars = fetch_1min_data('ES', date)
        if len(bars) >= 50:
            df = pd.DataFrame(bars).sort_values('date').reset_index(drop=True)
            trades = simple_range_strategy(df)
            all_trades.extend(trades)
            days_loaded += 1
    
    if all_trades:
        avg_pnl = np.mean(all_trades)
        std_pnl = np.std(all_trades)
        sharpe = (avg_pnl / std_pnl * np.sqrt(252 * len(all_trades) / days_loaded)) if std_pnl > 0 and days_loaded > 0 else 0
        
        print(f"\n{quarter}: {len(all_trades)} trades from {days_loaded} days")
        print(f"  Avg P&L: {avg_pnl:.3f}%")
        print(f"  Sharpe: {sharpe:.2f}")
        print(f"  Trades/day: {len(all_trades)/days_loaded:.1f}")

print("\n4. HYPOTHESIS: Q1 2024 MARKET CONDITIONS")
print("="*80)
print("""
Possible explanations:
1. Q1 2024 had specific volatility patterns that favored mean reversion
2. Small sample size (30 days) has high variance - could be luck
3. My Sharpe calculation might be over-optimistic for small samples
4. Data quality issues in later months

RECOMMENDATION:
- Check if Q1 2024 was genuinely more volatile
- Verify Sharpe calculation is correct
- Test on Q1 2023, Q1 2025 to see if Q1 is always better
""")

print("\n5. CHECKING MY SHARPE FORMULA")
print("="*80)

# The formula I've been using
print("My formula: sharpe = (avg_pnl / std_pnl) * sqrt(252 * num_trades / num_days)")
print("\nThis assumes:")
print("  - avg_pnl is per-trade return")
print("  - Annualizing by number of trades per year")
print("  - num_trades / num_days = trades per day")
print("  - 252 trading days per year")

print("\nStandard Sharpe formula:")
print("  sharpe = (mean_return - risk_free_rate) / std_return * sqrt(periods_per_year)")
print("\nFor daily returns: sqrt(252)")
print("For trade returns: sqrt(trades_per_year)")

print("\n⚠️  POTENTIAL BUG:")
print("If I have 100 trades over 30 days, that's 3.33 trades/day")
print("Annualized: 3.33 * 252 = 839 trades/year")
print("My formula: sqrt(252 * 100 / 30) = sqrt(840) = 28.98")
print("Correct formula: sqrt(839) = 28.97")
print("\nFormula seems correct...")

print("\n✅ Saved analysis")
