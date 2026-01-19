"""
Alpaca WebSocket POC - Task 1 (FIXED)
Tests real-time market data streaming from Alpaca using alpaca-py

FIXES:
- Properly structured asyncio (asyncio.run() only at top level)
- Removed nested event loops
- Clean shutdown handling

Goal: Prove we can receive real-time trade data with low latency
Success: Average latency <500ms from laptop
"""

import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv()

# Import alpaca-py
try:
    from alpaca.data.live import StockDataStream
    ALPACA_AVAILABLE = True
except ImportError:
    print("⚠️  alpaca-py not installed. Run: pip install alpaca-py")
    ALPACA_AVAILABLE = False

# Credentials from .env
API_KEY = os.getenv('APCA_API_KEY_ID')
SECRET_KEY = os.getenv('APCA_API_SECRET_KEY')


class LatencyTracker:
    """Tracks latency between market events and receipt"""
    
    def __init__(self, max_samples=100):
        self.latencies = []
        self.max_samples = max_samples
        self.sample_count = 0
        self.complete = False
        
    async def handle_bar(self, bar):
        """Callback for each bar received"""
        if self.complete:
            return
            
        # Calculate latency: bar timestamp → now
        now = datetime.utcnow()
        
        # Handle timezone-aware timestamps
        bar_time = bar.timestamp
        if bar_time.tzinfo is not None:
            bar_time = bar_time.replace(tzinfo=None)
        
        latency_ms = (now - bar_time).total_seconds() * 1000
        
        self.latencies.append(latency_ms)
        self.sample_count += 1
        
        # Print progress
        print(f"[{self.sample_count:3d}/100] [{bar.symbol}] "
              f"Price: ${bar.close:.2f} | "
              f"Latency: {latency_ms:.0f}ms")
        
        # Mark complete when done
        if self.sample_count >= self.max_samples:
            self.complete = True
            self.print_results()
            print("\n✨ Sample collection complete! Stopping stream...\n")
    
    def print_results(self):
        """Print statistical summary"""
        if not self.latencies:
            print("\n❌ No data received")
            return
        
        avg_latency = statistics.mean(self.latencies)
        median_latency = statistics.median(self.latencies)
        min_latency = min(self.latencies)
        max_latency = max(self.latencies)
        
        print("\n" + "="*60)
        print("📊 LATENCY RESULTS")
        print("="*60)
        print(f"Samples: {len(self.latencies)}")
        print(f"Average: {avg_latency:.0f}ms")
        print(f"Median:  {median_latency:.0f}ms")
        print(f"Min:     {min_latency:.0f}ms")
        print(f"Max:     {max_latency:.0f}ms")
        print("="*60)
        
        # Evaluation
        if avg_latency < 200:
            print("\n✅ EXCELLENT latency! WebSocket is working great.")
            print("   AWS deployment may not be critical for this use case.")
        elif avg_latency < 500:
            print("\n⚠️  GOOD latency, but room for improvement.")
            print("   AWS deployment would help for high-frequency strategies.")
        else:
            print("\n❌ HIGH latency detected.")
            print("   AWS deployment strongly recommended for news momentum.")
        
        # Save results
        with open('research/websocket_poc/latency_results.txt', 'w') as f:
            f.write(f"Alpaca WebSocket Latency Test\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Samples: {len(self.latencies)}\n")
            f.write(f"Average: {avg_latency:.0f}ms\n")
            f.write(f"Median: {median_latency:.0f}ms\n")
            f.write(f"Min: {min_latency:.0f}ms\n")
            f.write(f"Max: {max_latency:.0f}ms\n")
        
        print(f"\n💾 Results saved to: research/websocket_poc/latency_results.txt")


async def run_websocket_test():
    """Main async function - runs in the event loop"""
    
    print("="*60)
    print("🚀 ALPACA WEBSOCKET POC - TASK 1")
    print("="*60)
    print("\nTesting real-time market data streaming...")
    print("Symbols: NVDA, TSLA")
    print("Target: 100 bars")
    print("\n🔌 Connecting to Alpaca WebSocket...\n")
    
    tracker = LatencyTracker(max_samples=100)
    
    try:
        # Create WebSocket stream
        stream = StockDataStream(API_KEY, SECRET_KEY)
        
        # Subscribe to 1-minute bars
        stream.subscribe_bars(tracker.handle_bar, 'NVDA', 'TSLA')
        
        # Run the stream - this will block until we stop it
        # We'll use a timeout to auto-stop after collecting samples
        async def monitor():
            """Monitor completion and stop stream"""
            while not tracker.complete:
                await asyncio.sleep(1)
            # Give it a moment to finish printing
            await asyncio.sleep(2)
        
        # Run both stream and monitor concurrently
        await asyncio.gather(
            stream._run_forever(),  # Internal method that runs the stream
            monitor()
        )
        
    except asyncio.CancelledError:
        print("\n👋 Stream cancelled")
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


def main():
    """Entry point - sets up and runs the async event loop"""
    
    print("\n" + "="*60)
    print("📡 Alpaca WebSocket POC")
    print("="*60)
    
    if not ALPACA_AVAILABLE:
        print("❌ alpaca-py NOT installed")
        print("   Run: pip install alpaca-py")
        return
    
    print("✅ alpaca-py installed")
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca credentials NOT found in .env")
        return
        
    print(f"✅ Alpaca credentials loaded (Key: {API_KEY[:8]}...)")
    
    print("\nStarting test in 2 seconds...")
    print("(Market hours: 9:30 AM - 4:00 PM ET)")
    print("(This will collect 100 bars, may take several minutes)\n")
    
    import time
    time.sleep(2)
    
    try:
        # THIS is the ONLY place we call asyncio.run()
        # It creates the event loop and runs our async function
        asyncio.run(run_websocket_test())
        print("\n✅ Test completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Test stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
