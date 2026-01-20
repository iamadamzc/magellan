"""
IMPROVED Strategy Simulator - Q4 2024 with Proper Lookback
Includes historical data for indicator calculation
"""
import pandas as pd
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, str(project_root / 'research' / 'Perturbations'))
from bear_trap.bear_trap_strategy import run_bear_trap

from src.data_cache import cache
import numpy as np

# === SIMULATION PERIODS ===
# Need lookback for RSI calculation, but only report Dec results
LOOKBACK_START = '2024-10-01'  # 2 months lookback for indicators
TEST_START = '2024-12-01'
TEST_END = '2024-12-31'

print("="*80)
print("MAGELLAN Q4 2024 STRATEGY SIMULATION")
print("="*80)
print(f"Indicator Lookback: {LOOKBACK_START}")
print(f"Test Period: {TEST_START} to {TEST_END}\n")

def calculate_rsi(prices, period=21):
    """Calculate RSI"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def run_daily_trend(symbol, config, lookback_start, test_start, test_end):
    """RSI Hysteresis with proper lookback"""
    try:
        # Fetch data with lookback for indicator calculation
        df = cache.get_or_fetch_equity(symbol, '1day', lookback_start, test_end)
        if df is None or len(df) < 30:
            return None
        
        # Calculate RSI on full data
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        
        # Generate signals
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            if pd.isna(rsi_val):
                signals.append(position)
                continue
            
            if position == 0:
                if rsi_val > config['upper_band']:
                    position = 1
            elif position == 1:
                if rsi_val < config['lower_band']:
                    position = 0
            
            signals.append(position)
        
        df['signal'] = signals
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # Filter to test period only
        df_test = df[df.index >= test_start].copy()
        
        trades = (df_test['signal'].diff() != 0).sum()
        friction = trades * 0.001  # 10 bps per trade
        total_return = (1 + df_test['strategy_returns']).prod() - 1 - friction
        
        return {
            'return_pct': total_return * 100,
            'trades': trades,
            'days_in_market': (df_test['signal'] == 1).sum(),
            'total_days': len(df_test)
        }
    except Exception as e:
        print(f"  Error: {e}")
        return None

# ===============================================================================
# STRATEGY 1: DAILY TREND HYSTERESIS
# ===============================================================================
print("\n" + "="*80)
print("STRATEGY 1: DAILY TREND HYSTERESIS (Daily Bars)")
print("="*80)

DAILY_CONFIGS = {
    "SPY": {"rsi_period": 21, "upper_band": 58, "lower_band": 42},
    "QQQ": {"rsi_period": 21, "upper_band": 60, "lower_band": 40},
    "IWM": {"rsi_period": 28, "upper_band": 65, "lower_band": 35},
    "GLD": {"rsi_period": 21, "upper_band": 65, "lower_band": 35},
}

daily_results = []
for symbol, config in DAILY_CONFIGS.items():
    print(f"\n{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
    result = run_daily_trend(symbol, config, LOOKBACK_START, TEST_START, TEST_END)
    if result:
        print(f"  ✓ Return: {result['return_pct']:+.2f}% | Trades: {result['trades']} | Days in market: {result['days_in_market']}/{result['total_days']}")
        daily_results.append({'Symbol': symbol, **result})
    else:
        print(f"  ✗ No data")

# ===============================================================================
# STRATEGY 2: HOURLY SWING
# ===============================================================================
print("\n" + "="*80)
print("STRATEGY 2: HOURLY SWING (1-Hour Bars)")
print("="*80)

HOURLY_CONFIGS = {
    "TSLA": {"rsi_period": 14, "upper_band": 60, "lower_band": 40},
    "NVDA": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
}

def run_hourly_swing(symbol, config, lookback_start, test_start, test_end):
    """Hourly RSI with lookback"""
    try:
        df = cache.get_or_fetch_equity(symbol, '1hour', lookback_start, test_end)
        if df is None or len(df) < 100:
            return None
        
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            if pd.isna(rsi_val):
                signals.append(position)
                continue
            
            if position == 0:
                if rsi_val > config['upper_band']:
                    position = 1
            elif position == 1:
                if rsi_val < config['lower_band']:
                    position = 0
            
            signals.append(position)
        
        df['signal'] = signals
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        df_test = df[df.index >= test_start].copy()
        
        trades = (df_test['signal'].diff() != 0).sum()
        friction = trades * 0.0005  # 5 bps for hourly (tighter spreads)
        total_return = (1 + df_test['strategy_returns']).prod() - 1 - friction
        
        return {
            'return_pct': total_return * 100,
            'trades': trades,
        }
    except Exception as e:
        print(f"  Error: {e}")
        return None

hourly_results = []
for symbol, config in HOURLY_CONFIGS.items():
    print(f"\n{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
    result = run_hourly_swing(symbol, config, LOOKBACK_START, TEST_START, TEST_END)
    if result:
        print(f"  ✓ Return: {result['return_pct']:+.2f}% | Trades: {result['trades']}")
        hourly_results.append({'Symbol': symbol, **result})
    else:
        print(f"  ✗ No data")

# ===============================================================================
# STRATEGY 5: BEAR TRAP
# ===============================================================================
print("\n" + "="*80)
print("STRATEGY 5: BEAR TRAP (1-Minute Intraday)")
print("="*80)

BEAR_TRAP_SYMBOLS = ['MULN', 'ONDS', 'NKLA', 'AMC', 'SENS', 'ACB', 'GOEV', 'BTCS', 'WKHS']

bear_trap_results = []
for symbol in BEAR_TRAP_SYMBOLS:
    try:
        result = run_bear_trap(symbol, TEST_START, TEST_END, initial_capital=100000)
        if result and result['total_trades'] > 0:
            bear_trap_results.append(result)
    except Exception as e:
        print(f"{symbol}: Error - {e}")

# ===============================================================================
# SUMMARY
# ===============================================================================
print("\n" + "="*80)
print("DECEMBER 2024 SIMULATION RESULTS")
print("="*80)

if daily_results:
    print("\n[Strategy 1] Daily Trend Hysteresis:")
    df_daily = pd.DataFrame(daily_results)
    print(df_daily[['Symbol', 'return_pct', 'trades']].to_string(index=False))
    print(f"\n  Portfolio Return (equal weight): {df_daily['return_pct'].mean():+.2f}%")
    print(f"  Total Trades: {df_daily['trades'].sum()}")

if hourly_results:
    print("\n[Strategy 2] Hourly Swing:")
    df_hourly = pd.DataFrame(hourly_results)
    print(df_hourly[['Symbol', 'return_pct', 'trades']].to_string(index=False))
    print(f"\n  Portfolio Return (equal weight): {df_hourly['return_pct'].mean():+.2f}%")

if bear_trap_results:
    print("\n[Strategy 5] Bear Trap (Intraday Small-Caps):")
    df_bear = pd.DataFrame(bear_trap_results)[['symbol', 'total_trades', 'win_rate', 'total_pnl_pct']]
    df_bear.columns = ['Symbol', 'Trades', 'Win%', 'Return%']
    print(df_bear.to_string(index=False))
    print(f"\n  Portfolio Return: {df_bear['Return%'].sum():+.2f}%")
    print(f"  Total Trades: {df_bear['Trades'].sum()}")
    print(f"  Avg Win Rate: {df_bear['Win%'].mean():.1f}%")

print("\n" + "="*80)
print("Notes:")
print("  - Daily/Hourly strategies use 2-month lookback for RSI calculation")
print("  - Returns shown are for December 2024 only")
print("  - Bear Trap is intraday only (no overnight risk)")
print("  - GSB (futures) and Options strategies require additional setup")
print("="*80)
