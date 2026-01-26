"""
Sentiment Diagnostic Script
Tests what FMP actually returns for SPY news sentiment
"""

import os
import sys

# Load environment from .env file manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Check if FMP_API_KEY is set
fmp_key = os.getenv('FMP_API_KEY')
if not fmp_key:
    print("[ERROR] FMP_API_KEY not found in environment or .env file")
    sys.exit(1)

print(f"[OK] FMP_API_KEY found: {fmp_key[:4]}...{fmp_key[-4:]}")

import requests
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter

# Configuration
symbol = 'SPY'
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print(f"\n{'='*60}")
print(f"SENTIMENT DIAGNOSTIC FOR {symbol}")
print(f"Date Range: {start_str} to {end_str}")
print(f"{'='*60}")

# Fetch from FMP Stable API
url = "https://financialmodelingprep.com/stable/news/stock"
params = {
    'symbols': symbol,
    'from': start_str,
    'to': end_str,
    'apikey': fmp_key
}

print(f"\n[1] Fetching news from FMP Stable API...")
try:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    print(f"[OK] Received {len(data)} articles")
except Exception as e:
    print(f"[ERROR] Failed to fetch: {e}")
    sys.exit(1)

if not data:
    print("[WARNING] No articles returned!")
    sys.exit(0)

# Analyze sentiment field
print(f"\n[2] Analyzing sentiment field in {len(data)} articles...")
print("-" * 60)

sentiment_values = []
sentiment_types = []
articles_with_sentiment = 0
articles_without_sentiment = 0

for i, article in enumerate(data[:20]):  # Show first 20
    title = article.get('title', 'No title')[:50]
    pub_date = article.get('publishedDate', 'Unknown')
    sentiment = article.get('sentiment', None)
    
    if sentiment is not None:
        articles_with_sentiment += 1
        sentiment_values.append(sentiment)
        sentiment_types.append(type(sentiment).__name__)
    else:
        articles_without_sentiment += 1
    
    sent_display = f"'{sentiment}'" if sentiment is not None else "NULL"
    print(f"  [{i+1}] {pub_date[:16]} | Sentiment: {sent_display:12} | {title}...")

print("-" * 60)

# Summary statistics
print(f"\n[3] SENTIMENT FIELD SUMMARY")
print("=" * 60)
print(f"Total Articles:              {len(data)}")
print(f"Articles WITH sentiment:     {articles_with_sentiment}")
print(f"Articles WITHOUT sentiment:  {articles_without_sentiment}")

if sentiment_values:
    # Count unique values
    value_counts = Counter(sentiment_values)
    print(f"\nUnique sentiment values:     {len(value_counts)}")
    print(f"\nValue distribution:")
    for val, count in value_counts.most_common(10):
        pct = (count / len(sentiment_values)) * 100
        print(f"  '{val}': {count} ({pct:.1f}%)")
    
    # Check if all values are the same
    if len(value_counts) == 1:
        print(f"\n🚨 CRITICAL: ALL sentiment values are IDENTICAL!")
        print(f"   This triggers the frequency-proxy fallback!")
    elif len(value_counts) <= 3:
        print(f"\n⚠️ WARNING: Only {len(value_counts)} unique sentiment values")
        print(f"   Limited sentiment diversity may reduce signal quality")
    else:
        print(f"\n✓ Sentiment has {len(value_counts)} unique values - appears usable")

else:
    print(f"\n🚨 CRITICAL: NO sentiment values found in any article!")
    print(f"   The 'sentiment' factor is ENTIRELY based on article count!")

# Check data types
if sentiment_types:
    type_counts = Counter(sentiment_types)
    print(f"\nData types in sentiment field:")
    for t, count in type_counts.items():
        print(f"  {t}: {count}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
