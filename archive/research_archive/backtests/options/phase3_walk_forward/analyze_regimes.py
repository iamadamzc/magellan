"""
Regime Analysis for Premium Selling Strategy

Objective: Understand why strategy works in some periods (W7-W9) but fails in others (W4, W10)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.features import calculate_rsi

print("="*80)
print("REGIME ANALYSIS - PREMIUM SELLING STRATEGY")
print("="*80)

# Load WFA results
wfa_results = pd.read_csv('research/backtests/options/phase3_walk_forward/wfa_results/wfa_detailed_results.csv')

# Fetch SPY data
alpaca = AlpacaDataClient()
spy_data = alpaca.fetch_historical_bars('SPY', '1Day', '2020-01-01', '2025-12-31')

# Calculate regime indicators
spy_data['returns'] = spy_data['close'].pct_change()
spy_data['volatility_20d'] = spy_data['returns'].rolling(20).std() * np.sqrt(252) * 100  # Annualized vol
spy_data['trend_50d'] = (spy_data['close'] / spy_data['close'].rolling(50).mean() - 1) * 100  # % above 50-day MA
spy_data['rsi'] = calculate_rsi(spy_data['close'], period=21)
spy_data['rsi_range'] = spy_data['rsi'].rolling(20).max() - spy_data['rsi'].rolling(20).min()  # RSI volatility

print("\nAnalyzing market regimes for each WFA window...\n")

# Analyze each window
for idx, row in wfa_results.iterrows():
    window_name = row['window']
    test_start = row['test_start']
    test_end = row['test_end']
    oos_sharpe = row['oos_sharpe']
    
    # Get regime data for test period
    test_data = spy_data[(spy_data.index >= test_start) & (spy_data.index <= test_end)]
    
    avg_vol = test_data['volatility_20d'].mean()
    avg_trend = test_data['trend_50d'].mean()
    avg_rsi_range = test_data['rsi_range'].mean()
    spy_return = (test_data['close'].iloc[-1] / test_data['close'].iloc[0] - 1) * 100
    
    performance = "✅ GOOD" if oos_sharpe > 0.5 else "❌ BAD" if oos_sharpe < 0 else "⚠️ NEUTRAL"
    
    print(f"{window_name} ({test_start} to {test_end}) - Sharpe: {oos_sharpe:.2f} {performance}")
    print(f"  SPY Return: {spy_return:+.1f}%")
    print(f"  Avg Volatility: {avg_vol:.1f}%")
    print(f"  Avg Trend: {avg_trend:+.1f}% (vs 50-day MA)")
    print(f"  RSI Range: {avg_rsi_range:.1f}")
    print()

# Correlation analysis
print("="*80)
print("REGIME CORRELATION ANALYSIS")
print("="*80)

# Add regime data to WFA results
regime_data = []
for idx, row in wfa_results.iterrows():
    test_data = spy_data[(spy_data.index >= row['test_start']) & (spy_data.index <= row['test_end'])]
    regime_data.append({
        'window': row['window'],
        'oos_sharpe': row['oos_sharpe'],
        'avg_vol': test_data['volatility_20d'].mean(),
        'avg_trend': test_data['trend_50d'].mean(),
        'avg_rsi_range': test_data['rsi_range'].mean(),
        'spy_return': (test_data['close'].iloc[-1] / test_data['close'].iloc[0] - 1) * 100
    })

regime_df = pd.DataFrame(regime_data)

# Calculate correlations
print("\nCorrelation with Strategy Performance (Sharpe):")
print(f"  Volatility: {regime_df['avg_vol'].corr(regime_df['oos_sharpe']):.3f}")
print(f"  Trend: {regime_df['avg_trend'].corr(regime_df['oos_sharpe']):.3f}")
print(f"  RSI Range: {regime_df['avg_rsi_range'].corr(regime_df['oos_sharpe']):.3f}")
print(f"  SPY Return: {regime_df['spy_return'].corr(regime_df['oos_sharpe']):.3f}")

# Identify good vs bad regimes
good_windows = regime_df[regime_df['oos_sharpe'] > 0.5]
bad_windows = regime_df[regime_df['oos_sharpe'] < 0]

print(f"\n📊 Good Windows (Sharpe > 0.5): {len(good_windows)}")
print(f"  Avg Volatility: {good_windows['avg_vol'].mean():.1f}%")
print(f"  Avg Trend: {good_windows['avg_trend'].mean():+.1f}%")
print(f"  Avg RSI Range: {good_windows['avg_rsi_range'].mean():.1f}")

print(f"\n📊 Bad Windows (Sharpe < 0): {len(bad_windows)}")
print(f"  Avg Volatility: {bad_windows['avg_vol'].mean():.1f}%")
print(f"  Avg Trend: {bad_windows['avg_trend'].mean():+.1f}%")
print(f"  Avg RSI Range: {bad_windows['avg_rsi_range'].mean():.1f}")

# Recommendation
print("\n" + "="*80)
print("REGIME FILTER RECOMMENDATION")
print("="*80)

if abs(regime_df['avg_vol'].corr(regime_df['oos_sharpe'])) > 0.5:
    print("\n✅ Volatility is a strong predictor")
    print(f"   Recommendation: Only trade when volatility is in optimal range")
elif abs(regime_df['avg_trend'].corr(regime_df['oos_sharpe'])) > 0.5:
    print("\n✅ Trend is a strong predictor")
    print(f"   Recommendation: Only trade in specific trend regimes")
elif abs(regime_df['avg_rsi_range'].corr(regime_df['oos_sharpe'])) > 0.5:
    print("\n✅ RSI range is a strong predictor")
    print(f"   Recommendation: Only trade when RSI is volatile enough")
else:
    print("\n⚠️ No single regime indicator is strongly predictive")
    print("   Recommendation: Strategy may not be salvageable with simple regime filter")

print("\n" + "="*80)
