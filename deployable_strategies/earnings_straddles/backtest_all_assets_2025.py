"""
Earnings Straddles - All Assets Backtest 2025
Tests all 11 configured tickers with $100,000 starting capital per event

Tickers: AAPL, AMD, AMZN, COIN, GOOGL, META, MSFT, NFLX, NVDA, PLTR, TSLA
Strategy: Buy ATM straddle 2 days before earnings, exit 1 day after
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[2]
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("=" * 90)
print("EARNINGS STRADDLES - ALL ASSETS BACKTEST 2025")
print("=" * 90)
print("Testing all 11 configured tickers with $100,000 starting capital per event")
print("Strategy: 3-day hold ATM straddle (T-2 to T+1)\n")

# Earnings dates for 2025 (approximate - quarterly earnings)
# Note: These are estimates - verify actual dates before trading
EARNINGS_2025 = {
    "GOOGL": ["2025-01-28", "2025-04-24", "2025-07-24", "2025-10-28"],
    "AAPL": ["2025-01-30", "2025-04-30", "2025-07-31", "2025-10-30"],
    "AMD": ["2025-01-28", "2025-04-29", "2025-07-29", "2025-10-28"],
    "NVDA": ["2025-02-26", "2025-05-28", "2025-08-27", "2025-11-19"],
    "TSLA": ["2025-01-29", "2025-04-23", "2025-07-23", "2025-10-22"],
    "MSFT": ["2025-01-28", "2025-04-24", "2025-07-29", "2025-10-28"],
    "AMZN": ["2025-01-30", "2025-04-29", "2025-07-31", "2025-10-30"],
    "META": ["2025-01-29", "2025-04-23", "2025-07-30", "2025-10-29"],
    "NFLX": ["2025-01-21", "2025-04-17", "2025-07-17", "2025-10-16"],
    "COIN": ["2025-02-13", "2025-05-08", "2025-08-07", "2025-11-06"],
    "PLTR": ["2025-02-03", "2025-05-05", "2025-08-04", "2025-11-03"],
}

# Get all tickers from assets directory
assets_dir = Path(__file__).parent / "assets"
all_tickers = [d.name for d in assets_dir.iterdir() if d.is_dir()]
print(f"Found {len(all_tickers)} tickers in assets directory: {', '.join(sorted(all_tickers))}\n")

# Filter to only tickers with 2025 earnings data
tickers_to_test = [t for t in all_tickers if t in EARNINGS_2025]
print(f"Testing {len(tickers_to_test)} tickers with 2025 earnings dates: {', '.join(sorted(tickers_to_test))}\n")

total_events = sum(len(dates) for ticker, dates in EARNINGS_2025.items() if ticker in tickers_to_test)
print(f"Total earnings events to simulate: {total_events}\n")

# Fetch price data
print("[1/3] Fetching price data...")
alpaca = AlpacaDataClient()

price_data = {}
for ticker in sorted(tickers_to_test):
    print(f"  Fetching {ticker}...", end="")
    try:
        df = alpaca.fetch_historical_bars(ticker, "1Day", "2025-01-01", "2025-12-31", feed="sip")
        price_data[ticker] = df
        print(f" ✓ {len(df)} daily bars")
    except Exception as e:
        print(f" ❌ Error: {e}")

print()

# Simulate earnings straddles
print("[2/3] Simulating earnings straddles...")

INITIAL_CAPITAL = 100000  # $100k per event
r = 0.04  # Risk-free rate

# IV estimates by ticker
IV_BY_TICKER = {
    "GOOGL": 0.25,
    "AAPL": 0.22,
    "AMD": 0.40,
    "NVDA": 0.45,
    "TSLA": 0.50,
    "MSFT": 0.23,
    "AMZN": 0.28,
    "META": 0.32,
    "NFLX": 0.35,
    "COIN": 0.60,
    "PLTR": 0.45,
}

all_trades = []
results_by_ticker = {}

for ticker in sorted(tickers_to_test):
    if ticker not in price_data:
        continue

    print(f"\n{ticker}:")
    ticker_trades = []
    sigma = IV_BY_TICKER.get(ticker, 0.35)

    for earnings_date_str in EARNINGS_2025[ticker]:
        earnings_date = pd.to_datetime(earnings_date_str)

        # Entry: 2 days before
        entry_date = earnings_date - timedelta(days=2)
        exit_date = earnings_date + timedelta(days=1)

        # Find closest trading days
        entry_price_data = price_data[ticker][price_data[ticker].index <= entry_date]
        if len(entry_price_data) == 0:
            print(f"  ⚠️  {earnings_date.date()}: No entry data (future date)")
            continue
        entry_date_actual = entry_price_data.index[-1]
        entry_price = entry_price_data.iloc[-1]["close"]

        exit_price_data = price_data[ticker][price_data[ticker].index >= exit_date]
        if len(exit_price_data) == 0:
            print(f"  ⚠️  {earnings_date.date()}: No exit data (future date)")
            continue
        exit_date_actual = exit_price_data.index[0]
        exit_price = exit_price_data.iloc[0]["close"]

        # Calculate straddle P&L using Black-Scholes
        strike = round(entry_price / 5) * 5  # Round to nearest $5
        T_entry = 7 / 365.0  # 7 days to expiration

        # Entry: Buy Call + Put
        call_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type="call"
        )

        put_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=entry_price, K=strike, T=T_entry, r=r, sigma=sigma, option_type="put"
        )

        # Add 1% slippage for entry
        call_entry_price = call_greeks["price"] * 1.01
        put_entry_price = put_greeks["price"] * 1.01

        # Position size: use full capital / straddle cost
        straddle_price_per_contract = (call_entry_price + put_entry_price) * 100
        contracts = max(1, int(INITIAL_CAPITAL / straddle_price_per_contract))

        straddle_cost = straddle_price_per_contract * contracts
        fees = 0.65 * contracts * 2  # $0.65 per contract
        total_cost = straddle_cost + fees

        # Exit: Sell Call + Put
        hold_days = (exit_date_actual - entry_date_actual).days
        T_exit = max((7 - hold_days) / 365.0, 0.001)

        call_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type="call"
        )

        put_exit_greeks = OptionsFeatureEngineer.calculate_black_scholes_greeks(
            S=exit_price, K=strike, T=T_exit, r=r, sigma=sigma, option_type="put"
        )

        # Subtract 1% slippage for exit
        call_exit_price = call_exit_greeks["price"] * 0.99
        put_exit_price = put_exit_greeks["price"] * 0.99

        straddle_proceeds = (call_exit_price + put_exit_price) * contracts * 100
        exit_fees = 0.65 * contracts * 2
        net_proceeds = straddle_proceeds - exit_fees

        # Calculate P&L
        pnl = net_proceeds - total_cost
        pnl_pct = (pnl / total_cost) * 100
        price_move_pct = abs((exit_price - entry_price) / entry_price) * 100

        trade = {
            "ticker": ticker,
            "earnings_date": earnings_date.date(),
            "entry_date": entry_date_actual.date(),
            "exit_date": exit_date_actual.date(),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "price_move_pct": price_move_pct,
            "contracts": contracts,
            "cost": total_cost,
            "proceeds": net_proceeds,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "hold_days": hold_days,
            "win": pnl > 0,
        }

        ticker_trades.append(trade)
        all_trades.append(trade)

        win_symbol = "✅" if trade["win"] else "❌"
        print(
            f"  {earnings_date.date()} | ${entry_price:.2f} → ${exit_price:.2f} ({price_move_pct:+.1f}%) | "
            f"{contracts}x | 💰 ${pnl:+,.0f} ({pnl_pct:+.1f}%) {win_symbol}"
        )

    # Calculate ticker metrics
    if len(ticker_trades) > 0:
        ticker_df = pd.DataFrame(ticker_trades)
        win_rate = (ticker_df["pnl"] > 0).mean() * 100
        avg_pnl = ticker_df["pnl"].mean()
        total_pnl = ticker_df["pnl"].sum()

        # Sharpe
        trade_returns = ticker_df["pnl_pct"] / 100
        sharpe = (
            (trade_returns.mean() / trade_returns.std() * np.sqrt(len(ticker_trades))) if trade_returns.std() > 0 else 0
        )

        results_by_ticker[ticker] = {
            "trades": len(ticker_trades),
            "win_rate": win_rate,
            "avg_pnl": avg_pnl,
            "total_pnl": total_pnl,
            "sharpe": sharpe,
            "best_trade": ticker_df["pnl"].max(),
            "worst_trade": ticker_df["pnl"].min(),
        }

        print(
            f"  {ticker} Summary: {len(ticker_trades)} trades | Win Rate: {win_rate:.1f}% | "
            f"Total P&L: ${total_pnl:+,.0f} | Sharpe: {sharpe:.2f}"
        )

print(f"\n✓ Simulated {len(all_trades)} earnings events\n")

# Calculate overall metrics
print("[3/3] Analyzing results...")

if len(all_trades) == 0:
    print("\n❌ No trades executed (all earnings dates are in the future)")
    print("   This backtest is for 2025 data - most earnings haven't occurred yet")
    sys.exit(0)

trades_df = pd.DataFrame(all_trades)

# Overall metrics
total_capital_deployed = len(all_trades) * INITIAL_CAPITAL
total_pnl = trades_df["pnl"].sum()
win_rate = (trades_df["pnl"] > 0).mean() * 100
avg_pnl = trades_df["pnl"].mean()

# Sharpe ratio
trade_returns = trades_df["pnl_pct"] / 100
sharpe = (trade_returns.mean() / trade_returns.std() * np.sqrt(len(all_trades))) if trade_returns.std() > 0 else 0

# Print results by ticker
print("\n" + "=" * 90)
print("RESULTS BY TICKER")
print("=" * 90)

print(
    f"\n{'Ticker':<8} | {'Trades':>6} | {'Win%':>5} | {'Avg P&L':>12} | {'Total P&L':>14} | {'Sharpe':>6} | {'Status':>8}"
)
print("-" * 90)

for ticker in sorted(results_by_ticker.keys()):
    r = results_by_ticker[ticker]
    status = "✅" if r["total_pnl"] > 0 else "❌"
    print(
        f"{ticker:<8} | {r['trades']:6d} | {r['win_rate']:5.1f}% | ${r['avg_pnl']:>11,.0f} | "
        f"${r['total_pnl']:>13,.0f} | {r['sharpe']:6.2f} | {status:>8}"
    )

# Overall portfolio
print("\n" + "=" * 90)
print("OVERALL PORTFOLIO METRICS (2025)")
print("=" * 90)

print(f"\n📊 Performance:")
print(f"  Total Events:     {len(all_trades)}")
print(f"  Starting Capital: ${INITIAL_CAPITAL:,.0f} per event")
print(f"  Capital Deployed: ${total_capital_deployed:,.0f}")
print(f"  Win Rate:         {win_rate:.1f}% ({int(win_rate/100 * len(all_trades))}/{len(all_trades)} wins)")
print(f"  Best Trade:       ${trades_df['pnl'].max():+,.0f} ({trades_df['pnl_pct'].max():+.1f}%)")
print(f"  Worst Trade:      ${trades_df['pnl'].min():+,.0f} ({trades_df['pnl_pct'].min():+.1f}%)")

print(f"\n💰 PROFIT & LOSS:")
print(f"  Total P&L:        ${total_pnl:+,.0f}")
print(f"  Average per Event:${avg_pnl:+,.0f}")
print(f"  Total Return:     {(total_pnl/total_capital_deployed)*100:+.1f}%")

print(f"\n📈 Risk-Adjusted:")
print(f"  Portfolio Sharpe: {sharpe:.2f}")
print(f"  Std Dev:          {trades_df['pnl_pct'].std():.2f}%")

# Save results
output_dir = Path(__file__).parent
trades_df.to_csv(output_dir / "earnings_2025_all_assets_trades.csv", index=False)
summary_df = pd.DataFrame(results_by_ticker).T
summary_df.to_csv(output_dir / "earnings_2025_all_assets_summary.csv")

print(f"\n📁 Results saved:")
print(f"  - {output_dir / 'earnings_2025_all_assets_trades.csv'}")
print(f"  - {output_dir / 'earnings_2025_all_assets_summary.csv'}")

# Verdict
print("\n" + "=" * 90)
print("DEPLOYMENT RECOMMENDATIONS")
print("=" * 90)

if len(results_by_ticker) > 0:
    # Rank by total P&L
    ranked = sorted(results_by_ticker.items(), key=lambda x: x[1]["total_pnl"], reverse=True)

    print("\n🟢 Top Performers (Deploy First):")
    for ticker, r in ranked[:3]:
        if r["total_pnl"] > 0:
            print(
                f"  {ticker}: ${r['total_pnl']:+,.0f} total P&L | {r['win_rate']:.1f}% win rate | Sharpe {r['sharpe']:.2f}"
            )

    print("\n🟡 Medium Performers (Paper Trade First):")
    for ticker, r in ranked[3:6]:
        print(
            f"  {ticker}: ${r['total_pnl']:+,.0f} total P&L | {r['win_rate']:.1f}% win rate | Sharpe {r['sharpe']:.2f}"
        )

    if len(ranked) > 6:
        print("\n⚪ Lower Performers (Monitor or Skip):")
        for ticker, r in ranked[6:]:
            print(
                f"  {ticker}: ${r['total_pnl']:+,.0f} total P&L | {r['win_rate']:.1f}% win rate | Sharpe {r['sharpe']:.2f}"
            )

print("\n" + "=" * 90)
print("✅ Analysis complete!")
print("=" * 90)
