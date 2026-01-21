"""
Daily Trend - Crypto Test via FMP (HOURLY + WEEKLY FILTER)
Tests BTC and ETH using 1-Hour Hysteresis + Weekly RSI Filter.

Hypothesis: Weekly filter will prevent counter-trend trades on BTC.
Expected Improvement: BTC Sharpe 0.42 -> 1.0+
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
print("HOURLY TREND + WEEKLY FILTER - CRYPTO VALIDATION")
print("=" * 80)
print("\nTesting BTC and ETH (2020-2025)")
print("Logic: Enter if Hourly RSI > 55 AND Weekly RSI > 50\n")

# FMP API
FMP_API_KEY = os.getenv("FMP_API_KEY")

# Strategy parameters
RSI_PERIOD = 14
UPPER_BAND = 55
LOWER_BAND = 45
WEEKLY_FILTER_THRESHOLD = 50

# Annualization
ANNUALIZATION = np.sqrt(8760)


def fetch_daily_data(symbol):
    """Fetch daily data to calculate Weekly RSI"""
    # CORRECT ENDPOINT per docs: https://financialmodelingprep.com/stable/historical-price-eod/full?symbol=BTCUSD
    url = f"https://financialmodelingprep.com/stable/historical-price-eod/full"
    params = {"symbol": symbol, "apikey": FMP_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        # NOTE: historical-price-eod/full might return a LIST directly (not dict with historical)
        # Check type
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            # FMP might return 'close' or 'adjClose'
            return df
        elif isinstance(data, dict) and "historical" in data:
            df = pd.DataFrame(data["historical"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            return df

    except Exception as e:
        print(f"  ❌ Daily fetch error: {e}")
        return None
    return None


def fetch_hourly_data(symbol, start_year=2020, end_year=2025):
    """Fetch hourly data (chunked)"""
    base_url = f"https://financialmodelingprep.com/stable/historical-chart/1hour"
    all_dfs = []

    start_date = datetime(start_year, 1, 1)
    final_date = datetime(end_year, 12, 31)
    current_date = start_date

    while current_date < final_date:
        next_date = current_date + timedelta(days=90)
        if next_date > final_date:
            next_date = final_date

        params = {
            "symbol": symbol,
            "apikey": FMP_API_KEY,
            "from": current_date.strftime("%Y-%m-%d"),
            "to": next_date.strftime("%Y-%m-%d"),
        }

        try:
            r = requests.get(base_url, params=params, timeout=30)
            if r.status_code == 200 and r.json():
                all_dfs.append(pd.DataFrame(r.json()))
        except:
            pass

        current_date = next_date + timedelta(days=1)

    if not all_dfs:
        return None

    df = pd.concat(all_dfs, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates("date").set_index("date").sort_index()
    # FMP return keys: date, open, low, high, close, volume...
    # Rename to lowercase just in case
    df.columns = [c.lower() for c in df.columns]

    # Filter range
    df = df[(df.index >= "2020-01-01") & (df.index <= "2025-12-31")]
    return df


def calculate_rsi(series, period=14):
    delta = series.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    return 100 - (100 / (1 + rs))


def backtest_filtered(symbol):
    # 1. Fetch Data
    print(f"Fetching {symbol} data...")
    hourly_df = fetch_hourly_data(symbol)
    daily_df = fetch_daily_data(symbol)

    if hourly_df is None:
        print("  ❌ Hourly Data fetch failed")
        return None
    if daily_df is None:
        print("  ❌ Daily Data fetch failed")
        return None

    print(f"  Hourly bars: {len(hourly_df)}")
    print(f"  Daily bars: {len(daily_df)}")

    # 2. Calculate Weekly RSI (resample Daily -> Weekly)
    weekly_df = daily_df.resample("W-FRI").last()  # weekly close
    weekly_rsi = calculate_rsi(weekly_df["close"])

    # 3. Align Weekly RSI to Hourly Data (ffill)
    combined = hourly_df[["close"]].copy()
    combined["rsi"] = calculate_rsi(combined["close"])

    # Reindex weekly to hourly
    # Warning: this uses FUTURE weekly close for the week? No, resample 'W-FRI' sets date to Friday.
    # If we are on Tuesday, we shouldn't know Friday's close.
    # CORRECT WAY: Resample Daily to Weekly, shift 1 week?
    # Actually, let's keep it simple: Use Daily RSI as a proxy for higher timeframe?
    # Roadmap said "Weekly".
    # To avoid lookahead: weekly_rsi.shift(1) (Past week's RSI).

    weekly_rsi_shifted = weekly_rsi.shift(1)

    # Now reindex to hourly. ffill will fill the week with Last Week's RSI.
    weekly_rsi_aligned = weekly_rsi_shifted.reindex(hourly_df.index, method="ffill")
    combined["weekly_rsi"] = weekly_rsi_aligned

    # Dropna (start of data)
    combined = combined.dropna()

    # 4. Simulation
    cash, shares, position = 10000.0, 0, 0
    equity = []

    closes = combined["close"].values
    hr_rsis = combined["rsi"].values
    wk_rsis = combined["weekly_rsi"].values

    for i in range(len(combined)):
        price = closes[i]
        hr_rsi = hr_rsis[i]
        wk_rsi = wk_rsis[i]

        # Logic:
        # Enter if Hourly > 55 AND Weekly > 50 (Trend aligned)
        # Exit if Hourly < 45 (Standard exit)

        if position == 0:
            if hr_rsi > UPPER_BAND and wk_rsi > WEEKLY_FILTER_THRESHOLD:
                # Buy
                shares = cash / price
                cash = 0
                position = 1
        elif position == 1:
            if hr_rsi < LOWER_BAND:
                # Sell
                cash = shares * price
                shares = 0
                position = 0

        equity.append(cash + (shares * price))

    equity = np.array(equity)
    if len(equity) == 0:
        return None

    # Metrics
    s = pd.Series(equity)
    r = s.pct_change().dropna()
    sharpe = (r.mean() / r.std() * ANNUALIZATION) if r.std() > 0 else 0

    ret = (equity[-1] / 10000 - 1) * 100

    running_max = s.expanding().max()
    dd = (s - running_max) / running_max
    max_dd = dd.min() * 100

    return {"symbol": symbol, "sharpe": sharpe, "return": ret, "max_dd": max_dd}


# Run
final_results = []
for sym in ["BTCUSD", "ETHUSD"]:
    res = backtest_filtered(sym)
    if res:
        final_results.append(res)
        print(f"\n  {sym} Results:")
        print(f"    Sharpe: {res['sharpe']:.2f}")
        print(f"    Return: {res['return']:.1f}%")
        print(f"    Max DD: {res['max_dd']:.1f}%")

# Save
if final_results:
    pd.DataFrame(final_results).to_csv(
        Path(__file__).parent / "crypto_filtered_results.csv", index=False
    )
