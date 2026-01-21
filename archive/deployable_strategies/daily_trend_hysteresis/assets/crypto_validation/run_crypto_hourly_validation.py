"""
Daily Trend - Crypto Test via FMP (HOURLY) - CHUNKED FETCH
Tests BTC and ETH using FMP's crypto historical data API on HOURLY timeframe.
Fetches data in chunks to ensure full history (2020-2025).

Hypothesis: Hourly signals will capture crypto's intraday momentum better.
Expected Improvement: Sharpe 0.68 -> 1.2-1.8
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta

script_path = Path(__file__).resolve()
project_root = script_path.parents[6]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

print("=" * 80)
print("DAILY TREND (HOURLY) - CRYPTO VALIDATION (FMP) - FULL HISTORY")
print("=" * 80)
print("\nTesting BTC and ETH (2020-2025) on HOURLY timeframe")
print("Target: Sharpe > 1.2\n")

# FMP API
FMP_API_KEY = os.getenv("FMP_API_KEY")
if not FMP_API_KEY:
    print("❌ FMP_API_KEY not found in environment")
    exit(1)

# Crypto symbols (FMP format uses BTCUSD, ETHUSD)
CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD"]

# Strategy parameters
RSI_PERIOD = 14
UPPER_BAND = 55
LOWER_BAND = 45

# Annualization factor for hourly crypto (24/7)
ANNUALIZATION = np.sqrt(8760)


def fetch_crypto_data_hourly_chunked(symbol, start_year=2020, end_year=2025):
    """Fetch hourly crypto data from FMP Stable Endpoint in chunks"""
    base_url = f"https://financialmodelingprep.com/stable/historical-chart/1hour"

    all_dfs = []

    # Iterate by 3-month chunks to avoid limits
    start_date = datetime(start_year, 1, 1)
    final_date = datetime(end_year, 12, 31)

    current_date = start_date
    while current_date < final_date:
        next_date = current_date + timedelta(days=90)
        if next_date > final_date:
            next_date = final_date

        rec_from = current_date.strftime("%Y-%m-%d")
        rec_to = next_date.strftime("%Y-%m-%d")

        params = {
            "symbol": symbol,
            "apikey": FMP_API_KEY,
            "from": rec_from,
            "to": rec_to,
        }

        # print(f"  Fetching {symbol} {rec_from} to {rec_to}...")
        try:
            response = requests.get(base_url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    df = pd.DataFrame(data)
                    all_dfs.append(df)
            else:
                print(f"    ⚠️ Warning: {response.status_code} for {rec_from}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

        current_date = next_date + timedelta(days=1)

    if not all_dfs:
        return None

    # Combine
    full_df = pd.concat(all_dfs, ignore_index=True)
    full_df["date"] = pd.to_datetime(full_df["date"])
    full_df = full_df.drop_duplicates(subset=["date"]).set_index("date").sort_index()

    # Filter 2020-2025
    full_df = full_df[(full_df.index >= "2020-01-01") & (full_df.index <= "2025-12-31")]

    return full_df


def backtest_crypto_hourly(symbol, data):
    """Run Hourly Trend backtest"""
    # Calculate RSI
    delta = data["close"].diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=RSI_PERIOD, adjust=False).mean()
    avg_loss = losses.ewm(span=RSI_PERIOD, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi_vals = (100 - (100 / (1 + rs))).values
    prices = data["close"].values

    # Simulation
    cash, shares, position = 10000.0, 0, 0
    equity = []

    for i in range(len(data)):
        if i < RSI_PERIOD:
            equity.append(cash)
            continue

        cur_rsi = rsi_vals[i]
        price = prices[i]

        # Hysteresis Logic
        if position == 0 and cur_rsi > UPPER_BAND:
            shares = cash / price
            cash = 0
            position = 1
        elif position == 1 and cur_rsi < LOWER_BAND:
            cash = shares * price
            shares = 0
            position = 0

        equity.append(cash + (shares * price))

    equity = np.array(equity)
    if len(equity) == 0:
        return 0, 0, 0

    ret = (equity[-1] / 10000 - 1) * 100

    # Sharpe
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * ANNUALIZATION) if r.std() > 0 else 0

    # Max DD
    running_max = s.expanding().max()
    drawdown = (s - running_max) / running_max
    max_dd = drawdown.min() * 100

    return sharpe, ret, max_dd


# Test each crypto
results = []

for symbol in CRYPTO_SYMBOLS:
    print(f"\nProcessing {symbol}...")
    try:
        data = fetch_crypto_data_hourly_chunked(symbol, 2020, 2025)
        if data is None or len(data) == 0:
            print(f"  ❌ No data for {symbol}")
            continue

        print(
            f"  ✓ Fetched {len(data)} hourly bars ({data.index.min()} to {data.index.max()})"
        )

        sharpe, ret, max_dd = backtest_crypto_hourly(symbol, data)
        bh_ret = (data.iloc[-1]["close"] / data.iloc[0]["close"] - 1) * 100

        results.append(
            {
                "symbol": symbol,
                "sharpe": sharpe,
                "return": ret,
                "bh_return": bh_ret,
                "max_dd": max_dd,
                "alpha": ret - bh_ret,
            }
        )

        status = "✅" if sharpe > 1.2 else ("⚠️" if sharpe > 0.8 else "❌")
        print(f"  {symbol} {status}")
        print(f"    Sharpe: {sharpe:.2f}")
        print(f"    Return: {ret:+.1f}%")
        print(f"    Buy & Hold: {bh_ret:+.1f}%")
        print(f"    Alpha: {ret-bh_ret:+.1f}%")
        print(f"    Max DD: {max_dd:.1f}%")

    except Exception as e:
        print(f"  ❌ Error: {e}")

# Summary
print("\n" + "=" * 80)
print("CRYPTO HOURLY VALIDATION VERDICT (5-YEAR)")
print("=" * 80)

if results:
    avg_sharpe = np.mean([r["sharpe"] for r in results])
    avg_alpha = np.mean([r["alpha"] for r in results])

    print(f"\nAverage Sharpe: {avg_sharpe:.2f}")
    print(f"Average Alpha: {avg_alpha:+.1f}%")

    if avg_sharpe > 1.2:
        print("\n✅ HOURLY STRATEGY IS SALVAGEABLE!")
        print("   Hourly Trend logic WORKS on pure momentum assets")
        print("\n   Next Steps:")
        print("     1. Deploy on BTC/ETH (Hourly)")
    elif avg_sharpe > 1.0:
        print("\n✅ STRATEGY IS DEPLOYABLE (MARGINAL)")
        print("   Sharpe > 1.0 threshold met")
    elif avg_sharpe > 0.8:
        print("\n⚠️ STRATEGY IS MARGINAL")
        print("   Better than daily but still not great")
    else:
        print("\n❌ STRATEGY LOGIC IS FLAWED")
        print("   Hourly didn't help enough")

    # Save
    out_file = Path(__file__).parent / "crypto_fmp_hourly_results_full.csv"
    pd.DataFrame(results).to_csv(out_file, index=False)
    print(f"\n✓ Saved to {out_file}")
else:
    print("\n❌ No results - data fetch failed")

print("\n" + "=" * 80)
