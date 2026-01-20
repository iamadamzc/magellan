"""
MAG7 Lockdown Verification Script
Tests hysteresis logic and edge-triggered logging
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.logger import LOG

def test_edge_triggered_logging():
    """Test that edge-triggered logging only prints on state changes."""
    print("\n" + "="*60)
    print("TEST 1: Edge-Triggered Logging")
    print("="*60)
    
    # Simulate AAPL state transitions
    print("\n[Expected: Print] AAPL first BUY signal:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.52 | Status: BUY")
    
    print("\n[Expected: SILENT] AAPL stays in BUY (no output):")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.53 | Status: BUY")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.54 | Status: BUY")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.51 | Status: BUY")
    
    print("\n[Expected: Print] AAPL transitions to FILTER:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.47 | Status: FILTER")
    
    print("\n[Expected: SILENT] AAPL stays in FILTER (no output):")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.48 | Status: FILTER")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.46 | Status: FILTER")
    
    print("\n[Expected: Print] AAPL transitions back to BUY:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: AAPL | Carrier: 0.53 | Status: BUY")
    
    print("\n" + "="*60)
    print("TEST 1 COMPLETE: Verify only state transitions printed")
    print("="*60)

def test_multi_ticker_independence():
    """Test that different tickers maintain independent state."""
    print("\n" + "="*60)
    print("TEST 2: Multi-Ticker State Independence")
    print("="*60)
    
    print("\n[Expected: Print] NVDA first BUY:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: NVDA | Carrier: 0.55 | Status: BUY")
    
    print("\n[Expected: Print] TSLA first FILTER:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: TSLA | Carrier: 0.48 | Status: FILTER")
    
    print("\n[Expected: SILENT] NVDA stays BUY, TSLA stays FILTER:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: NVDA | Carrier: 0.56 | Status: BUY")
    LOG.phase_lock("[PHASE-LOCK] Ticker: TSLA | Carrier: 0.47 | Status: FILTER")
    
    print("\n[Expected: Print] NVDA transitions to FILTER:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: NVDA | Carrier: 0.45 | Status: FILTER")
    
    print("\n[Expected: Print] TSLA transitions to BUY:")
    LOG.phase_lock("[PHASE-LOCK] Ticker: TSLA | Carrier: 0.54 | Status: BUY")
    
    print("\n" + "="*60)
    print("TEST 2 COMPLETE: Verify independent state tracking")
    print("="*60)

def test_hysteresis_concept():
    """Demonstrate hysteresis deadband concept."""
    print("\n" + "="*60)
    print("TEST 3: Hysteresis Deadband Concept")
    print("="*60)
    
    print("\nHysteresis prevents rapid oscillations at threshold boundaries.")
    print("\nWithout Hysteresis (CHATTER):")
    print("  Carrier: 0.499 -> FILTER")
    print("  Carrier: 0.501 -> BUY")
    print("  Carrier: 0.499 -> FILTER  <- RAPID FLIP")
    print("  Carrier: 0.502 -> BUY     <- RAPID FLIP")
    
    print("\nWith Hysteresis (STABLE):")
    print("  Carrier: 0.499 -> FILTER")
    print("  Carrier: 0.501 -> FILTER  <- STAYS (need 0.52 to flip)")
    print("  Carrier: 0.510 -> FILTER  <- STAYS (need 0.52 to flip)")
    print("  Carrier: 0.521 -> BUY     <- CLEAN FLIP (exceeded 0.52)")
    print("  Carrier: 0.510 -> BUY     <- STAYS (need 0.48 to flip back)")
    print("  Carrier: 0.479 -> FILTER  <- CLEAN FLIP (dropped below 0.48)")
    
    print("\nDeadband = 0.02")
    print("BUY Entry:  Carrier > 0.52 (Gate + 0.02)")
    print("BUY Exit:   Carrier < 0.48 (Gate - 0.02)")
    print("Neutral Zone: [0.48, 0.52] - No state change")
    
    print("\n" + "="*60)
    print("TEST 3 COMPLETE: Hysteresis concept explained")
    print("="*60)

def verify_mag7_config():
    """Verify MAG7 configuration loaded correctly."""
    print("\n" + "="*60)
    print("TEST 4: MAG7 Configuration Verification")
    print("="*60)
    
    import json
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'nodes', 'master_config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        mag7_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]
        etf_tickers = ["SPY", "QQQ", "IWM", "VTV", "VSS"]
        
        print("\nExpected MAG7 Tickers:")
        for ticker in mag7_tickers:
            if ticker in config:
                print(f"  ✓ {ticker} - FOUND")
            else:
                print(f"  ✗ {ticker} - MISSING (ERROR)")
        
        print("\nRemoved ETF Tickers:")
        for ticker in etf_tickers:
            if ticker not in config:
                print(f"  ✓ {ticker} - REMOVED")
            else:
                print(f"  ✗ {ticker} - STILL PRESENT (ERROR)")
        
        print(f"\nTotal tickers in config: {len(config)}")
        print(f"Expected: 7 (MAG7 only)")
        
        if len(config) == 7 and all(t in config for t in mag7_tickers):
            print("\n✓ MAG7 LOCKDOWN VERIFIED")
        else:
            print("\n✗ MAG7 LOCKDOWN FAILED")
    
    except Exception as e:
        print(f"\n✗ ERROR loading config: {e}")
    
    print("\n" + "="*60)
    print("TEST 4 COMPLETE: Configuration verification")
    print("="*60)

def main():
    """Run all verification tests."""
    print("\n" + "#"*60)
    print("# MAG7 LOCKDOWN & TELEMETRY SQUELCH VERIFICATION")
    print("#"*60)
    
    test_edge_triggered_logging()
    test_multi_ticker_independence()
    test_hysteresis_concept()
    verify_mag7_config()
    
    print("\n" + "#"*60)
    print("# ALL TESTS COMPLETE")
    print("#"*60)
    print("\nNOTE: Tests 1-2 verify edge-triggered logging.")
    print("      Only state transitions should produce output.")
    print("      Stable states (BUY->BUY, FILTER->FILTER) are SILENT.")
    print("\n      Test 3 explains hysteresis concept (no code execution).")
    print("      Test 4 verifies MAG7 configuration file.")
    print("\n" + "#"*60)

if __name__ == "__main__":
    main()
