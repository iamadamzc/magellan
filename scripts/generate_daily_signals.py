"""
Daily Signal Generator for Regime Sentiment Filter
--------------------------------------------------
Run this script daily after market close to generate trading signals
for the next day.

Usage:
    python scripts/generate_daily_signals.py

Logic:
    1. Update data for all Tier 1 assets
    2. Check entry/exit conditions on the latest bar
    3. Output clear ACTIONABLE signals
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import argparse
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
from src.data_handler import FMPDataClient

# Define Tier 1 Assets
TIER_1_ASSETS = ['META', 'NVDA', 'AMZN', 'COIN', 'QQQ']
TIER_2_ASSETS = ['PLTR', 'AAPL', 'MSFT', 'SPY', 'AMD', 'NFLX']

def get_latest_sentiment(symbol):
    """Fetch latest sentiment for a symbol"""
    fmp = FMPDataClient()
    # Fetch last 30 days of news to ensure we have recent context
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    
    news = fmp.fetch_historical_news(symbol, start_date, end_date)
    if not news:
        return 0.0
    
    # Calculate sentiment from last 5 articles
    df = pd.DataFrame(news)
    df['publishedDate'] = pd.to_datetime(df['publishedDate'])
    df = df.sort_values('publishedDate')
    
    recent = df.tail(10)
    if len(recent) == 0:
        return 0.0
        
    return recent['sentiment'].mean()

def calculate_indicators(df):
    """Calculate RSI and Regime"""
    # RSI 28
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=28).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=28).mean()
    rs = gain / loss
    df['rsi_28'] = 100 - (100 / (1 + rs))
    
    # SPY Regime (would need SPY data)
    # For now, we'll assume SPY data is passed in or fetched separately
    return df

def get_spy_regime():
    """Check if SPY is in bull regime (Price > 200 MA)"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - pd.Timedelta(days=400)).strftime('%Y-%m-%d')
    
    df = cache.get_or_fetch_equity('SPY', '1day', start_date, end_date)
    df['ma_200'] = df['close'].rolling(200).mean()
    
    last_close = df['close'].iloc[-1]
    last_ma = df['ma_200'].iloc[-1]
    
    return 1 if last_close > last_ma else 0, last_close, last_ma

def analyze_asset(symbol, spy_regime):
    """Analyze a single asset for signals"""
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - pd.Timedelta(days=100)).strftime('%Y-%m-%d')
    
    # Get Price Data
    df = cache.get_or_fetch_equity(symbol, '1day', start_date, end_date)
    df = calculate_indicators(df)
    
    last_row = df.iloc[-1]
    rsi = last_row['rsi_28']
    price = last_row['close']
    date = df.index[-1]
    
    # Get Sentiment
    sentiment = get_latest_sentiment(symbol)
    
    # Logic
    # Entry Path 1: Bull Regime
    bull_entry = (rsi > 55) and (spy_regime == 1) and (sentiment > -0.2)
    
    # Entry Path 2: Strong Breakout
    strong_entry = (rsi > 65) and (sentiment > 0.0)
    
    # Exit
    exit_signal = (rsi < 45) or (sentiment < -0.3)
    
    signal = "HOLD/FLAT"
    details = []
    
    if bull_entry or strong_entry:
        signal = "BUY/LONG"
        if bull_entry: details.append("Bull Regime Entry (RSI > 55, SPY > 200MA)")
        if strong_entry: details.append("Strong Breakout (RSI > 65)")
    elif exit_signal:
        signal = "SELL/EXIT"
        if rsi < 45: details.append("Momentum Loss (RSI < 45)")
        if sentiment < -0.3: details.append("Negative Sentiment")
    
    return {
        "symbol": symbol,
        "date": date,
        "price": price,
        "rsi": rsi,
        "sentiment": sentiment,
        "signal": signal,
        "details": ", ".join(details)
    }

def main():
    print("="*80)
    print(f"DAILY SIGNAL GENERATOR - {datetime.now().strftime('%Y-%m-%d')}")
    print("="*80)
    
    # Check SPY Regime
    try:
        spy_status, spy_price, spy_ma = get_spy_regime()
        regime_str = "BULL" if spy_status == 1 else "BEAR"
        print(f"MARKET REGIME: {regime_str} (SPY ${spy_price:.2f} vs 200MA ${spy_ma:.2f})")
    except Exception as e:
        print(f"Error fetching SPY regime: {e}")
        spy_status = 0
    
    print("-" * 80)
    print(f"{'ASSET':<6} {'RSI':<6} {'SENT':<6} {'SIGNAL':<10} {'DETAILS'}")
    print("-" * 80)
    
    all_assets = TIER_1_ASSETS
    
    for symbol in all_assets:
        try:
            res = analyze_asset(symbol, spy_status)
            
            # Color coding (if terminal supports it, otherwise plain text)
            sig = res['signal']
            
            print(f"{symbol:<6} {res['rsi']:<6.1f} {res['sentiment']:<6.2f} {sig:<10} {res['details']}")
            
        except Exception as e:
            print(f"{symbol:<6} ERROR: {e}")
            
    print("-" * 80)
    print("NOTE: Verify all signals with chart visual inspection before execution.")

if __name__ == "__main__":
    main()
