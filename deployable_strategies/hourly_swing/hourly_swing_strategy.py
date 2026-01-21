"""
Hourly Swing Trading - Validation Test
Tests TSLA and NVDA with 1-hour RSI Hysteresis on 2024-2025 data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.data_handler import AlpacaDataClient
from alpaca.data.timeframe import TimeFrame

print("=" * 80)
print("HOURLY SWING TRADING - VALIDATION TEST")
print("=" * 80)
print("Assets: TSLA, NVDA")
print("Period: 2024-01-01 to 2025-12-31")
print("Timeframe: 1-Hour bars")
print("=" * 80)

# Strategy config
ASSETS = {
    "TSLA": {"rsi_period": 14, "upper": 60, "lower": 40},
    "NVDA": {"rsi_period": 28, "upper": 55, "lower": 45},
}

INITIAL_CAPITAL = 10000
TRANSACTION_COST_BPS = 5.0  # 0.05% (higher for hourly)
START_DATE = "2024-01-01"
END_DATE = "2025-12-31"

client = AlpacaDataClient()
results = {}

for symbol, config in ASSETS.items():
    print(f"\n{'='*80}")
    print(f"Testing {symbol}")
    print(f"{'='*80}")

    rsi_period = config["rsi_period"]
    upper_band = config["upper"]
    lower_band = config["lower"]

    print(f"Config: RSI-{rsi_period}, Bands {upper_band}/{lower_band}")

    # Fetch hourly data
    try:
        print(f"Fetching hourly bars...")
        raw_df = client.fetch_historical_bars(
            symbol=symbol,
            timeframe=TimeFrame.Hour,
            start=START_DATE,
            end=END_DATE,
            feed="sip",
        )

        # Force resample if needed (same bug as daily)
        if len(raw_df) > 10000:  # Likely minute data
            print(f"⚠️  Got {len(raw_df)} bars, resampling to hourly...")
            df = (
                raw_df.resample("1H")
                .agg(
                    {
                        "open": "first",
                        "high": "max",
                        "low": "min",
                        "close": "last",
                        "volume": "sum",
                    }
                )
                .dropna()
            )
        else:
            df = raw_df

        print(f"✓ {len(df)} hourly bars")

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        continue

    # Calculate RSI
    delta = df["close"].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)

    avg_gain = gains.ewm(span=rsi_period, adjust=False).mean()
    avg_loss = losses.ewm(span=rsi_period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.inf)
    df["rsi"] = 100 - (100 / (1 + rs))

    df.loc[avg_loss == 0, "rsi"] = 100.0
    df.loc[avg_gain == 0, "rsi"] = 0.0

    # Run backtest with overnight holds
    cash = INITIAL_CAPITAL
    shares = 0
    position = "flat"
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

        # Hysteresis Logic (same as daily)
        if position == "flat" and rsi > upper_band:
            cost = TRANSACTION_COST_BPS / 10000
            shares = int(cash / (price * (1 + cost)))
            if shares > 0:
                cash -= shares * price * (1 + cost)
                position = "long"
                entry_price = price
                entry_date = date

        elif position == "long" and rsi < lower_band:
            cost = TRANSACTION_COST_BPS / 10000
            proceeds = shares * price * (1 - cost)
            pnl = proceeds - (shares * entry_price)
            pnl_pct = (price / entry_price - 1) * 100
            hold_hours = (date - entry_date).total_seconds() / 3600

            trades.append(
                {
                    "entry_date": entry_date,
                    "exit_date": date,
                    "entry_price": entry_price,
                    "exit_price": price,
                    "hold_hours": hold_hours,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                }
            )

            cash += proceeds
            shares = 0
            position = "flat"
            entry_price = None

        current_equity = cash + shares * price
        equity_curve.append(current_equity)

    # Close any open position
    if position == "long" and shares > 0:
        price = df.iloc[-1]["close"]
        date = df.index[-1]
        cost = TRANSACTION_COST_BPS / 10000
        proceeds = shares * price * (1 - cost)
        pnl = proceeds - (shares * entry_price)
        pnl_pct = (price / entry_price - 1) * 100
        hold_hours = (date - entry_date).total_seconds() / 3600

        trades.append(
            {
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": price,
                "hold_hours": hold_hours,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )

        cash += proceeds
        shares = 0

    # Calculate metrics
    final_equity = equity_curve[-1]
    total_return = (final_equity / INITIAL_CAPITAL - 1) * 100
    bh_return = (df.iloc[-1]["close"] / df.iloc[0]["close"] - 1) * 100

    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_dd = drawdown.min() * 100

    if len(equity_curve) > 1:
        returns = equity_series.pct_change().dropna()
        # Annualize for hourly (assume 6.5 trading hours/day, 252 days)
        sharpe = (
            (returns.mean() / returns.std()) * np.sqrt(252 * 6.5)
            if returns.std() > 0
            else 0
        )
    else:
        sharpe = 0

    if trades:
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df["pnl"] > 0]
        win_rate = (len(winning_trades) / len(trades)) * 100
        avg_hold = trades_df["hold_hours"].mean()
    else:
        win_rate = 0
        avg_hold = 0

    # Store results
    results[symbol] = {
        "total_return": total_return,
        "bh_return": bh_return,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "trades": len(trades),
        "win_rate": win_rate,
        "avg_hold_hours": avg_hold,
    }

    # Print results
    print(f"\n{symbol} RESULTS:")
    print(f"  Return:          {total_return:+.1f}%")
    print(f"  Buy & Hold:      {bh_return:+.1f}%")
    print(f"  Sharpe:          {sharpe:.2f}")
    print(f"  Max DD:          {max_dd:.1f}%")
    print(f"  Trades:          {len(trades)}")
    print(f"  Win Rate:        {win_rate:.1f}%")
    print(f"  Avg Hold:        {avg_hold:.1f} hours")

# Summary
print(f"\n{'='*80}")
print("HOURLY SWING SUMMARY")
print(f"{'='*80}")

for symbol, res in results.items():
    status = "✅" if res["total_return"] > 0 else "❌"
    print(
        f"\n{symbol}: {res['total_return']:+.1f}% (Sharpe {res['sharpe']:.2f}) {status}"
    )
    print(f"  Claimed: TSLA +41.5%, NVDA +16.2% (2025 only)")
    print(f"  Tested: 2024-2025 (2 full years)")

print(f"\n{'='*80}")

# Save results
results_df = pd.DataFrame(results).T
results_df.to_csv("hourly_swing_results.csv")
print(f"\n✅ Results saved to hourly_swing_results.csv")
