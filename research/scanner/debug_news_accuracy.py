import yfinance as yf
import json

def check_news(ticker):
    print(f"\n--- Checking News for {ticker} ---")
    t = yf.Ticker(ticker)
    
    # Get Company Name for matching
    try:
        info = t.info
        short_name = info.get('shortName', 'Unknown')
        long_name = info.get('longName', 'Unknown')
        print(f"Company: {short_name} / {long_name}")
    except Exception as e:
        print(f"Could not fetch info: {e}")

    news = t.news
    if not news:
        print("No news found.")
        return

    for i, article in enumerate(news[:5]):
        title = article.get('title', '')
        if not title:
             title = article.get('content', {}).get('title', 'No Title')
             
        publisher = article.get('publisher', 'Unknown')
        link = article.get('link', '#')
        related_tickers = article.get('relatedTickers', [])
        
        print(f"\n[{i+1}] {title}")
        print(f"    Publisher: {publisher}")
        print(f"    Related Tickers: {related_tickers}")
        print(f"    Link: {link}")

if __name__ == "__main__":
    check_news("QNTM")
    check_news("LYRA")
