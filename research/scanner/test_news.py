import yfinance as yf

def test_news():
    ticker = "AAPL" # Use a major ticker to ensure news exists
    print(f"Fetching news for {ticker}...")
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if news:
            print(f"Found {len(news)} articles.")
            print("First article:", news[0])
        else:
            print("No news found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_news()
