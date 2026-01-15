"""
Information Coefficient (IC) Analysis Script - Timeframe Ablation Scan

Purpose: Determine the optimal timeframe for trading NVDA.
Comparison: 1Min vs 5Min vs 1Hour vs 1Day

Hypothesis:
    - 1Min/5Min will show Negative IC (Mean Reversion)
    - 1Hour/1Day will show Positive IC (Momentum)

Usage:
    python inspect_ic.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import spearmanr
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Import Magellan components
from src.data_handler import AlpacaDataClient
from src.features import FeatureEngineer, add_technical_indicators

TIMEFRAMES = ['1Min', '5Min', '15Min', '1Hour']
DAYS = 60 # Shorten lookback for 1Min data to avoid API overload

def fetch_data(timeframe):
    """Fetch historical data for NVDA at specific timeframe."""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime('%Y-%m-%d')
    
    alpaca = AlpacaDataClient()
    try:
        print(f"   Fetching {timeframe}...", end="", flush=True)
        bars = alpaca.fetch_historical_bars(
            symbol='NVDA',
            start=start_date,
            end=end_date,
            timeframe=timeframe
        )
        print(f" Done ({len(bars)} bars)")
        return bars
    except Exception as e:
        print(f" Failed: {e}")
        return None

def generate_features(bars, timeframe):
    """Generate features with timeframe-adjusted lookahead."""
    df = bars.copy()
    
    # Base features
    df['log_return'] = FeatureEngineer.calculate_log_return(df)
    
    # Technicals
    df = add_technical_indicators(df, node_config=None)
    
    # Forward Return Window Adjustment
    # 1Min -> look 15 mins ahead (15 bars)
    # 5Min -> look 75 mins ahead (15 bars)
    # 1Hour -> look 15 hours ahead (15 bars) - maybe too long?
    # Let's standardize on ~1 hour horizon validity?
    # No, keep "15 bars" as the system logic is bar-based
    
    df['forward_return'] = df['close'].shift(-15) / df['close'] - 1.0
    
    return df.dropna()

def analyze_ic(df, timeframe):
    """Calculate IC for key features."""
    features = ['rsi_14', 'volume_zscore', 'log_return']
    results = []
    
    for feat in features:
        if feat in df.columns:
            ic, p_val = spearmanr(df[feat], df['forward_return'], nan_policy='omit')
            results.append({
                'timeframe': timeframe,
                'feature': feat,
                'ic': ic,
                'p_value': p_val,
                'bars': len(df)
            })
    return results

def main():
    print(f"\n🚀 Starting Timeframe Ablation Scan (NVDA)...")
    print(f"   Lookback: {DAYS} days")
    print("-" * 60)
    
    all_results = []
    
    for tf in TIMEFRAMES:
        bars = fetch_data(tf)
        if bars is not None:
            df = generate_features(bars, tf)
            res = analyze_ic(df, tf)
            all_results.extend(res)
            time.sleep(0.5)
            
    print("-" * 60)
    
    # Print Summary
    print("\n📊 TIMEFRAME PERFORMANCE MATRIX (NVDA)")
    print("="*60)
    print(f"{'Timeframe':<10} | {'Feature':<15} | {'IC':<10} | {'Type'}")
    print("-" * 60)
    
    for r in all_results:
        ic_type = "REVERSION (Short)" if r['ic'] < -0.02 else ("MOMENTUM (Long)" if r['ic'] > 0.02 else "NOISE")
        star = "⭐" if abs(r['ic']) > 0.05 else ""
        print(f"{r['timeframe']:<10} | {r['feature']:<15} | {r['ic']:+.4f} {star} | {ic_type}")

    # Save
    pd.DataFrame(all_results).to_csv("timeframe_scan.csv", index=False)
    print(f"\n💾 Results saved to timeframe_scan.csv")

if __name__ == '__main__':
    main()
