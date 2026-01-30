"""
=============================================================================
DATA FORENSIC AUDIT: Targeted & Random Integrity Check
=============================================================================

PROTOCOL:
- Mandatory Targets: 2025-01-02 (Ghost Crash?), 2025-01-27 (DeepSeek Crash)
- Random Sampling: 10 additional random dates
- External Truth: yfinance NQ=F (Nasdaq 100 Futures)
- Comparison: My data vs Official Exchange Data

Author: Magellan Quant Research (Forensic Auditor)
Date: 2026-01-30
"""

import pandas as pd
import numpy as np
from pathlib import Path
import yfinance as yf
from datetime import datetime, timedelta
import random
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

MNQ_CSV = Path(r"A:\1\Magellan\data\cache\futures\MNQ\glbx-mdp3-20210129-20260128.ohlcv-1m.csv")
OUTPUT_DIR = Path(r"a:\1\Magellan\research\mnq_buy_low_edge_analysis\03_backtest")

# Mandatory target dates
TARGET_DATES = [
    "2025-01-02",  # Ghost Crash Suspect
    "2025-01-27",  # DeepSeek Real Crash
]

# Tolerance
PRICE_TOLERANCE_PCT = 0.5  # 0.5% tolerance
CORRUPTION_THRESHOLD = 100  # Points difference to flag as corrupted

# =============================================================================
# LOAD MY DATA
# =============================================================================

