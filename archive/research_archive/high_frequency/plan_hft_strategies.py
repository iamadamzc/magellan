"""
High-Frequency Trading Strategy Suite

Goal: Test intraday and scalping strategies leveraging 67ms latency

Strategies to Test:
1. RSI Mean Reversion (1-min bars, RSI < 30 buy, RSI > 70 sell)
2. VWAP Reversion (price deviates >0.5% from VWAP)
3. Opening Range Breakout (first 30-min range)
4. Bollinger Band Squeeze (volatility expansion)
5. Volume Spike Reversal (unusual volume detection)

Instruments:
- Equities: SPY, QQQ, IWM, NVDA, TSLA, AAPL
- Futures: ES (S&P 500), NQ (Nasdaq 100)

Hold Times: 1-5 minutes (scalping), 15-60 minutes (intraday)
Expected Sharpe: 0.8-1.5 (if latency edge exists)

Critical: Test with realistic slippage (67ms vs 500ms comparison)
"""

import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
FMP_API_KEY = os.getenv('FMP_API_KEY')

print("="*80)
print("HIGH-FREQUENCY TRADING STRATEGY SUITE")
print("="*80)
print("\nPhase 1 Finding: 67ms latency (7.5x faster than assumed)")
print("Hypothesis: Can capture intraday moves that were previously too fast")

# Test data access for various instruments
instruments = {
    'equities': ['SPY', 'QQQ', 'IWM', 'NVDA', 'TSLA', 'AAPL', 'MSFT'],
    'futures': ['ES', 'NQ']  # May need different endpoint
}

print("\n" + "="*80)
print("DATA ACCESS TEST")
print("="*80)

def test_1min_data(symbol, date='2024-06-12'):
    """Test if 1-min data is available"""
    url = "https://financialmodelingprep.com/stable/historical-chart/1min"
    params = {
        'symbol': symbol,
        'from': date,
        'to': date,
        'apikey': FMP_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return len(data) if isinstance(data, list) else 0
        return 0
    except:
        return 0

print("\nTesting 1-minute data access...")
print("\nEquities:")
equity_access = {}
for symbol in instruments['equities']:
    bars = test_1min_data(symbol)
    equity_access[symbol] = bars
    status = "✅" if bars > 0 else "❌"
    print(f"  {symbol:6s}: {status} {bars:4d} bars")

print("\nFutures:")
futures_access = {}
for symbol in instruments['futures']:
    bars = test_1min_data(symbol)
    futures_access[symbol] = bars
    status = "✅" if bars > 0 else "❌"
    print(f"  {symbol:6s}: {status} {bars:4d} bars")

# Strategy definitions
print("\n" + "="*80)
print("STRATEGY PARAMETERS")
print("="*80)

strategies = {
    'RSI Mean Reversion': {
        'timeframe': '1-min',
        'signal': 'RSI(14) < 30 (buy) or > 70 (sell)',
        'hold': '5-15 minutes',
        'target': '0.10-0.25%',
        'stop': '0.15%',
        'expected_sharpe': '0.9-1.3'
    },
    'VWAP Reversion': {
        'timeframe': '1-min',
        'signal': 'Price > 1.005 * VWAP (sell) or < 0.995 * VWAP (buy)',
        'hold': '5-10 minutes',
        'target': '0.05-0.15%',
        'stop': '0.10%',
        'expected_sharpe': '0.8-1.2'
    },
    'Opening Range Breakout': {
        'timeframe': '5-min',
        'signal': 'Break above/below first 30-min range',
        'hold': '30-60 minutes',
        'target': '0.20-0.50%',
        'stop': '0.20%',
        'expected_sharpe': '1.0-1.5'
    },
    'Bollinger Squeeze': {
        'timeframe': '5-min',
        'signal': 'BB width < 0.5% then breakout',
        'hold': '15-30 minutes',
        'target': '0.15-0.30%',
        'stop': '0.15%',
        'expected_sharpe': '0.9-1.4'
    }
}

for name, params in strategies.items():
    print(f"\n{name}:")
    for key, value in params.items():
        print(f"  {key:20s}: {value}")

# Slippage analysis
print("\n" + "="*80)
print("LATENCY & SLIPPAGE ASSUMPTIONS")
print("="*80)

slippage_scenarios = {
    '67ms (actual)': {
        'latency': '67ms',
        'slippage_bps': 1.0,  # 0.01% = very tight
        'win_rate_boost': '+2%',  # Faster fills = better prices
    },
    '500ms (legacy)': {
        'latency': '500ms',
        'slippage_bps': 3.0,  # 0.03% = realistic retail
        'win_rate_boost': '0%',  # Baseline
    }
}

print("\nScenario comparison:")
for scenario, params in slippage_scenarios.items():
    print(f"\n{scenario}:")
    for key, value in params.items():
        print(f"  {key:20s}: {value}")

print("\n💡 Hypothesis: 67ms latency reduces slippage by 2-3 bps")
print("   This could make previously unprofitable strategies viable!")

# Next steps
print("\n" + "="*80)
print("BACKTEST PLAN")
print("="*80)

accessible_equities = [s for s, bars in equity_access.items() if bars > 0]
accessible_futures = [s for s, bars in futures_access.items() if bars > 0]

print(f"\n✅ Accessible equities ({len(accessible_equities)}): {', '.join(accessible_equities)}")
if accessible_futures:
    print(f"✅ Accessible futures ({len(accessible_futures)}): {', '.join(accessible_futures)}")
else:
    print("❌ Futures data not available via standard endpoint")
    print("   Alternative: Use Alpaca or dedicated futures provider")

print("\nPriority order:")
print("1. RSI Mean Reversion on SPY (highest liquidity)")
print("2. VWAP Reversion on QQQ (tech momentum)")
print("3. Opening Range Breakout on NVDA (high volatility)")
print("4. Futures strategies (if data accessible)")

print("\nEstimated time:")
print("  • Strategy 1: 2-3 hours (build + backtest + analyze)")
print("  • Strategy 2-3: 1-2 hours each (reuse framework)")
print("  • Total: 6-8 hours for comprehensive suite")

print("\n" + "="*80)
print("NEXT: Build RSI Mean Reversion backtest on SPY")
print("="*80)
