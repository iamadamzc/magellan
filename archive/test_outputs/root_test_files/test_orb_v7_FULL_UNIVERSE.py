"""
ORB V7 - COMPREHENSIVE UNIVERSE TEST
=====================================
Test on EVERYTHING: equities, crypto, futures, commodities, ETFs, indices

This will take a while. Grab coffee.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7
from research.new_strategy_builds.strategies.orb_v7_futures import run_orb_v7_futures

# ============================================================================
# UNIVERSE DEFINITION
# ============================================================================

# CRYPTO STOCKS (High Beta)
crypto_stocks = [
    'RIOT', 'MARA', 'CLSK', 'HUT', 'BITF', 'CIFR', 'IREN',
    'COIN', 'MSTR', 'SQ', 'HOOD'
]

# TECH LARGE CAPS
tech_large = [
    'NVDA', 'TSLA', 'AMD', 'AAPL', 'MSFT', 'GOOGL', 'META', 
    'AMZN', 'NFLX', 'AVGO', 'CRM', 'ORCL', 'ADBE'
]

# MEME/HIGH BETA STOCKS
meme_stocks = [
    'GME', 'AMC', 'BBBY', 'PLTR', 'SOFI', 'NIO', 'LCID', 'RIVN'
]

# SMALL CAP MOVERS
small_caps = [
    'JCSE', 'LCFY', 'CTMX', 'IBRX', 'CGTL', 'TNMG', 'VERO', 
    'TYGO', 'NEOV', 'BIYA', 'RIOX'
]

# ENERGY
energy = [
    'XOM', 'CVX', 'COP', 'SLB', 'MPC', 'PSX', 'VLO', 'OXY'
]

# FINANCIALS
financials = [
    'JPM', 'BAC', 'GS', 'MS', 'WFC', 'C', 'BLK', 'SCHW'
]

# ETFS - INDICES
etf_indices = [
    'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'EFA', 'EEM'
]

# ETFS - SECTOR
etf_sectors = [
    'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLB'
]

# ETFS - VOLATILITY
etf_vol = [
    'VXX', 'UVXY', 'SVXY', 'VIXY'
]

# FUTURES - INDICES
futures_indices = [
    'ES', 'NQ', 'YM', 'RTY'  # S&P, Nasdaq, Dow, Russell
]

# FUTURES - COMMODITIES
futures_commodities = [
    'GC', 'SI', 'HG', 'PL',  # Metals: Gold, Silver, Copper, Platinum
    'CL', 'NG', 'RB', 'HO',  # Energy: Crude, Nat Gas, RBOB, Heating Oil
    'ZC', 'ZS', 'ZW', 'ZL',  # Ags: Corn, Soybeans, Wheat, Soy Oil
    'KC', 'SB', 'CC', 'CT',  # Softs: Coffee, Sugar, Cocoa, Cotton
    'LE', 'GF', 'HE'         # Livestock: Live Cattle, Feeder, Lean Hogs
]

# FUTURES - RATES
futures_rates = [
    'ZN', 'ZB', 'ZF', 'ZT', 'ZQ'  # 10Y, 30Y, 5Y, 2Y, 30D
]

# FUTURES - FX
futures_fx = [
    '6E', '6J', '6B', '6C', '6A', '6S'  # EUR, JPY, GBP, CAD, AUD, CHF
]

# ============================================================================
# BATCH TEST FUNCTION
# ============================================================================

def test_universe_class(symbols, name, is_futures=False):
    """Test a class of symbols"""
    print(f"\n{'='*80}")
    print(f"Testing {name} ({len(symbols)} symbols)")
    print(f"{'='*80}")
    
    results = []
    for symbol in symbols:
        try:
            if is_futures:
                result = run_orb_v7_futures(symbol, '2024-11-01', '2025-01-17', '1hour')
            else:
                result = run_orb_v7(symbol, '2024-11-01', '2025-01-17')
            
            if result['total_trades'] > 0:
                results.append(result)
        except Exception as e:
            print(f"✗ {symbol}: {str(e)[:50]}")
    
    if results:
        df = pd.DataFrame(results)
        df['asset_class'] = name
        
        # Show top performers
        top = df.nlargest(3, 'total_pnl')
        if len(top) > 0:
            print(f"\n{'='*80}")
            print(f"{name} - TOP PERFORMERS")
            print(f"{'='*80}")
            print(top[['symbol', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
        
        return df
    else:
        print(f"⚠️  No valid results for {name}")
        return pd.DataFrame()

# ============================================================================
# RUN TESTS
# ============================================================================

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    ORB V7 - FULL UNIVERSE SCAN                             ║
║                                                                            ║
║  Testing on 100+ symbols across all asset classes                         ║
║  Period: Nov 1, 2024 - Jan 17, 2025                                       ║
║                                                                            ║
║  This will take 10-15 minutes. Results will be aggregated at the end.     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

all_results = []

# Test each class
all_results.append(test_universe_class(crypto_stocks, "CRYPTO STOCKS", False))
all_results.append(test_universe_class(tech_large, "TECH LARGE CAPS", False))
all_results.append(test_universe_class(meme_stocks, "MEME/HIGH BETA", False))
all_results.append(test_universe_class(small_caps, "SMALL CAPS", False))
all_results.append(test_universe_class(energy, "ENERGY", False))
all_results.append(test_universe_class(financials, "FINANCIALS", False))
all_results.append(test_universe_class(etf_indices, "ETF - INDICES", False))
all_results.append(test_universe_class(etf_sectors, "ETF - SECTORS", False))
all_results.append(test_universe_class(etf_vol, "ETF - VOLATILITY", False))
all_results.append(test_universe_class(futures_indices, "FUTURES - INDICES", True))
all_results.append(test_universe_class(futures_commodities, "FUTURES - COMMODITIES", True))
all_results.append(test_universe_class(futures_rates, "FUTURES - RATES", True))
all_results.append(test_universe_class(futures_fx, "FUTURES - FX", True))

# ============================================================================
# AGGREGATE RESULTS
# ============================================================================

# Combine all results
combined = pd.concat([r for r in all_results if len(r) > 0], ignore_index=True)

if len(combined) > 0:
    print(f"\n\n{'='*80}")
    print(f"{'='*80}")
    print(f"FINAL RESULTS - ALL ASSET CLASSES")
    print(f"{'='*80}")
    print(f"{'='*80}\n")
    
    # Overall stats
    total_symbols = len(combined)
    total_trades = combined['total_trades'].sum()
    profitable = combined[combined['total_pnl'] > 0]
    
    print(f"📊 OVERVIEW")
    print(f"  Symbols tested: {total_symbols}")
    print(f"  Total trades: {total_trades}")
    print(f"  Profitable symbols: {len(profitable)} ({len(profitable)/total_symbols*100:.1f}%)")
    print(f"  Aggregate P&L: {combined['total_pnl'].sum():+.2f}%")
    
    # Top 10 winners
    print(f"\n{'='*80}")
    print(f"🏆 TOP 10 WINNERS")
    print(f"{'='*80}")
    top10 = combined.nlargest(10, 'total_pnl')
    print(top10[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
    
    # Bottom 10 losers
    print(f"\n{'='*80}")
    print(f"💀 BOTTOM 10 LOSERS")
    print(f"{'='*80}")
    bottom10 = combined.nsmallest(10, 'total_pnl')
    print(bottom10[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
    
    # By asset class
    print(f"\n{'='*80}")
    print(f"📈 PERFORMANCE BY ASSET CLASS")
    print(f"{'='*80}")
    by_class = combined.groupby('asset_class').agg({
        'total_trades': 'sum',
        'total_pnl': ['sum', 'mean', 'count']
    }).round(2)
    by_class.columns = ['Total Trades', 'Total P&L', 'Avg P&L', 'Count']
    by_class = by_class.sort_values('Total P&L', ascending=False)
    print(by_class)
    
    # Save results
    combined.to_csv('research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv', index=False)
    print(f"\n✅ Results saved to: research/new_strategy_builds/results/ORB_V7_FULL_UNIVERSE.csv")
    
    # Deployment recommendations
    print(f"\n{'='*80}")
    print(f"🚀 DEPLOYMENT CANDIDATES (Win Rate > 55%, Total P&L > 2%)")
    print(f"{'='*80}")
    candidates = combined[(combined['win_rate'] > 55) & (combined['total_pnl'] > 2.0)]
    if len(candidates) > 0:
        print(candidates[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
    else:
        print("No symbols meet deployment criteria")
        print("\nRelaxed criteria (Win Rate > 50%, Total P&L > 0%):")
        relaxed = combined[(combined['win_rate'] > 50) & (combined['total_pnl'] > 0)]
        if len(relaxed) > 0:
            print(relaxed[['symbol', 'asset_class', 'total_trades', 'win_rate', 'avg_pnl', 'total_pnl']].to_string(index=False))
else:
    print("❌ No valid results across all asset classes")

print(f"\n{'='*80}")
print(f"SCAN COMPLETE")
print(f"{'='*80}\n")
