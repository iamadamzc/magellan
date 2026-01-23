"""
Intraday Analysis Module - Phase 3
Provides 1-minute granularity analysis for opening drive strength
"""

import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_STABLE_URL = "https://financialmodelingprep.com/stable"

logger = logging.getLogger(__name__)

def get_opening_drive_strength(ticker):
    """
    Calculates "Opening Drive Strength" - how strong the first 5 minutes are
    compared to historical first-5-minute averages.
    
    Returns:
        dict: {
            'first_5min_volume': int,
            'avg_first_5min_volume': int,
            'opening_drive_ratio': float,  # Current / Historical Avg
            'verdict': str  # "STRONG", "NORMAL", "WEAK"
        }
    """
    if not FMP_API_KEY:
        return None
    
    try:
        # Get today's 1-minute data
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Fetch 1-min bars for today
        url = f"{FMP_STABLE_URL}/historical-chart/1min?symbol={ticker}&from={today_start.strftime('%Y-%m-%d')}&to={now.strftime('%Y-%m-%d')}&apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data:
            return None
        
        # Filter for first 5 minutes after market open (9:30-9:35 AM EST = 8:30-8:35 CST)
        # Assuming data is in EST, adjust if needed
        first_5_bars = []
        for bar in data:
            bar_time = datetime.strptime(bar['date'], '%Y-%m-%d %H:%M:%S')
            # Check if between 9:30 and 9:35 EST (market open)
            if bar_time.hour == 9 and 30 <= bar_time.minute < 35:
                first_5_bars.append(bar)
        
        if not first_5_bars:
            return None
        
        # Calculate current first-5-min volume
        current_first_5_vol = sum(bar['volume'] for bar in first_5_bars)
        
        # Get historical data (last 20 trading days)
        hist_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        hist_url = f"{FMP_STABLE_URL}/historical-chart/1min?symbol={ticker}&from={hist_start}&to={today_start.strftime('%Y-%m-%d')}&apikey={FMP_API_KEY}"
        hist_response = requests.get(hist_url, timeout=10)
        
        if hist_response.status_code != 200:
            # Fallback: use current as baseline
            return {
                'first_5min_volume': current_first_5_vol,
                'avg_first_5min_volume': current_first_5_vol,
                'opening_drive_ratio': 1.0,
                'verdict': "NORMAL"
            }
        
        hist_data = hist_response.json()
        
        # Calculate average first-5-min volume over historical period
        daily_first_5_vols = []
        current_date = None
        daily_vol = 0
        
        for bar in hist_data:
            bar_time = datetime.strptime(bar['date'], '%Y-%m-%d %H:%M:%S')
            bar_date = bar_time.date()
            
            # Reset on new day
            if current_date != bar_date:
                if daily_vol > 0:
                    daily_first_5_vols.append(daily_vol)
                current_date = bar_date
                daily_vol = 0
            
            # Accumulate first 5 minutes
            if bar_time.hour == 9 and 30 <= bar_time.minute < 35:
                daily_vol += bar['volume']
        
        # Add last day
        if daily_vol > 0:
            daily_first_5_vols.append(daily_vol)
        
        if not daily_first_5_vols:
            avg_first_5 = current_first_5_vol
        else:
            avg_first_5 = sum(daily_first_5_vols) / len(daily_first_5_vols)
        
        # Calculate ratio
        ratio = current_first_5_vol / avg_first_5 if avg_first_5 > 0 else 1.0
        
        # Verdict
        if ratio >= 3.0:
            verdict = "🔥 EXPLOSIVE"
        elif ratio >= 1.5:
            verdict = "💪 STRONG"
        elif ratio >= 0.8:
            verdict = "➡️ NORMAL"
        else:
            verdict = "⚠️ WEAK"
        
        return {
            'first_5min_volume': current_first_5_vol,
            'avg_first_5min_volume': int(avg_first_5),
            'opening_drive_ratio': round(ratio, 2),
            'verdict': verdict
        }
        
    except Exception as e:
        logger.error(f"Error calculating opening drive for {ticker}: {e}")
        return None


def get_earnings_transcript_sentiment(ticker):
    """
    Fetches the latest earnings transcript and scans for bullish/bearish keywords.
    
    Returns:
        dict: {
            'quarter': str,
            'sentiment': str,  # "BULLISH", "BEARISH", "NEUTRAL"
            'keywords_found': list,
            'snippet': str
        }
    """
    if not FMP_API_KEY:
        return None
    
    try:
        # Get latest transcript
        url = f"{FMP_STABLE_URL}/earning-call-transcript-latest?symbol={ticker}&apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        if not data:
            return None
        
        transcript = data[0] if isinstance(data, list) else data
        content = transcript.get('content', '').lower()
        
        if not content:
            return None
        
        # Bullish keywords
        bullish = [
            'guidance raised', 'beat expectations', 'exceeded', 'strong demand',
            'record revenue', 'accelerating growth', 'expanding margins',
            'ai opportunity', 'market share gains', 'outperformed'
        ]
        
        # Bearish keywords
        bearish = [
            'guidance lowered', 'missed expectations', 'headwinds', 'challenges',
            'declining revenue', 'margin pressure', 'competitive pressure',
            'slowing growth', 'uncertainty', 'restructuring'
        ]
        
        bullish_found = [kw for kw in bullish if kw in content]
        bearish_found = [kw for kw in bearish if kw in content]
        
        # Determine sentiment
        if len(bullish_found) > len(bearish_found) + 2:
            sentiment = "🚀 BULLISH"
        elif len(bearish_found) > len(bullish_found) + 2:
            sentiment = "📉 BEARISH"
        else:
            sentiment = "➡️ NEUTRAL"
        
        # Extract snippet
        snippet = content[:200] + "..." if len(content) > 200 else content
        
        return {
            'quarter': f"{transcript.get('year', 'N/A')} Q{transcript.get('quarter', 'N/A')}",
            'sentiment': sentiment,
            'keywords_found': bullish_found + bearish_found,
            'snippet': snippet
        }
        
    except Exception as e:
        logger.error(f"Error analyzing transcript for {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Test
    print("Testing Intraday Analysis...")
    print("\n1. Opening Drive Strength (AAPL):")
    result = get_opening_drive_strength("AAPL")
    print(result)
    
    print("\n2. Earnings Transcript Sentiment (AAPL):")
    result = get_earnings_transcript_sentiment("AAPL")
    print(result)
