"""
Earnings Straddles - Multi-Ticker Portfolio Backtest

Tests the Earnings Straddles strategy on multiple tech stocks to validate
the claimed performance across different tickers.

Strategy:
- Entry: 2 days before earnings announcement
- Position: Buy ATM straddle (1 call + 1 put)
- Exit: 1 day after earnings (3-day total hold)

Tickers to Test:
- GOOGL: Claimed Sharpe 4.80, Win Rate 62.5%
- AAPL: Claimed Sharpe 2.90, Win Rate 54.2%
- AMD: Claimed Sharpe 2.52, Win Rate 58.3%
- NVDA: Claimed Sharpe 2.38, Win Rate 45.8%
- TSLA: Claimed Sharpe 2.00, Win Rate 50.0%
- MSFT: Claimed Sharpe 1.45, Win Rate 50.0%
- AMZN: Claimed Sharpe 1.12, Win Rate 30.0%
- META: Additional test ticker

Test Period: 2024-01-01 to 2024-12-31 (1 year, ~4 earnings per ticker)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os

# Add project root to path
script_path = Path(__file__).resolve()
project_root = script_path.parents[4]
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv

load_dotenv()

from src.data_handler import AlpacaDataClient
from src.options.features import OptionsFeatureEngineer

print("=" * 80)
print("EARNINGS STRADDLES - MULTI-TICKER PORTFOLIO BACKTEST")
print("=" * 80)
print("\nObjective: Validate Earnings Straddles across multiple tech stocks")
print("Strategy: 3-day hold ATM straddle (T-2 to T+1)\n")

# Earnings dates for 2024 (approximate - Q1, Q2, Q3, Q4)
# Source: Company investor relations calendars
EARNINGS_2024 = {
    "GOOGL": [
        "2024-01-30",  # Q4 2023
        "2024-04-25",  # Q1 2024
        "2024-07-23",  # Q2 2024
        "2024-10-29",  # Q3 2024
    ],
    "AAPL": [
        "2024-02-01",  # Q1 2024
        "2024-05-02",  # Q2 2024
        "2024-08-01",  # Q3 2024
        "2024-10-31",  # Q4 2024
    ],
    "AMD": [
        "2024-01-30",  # Q4 2023
        "2024-04-30",  # Q1 2024
        "2024-07-30",  # Q2 2024
        "2024-10-29",  # Q3 2024
    ],
    "NVDA": [
        "2024-02-21",  # Q4 2024
        "2024-05-22",  # Q1 2025
        "2024-08-28",  # Q2 2025
        "2024-11-20",  # Q3 2025
    ],
    "TSLA": [
        "2024-01-24",  # Q4 2023
        "2024-04-23",  # Q1 2024
        "2024-07-23",  # Q2 2024
        "2024-10-23",  # Q3 2024
    ],
    "MSFT": [
        "2024-01-30",  # Q2 2024
        "2024-04-25",  # Q3 2024
        "2024-07-30",  # Q4 2024
        "2024-10-30",  # Q1 2025
    ],
    "AMZN": [
        "2024-02-01",  # Q4 2023
        "2024-04-30",  # Q1 2024
        "2024-08-01",  # Q2 2024
        "2024-10-31",  # Q3 2024
    ],
    "META": [
        "2024-02-01",  # Q4 2023
        "2024-04-24",  # Q1 2024
        "2024-07-31",  # Q2 2024
        "2024-10-30",  # Q3 2024
    ],
}

print(
    f"Testing {sum(len(dates) for dates in EARNINGS_2024.values())} earnings events across {len(EARNINGS_2024)} tickers\n"
)

# Fetch price data for all tickers
print("[1/3] Fetching price data for all tickers...")
alpaca = AlpacaDataClient()

price_data = {}
for ticker in EARNINGS_2024.keys():
    print(f"  Fetching {ticker}...", end="")
    df = alpaca.fetch_historical_bars(ticker, "1Day", "2024-01-01", "2024-12-31", feed="sip")
    price_data[ticker] = df
    print(f" ✓ {len(df)} daily bars")

print()

# Simulate earnings straddles
print("[2/3] Simulating earnings straddles...")

INITIAL_CAPITAL = 10000  # $10k per event
r = 0.04  # Risk-free rate

# IV estimates by ticker (approximate)
IV_BY_TICKER = {
    "GOOGL": 0.25,  # Lower volatility (large cap)
    "AAPL": 0.22,  # Lower volatility (mega cap)
    "AMD": 0.40,  # High volatility (semiconductor)
    "NVDA": 0.45,  # High volatility (AI boom)
    "TSLA": 0.50,  # Highest volatility
    "MSFT": 0.23,  # Lower volatility (mega cap)
    "AMZN": 0.28,  # Moderate volatility
    "META": 0.32,  # Moderate-high volatility
}

all_trades = []
results_by_ticker = {}

for ticker, earnings_dates in EARNINGS_2024.items():
    print(f"\n{ticker}:")
    ticker_trades = []
    sigma = IV_BY_TICKER[ticker]

    for earnings_date_str in earnings_dates:
        earnings_date = pd.to_datetime(earnings_date_str)

        # Entry: 2 days before
        entry_date = earnings_date - timedelta(days=2)
        exit_date = earnings_date + timedelta(days=1)

        # Find closest trading days
        entry_price_data = price_data[ticker][price_data[ticker].index <= entry_date]
        if len(entry_price_data) == 0:
            print(f"  ❌ {earnings_date.date()}: No entry data")
            continue
        entry_date_actual = entry_price_data.index[-1]
        entry_price = entry_price_data.iloc[-1]["close"]

        exit_price_data = price_data[ticker][price_data[ticker].index >= exit_date]
        if len(exit_price_data) == 0:
            print(f"  ❌ {earnings_date.date()}: No exit data")
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

        # Calculate position size (contracts)
        contracts = max(1, int(5000 / (entry_price * 0.5)))

        straddle_cost = (call_entry_price + put_entry_price) * contracts * 100
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
            "entry_price": entry_price,
            "exit_price": exit_price,
            "price_move_pct": price_move_pct,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "hold_days": hold_days,
            "win": pnl > 0,
        }

        ticker_trades.append(trade)
        all_trades.append(trade)

        win_symbol = "✅" if trade["win"] else "❌"
        print(
            f"  {earnings_date.date()} | ${entry_price:.2f} → ${exit_price:.2f} ({price_move_pct:+.2f}%) | P&L: {pnl_pct:+.2f}% {win_symbol}"
        )

    # Calculate ticker metrics
    if len(ticker_trades) > 0:
        ticker_df = pd.DataFrame(ticker_trades)
        win_rate = (ticker_df["pnl"] > 0).mean() * 100
        avg_pnl_pct = ticker_df["pnl_pct"].mean()

        # Sharpe
        trade_returns = ticker_df["pnl_pct"] / 100
        sharpe = (
            (trade_returns.mean() / trade_returns.std() * np.sqrt(len(ticker_trades))) if trade_returns.std() > 0 else 0
        )

        results_by_ticker[ticker] = {
            "trades": len(ticker_trades),
            "win_rate": win_rate,
            "avg_pnl_pct": avg_pnl_pct,
            "sharpe": sharpe,
            "total_pnl": ticker_df["pnl"].sum(),
        }

print(f"\n✓ Simulated {len(all_trades)} earnings events\n")

# Calculate overall metrics
print("[3/3] Analyzing results...")

trades_df = pd.DataFrame(all_trades)

# Overall metrics
total_pnl = trades_df["pnl"].sum()
total_return = (total_pnl / (INITIAL_CAPITAL * len(all_trades))) * 100
win_rate = (trades_df["pnl"] > 0).mean() * 100
avg_pnl_pct = trades_df["pnl_pct"].mean()

# Sharpe ratio
trade_returns = trades_df["pnl_pct"] / 100
sharpe = (trade_returns.mean() / trade_returns.std() * np.sqrt(len(all_trades))) if trade_returns.std() > 0 else 0

# Print results by ticker
print("\n" + "=" * 80)
print("RESULTS BY TICKER")
print("=" * 80)

print(
    f"\n{'Ticker':<8} | {'Trades':>6} | {'Win%':>5} | {'Avg P&L':>8} | {'Sharpe':>6} | {'Claimed Sharpe':>14} | {'Status':>8}"
)
print("-" * 80)

claimed_sharpe = {
    "GOOGL": 4.80,
    "AAPL": 2.90,
    "AMD": 2.52,
    "NVDA": 2.38,
    "TSLA": 2.00,
    "MSFT": 1.45,
    "AMZN": 1.12,
    "META": 0.00,  # No claim, testing for completeness
}

for ticker in ["GOOGL", "AAPL", "AMD", "NVDA", "TSLA", "MSFT", "AMZN", "META"]:
    if ticker in results_by_ticker:
        r = results_by_ticker[ticker]
        claimed = claimed_sharpe[ticker]
        status = "✅" if r["sharpe"] > 0.5 else "❌"
        print(
            f"{ticker:<8} | {r['trades']:6d} | {r['win_rate']:5.1f}% | {r['avg_pnl_pct']:7.2f}% | {r['sharpe']:6.2f} | {claimed:14.2f} | {status:>8}"
        )

# Overall portfolio
print("\n" + "=" * 80)
print("OVERALL PORTFOLIO METRICS")
print("=" * 80)

print(f"\n📊 Performance:")
print(f"  Total Trades: {len(all_trades)}")
print(f"  Win Rate: {win_rate:.1f}% ({int(win_rate/100 * len(all_trades))}/{len(all_trades)} wins)")
print(f"  Average P&L: {avg_pnl_pct:+.2f}% per event")
print(f"  Best Trade: {trades_df['pnl_pct'].max():+.2f}%")
print(f"  Worst Trade: {trades_df['pnl_pct'].min():+.2f}%")

print(f"\n📈 Risk-Adjusted:")
print(f"  Portfolio Sharpe: {sharpe:.2f}")
print(f"  Claimed Sharpe: 2.25 (WFA average)")
print(f"  Std Dev: {trades_df['pnl_pct'].std():.2f}%")

print(f"\n💰 Returns:")
print(f"  Total P&L: ${total_pnl:,.2f}")
print(f"  Average Return per Event: {avg_pnl_pct:.2f}%")

# Save results
output_file = Path(__file__).parent / "results.csv"
trades_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Verdict
print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print("\nClaimed Performance (VALIDATED_STRATEGIES_FINAL.md):")
print("  GOOGL: Sharpe 4.80, Win Rate 62.5%")
print("  AAPL: Sharpe 2.90, Win Rate 54.2%")
print("  NVDA: Sharpe 2.38, Win Rate 45.8%")
print("  TSLA: Sharpe 2.00, Win Rate 50.0%")
print("  Portfolio: Sharpe 2.25, Win Rate 58.3%")

print(f"\nActual Performance (2024 Test):")
for ticker in ["GOOGL", "AAPL", "NVDA", "TSLA"]:
    if ticker in results_by_ticker:
        r = results_by_ticker[ticker]
        print(f"  {ticker}: Sharpe {r['sharpe']:.2f}, Win Rate {r['win_rate']:.1f}%")
print(f"  Portfolio: Sharpe {sharpe:.2f}, Win Rate {win_rate:.1f}%")

print("\n" + "=" * 80)
print("VERDICT")
print("=" * 80)

if sharpe >= 1.0 and win_rate >= 50:
    print("\n✅ STRATEGY VALIDATED")
    print("   Performance is positive across multiple tickers")
    print("   Ready for paper trading deployment")
elif sharpe >= 0.5:
    print("\n⚠️  STRATEGY PARTIALLY VALIDATED")
    print("   Performance is positive but below claims")
    print("   Consider selective deployment (best tickers only)")
else:
    print("\n❌ STRATEGY FAILED VALIDATION")
    print("   Performance does not match claims")
    print("   Requires further research or rejection")

print("\n" + "=" * 80)
