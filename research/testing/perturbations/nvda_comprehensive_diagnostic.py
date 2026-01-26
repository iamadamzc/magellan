"""
Comprehensive NVDA Daily Trend Diagnostic

Tests multiple scenarios to determine true performance:
1. Full validation period (Jun 2024 - Jan 2026) - includes split
2. Post-split only (Jun 10, 2024 onwards) - clean data
3. Pre-split only (Jun 3-9, 2024) - for comparison

Config: RSI-28, Bands 58/42, 2 bps friction
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
import pandas as pd
import numpy as np

def calculate_rsi(prices, period=28):
    """Calculate RSI"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    return rsi.replace([np.inf, -np.inf], np.nan).fillna(50)

def run_daily_trend_backtest(df, config, label):
    """Run Daily Trend Hysteresis backtest"""
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
    
    # Generate signals (hysteresis)
    position = 0
    signals = []
    
    for i in range(len(df)):
        rsi_val = df['rsi'].iloc[i]
        
        if pd.isna(rsi_val):
            signals.append(position)
            continue
        
        if position == 0:  # Flat
            if rsi_val > config['upper_band']:
                position = 1  # Go long
        elif position == 1:  # Long
            if rsi_val < config['lower_band']:
                position = 0  # Go flat
        
        signals.append(position)
    
    df['signal'] = signals
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['signal'].shift(1) * df['returns']
    
    # Count trades
    trades = (df['signal'].diff() != 0).sum()
    
    # Apply friction
    friction_cost = trades * (config['friction_bps'] / 10000)
    
    # Performance metrics
    total_return = (1 + df['strategy_returns']).prod() - 1 - friction_cost
    
    if df['strategy_returns'].std() > 0:
        sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    # Buy-hold
    buy_hold = (df['close'].iloc[-1] / df['close'].iloc[0]) - 1
    
    return {
        'label': label,
        'period': f"{df.index[0].date()} to {df.index[-1].date()}",
        'bars': len(df),
        'buy_hold': buy_hold * 100,
        'trades': trades,
        'friction_cost': friction_cost * 100,
        'strategy_return': total_return * 100,
        'sharpe': sharpe,
        'status': '✅' if total_return > 0 else '❌'
    }

# Configuration
config = {
    'rsi_period': 28,
    'upper_band': 58,
    'lower_band': 42,
    'friction_bps': 2  # Conservative 2 bps
}

print("="*80)
print("NVDA DAILY TREND COMPREHENSIVE DIAGNOSTIC")
print("="*80)
print(f"\nConfig: RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}, {config['friction_bps']} bps friction")
print("\n" + "="*80)

# Test 1: Full validation period (includes split anomaly)
print("\n[TEST 1] Full Validation Period (includes Jun 10 split)")
print("-"*80)
df_full = cache.get_or_fetch_equity('NVDA', '1day', '2024-06-01', '2026-01-18')
result_full = run_daily_trend_backtest(df_full.copy(), config, "Full Period (Jun 1, 2024+)")

print(f"  Period: {result_full['period']}")
print(f"  Bars: {result_full['bars']}")
print(f"  Buy-Hold: {result_full['buy_hold']:+.2f}% (includes split drop)")
print(f"  {result_full['status']} Strategy: {result_full['strategy_return']:+.2f}% (Sharpe: {result_full['sharpe']:.2f})")
print(f"  Trades: {result_full['trades']} | Friction: {result_full['friction_cost']:.2f}%")

# Test 2: Post-split only (clean data)
print("\n[TEST 2] Post-Split Only (clean period)")
print("-"*80)
df_post = cache.get_or_fetch_equity('NVDA', '1day', '2024-06-10', '2026-01-18')
result_post = run_daily_trend_backtest(df_post.copy(), config, "Post-Split (Jun 10, 2024+)")

print(f"  Period: {result_post['period']}")
print(f"  Bars: {result_post['bars']}")
print(f"  Buy-Hold: {result_post['buy_hold']:+.2f}%")
print(f"  {result_post['status']} Strategy: {result_post['strategy_return']:+.2f}% (Sharpe: {result_post['sharpe']:.2f})")
print(f"  Trades: {result_post['trades']} | Friction: {result_post['friction_cost']:.2f}%")

# Test 3: Last 6 months only (current regime)
print("\n[TEST 3] Recent Performance (last 6 months)")
print("-"*80)
df_recent = cache.get_or_fetch_equity('NVDA', '1day', '2025-07-18', '2026-01-18')  
result_recent = run_daily_trend_backtest(df_recent.copy(), config, "Recent 6mo")

print(f"  Period: {result_recent['period']}")
print(f"  Bars: {result_recent['bars']}")
print(f"  Buy-Hold: {result_recent['buy_hold']:+.2f}%")
print(f"  {result_recent['status']} Strategy: {result_recent['strategy_return']:+.2f}% (Sharpe: {result_recent['sharpe']:.2f})")
print(f"  Trades: {result_recent['trades']} | Friction: {result_recent['friction_cost']:.2f}%")

# Test 4: Full post-split to 2025 end
print("\n[TEST 4] Post-Split Through 2025")
print("-"*80)
df_2025 = cache.get_or_fetch_equity('NVDA', '1day', '2024-06-10', '2025-12-31')
result_2025 = run_daily_trend_backtest(df_2025.copy(), config, "Jun 10, 2024 - Dec 31, 2025")

print(f"  Period: {result_2025['period']}")
print(f"  Bars: {result_2025['bars']}")
print(f"  Buy-Hold: {result_2025['buy_hold']:+.2f}%")
print(f"  {result_2025['status']} Strategy: {result_2025['strategy_return']:+.2f}% (Sharpe: {result_2025['sharpe']:.2f})")
print(f"  Trades: {result_2025['trades']} | Friction: {result_2025['friction_cost']:.2f}%")

# Summary
print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

results = [result_full, result_post, result_recent, result_2025]

profitable_count = sum(1 for r in results if r['strategy_return'] > 0)
avg_return = np.mean([r['strategy_return'] for r in results])
avg_sharpe = np.mean([r['sharpe'] for r in results])

print(f"\nProfitable Periods: {profitable_count}/4")
print(f"Average Strategy Return: {avg_return:+.2f}%")
print(f"Average Sharpe: {avg_sharpe:.2f}")

print("\n" + "-"*80)
print("COMPARISON vs ORIGINAL VALIDATION")
print("-"*80)
print(f"  Original (from config): +24.55%, Sharpe 0.64, 7 trades/year")
print(f"  Post-Split Test 2: {result_post['strategy_return']:+.2f}%, Sharpe {result_post['sharpe']:.2f}, {result_post['trades']} trades")
print(f"  Post-Split Test 4: {result_2025['strategy_return']:+.2f}%, Sharpe {result_2025['sharpe']:.2f}, {result_2025['trades']} trades")

print("\n" + "-"*80)
print("VERDICT")
print("-"*80)

if profitable_count >= 3:
    print("✅ NVDA passes in most test periods")
    print("   Recommendation: DEPLOY with caution (monitor closely)")
elif profitable_count >= 2:
    print("⚠️  NVDA marginal (50/50 success rate)")
    print("   Recommendation: PAPER TRADE first")
else:
    print("❌ NVDA consistently fails")
    print("   Recommendation: EXCLUDE from deployment")
    print("   Reason: Daily Trend Hysteresis does not work for NVDA's volatility profile")

print("\n" + "="*80)
