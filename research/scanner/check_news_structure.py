import yfinance as yf
import json

def test_news_structure():
    t = yf.Ticker("AAPL")
    news = t.news
    if news:
        print(json.dumps(news[0], indent=2))
    else:
        print("No news found")

if __name__ == "__main__":
    test_news_structure()