def load_my_data():
    """Load and aggregate MNQ data to daily OHLC."""
    print("="*80)
    print("DATA FORENSIC AUDIT: Integrity Check")
    print("="*80)
    
    print(f"\n[1/5] Loading local dataset...")
    df = pd.read_csv(MNQ_CSV)
    
    df['datetime'] = pd.to_datetime(df['ts_event'].str[:19])
    df = df.set_index('datetime')
    df = df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # Aggregate by timestamp first (combine contracts)
    df_agg = df.groupby(df.index).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).sort_index()
    
    print(f"      Total 1-min rows: {len(df_agg):,}")
    print(f"      Date range: {df_agg.index.min()} to {df_agg.index.max()}")
    
    # Aggregate to daily
    df_daily = df_agg.resample('D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    print(f"      Daily bars: {len(df_daily):,}")
    
    return df_daily

def get_random_dates(df_daily, n=10):
    """Select n random dates from dataset (within 2025)."""
    print(f"\n[2/5] Selecting {n} random dates from 2025...")
    
    # Filter to 2025 only
    df_2025 = df_daily[(df_daily.index >= '2025-01-01') & (df_daily.index <= '2025-12-31')]
    
    # Get available dates
    available_dates = [d.strftime('%Y-%m-%d') for d in df_2025.index]
    
    # Remove target dates
    available_dates = [d for d in available_dates if d not in TARGET_DATES]
    
    # Random sample
    random.seed(42)  # Reproducible
    random_dates = random.sample(available_dates, min(n, len(available_dates)))
    random_dates = sorted(random_dates)
    
    print(f"      Selected: {random_dates}")
    
    return random_dates

def fetch_official_data(dates):
    """Fetch official NQ=F data from yfinance."""
    print(f"\n[3/5] Fetching official NQ=F data from yfinance...")
    
    # Expand date range for fetching
    min_date = min(dates)
    max_date = max(dates)
    start = (pd.to_datetime(min_date) - timedelta(days=5)).strftime('%Y-%m-%d')
    end = (pd.to_datetime(max_date) + timedelta(days=5)).strftime('%Y-%m-%d')
    
    print(f"      Fetching NQ=F from {start} to {end}...")
    
    try:
        nq = yf.download("NQ=F", start=start, end=end, progress=False)
        if len(nq) == 0:
            print("      WARNING: No data from NQ=F, trying alternative...")
            # Try alternative ticker
            nq = yf.download("^NDX", start=start, end=end, progress=False)
        
        print(f"      Official data rows: {len(nq)}")
        
        # Flatten multi-level columns if present
        if isinstance(nq.columns, pd.MultiIndex):
            nq.columns = nq.columns.get_level_values(0)
        
        return nq
    except Exception as e:
        print(f"      ERROR fetching data: {e}")
        return None

def perform_audit(my_daily, official, all_dates):
    """Compare my data against official data."""
    print(f"\n[4/5] Performing forensic comparison...")
    
    results = []
    
    for date_str in all_dates:
        date = pd.to_datetime(date_str)
        date_type = "TARGETED" if date_str in TARGET_DATES else "Random"
        
        # Get my data
        my_row = my_daily[my_daily.index.normalize() == date]
        
        if len(my_row) == 0:
            results.append({
                'Date': date_str,
                'Type': date_type,
                'My_Close': 'N/A',
                'Official_Close': 'N/A',
                'Diff_Points': 'N/A',
                'My_Low': 'N/A',
                'Official_Low': 'N/A',
                'Verdict': 'NO DATA'
            })
            continue
        
        my_close = my_row['close'].iloc[0]
        my_high = my_row['high'].iloc[0]
        my_low = my_row['low'].iloc[0]
        my_open = my_row['open'].iloc[0]
        
        # Get official data
        official_row = official[official.index.normalize() == date]
        
        if len(official_row) == 0:
            # Try next trading day
            next_day = date + timedelta(days=1)
            official_row = official[official.index.normalize() == next_day]
            
        if len(official_row) == 0:
            results.append({
                'Date': date_str,
                'Type': date_type,
                'My_Close': f"{my_close:.2f}",
                'Official_Close': 'N/A',
                'Diff_Points': 'N/A',
                'My_Low': f"{my_low:.2f}",
                'Official_Low': 'N/A',
                'Verdict': 'NO OFFICIAL DATA'
            })
            continue
        
        official_close = official_row['Close'].iloc[0]
        official_low = official_row['Low'].iloc[0]
        official_high = official_row['High'].iloc[0]
        
        # Calculate differences
        diff_close = my_close - official_close
        diff_pct = abs(diff_close / official_close) * 100
        diff_low = my_low - official_low
        
        # Verdict
        if abs(diff_close) > CORRUPTION_THRESHOLD:
            verdict = "CORRUPTED"
        elif diff_pct > PRICE_TOLERANCE_PCT:
            verdict = "FAIL"
        else:
            verdict = "PASS"
        
        results.append({
            'Date': date_str,
            'Type': date_type,
            'My_Close': f"{my_close:.2f}",
            'Official_Close': f"{official_close:.2f}",
            'Diff_Points': f"{diff_close:+.2f}",
            'Diff_Pct': f"{diff_pct:.2f}%",
            'My_Low': f"{my_low:.2f}",
            'Official_Low': f"{official_low:.2f}",
            'Verdict': verdict
        })
    
    return pd.DataFrame(results)

def print_forensic_table(results_df):
    """Print the forensic table."""
    print("\n" + "="*80)
    print("FORENSIC AUDIT TABLE")
    print("="*80)
    
    print(f"\n{'Date':<12} | {'Type':<10} | {'My Close':>12} | {'Official':>12} | {'Diff (pts)':>12} | {'Verdict':<12}")
    print("-"*80)
    
    for _, row in results_df.iterrows():
        marker = " ***" if row['Verdict'] in ['CORRUPTED', 'FAIL'] else ""
        print(f"{row['Date']:<12} | {row['Type']:<10} | {row['My_Close']:>12} | {row['Official_Close']:>12} | {row['Diff_Points']:>12} | {row['Verdict']:<12}{marker}")
    
    # Summary
    print("\n" + "-"*80)
    total = len(results_df)
    passed = (results_df['Verdict'] == 'PASS').sum()
    failed = (results_df['Verdict'] == 'FAIL').sum()
    corrupted = (results_df['Verdict'] == 'CORRUPTED').sum()
    no_data = results_df['Verdict'].str.contains('NO').sum()
    
    print(f"SUMMARY: {total} dates checked | {passed} PASS | {failed} FAIL | {corrupted} CORRUPTED | {no_data} No Data")

def check_specific_date_detail(my_daily, date_str):
    """Print detailed info for a specific date."""
    print(f"\n{'='*60}")
    print(f"DETAILED CHECK: {date_str}")
    print(f"{'='*60}")
    
    date = pd.to_datetime(date_str)
    my_row = my_daily[my_daily.index.normalize() == date]
    
    if len(my_row) == 0:
        print("  NO DATA for this date in local file!")
        return
    
    print(f"  Open:   {my_row['open'].iloc[0]:.2f}")
    print(f"  High:   {my_row['high'].iloc[0]:.2f}")
    print(f"  Low:    {my_row['low'].iloc[0]:.2f}")
    print(f"  Close:  {my_row['close'].iloc[0]:.2f}")
    print(f"  Volume: {my_row['volume'].iloc[0]:,.0f}")

def main():
    """Execute forensic audit."""
    
    # Load my data
    my_daily = load_my_data()
    
    # Get random dates
    random_dates = get_random_dates(my_daily, n=10)
    
    # Combine all dates
    all_dates = TARGET_DATES + random_dates
    all_dates = sorted(list(set(all_dates)))
    
    print(f"\n      Total dates to audit: {len(all_dates)}")
    print(f"      Targeted: {TARGET_DATES}")
    
    # Fetch official data
    official = fetch_official_data(all_dates)
    
    if official is None or len(official) == 0:
        print("\nERROR: Could not fetch official data. Proceeding with local data only...")
        
        # At least show my data for target dates
        print("\n" + "="*80)
        print("LOCAL DATA CHECK (No External Verification)")
        print("="*80)
        
        for date_str in TARGET_DATES:
            check_specific_date_detail(my_daily, date_str)
        
        return
    
    # Perform audit
    results_df = perform_audit(my_daily, official, all_dates)
    
    # Print results
    print_forensic_table(results_df)
    
    # Detailed check for suspicious dates
    for date_str in TARGET_DATES:
        check_specific_date_detail(my_daily, date_str)
    
    # Generate report
    print(f"\n[5/5] Generating report...")
    
    report = f"""# Data Forensic Audit Report

## Audit Protocol

| Parameter | Value |
|-----------|-------|
| Data Source | `{MNQ_CSV}` |
| External Truth | yfinance NQ=F |
| Tolerance | {PRICE_TOLERANCE_PCT}% |
| Corruption Threshold | {CORRUPTION_THRESHOLD} points |

---

## Mandatory Targets

| Date | Reason |
|------|--------|
| 2025-01-02 | "Ghost Crash" Suspect |
| 2025-01-27 | "DeepSeek" Real Crash |

---

## Forensic Audit Table

| Date | Type | My Close | Official | Diff (pts) | Verdict |
|------|------|----------|----------|------------|---------|
"""
    
    for _, row in results_df.iterrows():
        report += f"| {row['Date']} | {row['Type']} | {row['My_Close']} | {row['Official_Close']} | {row['Diff_Points']} | {row['Verdict']} |\n"
    
    # Summary
    total = len(results_df)
    passed = (results_df['Verdict'] == 'PASS').sum()
    failed = (results_df['Verdict'] == 'FAIL').sum()
    corrupted = (results_df['Verdict'] == 'CORRUPTED').sum()
    
    report += f"""
---

## Summary

| Status | Count |
|--------|-------|
| PASS | {passed} |
| FAIL | {failed} |
| CORRUPTED | {corrupted} |
| **Total Audited** | {total} |

---

## Detailed Check: Suspicious Dates

"""
    
    for date_str in TARGET_DATES:
        date = pd.to_datetime(date_str)
        my_row = my_daily[my_daily.index.normalize() == date]
        if len(my_row) > 0:
            report += f"""### {date_str}

| Metric | Value |
|--------|-------|
| Open | {my_row['open'].iloc[0]:.2f} |
| High | {my_row['high'].iloc[0]:.2f} |
| Low | {my_row['low'].iloc[0]:.2f} |
| Close | {my_row['close'].iloc[0]:.2f} |
| Volume | {my_row['volume'].iloc[0]:,.0f} |

"""
    
    report += f"""---

## Conclusion

{"**DATA INTEGRITY VERIFIED.** All checked dates pass within tolerance." if corrupted == 0 and failed == 0 else "**DATA INTEGRITY ISSUES FOUND.** Review flagged dates."}

---

*Generated by Magellan Quant Research - Forensic Auditor*  
*Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path = OUTPUT_DIR / "DATA_FORENSIC_AUDIT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"      Report saved: {report_path}")
    
    # Save results
    results_path = OUTPUT_DIR / "data_forensic_audit_results.csv"
    results_df.to_csv(results_path, index=False)
    print(f"      Results saved: {results_path}")
    
    print("\n" + "="*80)
    print("FORENSIC AUDIT COMPLETE")
    print("="*80)
    
    return results_df

if __name__ == "__main__":
    results = main()
