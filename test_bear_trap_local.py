"""
Test Bear Trap Strategy Locally
Validates logging and basic functionality before EC2 deployment
"""

import os
import sys
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deployable_strategies.bear_trap.bear_trap_strategy_production import BearTrapStrategy
import boto3

def get_alpaca_credentials():
    """Get credentials from AWS SSM"""
    ssm = boto3.client('ssm', region_name='us-east-2')
    account_id = 'PA3DDLQCBJSE'
    
    api_key = ssm.get_parameter(
        Name=f'/magellan/alpaca/{account_id}/API_KEY',
        WithDecryption=True
    )['Parameter']['Value']
    
    api_secret = ssm.get_parameter(
        Name=f'/magellan/alpaca/{account_id}/API_SECRET',
        WithDecryption=True
    )['Parameter']['Value']
    
    return api_key, api_secret

def test_strategy():
    """Test the Bear Trap strategy"""
    print("=" * 80)
    print("Bear Trap Strategy - Local Test")
    print("=" * 80)
    
    # Get credentials
    print("\n1. Retrieving Alpaca credentials from AWS SSM...")
    try:
        api_key, api_secret = get_alpaca_credentials()
        print("   ✓ Credentials retrieved")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Load config
    print("\n2. Loading configuration...")
    import json
    config_path = 'deployable_strategies/bear_trap/aws_deployment/config.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    print(f"   ✓ Config loaded: {len(config['symbols'])} symbols")
    
    # Initialize strategy
    print("\n3. Initializing Bear Trap strategy...")
    try:
        strategy = BearTrapStrategy(
            api_key=api_key,
            api_secret=api_secret,
            base_url="https://paper-api.alpaca.markets",
            symbols=config['symbols'],
            config=config
        )
        print("   ✓ Strategy initialized")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test account access
    print("\n4. Testing Alpaca account access...")
    try:
        status = strategy.get_status()
        print(f"   ✓ Account accessible")
        print(f"   - Open positions: {status['open_positions']}")
        print(f"   - P&L today: ${status['pnl_today']:.2f}")
        print(f"   - Trades today: {status['trades_today']}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test market data fetch
    print("\n5. Testing market data fetch...")
    try:
        strategy.process_market_data()
        print("   ✓ Market data processed")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Check logs
    print("\n6. Checking trade logs...")
    import glob
    log_files = glob.glob('logs/bear_trap_*.csv')
    if log_files:
        print(f"   ✓ Log files created: {len(log_files)}")
        for log_file in log_files:
            print(f"     - {log_file}")
    else:
        print("   ⚠ No log files created yet (expected if no trades)")
    
    # Test EOD report
    print("\n7. Testing EOD report generation...")
    try:
        strategy.generate_end_of_day_report()
        print("   ✓ EOD report generated")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nNext Steps:")
    print("1. Review logs in ./logs/ directory")
    print("2. Check Alpaca dashboard for any test orders")
    print("3. If everything looks good, deploy to EC2")
    print("\nTo deploy to EC2:")
    print("  git checkout deployment/aws-paper-trading-setup")
    print("  git merge feature/trade-logging-integration")
    print("  git push origin deployment/aws-paper-trading-setup")

if __name__ == '__main__':
    # Set AWS profile
    os.environ['AWS_PROFILE'] = 'magellan_deployer'
    
    test_strategy()
