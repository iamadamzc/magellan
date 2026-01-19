import pickle
from pathlib import Path

# Check both cache files
cache_files = [
    '.cache/fmp_news/8408e0d14265bfa19ebb74bbe6a30b87.pkl',
    '.cache/fmp_news/a21940d0f7e47c28ab5a75e456acb583.pkl'
]

for cache_path in cache_files:
    print(f"\n{'='*60}")
    print(f"Analyzing: {cache_path}")
    print('='*60)
    
    try:
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
        
        if not data:
            print("EMPTY CACHE FILE")
            continue
        
        print(f"Total articles: {len(data)}")
        print(f"\nFirst article:")
        print(f"  publishedDate: {data[0].get('publishedDate')}")
        print(f"  sentiment: {data[0].get('sentiment')}")
        print(f"  title: {data[0].get('title', '')[:60]}...")
        
        print(f"\nLast article:")
        print(f"  publishedDate: {data[-1].get('publishedDate')}")
        print(f"  sentiment: {data[-1].get('sentiment')}")
        
        # Check sentiment distribution
        sentiments = [article.get('sentiment', 0.0) for article in data]
        print(f"\nSentiment stats:")
        print(f"  Unique values: {len(set(sentiments))}")
        print(f"  All fields: {list(data[0].keys())}")
        
    except Exception as e:
        print(f"ERROR: {e}")
