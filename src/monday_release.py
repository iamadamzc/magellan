"""
Monday Release Protocol - Kinetic Gap Execution
Analyzes opening gap and volume impulse to determine optimal Monday trading strategy.
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
import pandas as pd


def monday_release_logic(alpaca_client, symbol: str, friday_close: float = None) -> Dict:
    """
    Implement Monday Release Logic for gap-based execution strategy.

    Analyzes the opening gap and first 5-minute volume impulse to determine
    the optimal trading approach for Monday mornings.

    Decision Matrix:
    - FADING_GAP: Large gap (>1.5%) with low volume (<0.8x avg) -> Mean reversion
    - MOMENTUM_FLOW: Large gap (>1.5%) with high volume (>1.5x avg) -> Follow gap
    - LAMINAR_NORMAL: Otherwise -> Standard RSI/Sentiment DNA

    Args:
        alpaca_client: AlpacaDataClient instance for fetching market data
        symbol: Ticker symbol to analyze
        friday_close: Previous Friday's closing price (optional, will fetch if not provided)

    Returns:
        Dict with status, gap_pct, impulse_volume_zscore, and recommendation
    """
    from alpaca.data.timeframe import TimeFrame

    print(f"\n[RELEASE] Monday Release Protocol - Analyzing {symbol}")
    print("-" * 60)

    try:
        # Get current time
        now = datetime.now()

        # Check if it's Monday
        is_monday = now.weekday() == 0
        if not is_monday:
            return {
                "status": "NOT_MONDAY",
                "gap_pct": 0.0,
                "impulse_volume_zscore": 0.0,
                "recommendation": "LAMINAR_NORMAL",
                "message": f'Today is {now.strftime("%A")}, not Monday',
            }

        # Fetch Friday's close if not provided
        if friday_close is None:
            # Get previous Friday (3 days ago for Monday)
            friday_date = now - timedelta(days=3)
            friday_str = friday_date.strftime("%Y-%m-%d")
            friday_end_str = (friday_date + timedelta(days=1)).strftime("%Y-%m-%d")

            print(f"[RELEASE] Fetching Friday close for {symbol} ({friday_str})...")

            friday_bars = alpaca_client.fetch_historical_bars(
                symbol=symbol, timeframe=TimeFrame.Day, start=friday_str, end=friday_end_str, feed="sip"
            )

            if len(friday_bars) > 0:
                friday_close = friday_bars["close"].iloc[-1]
                print(f"[RELEASE] Friday close: ${friday_close:.2f}")
            else:
                return {
                    "status": "ERROR",
                    "gap_pct": 0.0,
                    "impulse_volume_zscore": 0.0,
                    "recommendation": "LAMINAR_NORMAL",
                    "message": "Could not fetch Friday close price",
                }

        # Fetch today's 5-minute bars (first bar at 09:30-09:35)
        today_str = now.strftime("%Y-%m-%d")
        today_end_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"[RELEASE] Fetching 5-minute bars for {symbol}...")

        bars_5min = alpaca_client.fetch_historical_bars(
            symbol=symbol, timeframe=TimeFrame(5, TimeFrame.Minute), start=today_str, end=today_end_str, feed="sip"
        )

        if len(bars_5min) == 0:
            return {
                "status": "NO_DATA",
                "gap_pct": 0.0,
                "impulse_volume_zscore": 0.0,
                "recommendation": "LAMINAR_NORMAL",
                "message": "No 5-minute bars available yet",
            }

        # Get first 5-minute bar (09:30-09:35)
        first_bar = bars_5min.iloc[0]
        open_price = first_bar["open"]
        impulse_volume = first_bar["volume"]

        # Calculate Opening Gap %
        opening_gap_pct = ((open_price - friday_close) / friday_close) * 100

        # Calculate Volume Z-Score (using 20-day rolling average)
        # Fetch historical 5-minute bars for volume baseline
        lookback_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")

        print(f"[RELEASE] Fetching historical volume baseline...")

        historical_bars = alpaca_client.fetch_historical_bars(
            symbol=symbol, timeframe=TimeFrame(5, TimeFrame.Minute), start=lookback_start, end=today_str, feed="sip"
        )

        if len(historical_bars) > 0:
            # Calculate rolling average of first-bar volumes
            # Filter for first bar of each day (09:30-09:35)
            first_bars_only = historical_bars.groupby(historical_bars.index.date).first()

            volume_mean = first_bars_only["volume"].mean()
            volume_std = first_bars_only["volume"].std()

            if volume_std > 0:
                impulse_volume_zscore = (impulse_volume - volume_mean) / volume_std
            else:
                impulse_volume_zscore = 0.0

            rolling_avg = volume_mean
        else:
            # Fallback: use current bar's volume as baseline
            impulse_volume_zscore = 0.0
            rolling_avg = impulse_volume

        # Decision Matrix
        gap_threshold = 1.5  # 1.5% gap threshold
        low_volume_threshold = 0.8  # 80% of average
        high_volume_threshold = 1.5  # 150% of average

        abs_gap = abs(opening_gap_pct)
        volume_ratio = impulse_volume / rolling_avg if rolling_avg > 0 else 1.0

        if abs_gap > gap_threshold and volume_ratio < low_volume_threshold:
            status = "FADING_GAP"
            recommendation = "Target Mean Reversion - Fade the gap"
        elif abs_gap > gap_threshold and volume_ratio > high_volume_threshold:
            status = "MOMENTUM_FLOW"
            recommendation = "Follow Gap Direction - Momentum trade"
        else:
            status = "LAMINAR_NORMAL"
            recommendation = "Standard RSI/Sentiment DNA"

        # Telemetry (ASCII ONLY)
        print(f"[RELEASE] Monday Status: {status}")
        print(f"[RELEASE] Gap: {opening_gap_pct:+.2f}% | Impulse: {impulse_volume_zscore:.2f} Sigma")
        print(f"[RELEASE] Open: ${open_price:.2f} | Friday Close: ${friday_close:.2f}")
        print(f"[RELEASE] Volume Ratio: {volume_ratio:.2f}x (Impulse: {impulse_volume:,} vs Avg: {rolling_avg:,.0f})")
        print(f"[RELEASE] Recommendation: {recommendation}")
        print("-" * 60)

        return {
            "status": status,
            "gap_pct": opening_gap_pct,
            "impulse_volume_zscore": impulse_volume_zscore,
            "recommendation": recommendation,
            "open_price": open_price,
            "friday_close": friday_close,
            "impulse_volume": impulse_volume,
            "volume_ratio": volume_ratio,
            "rolling_avg": rolling_avg,
        }

    except Exception as e:
        error_msg = f"Monday Release Logic error: {e}"
        print(f"[RELEASE] ERROR: {error_msg}")
        return {
            "status": "ERROR",
            "gap_pct": 0.0,
            "impulse_volume_zscore": 0.0,
            "recommendation": "LAMINAR_NORMAL",
            "message": error_msg,
        }
