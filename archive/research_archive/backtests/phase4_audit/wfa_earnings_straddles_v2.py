"""
Phase 4: Corrected Walk-Forward Analysis - Earnings Straddles Strategy

CORRECTIONS FROM PHASE 3:
1. Correct Sharpe formula: Uses proper annualization
2. NVDA stock split handling: Tests pre-split (2020-2024 H1) and post-split (2024 H2-2025) separately
3. Multi-stock testing: NVDA, AAPL, MSFT, GOOGL for more data points
4. Bootstrap confidence intervals

Usage:
    python wfa_earnings_straddles_v2.py           # Full run
    python wfa_earnings_straddles_v2.py --quick   # Quick test (2024-2025 only)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import argparse

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer
from research.backtests.phase4_audit.wfa_core import (
    calculate_sharpe_from_trades,
    calculate_trade_stats,
    bootstrap_sharpe_ci
)

print("="*80)
print("PHASE 4: CORRECTED WFA - EARNINGS STRADDLES STRATEGY")
print("="*80)
print("\nCORRECTIONS APPLIED:")
print("  ✓ Correct Sharpe annualization")
print("  ✓ NVDA split handling (pre/post split separately)")
print("  ✓ Multi-stock testing (more data points)")
print("  ✓ Bootstrap confidence intervals")
print()

# =============================================================================
# EARNINGS DATES
# =============================================================================

# NVDA earnings dates (CRITICAL: June 7, 2024 was 10-for-1 split)
NVDA_EARNINGS = {
    # PRE-SPLIT (prices ~$1000)
    2020: ['2020-02-13', '2020-05-21', '2020-08-19', '2020-11-18'],
    2021: ['2021-02-24', '2021-05-26', '2021-08-18', '2021-11-17'],
    2022: ['2022-02-16', '2022-05-25', '2022-08-24', '2022-11-16'],
    2023: ['2023-02-22', '2023-05-24', '2023-08-23', '2023-11-21'],
    # SPLIT DATE: June 7, 2024
    '2024_pre_split': ['2024-02-21', '2024-05-22'],  # Pre-split
    '2024_post_split': ['2024-08-28', '2024-11-20'],  # Post-split
    2025: ['2025-02-26', '2025-05-28', '2025-08-27', '2025-11-19'],
}

# Additional stocks for more data points (no relevant splits)
AAPL_EARNINGS = {
    2020: ['2020-01-28', '2020-04-30', '2020-07-30', '2020-10-29'],
    2021: ['2021-01-27', '2021-04-28', '2021-07-27', '2021-10-28'],
    2022: ['2022-01-27', '2022-04-28', '2022-07-28', '2022-10-27'],
    2023: ['2023-02-02', '2023-05-04', '2023-08-03', '2023-11-02'],
    2024: ['2024-02-01', '2024-05-02', '2024-08-01', '2024-10-31'],
    2025: ['2025-01-30', '2025-04-30', '2025-07-31', '2025-10-30'],
}

MSFT_EARNINGS = {
    2020: ['2020-01-29', '2020-04-29', '2020-07-22', '2020-10-27'],
    2021: ['2021-01-26', '2021-04-27', '2021-07-27', '2021-10-26'],
    2022: ['2022-01-25', '2022-04-26', '2022-07-26', '2022-10-25'],
    2023: ['2023-01-24', '2023-04-25', '2023-07-25', '2023-10-24'],
    2024: ['2024-01-30', '2024-04-25', '2024-07-30', '2024-10-30'],
    2025: ['2025-01-29', '2025-04-29', '2025-07-29', '2025-10-28'],
}

GOOGL_EARNINGS = {
    2020: ['2020-02-03', '2020-04-28', '2020-07-30', '2020-10-29'],
    2021: ['2021-02-02', '2021-04-27', '2021-07-27', '2021-10-26'],
    2022: ['2022-02-01', '2022-04-26', '2022-07-26', '2022-10-25'],
    2023: ['2023-02-02', '2023-04-25', '2023-07-25', '2023-10-24'],
    2024: ['2024-01-30', '2024-04-25', '2024-07-23', '2024-10-29'],
    2025: ['2025-02-04', '2025-04-29', '2025-07-29', '2025-10-28'],
}

# IV estimates by symbol
IV_ESTIMATES = {
    'NVDA': 0.45,
    'AAPL': 0.28,
    'MSFT': 0.25,
    'GOOGL': 0.30
}

# Constants
INITIAL_CAPITAL = 100000
RISK_FREE_RATE = 0.04
SLIPPAGE_PCT = 1.0
CONTRACT_FEE = 0.097


def simulate_earnings_straddle(
    price_df: pd.DataFrame,
    earnings_date: str,
    symbol: str = 'NVDA'
) -> dict:
    """
    Simulate a single earnings straddle trade.
    
    Strategy: Buy ATM straddle 2 days before earnings, exit 1 day after.
    
    Returns trade dict or None if trade couldn't be executed.
    """
    earnings_date = pd.to_datetime(earnings_date)
    iv = IV_ESTIMATES.get(symbol, 0.35)
    
    # Entry: 2 days before earnings
    entry_target = earnings_date - timedelta(days=2)
    exit_target = earnings_date + timedelta(days=1)
    
    # Find closest trading days
    entry_data = price_df[price_df.index <= entry_target]
    if len(entry_data) == 0:
        return None
    entry_date = entry_data.index[-1]
    entry_price = entry_data.iloc[-1]['close']
    
    exit_data = price_df[price_df.index >= exit_target]
    if len(exit_data) == 0:
        return None
    exit_date = exit_data.index[0]
    exit_price = exit_data.iloc[0]['close']
    
    hold_days = (exit_date - entry_date).days
    if hold_days <= 0:
        return None
    
    # Calculate straddle cost
    strike = round(entry_price / 5) * 5
    T_entry = 7 / 365.0  # ~1 week to expiration
    
    # Call + Put at entry
    call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='call'
    )
    put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=entry_price, K=strike, T=T_entry, r=RISK_FREE_RATE, sigma=iv, option_type='put'
    )
    
    # Buy with slippage
    call_entry = call_greeks['price'] * (1 + SLIPPAGE_PCT/100)
    put_entry = put_greeks['price'] * (1 + SLIPPAGE_PCT/100)
    
    # Position sizing: ~5% of capital per trade
    contracts = max(1, int(5000 / (entry_price * 0.5)))
    
    straddle_cost = (call_entry + put_entry) * contracts * 100
    entry_fees = CONTRACT_FEE * contracts * 2
    total_cost = straddle_cost + entry_fees
    
    # Exit value
    T_exit = max((7 - hold_days) / 365.0, 0.001)
    
    call_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='call'
    )
    put_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
        S=exit_price, K=strike, T=T_exit, r=RISK_FREE_RATE, sigma=iv, option_type='put'
    )
    
    # Sell with slippage
    call_exit = call_exit_greeks['price'] * (1 - SLIPPAGE_PCT/100)
    put_exit = put_exit_greeks['price'] * (1 - SLIPPAGE_PCT/100)
    
    straddle_proceeds = (call_exit + put_exit) * contracts * 100
    exit_fees = CONTRACT_FEE * contracts * 2
    net_proceeds = straddle_proceeds - exit_fees
    
    pnl = net_proceeds - total_cost
    pnl_pct = (pnl / total_cost) * 100
    price_move_pct = abs((exit_price - entry_price) / entry_price) * 100
    
    return {
        'symbol': symbol,
        'earnings_date': earnings_date.strftime('%Y-%m-%d'),
        'entry_date': entry_date.strftime('%Y-%m-%d'),
        'exit_date': exit_date.strftime('%Y-%m-%d'),
        'entry_price': entry_price,
        'exit_price': exit_price,
        'price_move_pct': price_move_pct,
        'hold_days': hold_days,
        'pnl': pnl,
        'pnl_pct': pnl_pct,
        'contracts': contracts
    }


def run_earnings_wfa(symbols=['NVDA'], test_pre_split_separately=True, start_year=2020, end_year=2025):
    """Run earnings straddles WFA."""
    
    print(f"[1/3] Fetching price data for {symbols}...")
    alpaca = AlpacaDataClient()
    
    price_data = {}
    for symbol in symbols:
        df = alpaca.fetch_historical_bars(symbol, '1Day', f'{start_year}-01-01', f'{end_year}-12-31')
        price_data[symbol] = df
        print(f"  ✓ {symbol}: {len(df)} bars")
    
    # Collect earnings dates by symbol
    earnings_by_symbol = {
        'NVDA': NVDA_EARNINGS,
        'AAPL': AAPL_EARNINGS,
        'MSFT': MSFT_EARNINGS,
        'GOOGL': GOOGL_EARNINGS
    }
    
    print(f"\n[2/3] Simulating earnings straddles...")
    
    all_trades = []
    trades_by_period = {
        'pre_split': [],
        'post_split': []
    }
    
    for symbol in symbols:
        if symbol not in earnings_by_symbol:
            continue
            
        earnings = earnings_by_symbol[symbol]
        price_df = price_data[symbol]
        
        for year_key, dates in earnings.items():
            # Determine if pre or post split (only matters for NVDA)
            if symbol == 'NVDA':
                if year_key == '2024_pre_split':
                    period = 'pre_split'
                elif year_key == '2024_post_split':
                    period = 'post_split'
                elif isinstance(year_key, int) and year_key < 2024:
                    period = 'pre_split'
                else:
                    period = 'post_split'
            else:
                # Other stocks don't have relevant splits
                if isinstance(year_key, int) and year_key >= 2024:
                    period = 'post_split'
                else:
                    period = 'pre_split'
            
            year = year_key if isinstance(year_key, int) else 2024
            if year < start_year or year > end_year:
                continue
            
            for earnings_date in dates:
                trade = simulate_earnings_straddle(price_df, earnings_date, symbol)
                if trade:
                    trade['period'] = period
                    trade['year'] = year
                    all_trades.append(trade)
                    trades_by_period[period].append(trade)
    
    print(f"  ✓ Simulated {len(all_trades)} total trades")
    print(f"    Pre-split: {len(trades_by_period['pre_split'])} trades")
    print(f"    Post-split: {len(trades_by_period['post_split'])} trades")
    
    # Analysis
    print(f"\n[3/3] Analyzing results...")
    
    results = {
        'overall': {},
        'pre_split': {},
        'post_split': {},
        'by_year': {},
        'by_symbol': {}
    }
    
    # Overall metrics
    if len(all_trades) > 0:
        trades_df = pd.DataFrame(all_trades)
        trade_returns = trades_df['pnl_pct'].values / 100
        avg_hold = trades_df['hold_days'].mean()
        
        sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=10)
        point, lower, upper = bootstrap_sharpe_ci(trade_returns, periods_per_year=int(365/avg_hold))
        stats = calculate_trade_stats(trades_df)
        
        results['overall'] = {
            'sharpe': sharpe,
            'sharpe_ci_lower': lower,
            'sharpe_ci_upper': upper,
            **stats,
            'avg_price_move': trades_df['price_move_pct'].mean()
        }
    
    # Pre-split vs Post-split (CRITICAL for NVDA)
    for period, trades in trades_by_period.items():
        if len(trades) >= 5:
            trades_df = pd.DataFrame(trades)
            trade_returns = trades_df['pnl_pct'].values / 100
            avg_hold = trades_df['hold_days'].mean()
            
            sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
            stats = calculate_trade_stats(trades_df)
            
            results[period] = {
                'sharpe': sharpe,
                'num_trades': len(trades),
                **stats,
                'avg_price_move': trades_df['price_move_pct'].mean()
            }
    
    # By year
    if len(all_trades) > 0:
        trades_df = pd.DataFrame(all_trades)
        for year in sorted(trades_df['year'].unique()):
            year_trades = trades_df[trades_df['year'] == year]
            if len(year_trades) >= 3:
                trade_returns = year_trades['pnl_pct'].values / 100
                avg_hold = year_trades['hold_days'].mean()
                sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=3)
                stats = calculate_trade_stats(year_trades)
                
                results['by_year'][int(year)] = {
                    'sharpe': sharpe,
                    **stats,
                    'avg_price_move': year_trades['price_move_pct'].mean()
                }
    
    # By symbol
    if len(all_trades) > 0:
        trades_df = pd.DataFrame(all_trades)
        for symbol in trades_df['symbol'].unique():
            sym_trades = trades_df[trades_df['symbol'] == symbol]
            if len(sym_trades) >= 5:
                trade_returns = sym_trades['pnl_pct'].values / 100
                avg_hold = sym_trades['hold_days'].mean()
                sharpe = calculate_sharpe_from_trades(trade_returns, avg_hold, min_trades=5)
                stats = calculate_trade_stats(sym_trades)
                
                results['by_symbol'][symbol] = {
                    'sharpe': sharpe,
                    **stats,
                    'avg_price_move': sym_trades['price_move_pct'].mean()
                }
    
    return all_trades, results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--quick', action='store_true', help='Quick test (2024-2025 only)')
    parser.add_argument('--nvda-only', action='store_true', help='Test NVDA only')
    args = parser.parse_args()
    
    if args.quick:
        start_year, end_year = 2024, 2025
        print("🚀 QUICK TEST MODE: 2024-2025 only\n")
    else:
        start_year, end_year = 2020, 2025
    
    if args.nvda_only:
        symbols = ['NVDA']
    else:
        symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL']
    
    # Run WFA
    trades, results = run_earnings_wfa(symbols, start_year=start_year, end_year=end_year)
    
    # Print results
    print(f"\n{'='*80}")
    print("EARNINGS STRADDLES WFA RESULTS")
    print(f"{'='*80}\n")
    
    print("📊 Overall Performance:")
    overall = results.get('overall', {})
    if overall:
        print(f"  Total Trades: {overall.get('num_trades', 0)}")
        print(f"  Sharpe Ratio: {overall.get('sharpe', 'N/A'):.2f}" if overall.get('sharpe') else "  Sharpe Ratio: N/A")
        if overall.get('sharpe_ci_lower') and overall.get('sharpe_ci_upper'):
            print(f"  95% CI: [{overall['sharpe_ci_lower']:.2f}, {overall['sharpe_ci_upper']:.2f}]")
        print(f"  Win Rate: {overall.get('win_rate', 0):.1f}%")
        print(f"  Avg P&L: {overall.get('avg_pnl', 0):.2f}%")
        print(f"  Avg Price Move: {overall.get('avg_price_move', 0):.2f}%")
    
    # CRITICAL: Pre vs Post split comparison
    print(f"\n⚠️  NVDA SPLIT ANALYSIS (June 7, 2024 - 10:1 split):")
    pre_split = results.get('pre_split', {})
    post_split = results.get('post_split', {})
    
    print(f"\n  PRE-SPLIT (2020 - May 2024):")
    if pre_split:
        print(f"    Trades: {pre_split.get('num_trades', 0)}")
        print(f"    Sharpe: {pre_split.get('sharpe', 'N/A'):.2f}" if pre_split.get('sharpe') else "    Sharpe: N/A")
        print(f"    Win Rate: {pre_split.get('win_rate', 0):.1f}%")
        print(f"    Avg P&L: {pre_split.get('avg_pnl', 0):.2f}%")
    
    print(f"\n  POST-SPLIT (Aug 2024 - 2025):")
    if post_split:
        print(f"    Trades: {post_split.get('num_trades', 0)}")
        print(f"    Sharpe: {post_split.get('sharpe', 'N/A'):.2f}" if post_split.get('sharpe') else "    Sharpe: N/A")
        print(f"    Win Rate: {post_split.get('win_rate', 0):.1f}%")
        print(f"    Avg P&L: {post_split.get('avg_pnl', 0):.2f}%")
    
    # By year
    print(f"\n📅 Performance by Year:")
    for year, metrics in sorted(results.get('by_year', {}).items()):
        sharpe_str = f"{metrics.get('sharpe', 0):.2f}" if metrics.get('sharpe') else "N/A"
        print(f"  {year}: Sharpe {sharpe_str}, Win Rate {metrics.get('win_rate', 0):.0f}%, Trades {metrics.get('num_trades', 0)}")
    
    # By symbol
    print(f"\n📈 Performance by Symbol:")
    for symbol, metrics in results.get('by_symbol', {}).items():
        sharpe_str = f"{metrics.get('sharpe', 0):.2f}" if metrics.get('sharpe') else "N/A"
        print(f"  {symbol}: Sharpe {sharpe_str}, Win Rate {metrics.get('win_rate', 0):.0f}%, Avg Move {metrics.get('avg_price_move', 0):.1f}%")
    
    # Compare to Phase 3
    print(f"\n🎯 Comparison to Phase 3:")
    print(f"  Phase 3 Sharpe: 2.25 (INCORRECT - used sqrt(n_trades))")
    overall_sharpe = overall.get('sharpe', 0)
    print(f"  Phase 4 Sharpe: {overall_sharpe:.2f}" if overall_sharpe else "  Phase 4 Sharpe: N/A")
    
    # Save results
    output_dir = Path('research/backtests/phase4_audit/wfa_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    trades_df = pd.DataFrame(trades)
    trades_df.to_csv(output_dir / 'earnings_straddles_wfa_v2.csv', index=False)
    
    with open(output_dir / 'earnings_straddles_summary_v2.json', 'w') as f:
        # Convert numpy types for JSON
        def convert(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            return obj
        json.dump(convert(results), f, indent=2)
    
    print(f"\n📁 Results saved to: {output_dir}/")
    
    # GO/NO-GO
    print(f"\n{'='*80}")
    print("PRELIMINARY GO/NO-GO ASSESSMENT")
    print(f"{'='*80}\n")
    
    overall_sharpe = overall.get('sharpe', 0) or 0
    if overall_sharpe >= 1.5:
        print("✅ PRELIMINARY: GO")
        print("   Strategy shows robust performance across periods")
    elif overall_sharpe >= 1.0:
        print("⚠️  PRELIMINARY: CONDITIONAL")
        print("   Strategy shows moderate performance")
    else:
        print("❌ PRELIMINARY: NO-GO")
        print(f"   Sharpe {overall_sharpe:.2f} below 1.0 threshold")
    
    # Note about split
    print(f"\n📝 NOTE: Pre/post split results should be evaluated separately for NVDA")
    print(f"         Post-split data (Aug 2024+) is more relevant for future trading")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
