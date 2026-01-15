"""
Phase 1: Alpaca Options API Connection Test

Tests connection to Alpaca Options API and verifies:
1. Account has options trading enabled
2. Can fetch options chains
3. Can retrieve quotes with bid/ask spreads
4. Data quality is acceptable

Run: python research/options_api_test.py

Expected Runtime: 30 seconds
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  WARNING: python-dotenv not installed")
    print("   Install: pip install python-dotenv")
    print("   Continuing anyway (will use system environment variables)...\n")

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import GetOptionContractsRequest
    from alpaca.data.historical import OptionHistoricalDataClient
    from alpaca.data.requests import OptionLatestQuoteRequest
except ImportError:
    print("❌ ERROR: alpaca-py not installed")
    print("   Fix: pip install alpaca-py")
    sys.exit(1)


class OptionsAPITester:
    """Test suite for Alpaca Options API connectivity and data quality."""
    
    def __init__(self):
        """Initialize API clients from environment variables."""
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not self.api_key or not self.secret_key:
            print("❌ ERROR: Alpaca credentials not found in environment")
            print("   Fix: Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in .env")
            sys.exit(1)
        
        self.paper = "paper" in self.base_url.lower()
        
        print(f"🔧 Initializing clients ({'PAPER' if self.paper else 'LIVE'} mode)...")
        
        try:
            self.trading_client = TradingClient(
                self.api_key,
                self.secret_key,
                paper=self.paper
            )
            
            self.data_client = OptionHistoricalDataClient(
                self.api_key,
                self.secret_key
            )
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize clients: {e}")
            sys.exit(1)
        
        print("✅ Clients initialized successfully\n")
    
    def test_account_status(self):
        """Test 1: Verify account has options trading enabled."""
        print("=" * 60)
        print("TEST 1: Account Status & Options Approval")
        print("=" * 60)
        
        try:
            account = self.trading_client.get_account()
            
            print(f"Account ID: {account.id}")
            print(f"Status: {account.status}")
            print(f"Buying Power: ${float(account.buying_power):,.2f}")
            print(f"Cash: ${float(account.cash):,.2f}")
            print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
            print(f"\n📊 Options Trading Level: {account.options_approved_level}")
            
            if account.options_approved_level == 0:
                print("\n❌ FAILURE: Options trading not enabled!")
                print("   → Visit Alpaca dashboard: Settings → Options Trading")
                print("   → Apply for Level 2 approval (required for buying calls/puts)")
                return False
            
            print(f"✅ PASS: Options Level {account.options_approved_level} approved")
            return True
        
        except Exception as e:
            print(f"❌ FAILURE: Could not retrieve account: {e}")
            return False
    
    def test_options_chain(self, symbol='SPY', min_dte=30, max_dte=60):
        """Test 2: Fetch options chain and verify data quality."""
        print("\n" + "=" * 60)
        print(f"TEST 2: Options Chain Data ({symbol})")
        print("=" * 60)
        
        try:
            # Calculate expiration range
            start_date = (datetime.now() + timedelta(days=min_dte)).strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=max_dte)).strftime('%Y-%m-%d')
            
            print(f"Fetching contracts: {start_date} to {end_date}")
            print(f"DTE Range: {min_dte}-{max_dte} days\n")
            
            # Fetch call options
            request_calls = GetOptionContractsRequest(
                underlying_symbols=[symbol],
                expiration_date_gte=start_date,
                expiration_date_lte=end_date,
                type='call'
            )
            
            response_calls = self.trading_client.get_option_contracts(request_calls)
            contracts_calls = list(response_calls.option_contracts) if hasattr(response_calls, 'option_contracts') else []
            
            # Fetch put options
            request_puts = GetOptionContractsRequest(
                underlying_symbols=[symbol],
                expiration_date_gte=start_date,
                expiration_date_lte=end_date,
                type='put'
            )
            
            response_puts = self.trading_client.get_option_contracts(request_puts)
            contracts_puts = list(response_puts.option_contracts) if hasattr(response_puts, 'option_contracts') else []
            
            print(f"✅ Found {len(contracts_calls)} CALL contracts")
            print(f"✅ Found {len(contracts_puts)} PUT contracts")
            print(f"✅ Total: {len(contracts_calls) + len(contracts_puts)} contracts")
            
            if len(contracts_calls) == 0:
                print("\n❌ FAILURE: No call contracts found!")
                print("   Possible causes:")
                print("   - DTE range too narrow (try 7-90 days)")
                print("   - Market closed (options data only available during market hours)")
                print("   - Symbol incorrect")
                return False, None
            
            # Display sample contracts
            print(f"\n📋 Sample CALL Contracts (first 5):")
            for i, contract in enumerate(contracts_calls[:5], 1):
                print(f"{i}. {contract.symbol}")
                print(f"   Strike: ${contract.strike_price}")
                print(f"   Expiry: {contract.expiration_date}")
                print(f"   Type: {contract.type}")
            
            print(f"\n📋 Sample PUT Contracts (first 5):")
            for i, contract in enumerate(contracts_puts[:5], 1):
                print(f"{i}. {contract.symbol}")
                print(f"   Strike: ${contract.strike_price}")
                print(f"   Expiry: {contract.expiration_date}")
                print(f"   Type: {contract.type}")
            
            print("\n✅ PASS: Options chain data retrieved successfully")
            
            # Return first call contract for quote test
            return True, contracts_calls[0].symbol if contracts_calls else None
        
        except Exception as e:
            print(f"❌ FAILURE: Could not fetch options chain: {e}")
            return False, None
    
    def test_option_quote(self, option_symbol):
        """Test 3: Fetch option quote and verify bid/ask spread quality."""
        print("\n" + "=" * 60)
        print(f"TEST 3: Option Quote Data")
        print("=" * 60)
        
        if not option_symbol:
            print("⚠️  SKIPPED: No option symbol provided (chain fetch failed)")
            return False
        
        try:
            print(f"Fetching quote for: {option_symbol}\n")
            
            request = OptionLatestQuoteRequest(symbol_or_symbols=option_symbol)
            quote_data = self.data_client.get_option_latest_quote(request)
            
            if option_symbol not in quote_data:
                print(f"❌ FAILURE: No quote data returned for {option_symbol}")
                return False
            
            quote = quote_data[option_symbol]
            
            # Extract quote details
            bid = float(quote.bid_price)
            ask = float(quote.ask_price)
            mid = (bid + ask) / 2.0
            spread = ask - bid
            spread_pct = (spread / mid * 100) if mid > 0 else 0
            
            print(f"Bid: ${bid:.2f}")
            print(f"Ask: ${ask:.2f}")
            print(f"Mid: ${mid:.2f}")
            print(f"Spread: ${spread:.2f} ({spread_pct:.2f}%)")
            
            # Data quality checks
            print("\n🔍 Data Quality Checks:")
            
            checks_passed = 0
            checks_total = 4
            
            # Check 1: Bid > 0
            if bid > 0:
                print(f"  ✅ Bid price is positive (${bid:.2f})")
                checks_passed += 1
            else:
                print(f"  ❌ Bid price is zero or negative (${bid:.2f})")
            
            # Check 2: Ask > Bid
            if ask > bid:
                print(f"  ✅ Ask > Bid (valid market)")
                checks_passed += 1
            else:
                print(f"  ❌ Ask <= Bid (invalid market)")
            
            # Check 3: Spread reasonable (<10% for liquid options)
            if spread_pct < 10.0:
                print(f"  ✅ Spread is reasonable ({spread_pct:.2f}% < 10%)")
                checks_passed += 1
            else:
                print(f"  ⚠️  Spread is wide ({spread_pct:.2f}% > 10%) - may be illiquid")
                checks_passed += 0.5  # Partial credit
            
            # Check 4: Mid price reasonable ($0.05 - $50 typical range)
            if 0.05 <= mid <= 50.0:
                print(f"  ✅ Mid price in reasonable range (${mid:.2f})")
                checks_passed += 1
            else:
                print(f"  ⚠️  Mid price outside typical range (${mid:.2f})")
                checks_passed += 0.5
            
            print(f"\nChecks Passed: {checks_passed}/{checks_total}")
            
            if checks_passed >= 3.5:
                print("✅ PASS: Option quote data quality is acceptable")
                return True
            else:
                print("⚠️  WARNING: Option quote data quality is questionable")
                print("   → May indicate illiquid contract or market data issues")
                return False
        
        except Exception as e:
            print(f"❌ FAILURE: Could not fetch option quote: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite."""
        print("\n" + "=" * 60)
        print("ALPACA OPTIONS API TEST SUITE")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Account Status
        results['account'] = self.test_account_status()
        
        # Test 2: Options Chain
        results['chain'], sample_symbol = self.test_options_chain(symbol='SPY')
        
        # Test 3: Option Quote
        results['quote'] = self.test_option_quote(sample_symbol)
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUITE SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, passed_flag in results.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            print(f"{test_name.upper()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 SUCCESS: All tests passed! Alpaca Options API is ready.")
            print("\n📋 Next Steps:")
            print("   1. Proceed to Phase 2 (Backtesting)")
            print("   2. See: docs/options/BACKTEST_BATTLE_PLAN.md")
            return True
        else:
            print("\n❌ FAILURE: Some tests failed. Review errors above.")
            print("\n📋 Troubleshooting:")
            print("   1. Check Alpaca dashboard for options approval")
            print("   2. Verify .env file has correct credentials")
            print("   3. Ensure testing during market hours (9:30 AM - 4:00 PM ET)")
            print("   4. See: docs/options/OPTIONS_OPERATIONS.md#troubleshooting")
            return False


def main():
    """Main entry point."""
    tester = OptionsAPITester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
