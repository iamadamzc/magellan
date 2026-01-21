"""
FOMC Event Straddles - Multi-Asset Portfolio Backtest

Tests the FOMC Event Straddles strategy on multiple index ETFs to validate
performance across different market segments.

Strategy:
- Entry: 5 minutes before FOMC announcement (1:55 PM ET)
- Position: Buy ATM straddle on index ETF (1 call + 1 put)
- Exit: 5 minutes after announcement (2:05 PM ET)
- Hold Time: 10 minutes

Assets to Test:
- SPY: S&P 500 (primary)
- QQQ: Nasdaq 100 (tech-heavy)
- IWM: Russell 2000 (small caps)

Test Period: 2024-01-01 to 2024-12-31 (8 FOMC events)
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

print("=" * 80)
print("FOMC EVENT STRADDLES - MULTI-ASSET PORTFOLIO BACKTEST")
print("=" * 80)
print("\nObjective: Validate FOMC Event Straddles across multiple index ETFs")
print("Strategy: 10-minute hold ATM straddle (T-5 to T+5)\n")

# 2024 FOMC Events (8 total)
# Source: Federal Reserve FOMC Calendar
FOMC_EVENTS_2024 = [
    {"date": "2024-01-31", "time": "14:00"},  # Jan 31
    {"date": "2024-03-20", "time": "14:00"},  # Mar 20
    {"date": "2024-05-01", "time": "14:00"},  # May 1
    {"date": "2024-06-12", "time": "14:00"},  # Jun 12
    {"date": "2024-07-31", "time": "14:00"},  # Jul 31
    {"date": "2024-09-18", "time": "14:00"},  # Sep 18 (Fed pivot)
    {"date": "2024-11-07", "time": "14:00"},  # Nov 7
    {"date": "2024-12-18", "time": "14:00"},  # Dec 18
]

print(f"Testing {len(FOMC_EVENTS_2024)} FOMC events across 3 index ETFs\n")

# Fetch price data for all ETFs
print("[1/3] Fetching price data for all ETFs...")
alpaca = AlpacaDataClient()

price_data = {}
for ticker in ["SPY", "QQQ", "IWM"]:
    print(f"  Fetching {ticker}...", end="")
    df = alpaca.fetch_historical_bars(
        ticker, "1Min", "2024-01-01", "2024-12-31", feed="sip"
    )
    price_data[ticker] = df
    print(f" ✓ {len(df)} 1-minute bars")

print()

# Simulate FOMC event straddles
print("[2/3] Simulating FOMC event straddles...")

# Use simplified straddle pricing model (same as original research)
INITIAL_CAPITAL = 10000  # $10k per event
all_trades = []
results_by_ticker = {}

for ticker in ["SPY", "QQQ", "IWM"]:
    print(f"\n{ticker}:")
    ticker_trades = []

    for event in FOMC_EVENTS_2024:
        event_date = pd.to_datetime(event["date"])
        event_time = event["time"]

        # Entry: 5 minutes before (1:55 PM)
        entry_hour, entry_minute = 13, 55
        entry_datetime = event_date.replace(hour=entry_hour, minute=entry_minute)

        # Exit: 5 minutes after (2:05 PM)
        exit_hour, exit_minute = 14, 5
        exit_datetime = event_date.replace(hour=exit_hour, minute=exit_minute)

        # Find closest price bars
        entry_bars = price_data[ticker][price_data[ticker].index <= entry_datetime]
        if len(entry_bars) == 0:
            print(f"  ❌ {event_date.date()}: No entry data")
            continue
        entry_price = entry_bars.iloc[-1]["close"]
        entry_time_actual = entry_bars.index[-1]

        exit_bars = price_data[ticker][price_data[ticker].index >= exit_datetime]
        if len(exit_bars) == 0:
            print(f"  ❌ {event_date.date()}: No exit data")
            continue
        exit_price = exit_bars.iloc[0]["close"]
        exit_time_actual = exit_bars.index[0]

        # Calculate move (absolute value - straddle profits from movement in either direction)
        move_pct = abs((exit_price - entry_price) / entry_price) * 100

        # Simplified straddle pricing model:
        # - ATM straddle costs ~2% of ETF price
        # - For 10-minute hold, theta decay is negligible (~0.01%)
        # - Slippage = 0.05% (bid-ask spread on options)
        # - Profit = (realized move / straddle cost) * 100 - theta - slippage

        straddle_cost_pct = 2.0  # ATM straddle = 2% of ETF
        theta_decay_pct = 0.01  # 10 minutes = minimal time decay
        slippage_pct = 0.05  # Bid-ask spread on options

        # P&L calculation
        profit_pct = (
            (move_pct / straddle_cost_pct * 100) - theta_decay_pct - slippage_pct
        )

        # Calculate dollar P&L (assuming $10k position)
        dollar_pnl = INITIAL_CAPITAL * (profit_pct / 100)

        trade = {
            "ticker": ticker,
            "date": event_date.date(),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "move_pct": move_pct,
            "pnl_pct": profit_pct,
            "pnl_dollars": dollar_pnl,
            "win": profit_pct > 0,
        }

        ticker_trades.append(trade)
        all_trades.append(trade)

        win_symbol = "✅" if trade["win"] else "❌"
        print(
            f"  {event_date.date()} | ${entry_price:.2f} → ${exit_price:.2f} ({move_pct:+.2f}%) | P&L: {profit_pct:+.2f}% {win_symbol}"
        )

    # Calculate ticker metrics
    if len(ticker_trades) > 0:
        ticker_df = pd.DataFrame(ticker_trades)
        win_rate = (ticker_df["pnl_pct"] > 0).mean() * 100
        avg_pnl_pct = ticker_df["pnl_pct"].mean()

        # Sharpe
        trade_returns = ticker_df["pnl_pct"] / 100
        sharpe = (
            (trade_returns.mean() / trade_returns.std() * np.sqrt(len(ticker_trades)))
            if trade_returns.std() > 0
            else 0
        )

        results_by_ticker[ticker] = {
            "trades": len(ticker_trades),
            "win_rate": win_rate,
            "avg_pnl_pct": avg_pnl_pct,
            "sharpe": sharpe,
            "total_pnl": ticker_df["pnl_dollars"].sum(),
        }

print(f"\n✓ Simulated {len(all_trades)} FOMC events\n")

# Calculate overall metrics
print("[3/3] Analyzing results...")

trades_df = pd.DataFrame(all_trades)

# Overall metrics
total_pnl = trades_df["pnl_dollars"].sum()
total_return = (total_pnl / (INITIAL_CAPITAL * len(all_trades))) * 100
win_rate = (trades_df["pnl_pct"] > 0).mean() * 100
avg_pnl_pct = trades_df["pnl_pct"].mean()

# Sharpe ratio
trade_returns = trades_df["pnl_pct"] / 100
sharpe = (
    (trade_returns.mean() / trade_returns.std() * np.sqrt(len(all_trades)))
    if trade_returns.std() > 0
    else 0
)

# Print results by ticker
print("\n" + "=" * 80)
print("RESULTS BY TICKER")
print("=" * 80)

print(
    f"\n{'Ticker':<8} | {'Trades':>6} | {'Win%':>5} | {'Avg P&L':>8} | {'Sharpe':>6} | {'Status':>8}"
)
print("-" * 80)

for ticker in ["SPY", "QQQ", "IWM"]:
    if ticker in results_by_ticker:
        r = results_by_ticker[ticker]
        status = "✅" if r["sharpe"] > 1.0 else "⚠️" if r["sharpe"] > 0.5 else "❌"
        print(
            f"{ticker:<8} | {r['trades']:6d} | {r['win_rate']:5.1f}% | {r['avg_pnl_pct']:7.2f}% | {r['sharpe']:6.2f} | {status:>8}"
        )

# Overall portfolio
print("\n" + "=" * 80)
print("OVERALL PORTFOLIO METRICS")
print("=" * 80)

print(f"\n📊 Performance:")
print(f"  Total Trades: {len(all_trades)}")
print(
    f"  Win Rate: {win_rate:.1f}% ({int(win_rate/100 * len(all_trades))}/{len(all_trades)} wins)"
)
print(f"  Average P&L: {avg_pnl_pct:+.2f}% per event")
print(f"  Best Trade: {trades_df['pnl_pct'].max():+.2f}%")
print(f"  Worst Trade: {trades_df['pnl_pct'].min():+.2f}%")

print(f"\n📈 Risk-Adjusted:")
print(f"  Portfolio Sharpe: {sharpe:.2f}")
print(f"  SPY Sharpe (claimed): 1.17")
print(f"  Std Dev: {trades_df['pnl_pct'].std():.2f}%")

print(f"\n💰 Returns:")
print(f"  Total P&L: ${total_pnl:,.2f}")
print(f"  Average Return per Event: {avg_pnl_pct:.2f}%")
print(f"  Annual Return (8 events): {avg_pnl_pct * 8:.1f}%")

# Save results
output_file = Path(__file__).parent / "results_multi_asset.csv"
trades_df.to_csv(output_file, index=False)
print(f"\n📁 Results saved to: {output_file}")

# Verdict
print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print("\nClaimed Performance (SPY only):")
print("  Sharpe: 1.17")
print("  Win Rate: 100%")
print("  Annual Return: +102.7%")

print(f"\nActual Performance (Multi-Asset 2024):")
for ticker in ["SPY", "QQQ", "IWM"]:
    if ticker in results_by_ticker:
        r = results_by_ticker[ticker]
        print(
            f"  {ticker}: Sharpe {r['sharpe']:.2f}, Win Rate {r['win_rate']:.1f}%, Avg P&L {r['avg_pnl_pct']:+.2f}%"
        )
print(f"  Portfolio: Sharpe {sharpe:.2f}, Win Rate {win_rate:.1f}%")

print("\n" + "=" * 80)
print("VERDICT")
print("=" * 80)

if sharpe >= 1.0 and win_rate >= 75:
    print("\n✅ STRATEGY VALIDATED")
    print("   Performance is positive across multiple index ETFs")
    print("   Ready for paper trading deployment")
elif sharpe >= 0.5:
    print("\n⚠️  STRATEGY PARTIALLY VALIDATED")
    print("   Performance is positive but varies by ETF")
    print("   Consider selective deployment (best ETFs only)")
else:
    print("\n❌ STRATEGY FAILED VALIDATION")
    print("   Performance does not meet minimum thresholds")
    print("   Requires further research or rejection")

print("\n" + "=" * 80)
