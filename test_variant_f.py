"""
Test script for NVDA Variant F (Daily Hysteresis)
Runs a 365-day backtest to verify Schmidt Trigger reduces whipsaw
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_handler import AlpacaDataClient, FMPDataClient
from src.features import FeatureEngineer, add_technical_indicators, merge_news_pit, generate_master_signal
from src.discovery import trim_warmup_period
from src.backtester_pro import run_rolling_backtest, print_stress_test_summary, export_stress_test_results

# Load hysteresis config
with open('config/nodes/nvda_daily_hysteresis.json', 'r') as f:
    HYSTERESIS_CONFIG = json.load(f)

print("=" * 60)
print("VARIANT F: NVDA DAILY HYSTERESIS BACKTEST")
print("=" * 60)
print(f"Config: {HYSTERESIS_CONFIG}")
print("=" * 60)

# Date range: 365 days (2025-01-14 back to 2024-01-14)
end_date = datetime(2026, 1, 14)
start_date = datetime(2024, 1, 14)

# Override environment for testing
os.environ['PYTHONPATH'] = '.'

# Run backtest
result = run_rolling_backtest(
    symbol='NVDA',
    days=0,  # Will be calculated from date range
    in_sample_days=3,
    initial_capital=50000.0,
    start_date=start_date,
    end_date=end_date,
    report_only=False,
    quiet=False
)

# Print summary
print_stress_test_summary(result)

# Export results
export_stress_test_results(result, 'stress_test_NVDA_variant_f.csv')

print("\\n[VARIANT F TEST COMPLETE]")
print(f"Report saved to: {result.get('report_file_path')}")
