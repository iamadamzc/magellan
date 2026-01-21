"""
Simple Daily Trend Hysteresis Backtest - GET REAL RESULTS
Tests GOOGL with RSI-28, 55/45 bands on actual 2024-2025 data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("=" * 80)
print("DAILY TREND HYSTERESIS - REAL BACKTEST")
print("=" * 80)
print("Symbol: GOOGL")
print("Period: 2024-01-01 to 2025-12-31")
print("Strategy: RSI-28, Bands 55/45, Long-Only")
print("=" * 80)

# Configuration
SYMBOL = "GOOGL"
START_DATE = "2024-01-01"
END_DATE = "2025-12-31"
RSI_PERIOD = 28
UPPER_BAND = 55
LOWER_BAND = 45
INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 1.5  # 0.015%

# Fetch data
print(f"\n[1/4] Fetching daily bars from Alpaca...")
client = AlpacaDataClient()
raw_df = client.fetch_historical_bars(
    symbol=SYMBOL, timeframe=TimeFrame.Day, start=START_DATE, end=END_DATE, feed="sip"
)
print(f"✓ Fetched {len(raw_df)} bars")

# Force resample to daily if needed
if len(raw_df) > 1000:  # Likely minute data
    print(f"⚠️  Detected high-frequency data, resampling to daily...")
    df = (
        raw_df.resample("1D")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )
    print(f"✓ Resampled to {len(df)} daily bars")
else:
    df = raw_df

print(f"✓ Final dataset: {len(df)} daily bars")

# Calculate RSI
print(f"\n[2/4] Calculating RSI-{RSI_PERIOD}...")
delta = df["close"].diff()
gains = delta.where(delta > 0, 0.0)
losses = (-delta).where(delta < 0, 0.0)

avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()

rs = avg_gain / avg_loss.replace(0, np.inf)
df["rsi"] = 100 - (100 / (1 + rs))

# Handle edge cases
df.loc[avg_loss == 0, "rsi"] = 100.0
df.loc[avg_gain == 0, "rsi"] = 0.0

print(f"✓ RSI calculated (min: {df['rsi'].min():.1f}, max: {df['rsi'].max():.1f})")

# Run backtest with Hysteresis
print(f"\n[3/4] Running Hysteresis backtest (Bands: {UPPER_BAND}/{LOWER_BAND})...")

cash = INITIAL_CAPITAL
shares = 0
position = "flat"  # 'long' or 'flat'
trades = []
equity_curve = []

entry_price = None
entry_date = None

for date, row in df.iterrows():
    price = row["close"]
    rsi = row["rsi"]

    if pd.isna(rsi):
        equity_curve.append(cash + shares * price)
        continue

    # Hysteresis Logic
    if position == "flat" and rsi > UPPER_BAND:
        # Enter long
        cost = TRANSACTION_COST_BPS / 10000
        shares = int(cash / (price * (1 + cost)))
        if shares > 0:
            cash -= shares * price * (1 + cost)
            position = "long"
            entry_price = price
            entry_date = date

    elif position == "long" and rsi < LOWER_BAND:
        # Exit long
        cost = TRANSACTION_COST_BPS / 10000
        proceeds = shares * price * (1 - cost)
        pnl = proceeds - (shares * entry_price)
        pnl_pct = (price / entry_price - 1) * 100
        hold_days = (date - entry_date).days

        trades.append(
            {
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": price,
                "hold_days": hold_days,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )

        cash += proceeds
        shares = 0
        position = "flat"
        entry_price = None

    # Track equity
    current_equity = cash + shares * price
    equity_curve.append(current_equity)

# Close any open position at end
if position == "long" and shares > 0:
    price = df.iloc[-1]["close"]
    date = df.index[-1]
    cost = TRANSACTION_COST_BPS / 10000
    proceeds = shares * price * (1 - cost)
    pnl = proceeds - (shares * entry_price)
    pnl_pct = (price / entry_price - 1) * 100
    hold_days = (date - entry_date).days

    trades.append(
        {
            "entry_date": entry_date,
            "exit_date": date,
            "entry_price": entry_price,
            "exit_price": price,
            "hold_days": hold_days,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        }
    )

    cash += proceeds
    shares = 0

# Calculate metrics
print(f"✓ Backtest complete: {len(trades)} trades executed")

print(f"\n[4/4] Calculating performance metrics...")

final_equity = equity_curve[-1]
total_return = (final_equity / INITIAL_CAPITAL - 1) * 100

# Buy & Hold comparison
bh_return = (df.iloc[-1]["close"] / df.iloc[0]["close"] - 1) * 100

# Max Drawdown
equity_series = pd.Series(equity_curve)
running_max = equity_series.expanding().max()
drawdown = (equity_series - running_max) / running_max
max_dd = drawdown.min() * 100

# Sharpe Ratio (annualized)
if len(equity_curve) > 1:
    returns = equity_series.pct_change().dropna()
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
else:
    sharpe = 0

# Trade stats
if trades:
    trades_df = pd.DataFrame(trades)
    winning_trades = trades_df[trades_df["pnl"] > 0]
    losing_trades = trades_df[trades_df["pnl"] <= 0]
    win_rate = (len(winning_trades) / len(trades)) * 100
    avg_win = winning_trades["pnl_pct"].mean() if len(winning_trades) > 0 else 0
    avg_loss = losing_trades["pnl_pct"].mean() if len(losing_trades) > 0 else 0
    avg_hold = trades_df["hold_days"].mean()
else:
    win_rate = 0
    avg_win = 0
    avg_loss = 0
    avg_hold = 0

# Print Results
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

print(f"\n💰 PERFORMANCE:")
print(f"  Initial Capital:     ${INITIAL_CAPITAL:,.2f}")
print(f"  Final Equity:        ${final_equity:,.2f}")
print(f"  Total Return:        {total_return:+.2f}%")
print(f"  Buy & Hold Return:   {bh_return:+.2f}%")
print(f"  Outperformance:      {total_return - bh_return:+.2f}%")

print(f"\n📊 RISK METRICS:")
print(f"  Max Drawdown:        {max_dd:.2f}%")
print(f"  Sharpe Ratio:        {sharpe:.2f}")

print(f"\n📈 TRADING STATS:")
print(f"  Total Trades:        {len(trades)}")
print(f"  Win Rate:            {win_rate:.1f}%")
print(f"  Avg Win:             {avg_win:+.2f}%")
print(f"  Avg Loss:            {avg_loss:+.2f}%")
print(f"  Avg Hold Period:     {avg_hold:.0f} days")

print("\n" + "=" * 80)

# Verdict
if total_return > 0 and sharpe > 0.5:
    print("✅ VERDICT: Strategy is PROFITABLE")
elif total_return > 0:
    print("⚠️  VERDICT: Strategy is profitable but low Sharpe (risky)")
else:
    print("❌ VERDICT: Strategy is LOSING MONEY")

print("=" * 80)

# Save trades to CSV
if trades:
    trades_df.to_csv("googl_hysteresis_trades.csv", index=False)
    print(f"\n📁 Trade log saved to: googl_hysteresis_trades.csv")

print("\nDone!")
