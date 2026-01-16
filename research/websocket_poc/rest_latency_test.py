"""
Alpaca REST API Latency Test - Task 4 (FIXED)
Measures baseline REST API latency from laptop

FIXES:
- Removed duplicate /v2 in BASE_URL
- Using base URL without version path

Goal: Establish baseline latency for comparison
Success: Complete 100 requests, report statistics
"""

import time
import os
from dotenv import load_dotenv
import statistics
from datetime import datetime

# Load environment variables
load_dotenv()

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    print("⚠️  alpaca-trade-api not installed")
    ALPACA_AVAILABLE = False

# Credentials - FIX: Use base URL without /v2
API_KEY = os.getenv('APCA_API_KEY_ID')
SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')
BASE_URL = 'https://paper-api.alpaca.markets'  # No /v2 suffix!


def test_api_latency(iterations=100):
    """Measure REST API round-trip latency"""
    
    if not ALPACA_AVAILABLE or not API_KEY or not SECRET_KEY:
        print("❌ Cannot run test")
        return None
    
    api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
    
    latencies = []
    print(f"\n🏓 Testing API latency ({iterations} requests)...\n")
    
    for i in range(iterations):
        start = time.time()
        try:
            # Simple API call
            api.get_account()
            latency_ms = (time.time() - start) * 1000
            latencies.append(latency_ms)
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i+1}/{iterations} | "
                      f"Last: {latency_ms:.0f}ms | "
                      f"Avg so far: {sum(latencies)/len(latencies):.0f}ms")
        except Exception as e:
            print(f"Error on request {i+1}: {e}")
            continue
    
    if not latencies:
        print("\n❌ No successful requests")
        return None
    
    return {
        'count': len(latencies),
        'mean': statistics.mean(latencies),
        'median': statistics.median(latencies),
        'min': min(latencies),
        'max': max(latencies),
        'p90': statistics.quantiles(latencies, n=10)[8] if len(latencies) >= 10 else None,
        'p99': statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else None,
    }


def print_results(results):
    """Print and save results"""
    if not results:
        return
    
    print("\n" + "="*60)
    print("📊 REST API LATENCY RESULTS")
    print("="*60)
    print(f"Requests: {results['count']}")
    print(f"Mean:     {results['mean']:.0f}ms")
    print(f"Median:   {results['median']:.0f}ms")
    print(f"Min:      {results['min']:.0f}ms")
    print(f"Max:      {results['max']:.0f}ms")
    if results['p90']:
        print(f"P90:      {results['p90']:.0f}ms")
    if results['p99']:
        print(f"P99:      {results['p99']:.0f}ms")
    print("="*60)
    
    # Evaluation
    if results['median'] < 100:
        print("\n✅ EXCELLENT latency!")
        print("   WebSocket will likely be <100ms")
        print("   AWS deployment may not be immediately necessary")
    elif results['median'] < 200:
        print("\n⚠️  GOOD latency")
        print("   WebSocket should achieve <150ms")
        print("   AWS would help for high-frequency strategies")
    else:
        print("\n❌ HIGH latency")
        print("   WebSocket may still be 200-300ms")
        print("   AWS deployment strongly recommended")
    
    # Save results
    with open('research/websocket_poc/rest_latency_results.txt', 'w') as f:
        f.write(f"Alpaca REST API Latency Test\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Requests: {results['count']}\n")
        f.write(f"Mean: {results['mean']:.0f}ms\n")
        f.write(f"Median: {results['median']:.0f}ms\n")
        f.write(f"Min: {results['min']:.0f}ms\n")
        f.write(f"Max: {results['max']:.0f}ms\n")
        if results['p90']:
            f.write(f"P90: {results['p90']:.0f}ms\n")
        if results['p99']:
            f.write(f"P99: {results['p99']:.0f}ms\n")
    
    print(f"\n💾 Results saved to: research/websocket_poc/rest_latency_results.txt\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📡 Alpaca REST API Latency Test")
    print("="*60)
    
    if ALPACA_AVAILABLE:
        print("✅ alpaca-trade-api installed")
    else:
        print("❌ alpaca-trade-api NOT installed")
        exit(1)
    
    if API_KEY and SECRET_KEY:
        print(f"✅ Alpaca credentials loaded (Key: {API_KEY[:8]}...)")
    else:
        print("❌ Alpaca credentials NOT found")
        exit(1)
    
    print("\nThis test measures baseline REST API latency")
    print("WebSocket latency will be compared against this baseline\n")
    
    input("Press Enter to start...")
    
    results = test_api_latency(100)
    print_results(results)
    
    print("\n✅ Test complete!")
    print("\nNEXT STEP: Run alpaca_ws_poc.py to test WebSocket latency")
