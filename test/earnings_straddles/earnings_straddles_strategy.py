"""
Walk-Forward Analysis for Earnings Straddles Strategy

Purpose: Validate earnings straddles strategy across multiple years.
Tests NVDA earnings from 2020-2025.

Note: This is simpler than premium selling WFA because:
- No parameter optimization needed (fixed 2-day entry, 1-day exit)
- Just testing consistency across earnings events
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("=" * 80)
print("WALK-FORWARD ANALYSIS - EARNINGS STRADDLES STRATEGY")
print("=" * 80)
print("\nObjective: Validate earnings straddles consistency across years")
print("Strategy: Buy ATM straddle 2 days before earnings, exit 1 day after\n")

# NVDA earnings dates (2020-2025)
# Source: NVDA investor relations
NVDA_EARNINGS = {
    2020: ["2020-02-13", "2020-05-21", "2020-08-19", "2020-11-18"],
    2021: ["2021-02-24", "2021-05-26", "2021-08-18", "2021-11-17"],
    2022: ["2022-02-16", "2022-05-25", "2022-08-24", "2022-11-16"],
    2023: ["2023-02-22", "2023-05-24", "2023-08-23", "2023-11-21"],
    2024: ["2024-02-21", "2024-05-22", "2024-08-28", "2024-11-20"],
    2025: ["2025-02-26", "2025-05-28", "2025-08-27", "2025-11-19"],
}

# Flatten to list
all_earnings = []
for year, dates in NVDA_EARNINGS.items():
    for date in dates:
        all_earnings.append({"date": pd.to_datetime(date), "year": year})

earnings_df = pd.DataFrame(all_earnings)

print(f"Testing {len(earnings_df)} NVDA earnings events (2020-2025)\n")

# Fetch NVDA price data
print("[1/3] Fetching NVDA price data...")
alpaca = AlpacaDataClient()
price_df = alpaca.fetch_historical_bars("NVDA", "1Day", "2020-01-01", "2025-12-31")
print(f"✓ Fetched {len(price_df)} daily bars\n")

# Simulate earnings straddles
print("[2/3] Simulating earnings straddles...")

INITIAL_CAPITAL = 100000
r = 0.04
sigma = 0.40  # NVDA IV

results_by_year = {}
all_trades = []

for year in range(2020, 2026):
    year_earnings = earnings_df[earnings_df["year"] == year]

    if len(year_earnings) == 0:
        continue

    cash = INITIAL_CAPITAL
    year_trades = []

    for idx, earnings_row in year_earnings.iterrows():
        earnings_date = earnings_row["date"]

        # Entry: 2 days before
        entry_date = earnings_date - timedelta(days=2)
        exit_date = earnings_date + timedelta(days=1)

        # Find closest trading days
        entry_price_data = price_df[price_df.index <= entry_date]
        if len(entry_price_data) == 0:
            continue
        entry_date_actual = entry_price_data.index[-1]
        entry_price = entry_price_data.iloc[-1]["close"]

        exit_price_data = price_df[price_df.index >= exit_date]
        if len(exit_price_data) == 0:
            continue
        exit_date_actual = exit_price_data.index[0]
        exit_price = exit_price_data.iloc[0]["close"]

        # Calculate straddle
        strike = round(entry_price / 5) * 5
        T_entry = 7 / 365.0

        # Call + Put
        call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type="call"
        )

        put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type="put"
        )

        # Buy both
        call_entry_price = call_greeks["price"] * 1.01
        put_entry_price = put_greeks["price"] * 1.01

        contracts = max(1, int(5000 / (entry_price * 0.5)))

        straddle_cost = (call_entry_price + put_entry_price) * contracts * 100
        fees = 0.097 * contracts * 2
        total_cost = straddle_cost + fees

        if total_cost > cash:
            continue

        # Exit
        hold_days = (exit_date_actual - entry_date_actual).days
        T_exit = max((7 - hold_days) / 365.0, 0.001)

        call_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type="call"
        )

        put_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type="put"
        )

        call_exit_price = call_exit_greeks["price"] * 0.99
        put_exit_price = put_exit_greeks["price"] * 0.99

        straddle_proceeds = (call_exit_price + put_exit_price) * contracts * 100
        exit_fees = 0.097 * contracts * 2
        net_proceeds = straddle_proceeds - exit_fees

        pnl = net_proceeds - total_cost
        pnl_pct = (pnl / total_cost) * 100
        price_move_pct = abs((exit_price - entry_price) / entry_price) * 100

        trade = {
            "year": year,
            "earnings_date": earnings_date,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "price_move_pct": price_move_pct,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "hold_days": hold_days,
        }

        year_trades.append(trade)
        all_trades.append(trade)
        cash += pnl

    # Calculate year metrics
    if len(year_trades) > 0:
        trades_df = pd.DataFrame(year_trades)
        total_return = (cash / INITIAL_CAPITAL - 1) * 100
        win_rate = (trades_df["pnl"] > 0).mean() * 100

        # Sharpe
        trade_returns = trades_df["pnl_pct"] / 100
        sharpe = (
            (trade_returns.mean() / trade_returns.std() * np.sqrt(len(year_trades)))
            if trade_returns.std() > 0
            else 0
        )

        results_by_year[year] = {
            "num_trades": len(year_trades),
            "total_return": total_return,
            "sharpe": sharpe,
            "win_rate": win_rate,
            "avg_pnl_pct": trades_df["pnl_pct"].mean(),
            "avg_price_move": trades_df["price_move_pct"].mean(),
        }

print(f"✓ Simulated {len(all_trades)} earnings straddles\n")

# Analysis
print("[3/3] Analyzing results...")

print("\n" + "=" * 80)
print("RESULTS BY YEAR")
print("=" * 80)

for year in sorted(results_by_year.keys()):
    metrics = results_by_year[year]
    print(f"\n{year}:")
    print(f"  Trades: {metrics['num_trades']}")
    print(f"  Return: {metrics['total_return']:+.2f}%")
    print(f"  Sharpe: {metrics['sharpe']:.2f}")
    print(f"  Win Rate: {metrics['win_rate']:.1f}%")
    print(f"  Avg P&L: {metrics['avg_pnl_pct']:+.2f}%")
    print(f"  Avg Price Move: {metrics['avg_price_move']:.2f}%")

# Overall statistics
all_trades_df = pd.DataFrame(all_trades)
overall_return = all_trades_df["pnl"].sum() / INITIAL_CAPITAL * 100
overall_win_rate = (all_trades_df["pnl"] > 0).mean() * 100
overall_sharpe = (
    (
        all_trades_df["pnl_pct"].mean()
        / all_trades_df["pnl_pct"].std()
        * np.sqrt(len(all_trades))
    )
    if all_trades_df["pnl_pct"].std() > 0
    else 0
)

print("\n" + "=" * 80)
print("OVERALL STATISTICS (2020-2025)")
print("=" * 80)

print(f"\n📊 Performance:")
print(f"  Total Trades: {len(all_trades)}")
print(f"  Cumulative Return: {overall_return:+.2f}%")
print(f"  Overall Sharpe: {overall_sharpe:.2f}")
print(f"  Overall Win Rate: {overall_win_rate:.1f}%")
print(f"  Avg P&L per Trade: {all_trades_df['pnl_pct'].mean():+.2f}%")

# Year-to-year consistency
year_sharpes = [metrics["sharpe"] for metrics in results_by_year.values()]
year_returns = [metrics["total_return"] for metrics in results_by_year.values()]
year_win_rates = [metrics["win_rate"] for metrics in results_by_year.values()]

print(f"\n📈 Consistency:")
print(f"  Sharpe Std Dev: {np.std(year_sharpes):.2f} (lower = more consistent)")
print(f"  Return Std Dev: {np.std(year_returns):.2f}%")
print(f"  Win Rate Std Dev: {np.std(year_win_rates):.2f}%")

# Comparison to Phase 2
print(f"\n🎯 Comparison to Phase 2 (2024-2025 only):")
print(f"  Phase 2: 87.5% win rate, ~110%/year return")
print(
    f"  WFA (2020-2025): {overall_win_rate:.1f}% win rate, {overall_return/6:.1f}%/year return"
)

# Save results
output_dir = Path("research/backtests/options/phase3_walk_forward/wfa_results")
all_trades_df.to_csv(output_dir / "earnings_straddles_wfa.csv", index=False)

year_summary = pd.DataFrame(
    [{"year": year, **metrics} for year, metrics in results_by_year.items()]
)
year_summary.to_csv(output_dir / "earnings_straddles_by_year.csv", index=False)

print(f"\n📁 Results saved to: {output_dir}/")

# Recommendation
print("\n" + "=" * 80)
print("RECOMMENDATION")
print("=" * 80)

if overall_sharpe >= 1.0 and overall_win_rate >= 60:
    print("\n✅ EARNINGS STRADDLES ARE ROBUST")
    print("   Strategy works consistently across years")
    print("   Deploy with confidence")
elif overall_sharpe >= 0.5:
    print("\n⚠️  EARNINGS STRADDLES ARE MODERATELY ROBUST")
    print("   Consider selective deployment or parameter tuning")
else:
    print("\n❌ EARNINGS STRADDLES ARE NOT ROBUST")
    print("   Do NOT deploy - requires further research")

print("\n" + "=" * 80)
