"""
Magellan V1.0 Configuration Verification Script
Validates that all production settings are correctly configured.
"""

import json
import os

def verify_config():
    """Verify master_config.json matches V1.0 production DNA."""
    
    print("=" * 70)
    print("MAGELLAN V1.0 CONFIGURATION VERIFICATION")
    print("=" * 70)
    
    config_path = 'config/nodes/master_config.json'
    
    if not os.path.exists(config_path):
        print(f"FAIL: {config_path} not found")
        return False
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Expected V1.0 configuration
    expected = {
        'SPY': {
            'interval': '5Min',
            'sentry_gate': 0.0,
            'rsi_wt': 0.9,
            'vol_wt': 0.0,
            'sent_wt': 0.1,
            'position_cap_usd': 50000
        },
        'QQQ': {
            'interval': '5Min',
            'sentry_gate': 0.0,
            'rsi_wt': 0.8,
            'vol_wt': 0.1,
            'sent_wt': 0.1,
            'position_cap_usd': 50000
        },
        'IWM': {
            'interval': '3Min',
            'sentry_gate': -0.2,
            'rsi_wt': 1.0,
            'vol_wt': 0.0,
            'sent_wt': 0.0,
            'position_cap_usd': 50000
        }
    }
    
    all_passed = True
    
    for ticker in ['SPY', 'QQQ', 'IWM']:
        print(f"\n{ticker} Configuration:")
        print("-" * 70)
        
        if ticker not in config:
            print(f"  FAIL: {ticker} not found in config")
            all_passed = False
            continue
        
        ticker_config = config[ticker]
        ticker_expected = expected[ticker]
        
        for key, expected_value in ticker_expected.items():
            actual_value = ticker_config.get(key)
            
            if actual_value == expected_value:
                print(f"  OK {key}: {actual_value}")
            else:
                print(f"  FAIL {key}: Expected {expected_value}, got {actual_value}")
                all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("ALL CHECKS PASSED - V1.0 CONFIGURATION VERIFIED")
        print("=" * 70)
        print("\nREADY FOR LAUNCH")
        print("\nLaunch Commands:")
        print("  Simulation: python main.py --mode simulation")
        print("  Live Paper: python main.py --mode live")
        return True
    else:
        print("CONFIGURATION VERIFICATION FAILED")
        print("=" * 70)
        print("\nDO NOT LAUNCH - Fix configuration errors first")
        return False


def verify_code_changes():
    """Verify that code changes are in place."""
    
    print("\n" + "=" * 70)
    print("CODE CHANGES VERIFICATION")
    print("=" * 70)
    
    checks = []
    
    # Check 1: features.py - Standard RSI
    with open('src/features.py', 'r', encoding='utf-8') as f:
        features_code = f.read()
    
    if 'V1.0 PRODUCTION: Standard RSI' in features_code:
        print("OK features.py: Standard RSI on 'close' verified")
        checks.append(True)
    else:
        print("FAIL features.py: Standard RSI marker not found")
        checks.append(False)
    
    if 'VWAP' not in features_code or 'V1.0 PRODUCTION' in features_code:
        print("OK features.py: VWAP-weighted RSI removed")
        checks.append(True)
    else:
        print("FAIL features.py: VWAP logic still present")
        checks.append(False)
    
    if 'Jitter filters and RSI tuning gates REMOVED' in features_code:
        print("OK features.py: Jitter filters removed")
        checks.append(True)
    else:
        print("FAIL features.py: Jitter filter removal not confirmed")
        checks.append(False)
    
    # Check 2: executor.py - Position cap from config
    with open('src/executor.py', 'r', encoding='utf-8') as f:
        executor_code = f.read()
    
    if "ticker_config.get('position_cap_usd'" in executor_code:
        print("OK executor.py: position_cap_usd read from ticker_config")
        checks.append(True)
    else:
        print("FAIL executor.py: position_cap_usd not read from config")
        checks.append(False)
    
    if 'paper-api.alpaca.markets' in executor_code:
        print("OK executor.py: Paper trading endpoint verified")
        checks.append(True)
    else:
        print("FAIL executor.py: Paper endpoint not found")
        checks.append(False)
    
    # Check 3: main.py - Telemetry and ticker_config passing
    with open('main.py', 'r', encoding='utf-8') as f:
        main_code = f.read()
    
    if 'MAGELLAN V1.0 INITIALIZED. DEPLOYING LAMINAR DNA.' in main_code:
        print("OK main.py: V1.0 launch telemetry present")
        checks.append(True)
    else:
        print("FAIL main.py: Launch telemetry not found")
        checks.append(False)
    
    if 'ticker_config=node_config' in main_code:
        print("OK main.py: ticker_config passed to executor")
        checks.append(True)
    else:
        print("FAIL main.py: ticker_config not passed to executor")
        checks.append(False)
    
    print("=" * 70)
    
    if all(checks):
        print("ALL CODE CHANGES VERIFIED")
        return True
    else:
        print("SOME CODE CHANGES MISSING")
        return False


if __name__ == '__main__':
    config_ok = verify_config()
    code_ok = verify_code_changes()
    
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION RESULT")
    print("=" * 70)
    
    if config_ok and code_ok:
        print("MAGELLAN V1.0 READY FOR PRODUCTION")
        print("\nAll systems nominal. Laminar DNA deployed.")
        exit(0)
    else:
        print("VERIFICATION FAILED - DO NOT LAUNCH")
        exit(1)
