import requests
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")

# --- Configuration ---
FMP_STABLE_URL = "https://financialmodelingprep.com/stable"

def get_fmp_news(ticker, limit=10):
    """Fetches stock news from FMP."""
    if not FMP_API_KEY:
        return []
    
    url = f"{FMP_STABLE_URL}/news/stock?symbols={ticker}&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching FMP news for {ticker}: {e}")
    return []

def has_recent_news(ticker, hours=24):
    """
    Quick check if ticker has ANY news in last N hours.
    Used as hard filter for momentum scalping.
    """
    if not FMP_API_KEY:
        return False
    
    news = get_fmp_news(ticker, limit=5)
    if not news:
        return False
    
    cutoff = datetime.now() - timedelta(hours=hours)
    for item in news:
        pub_date = item.get('publishedDate', '')
        if pub_date:
            try:
                pub_dt = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S')
                if pub_dt >= cutoff:
                    return True
            except:
                continue
    return False


def get_insider_trading(ticker, limit=20):
    """
    Fetches recent insider trading activity.
    Returns list of significant 'P-Purchase' transactions in the last 30 days.
    """
    if not FMP_API_KEY:
        return []

    # Use search endpoint with symbol filter
    url = f"{FMP_STABLE_URL}/insider-trading/search?symbol={ticker}&page=0&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Filter for Purchases
            recent_buys = []
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            for item in data:
                t_date = item.get('filingDate', '1900-01-01')
                t_type = item.get('transactionType', '')
                
                if t_date >= cutoff_date and 'Purchase' in t_type:
                    recent_buys.append(item)
            return recent_buys
            
    except Exception as e:
        print(f"Error fetching insider trades for {ticker}: {e}")
    return []

def clean_html(raw_html):
    """Removes HTML tags from text."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def analyze_news(ticker):
    """
    Scans FMP News and Insider Trading for catalysts.
    Prioritizes:
    1. Dilution (Killer)
    2. Insider Buying (Validation)
    3. High Conviction News (Catalyst)
    """
    # Initialize Default Verdict
    result = {
        'headline': "No recent news found.",
        'verdict': "Neutral",
        'url': "#",
        'publisher': 'FMP'
    }

    # 1. Fetch Data
    news_items = get_fmp_news(ticker)
    insider_buys = get_insider_trading(ticker)

    # 2. Check Insider Trading First (Validation Boost)
    insider_msg = ""
    if insider_buys:
        count = len(insider_buys)
        last_buyer = insider_buys[0].get('reportingName', 'Unknown')
        insider_msg = f" | 🏛️ INSIDER BUY: {last_buyer} +{count-1 if count > 1 else 0} others"

    # 3. Analyze News Headlines
    danger_zone = [
        'offering', 'private placement', 'direct placement', 'direct offering', 
        'mixed shelf', 'warrants', 'dilution', 'secondary offering', 
        'shelf registration', 'atm offering'
    ]
    high_conviction = [
        'fda', 'approval', 'approved', 'patent', 'merger', 'acquisition', 
        'buyout', 'earnings', 'guidance', 'agreement', 'partnership', 'phase 2', 'phase 3',
        'results', 'data', 'contract', 'award', 'clinical', 'launch',
        'buyback', 'repurchase', 'beat', 'upgrade'
    ]
    fluff_keywords = [
        'why', 'moving', 'jumps', 'soars', 'plummets', 'stocks to watch', 
        'alert', 'prediction', 'analysis', 'technical', 'deadline', 'reminder'
    ]

    best_match = None
    
    # Process News Items (Filter to last 24 hours for momentum scalping)
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for item in news_items:
        headline = item.get('title', '')
        url = item.get('url', '#')
        publisher = item.get('site', 'Unknown')
        published_date = item.get('publishedDate', '')
        
        # Filter: Only news from last 24 hours
        if published_date:
            try:
                pub_dt = datetime.strptime(published_date, '%Y-%m-%d %H:%M:%S')
                if pub_dt < cutoff_time:
                    continue  # Skip old news
            except:
                pass  # If parsing fails, include the news item
        
        headline_lower = headline.lower()

        # Priority 1: DILUTION (Overrides everything)
        if any(k in headline_lower for k in danger_zone):
            return {
                'headline': f"⚠️ {headline}", 
                'verdict': "💀 DILUTION / OFFERING", 
                'url': url,
                'publisher': publisher
            }

        # Priority 2: CATALYST
        if any(k in headline_lower for k in high_conviction):
            # If we already have a catalyst, keep the most recent (first one usually)
            return {
                'headline': headline + insider_msg, 
                'verdict': "🔥 HIGH CONVICTION" + (" + INSIDERS" if insider_msg else ""), 
                'url': url,
                'publisher': publisher
            }

        # Priority 3: FLUFF
        if any(k in headline_lower for k in fluff_keywords):
            if best_match is None:
                best_match = {
                    'headline': headline, 
                    'verdict': "☁️ FLUFF / NOISE", 
                    'url': url,
                    'publisher': publisher
                }
        
        # Fallback: Neutral but relevant
        if best_match is None:
             best_match = {
                'headline': headline,
                'verdict': "Neutral",
                'url': url,
                'publisher': publisher
            }

    # If we found a match (Fluff or Neutral), return it
    if best_match:
        # Append insider msg if valuable
        if insider_msg:
             best_match['headline'] += insider_msg
             # Upgrade verdict if it was just noise/neutral but insiders are buying
             if "FLUFF" in best_match['verdict'] or "Neutral" in best_match['verdict']:
                 best_match['verdict'] = "✅ INSIDER VALIDATION"
        return best_match

    # If no news at all but Insiders bought
    if insider_buys:
        return {
            'headline': f"No News.{insider_msg}",
            'verdict': "✅ INSIDER PLAY",
            'url': "https://financialmodelingprep.com", # Generic
            'publisher': "FMP Insider"
        }

    return result

if __name__ == "__main__":
    # Test with a known ticker
    print("Testing FMP News Bot...")
    # You can change this to a ticker you know has news/insider activity
    print(analyze_news("AAPL"))
