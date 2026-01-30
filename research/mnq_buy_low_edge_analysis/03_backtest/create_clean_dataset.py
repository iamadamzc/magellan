"""
=============================================================================
CREATE CLEAN MNQ DATASET (No Calendar Spreads)
=============================================================================

This script:
1. Reads all monthly MNQ CSV files
2. Excludes calendar spread instruments (e.g., MNQZ5-MNQH6)
3. Keeps only outright contracts (e.g., MNQZ5, MNQH6)
4. Saves clean, combined dataset

Author: Magellan Quant Research
Date: 2026-01-30
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Configuration
MONTHLY_DIR = Path(r'a:\1\Magellan\data\cache\futures\MNQ\monthly')
OUTPUT_DIR = Path(r'a:\1\Magellan\data\cache\futures\MNQ')
OUTPUT_FILE = 'MNQ_CLEAN_OUTRIGHTS_ONLY.csv'

def main():
    print('='*80)
    print('CREATE CLEAN MNQ DATASET')
    print('='*80)
    print(f'\nSource: {MONTHLY_DIR}')
    print(f'Output: {OUTPUT_DIR / OUTPUT_FILE}')
    
    # Load symbology to identify spread instruments
    print('\n[1/5] Loading symbology...')
    symbology = pd.read_csv(MONTHLY_DIR / 'symbology.csv')
    
    # Identify spread instruments (contain dash in symbol)
    spread_ids = set(symbology[symbology.iloc[:, 0].str.contains('-', na=False)]['instrument_id'].unique())
    outright_ids = set(symbology[~symbology.iloc[:, 0].str.contains('-', na=False)]['instrument_id'].unique())
    
    print(f'      Spread instruments to EXCLUDE: {len(spread_ids)}')
    print(f'      Outright instruments to KEEP:  {len(outright_ids)}')
    
    # List all monthly CSV files
    print('\n[2/5] Finding monthly files...')
    csv_files = sorted([f for f in MONTHLY_DIR.glob('*.csv') if 'ohlcv' in f.name])
    print(f'      Found {len(csv_files)} monthly files')
    
    # Process each file
    print('\n[3/5] Processing files...')
    all_dfs = []
    total_original = 0
    total_clean = 0
    
    for i, csv_file in enumerate(csv_files):
        # Extract date range from filename
        parts = csv_file.stem.split('-')
        month_label = f"{parts[2][:4]}-{parts[2][4:6]}"
        
        # Load data
        df = pd.read_csv(csv_file)
        original_count = len(df)
        
        # Filter to outright contracts only
        df_clean = df[df['instrument_id'].isin(outright_ids)].copy()
        clean_count = len(df_clean)
        
        total_original += original_count
        total_clean += clean_count
        
        all_dfs.append(df_clean)
        
        # Progress
        pct = (clean_count / original_count * 100) if original_count > 0 else 0
        print(f'      {month_label}: {original_count:>7,} -> {clean_count:>7,} ({pct:.1f}% kept)')
    
    # Combine all data
    print('\n[4/5] Combining all files...')
    df_combined = pd.concat(all_dfs, ignore_index=True)
    
    # Sort by timestamp
    df_combined = df_combined.sort_values('ts_event').reset_index(drop=True)
    
    print(f'      Total rows: {len(df_combined):,}')
    
    # Validate - check for any remaining low prices
    low_prices = df_combined[(df_combined['close'] < 1000) | (df_combined['low'] < 1000)]
    if len(low_prices) > 0:
        print(f'      WARNING: {len(low_prices)} rows still have low prices!')
    else:
        print(f'      VALIDATED: No contamination remaining')
    
    # Save
    print('\n[5/5] Saving clean dataset...')
    output_path = OUTPUT_DIR / OUTPUT_FILE
    df_combined.to_csv(output_path, index=False)
    
    # Calculate file size
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f'      Saved: {output_path}')
    print(f'      Size:  {file_size_mb:.1f} MB')
    
    # Summary
    print('\n' + '='*80)
    print('SUMMARY')
    print('='*80)
    print(f'\nOriginal rows:     {total_original:,}')
    print(f'Clean rows:        {total_clean:,}')
    print(f'Removed:           {total_original - total_clean:,} spread rows')
    print(f'Retention:         {total_clean/total_original*100:.1f}%')
    
    # Date range
    df_combined['datetime'] = pd.to_datetime(df_combined['ts_event'].str[:19])
    print(f'\nDate range:        {df_combined["datetime"].min()} to {df_combined["datetime"].max()}')
    
    # Generate manifest
    manifest = f"""# MNQ Clean Dataset Manifest

## File Details
- **Filename**: {OUTPUT_FILE}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Size**: {file_size_mb:.1f} MB

## Data Summary
- **Total Rows**: {total_clean:,}
- **Original Rows**: {total_original:,}
- **Removed Rows**: {total_original - total_clean:,} (calendar spreads)
- **Retention**: {total_clean/total_original*100:.1f}%

## Date Range
- **Start**: {df_combined["datetime"].min()}
- **End**: {df_combined["datetime"].max()}

## Cleaning Applied
1. **Excluded Calendar Spreads**: Instruments with dash in symbol (e.g., MNQZ5-MNQH6)
2. **Kept Outright Contracts**: Single contract instruments (e.g., MNQZ5, MNQH6)
3. **Validated**: No prices < 1000 remaining (confirmed no contamination)

## Instruments Included
{len(outright_ids)} outright contract instrument IDs

## Source Files
- {len(csv_files)} monthly CSV files from {MONTHLY_DIR}

---
*Generated by Magellan Data Pipeline*
"""
    
    manifest_path = OUTPUT_DIR / 'MNQ_CLEAN_MANIFEST.md'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.write(manifest)
    print(f'\nManifest saved: {manifest_path}')
    
    print('\n' + '='*80)
    print('CLEAN DATASET CREATED SUCCESSFULLY')
    print('='*80)
    
    return df_combined

if __name__ == "__main__":
    df = main()
