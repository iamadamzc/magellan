"""
Hangar Observation Layer (ORH)
Weekend and pre-market kinetic potential energy analysis.
Observes Opening Range High (ORH) patterns without executing trades.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List


def _setup_hangar_logger() -> logging.Logger:
    """Set up logger for hangar observations."""
    logger = logging.Logger('hangar_observation')
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.FileHandler('hangar_observation.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
    
    return logger


def calculate_kinetic_potential(
    current_price: float,
    friday_close: float,
    volume_zscore: float
) -> float:
    """
    Calculate Kinetic Potential Energy (Ep).
    
    Ep = (Current_ORH_Price - Friday_Close_Price) * (ORH_Volume_ZScore)
    
    This metric measures the "potential energy" built up during the opening range,
    weighted by volume activity. High Ep suggests strong directional momentum.
    
    Args:
        current_price: Current ORH price
        friday_close: Previous Friday's closing price
        volume_zscore: Z-score of current volume vs historical average
    
    Returns:
        Kinetic potential energy value
    """
    price_delta = current_price - friday_close
    ep = price_delta * volume_zscore
    return ep


def analyze_orh_bars(
    orh_bars: pd.DataFrame,
    friday_close: float,
    ticker: str
) -> Dict:
    """
    Analyze Opening Range High (ORH) bars for kinetic potential.
    
    Args:
        orh_bars: DataFrame with 1-hour ORH bars (OHLCV)
        friday_close: Previous Friday's closing price
        ticker: Symbol being analyzed
    
    Returns:
        Dict with ORH analysis results
    """
    logger = _setup_hangar_logger()
    
    if len(orh_bars) == 0:
        return {
            'ticker': ticker,
            'error': 'No ORH bars available',
            'ep': 0.0,
            'status': 'NO_DATA'
        }
    
    # Calculate volume Z-score for ORH period
    volume_mean = orh_bars['volume'].mean()
    volume_std = orh_bars['volume'].std()
    
    if volume_std > 0:
        current_volume = orh_bars['volume'].iloc[-1]
        volume_zscore = (current_volume - volume_mean) / volume_std
    else:
        volume_zscore = 0.0
    
    # Get current ORH price (last close in the ORH window)
    current_price = orh_bars['close'].iloc[-1]
    
    # Calculate Kinetic Potential Energy
    ep = calculate_kinetic_potential(current_price, friday_close, volume_zscore)
    
    # Determine status
    if abs(ep) > 1.0:
        status = "Building"
    elif abs(ep) > 0.5:
        status = "Moderate"
    else:
        status = "Stagnant"
    
    # Telemetry
    print(f"[HANGAR] {ticker} Potential Energy (Ep): {ep:.4f} | Status: {status}")
    print(f"[HANGAR] {ticker} Price: ${current_price:.2f} (Friday Close: ${friday_close:.2f})")
    print(f"[HANGAR] {ticker} Volume Z-Score: {volume_zscore:.2f}")
    
    # Log to file
    log_entry = (
        f"TICKER={ticker} | EP={ep:.4f} | STATUS={status} | "
        f"CURRENT_PRICE=${current_price:.2f} | FRIDAY_CLOSE=${friday_close:.2f} | "
        f"VOLUME_ZSCORE={volume_zscore:.2f}"
    )
    logger.info(log_entry)
    
    return {
        'ticker': ticker,
        'ep': ep,
        'status': status,
        'current_price': current_price,
        'friday_close': friday_close,
        'volume_zscore': volume_zscore,
        'price_delta': current_price - friday_close,
        'price_delta_pct': ((current_price - friday_close) / friday_close) * 100
    }


def run_hangar_observation(
    tickers: List[str],
    alpaca_client,
    lookback_days: int = 5
) -> Dict[str, Dict]:
    """
    Run Hangar Observation Layer for multiple tickers.
    
    Fetches 1-hour ORH bars and calculates kinetic potential energy
    without executing any trades (observation mode only).
    
    Args:
        tickers: List of ticker symbols to observe
        alpaca_client: AlpacaDataClient instance
        lookback_days: Days to look back for Friday close (default: 5)
    
    Returns:
        Dict mapping ticker symbols to their ORH analysis results
    """
    from alpaca.data.timeframe import TimeFrame
    
    print("\n" + "=" * 70)
    print("[HANGAR] OBSERVATION MODE - ORH KINETIC POTENTIAL ANALYSIS")
    print("=" * 70)
    print("[SAFETY] Trade execution DISABLED - Observation only")
    print("=" * 70)
    
    logger = _setup_hangar_logger()
    logger.info("=" * 70)
    logger.info("HANGAR OBSERVATION SESSION STARTED")
    logger.info("=" * 70)
    
    results = {}
    
    # Determine date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    
    # Find previous Friday's close
    # Go back up to 7 days to find the most recent Friday
    friday_date = end_date
    while friday_date.weekday() != 4:  # 4 = Friday
        friday_date -= timedelta(days=1)
        if (end_date - friday_date).days > 7:
            print("[HANGAR] WARNING: Could not find recent Friday, using 5 days ago")
            friday_date = end_date - timedelta(days=5)
            break
    
    print(f"[HANGAR] Reference Friday: {friday_date.strftime('%Y-%m-%d')}")
    print(f"[HANGAR] Observation Window: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("-" * 70)
    
    for ticker in tickers:
        print(f"\n[HANGAR] Analyzing {ticker}...")
        
        try:
            # Fetch 1-hour bars for ORH analysis
            orh_bars = alpaca_client.fetch_historical_bars(
                symbol=ticker,
                timeframe=TimeFrame.Hour,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                feed='sip'
            )
            
            print(f"[HANGAR] {ticker}: Fetched {len(orh_bars)} 1-hour bars")
            
            # Get Friday's closing price
            friday_str = friday_date.strftime('%Y-%m-%d')
            friday_end_str = (friday_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            friday_bars = alpaca_client.fetch_historical_bars(
                symbol=ticker,
                timeframe=TimeFrame.Day,
                start=friday_str,
                end=friday_end_str,
                feed='sip'
            )
            
            if len(friday_bars) > 0:
                friday_close = friday_bars['close'].iloc[-1]
            else:
                # Fallback: use first available close in ORH bars
                print(f"[HANGAR] {ticker}: Friday close not available, using first ORH bar")
                friday_close = orh_bars['close'].iloc[0] if len(orh_bars) > 0 else 0.0
            
            # Analyze ORH bars
            analysis = analyze_orh_bars(orh_bars, friday_close, ticker)
            results[ticker] = analysis
            
        except Exception as e:
            error_msg = f"Error analyzing {ticker}: {e}"
            print(f"[HANGAR] {error_msg}")
            logger.error(error_msg)
            results[ticker] = {
                'ticker': ticker,
                'error': str(e),
                'ep': 0.0,
                'status': 'ERROR'
            }
    
    # Summary
    print("\n" + "=" * 70)
    print("[HANGAR] OBSERVATION SUMMARY")
    print("=" * 70)
    
    for ticker, result in results.items():
        if 'error' not in result:
            print(f"{ticker:6} | Ep: {result['ep']:+8.4f} | Status: {result['status']:10} | "
                  f"Price Delta: {result['price_delta_pct']:+6.2f}%")
        else:
            print(f"{ticker:6} | ERROR: {result['error']}")
    
    print("=" * 70)
    print(f"[HANGAR] Observations logged to: hangar_observation.log")
    print("=" * 70)
    
    logger.info("=" * 70)
    logger.info("HANGAR OBSERVATION SESSION COMPLETED")
    logger.info("=" * 70)
    
    return results
