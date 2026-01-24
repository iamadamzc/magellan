
import logging
from gap_hunter import AlpacaScanner
import pandas as pd

# Setup concise logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("gap_hunter")
logger.setLevel(logging.DEBUG)

def debug_scan():
    print("--- STARTING DEBUG SCAN ---")
    scanner = AlpacaScanner()
    
    # 1. SET WIDE PARAMETERS (Matching User's screenshot)
    scanner.MIN_PRICE = 2.0
    scanner.MAX_PRICE = 60.0
    scanner.MIN_DAY_CHANGE_PCT = 0.03 # 3%
    scanner.MAX_FLOAT = 250_000_000
    scanner.MIN_RVOL = 0.5
    
    print(f"Params: Price={scanner.MIN_PRICE}-{scanner.MAX_PRICE}, Gap>={scanner.MIN_DAY_CHANGE_PCT*100}%, Float<={scanner.MAX_FLOAT}, RVOL>={scanner.MIN_RVOL}")

    # 2. UNIVERSE
    universe = scanner.get_universe()
    print(f"DEBUG: Universe Size: {len(universe)}")
    if not universe: return

    # 3. SNAPSHOTS (Pre-Filter)
    # We will inspect what get_snapshots returns
    df_snaps = scanner.get_snapshots(universe)
    print(f"DEBUG: Candidates after Snapshot Filter: {len(df_snaps)}")
    if not df_snaps.empty:
        print("Top 5 Pre-Filter Candidates:")
        print(df_snaps[['Ticker', 'Price', 'Gap%', 'DollarVol']].head())
    else:
        print("DEBUG: ALL candidates failed snapshot filter (Price/DollarVol/Gap)!")
        return

    # 4. HISTORY & RVOL
    df_hist = scanner.get_history_and_rvol(df_snaps)
    print(f"DEBUG: Candidates after History/RVOL Filter: {len(df_hist)}")
    
    # Check who failed
    if not df_snaps.empty and df_hist.empty:
         print("DEBUG: All candidates dropped at History/RVOL stage.")
         # Let's see why - we can't easily see inside the method without modifying it, 
         # but the previous logs showed "Using standard RVOL threshold".
         
    if not df_hist.empty:
        print("Top 5 Post-RVOL Candidates:")
        print(df_hist[['Ticker', 'RVOL', 'Warmup']].head())

    # 5. FLOAT
    df_float = scanner.enrich_float(df_hist)
    print(f"DEBUG: Candidates after Float Filter: {len(df_float)}")
    
    if not df_float.empty:
        print("Top 5 Final Candidates:")
        print(df_float[['Ticker', 'Float (M)', 'Score']].head())

if __name__ == "__main__":
    debug_scan()
