"""
ORB V17 "SIMPLE REGIME" - Skip Bad Days Entirely
-------------------------------------------------
Simpler approach: Calculate regime at day level, skip entire days.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache
from research.new_strategy_builds.strategies.orb_v7 import run_orb_v7

def run_orb_v17_simple_regime(symbol, start, end):
    """
    V17: Run V7 but only on days that pass regime filter
    """
    
    print(f"\nTesting {symbol} - V17 SIMPLE REGIME ({start} to {end})")
    
    # Get full data
    df = cache.get_or_fetch_equity(symbol, '1min', start, end)
    if df is None or len(df) == 0:
        return None
    
    # Calculate regime metrics
    df['date'] = df.index.date
    
    # Get daily data
    daily = df.groupby('date').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # 20-day MA
    daily['ma20'] = daily['close'].rolling(20).mean()
    
    # ATR
    daily['h_l'] = daily['high'] - daily['low']
    daily['h_pc'] = abs(daily['high'] - daily['close'].shift(1))
    daily['l_pc'] = abs(daily['low'] - daily['close'].shift(1))
    daily['tr'] = daily[['h_l', 'h_pc', 'l_pc']].max(axis=1)
    daily['atr'] = daily['tr'].rolling(14).mean()
    daily['atr_pct'] = (daily['atr'] / daily['close']) * 100
    
    # Gap from prior close
    daily['prior_close'] = daily['close'].shift(1)
    daily['gap_pct'] = ((daily['open'] - daily['prior_close']) / daily['prior_close']) * 100
    
    # Regime filter
    daily['regime_ok'] = (
        (daily['close'] > daily['ma20']) &  # Above 20MA
        (daily['atr_pct'] > 2.5) &  # High volatility
        (daily['gap_pct'] > -3.0)  # Not gapping down hard
    )
    
    # Get list of good days
    good_days = daily[daily['regime_ok']].index.tolist()
    bad_days = daily[~daily['regime_ok']].index.tolist()
    
    print(f"  Regime Filter: {len(good_days)} good days, {len(bad_days)} bad days ({len(bad_days)/(len(good_days)+len(bad_days))*100:.0f}% filtered)")
    
    if len(good_days) == 0:
        print(f"  ⚠️  No good days found!")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
    
    # Run V7 logic only on good days
    good_df = df[df['date'].isin(good_days)].copy()
    
    # Now run V7 on this filtered data
    # (Simplified - just call V7 with date filter)
    all_trades = []
    
    for good_day in good_days:
        day_start = pd.Timestamp(good_day).strftime('%Y-%m-%d')
        day_end = day_start
        
        # Run V7 on this single day
        result = run_orb_v7(symbol, day_start, day_end)
        if result and result['total_trades'] > 0:
            all_trades.append(result)
    
    if len(all_trades) == 0:
        print(f"  ⚠️  No trades on good days")
        return {'symbol': symbol, 'total_trades': 0, 'win_rate': 0, 'total_pnl': 0}
    
    # Aggregate results
    total_trades = sum(t['total_trades'] for t in all_trades)
    total_pnl = sum(t['total_pnl'] for t in all_trades)
    avg_win_rate = sum(t['win_rate'] * t['total_trades'] for t in all_trades) / total_trades
    
    print(f"✓ {total_trades} trades | {avg_win_rate:.1f}% win | {total_pnl:+.2f}% total")
    
    return {
        'symbol': symbol,
        'total_trades': total_trades,
        'win_rate': avg_win_rate,
        'total_pnl': total_pnl,
        'days_traded': len(good_days),
        'days_skipped': len(bad_days)
    }
