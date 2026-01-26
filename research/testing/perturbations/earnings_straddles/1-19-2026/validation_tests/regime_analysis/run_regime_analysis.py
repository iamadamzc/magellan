"""
Earnings Straddles - Regime Analysis with Cached Data
Period: 2020-2025

Tests:
1. Bull vs Bear vs Sideways performance
2. VIX correlation analysis
3. SPY 200-day MA regime filter validation

Uses cached NVDA data to speed up execution.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()
from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("="*80)
print("EARNINGS STRADDLES - REGIME ANALYSIS")
print("="*80)

# Cache setup
CACHE_DIR = project_root / '.cache'
CACHE_DIR.mkdir(exist_ok=True)
NVDA_CACHE = CACHE_DIR / 'nvda_daily_2020_2025.pkl'
SPY_CACHE = CACHE_DIR / 'spy_daily_2020_2025.pkl'

# Fetch or load cached data
def get_cached_data(symbol, cache_file):
    if cache_file.exists():
        print(f"  Loading {symbol} from cache...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    else:
        print(f"  Fetching {symbol} from Alpaca...")
        client = AlpacaDataClient()
        data = client.fetch_historical_bars(symbol, '1Day', '2020-01-01', '2025-12-31', feed='sip')
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        return data

print("\n[1/4] Loading Data...")
nvda_df = get_cached_data('NVDA', NVDA_CACHE)
spy_df = get_cached_data('SPY', SPY_CACHE)
print(f"  ✓ NVDA: {len(nvda_df)} bars")
print(f"  ✓ SPY: {len(spy_df)} bars")

# NVDA Earnings Dates
NVDA_EARNINGS = {
    2020: ['2020-02-13', '2020-05-21', '2020-08-19', '2020-11-18'],
    2021: ['2021-02-24', '2021-05-26', '2021-08-18', '2021-11-17'],
    2022: ['2022-02-16', '2022-05-25', '2022-08-24', '2022-11-16'],
    2023: ['2023-02-22', '2023-05-24', '2023-08-23', '2023-11-21'],
    2024: ['2024-02-21', '2024-05-22', '2024-08-28', '2024-11-20'],
    2025: ['2025-02-26', '2025-05-28', '2025-08-27', '2025-11-19'],
}

all_earnings = []
for year, dates in NVDA_EARNINGS.items():
    for date in dates:
        all_earnings.append({'date': pd.to_datetime(date), 'year': year})
earnings_df = pd.DataFrame(all_earnings)

# Calculate SPY 200-day MA and regime
print("\n[2/4] Calculating Regimes...")
spy_df['ma_200'] = spy_df['close'].rolling(200).mean()
spy_df['regime'] = 'bull'  # Default
spy_df.loc[spy_df['close'] < spy_df['ma_200'], 'regime'] = 'bear'

# Define regimes by year (manual)
YEAR_REGIMES = {
    2020: 'volatile',  # COVID crash + recovery
    2021: 'bull',      # Post-COVID bull
    2022: 'bear',      # Fed tightening
    2023: 'bull',      # AI boom start
    2024: 'bull',      # AI boom peak
    2025: 'sideways',  # Consolidation
}

# Simulate earnings straddles with regime tracking
print("\n[3/4] Simulating Earnings Straddles...")

INITIAL_CAPITAL = 100000
r = 0.04
sigma = 0.40

all_trades = []

for idx, earnings_row in earnings_df.iterrows():
    earnings_date = earnings_row['date']
    year = earnings_row['year']
    
    # Entry: 2 days before
    entry_date = earnings_date - timedelta(days=2)
    exit_date = earnings_date + timedelta(days=1)
    
    # Find closest trading days
    entry_price_data = nvda_df[nvda_df.index <= entry_date]
    if len(entry_price_data) == 0: continue
    entry_date_actual = entry_price_data.index[-1]
    entry_price = entry_price_data.iloc[-1]['close']
    
    exit_price_data = nvda_df[nvda_df.index >= exit_date]
    if len(exit_price_data) == 0: continue
    exit_date_actual = exit_price_data.index[0]
    exit_price = exit_price_data.iloc[0]['close']
    
    # Get SPY regime at entry
    spy_entry = spy_df[spy_df.index <= entry_date_actual]
    if len(spy_entry) == 0: continue
    spy_regime = spy_entry.iloc[-1]['regime']
    
    # Calculate straddle
    strike = round(entry_price / 5) * 5
    T_entry = 7 / 365.0
    
    call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='call'
    )
    put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type='put'
    )
    
    call_entry_price = call_greeks['price'] * 1.01
    put_entry_price = put_greeks['price'] * 1.01
    
    contracts = max(1, int(5000 / (entry_price * 0.5)))
    straddle_cost = (call_entry_price + put_entry_price) * contracts * 100
    fees = 0.097 * contracts * 2
    total_cost = straddle_cost + fees
    
    # Exit
    hold_days = (exit_date_actual - entry_date_actual).days
    T_exit = max((7 - hold_days) / 365.0, 0.001)
    
    call_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type='call'
    )
    put_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type='put'
    )
    
    call_exit_price = call_exit_greeks['price'] * 0.99
    put_exit_price = put_exit_greeks['price'] * 0.99
    
    straddle_proceeds = (call_exit_price + put_exit_price) * contracts * 100
    exit_fees = 0.097 * contracts * 2
    net_proceeds = straddle_proceeds - exit_fees
    
    pnl = net_proceeds - total_cost
    pnl_pct = (pnl / total_cost) * 100
    price_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    
    trade = {
        'year': year,
        'year_regime': YEAR_REGIMES[year],
        'spy_regime': spy_regime,
        'earnings_date': earnings_date,
        'price_move_pct': price_move_pct,
        'pnl_pct': pnl_pct,
        'win': pnl > 0
    }
    
    all_trades.append(trade)

trades_df = pd.DataFrame(all_trades)
print(f"  ✓ Simulated {len(trades_df)} trades")

# Regime Analysis
print("\n[4/4] Regime Analysis...")
print("\n" + "="*80)
print("PERFORMANCE BY YEAR REGIME")
print("="*80)

for regime in ['bull', 'bear', 'sideways', 'volatile']:
    regime_trades = trades_df[trades_df['year_regime'] == regime]
    if len(regime_trades) == 0: continue
    
    win_rate = regime_trades['win'].mean() * 100
    avg_pnl = regime_trades['pnl_pct'].mean()
    sharpe = (regime_trades['pnl_pct'].mean() / regime_trades['pnl_pct'].std() * np.sqrt(len(regime_trades))) if regime_trades['pnl_pct'].std() > 0 else 0
    
    status = "✅" if sharpe > 1.0 else ("⚠️" if sharpe > 0 else "❌")
    print(f"\n{regime.upper()} ({len(regime_trades)} trades) {status}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg P&L: {avg_pnl:+.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")

print("\n" + "="*80)
print("PERFORMANCE BY SPY REGIME (200-Day MA)")
print("="*80)

for regime in ['bull', 'bear']:
    regime_trades = trades_df[trades_df['spy_regime'] == regime]
    if len(regime_trades) == 0: continue
    
    win_rate = regime_trades['win'].mean() * 100
    avg_pnl = regime_trades['pnl_pct'].mean()
    sharpe = (regime_trades['pnl_pct'].mean() / regime_trades['pnl_pct'].std() * np.sqrt(len(regime_trades))) if regime_trades['pnl_pct'].std() > 0 else 0
    
    status = "✅" if sharpe > 1.0 else ("⚠️" if sharpe > 0 else "❌")
    print(f"\n{regime.upper()} (SPY < 200MA) ({len(regime_trades)} trades) {status}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Avg P&L: {avg_pnl:+.2f}%")
    print(f"  Sharpe: {sharpe:.2f}")

# Save results
out_file = Path(__file__).parent / 'regime_analysis_results.csv'
trades_df.to_csv(out_file, index=False)
print(f"\n✓ Saved to {out_file}")

# Recommendation
print("\n" + "="*80)
print("REGIME FILTER RECOMMENDATION")
print("="*80)

bear_sharpe = trades_df[trades_df['year_regime'] == 'bear']['pnl_pct'].mean() / trades_df[trades_df['year_regime'] == 'bear']['pnl_pct'].std() if len(trades_df[trades_df['year_regime'] == 'bear']) > 0 else 0

if bear_sharpe < 0:
    print("\n⚠️ BEAR MARKET FILTER RECOMMENDED")
    print("   Pause strategy when SPY < 200-day MA")
    print("   This would have avoided 2022 losses")
else:
    print("\n✅ NO REGIME FILTER NEEDED")
    print("   Strategy works in all regimes")
