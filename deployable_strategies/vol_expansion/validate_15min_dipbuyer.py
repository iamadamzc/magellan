"""
15-MINUTE "DIP BUYER" SWING STRATEGY - VALIDATION

Validates the 15-minute swing strategy with three configurations:
A. Raw Baseline - Exact thresholds from research
B. Trend Filter - Add Close > SMA(50) for uptrend only
C. Elite Filter - Tighter thresholds for top-tier signals

Author: Magellan Testing Framework
Date: January 25, 2026
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class BacktestConfig:
    """Configuration for backtest run."""
    name: str
    target_atr: float
    stop_atr: float
    slippage_per_share: float
    max_hold_bars: int
    use_trend_filter: bool = False
    use_elite_thresholds: bool = False
    # Elite threshold overrides
    effort_result_threshold: Optional[float] = None
    range_ratio_threshold: Optional[float] = None


@dataclass
class Trade:
    """Trade result."""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    atr: float
    pnl_gross: float
    pnl_net: float
    pnl_r: float
    is_win: bool
    exit_reason: str


class DipBuyerValidator:
    """
    Validate the 15-minute Dip Buyer swing strategy.
    """
    
    def __init__(self):
        # Load strategy results
        results_path = project_root / "test" / "vol_expansion" / "outputs_15min" / "15MIN_STRATEGY_RESULTS.json"
        with open(results_path) as f:
            self.strategy_results = json.load(f)
        
        print("="*70)
        print("15-MINUTE 'DIP BUYER' SWING STRATEGY VALIDATION")
        print("="*70)
        print("\nLoaded strategy thresholds from research")
    
    def load_15min_data(self, symbol: str) -> pd.DataFrame:
        """Load and aggregate data to 15-minute bars."""
        print(f"\nLoading {symbol} data...")
        
        # Load 1-minute data
        data_path = project_root / "data" / "cache" / "equities"
        files = sorted(data_path.glob(f"{symbol}_1min_202*.parquet"),
                      key=lambda x: x.stat().st_size, reverse=True)
        
        if not files:
            raise FileNotFoundError(f"No data for {symbol}")
        
        df = pd.read_parquet(files[0])
        
        # Aggregate to 15-minute
        df_15m = df.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Filter market hours
        df_15m = df_15m.between_time('09:30', '15:45')
        
        print(f"  1-min bars: {len(df):,}")
        print(f"  15-min bars: {len(df_15m):,}")
        
        return df_15m
    
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all required features for the strategy."""
        df = df.copy()
        
        # ATR (True Range)
        tr1 = df['high'] - df['low']
        tr2 = (df['high'] - df['close'].shift(1)).abs()
        tr3 = (df['low'] - df['close'].shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(20).mean()
        
        # SMA for trend filter
        df['sma_50'] = df['close'].rolling(50).mean()
        
        # Velocity
        df['velocity_1'] = df['close'].pct_change(1)
        df['velocity_4'] = df['close'].pct_change(4)
        
        # Volatility ratio
        atr_5 = true_range.rolling(5).mean()
        atr_20 = true_range.rolling(20).mean()
        df['volatility_ratio'] = atr_5 / (atr_20 + 0.0001)
        
        # Volume z-score
        vol_mean = df['volume'].rolling(20).mean()
        vol_std = df['volume'].rolling(20).std()
        df['volume_z'] = (df['volume'] - vol_mean) / (vol_std + 1)
        df['volume_z'] = df['volume_z'].clip(-5, 5)
        
        # Effort-result
        pct_change_abs = df['close'].pct_change().abs()
        df['effort_result'] = df['volume_z'] / (pct_change_abs + 0.0001)
        df['effort_result'] = df['effort_result'].clip(-100, 100)
        
        # Range ratio
        full_range = df['high'] - df['low']
        body = (df['close'] - df['open']).abs()
        df['range_ratio'] = full_range / (body + 0.0001)
        df['range_ratio'] = df['range_ratio'].clip(0, 20)
        
        # Body position
        df['body_position'] = (df['close'] - df['low']) / (full_range + 0.0001)
        
        # Aggregated features (20-bar lookback)
        lookback = 20
        for col in ['velocity_1', 'volatility_ratio', 'effort_result', 'range_ratio', 'volume_z']:
            df[f'{col}_mean'] = df[col].rolling(lookback).mean()
            df[f'{col}_std'] = df[col].rolling(lookback).std()
        
        return df
    
    def check_entry_signal(self, row: pd.Series, config: BacktestConfig, 
                           thresholds: dict) -> bool:
        """Check if entry conditions are met."""
        
        # Trend filter (Config B)
        if config.use_trend_filter:
            if pd.isna(row['sma_50']) or row['close'] <= row['sma_50']:
                return False
        
        # Get threshold values
        if config.use_elite_thresholds:
            # Use tighter thresholds
            effort_threshold = config.effort_result_threshold or -80
            range_threshold = config.range_ratio_threshold or 5.0
        else:
            # Use research thresholds
            effort_threshold = -61.0
            range_threshold = 3.88
        
        # Check conditions
        effort_result = row.get('effort_result_mean', 0)
        range_ratio = row.get('range_ratio_mean', 0)
        volatility_ratio = row.get('volatility_ratio_mean', 0)
        
        # Core conditions
        conditions = [
            effort_result < effort_threshold,
            range_ratio > range_threshold,
            volatility_ratio > 0.88
        ]
        
        return all(conditions)
    
    def run_backtest(self, df: pd.DataFrame, config: BacktestConfig, 
                     symbol: str) -> List[Trade]:
        """Run backtest with given configuration."""
        
        print(f"\n{'-'*60}")
        print(f"Running: {config.name}")
        print(f"{'-'*60}")
        
        # Get thresholds
        thresholds = self.strategy_results.get(symbol, {}).get('feature_profile', [])
        
        # Prepare arrays for speed
        df = df.dropna(subset=['atr', 'sma_50'])
        
        position = None
        trades = []
        signal_count = 0
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            
            if position is None:
                # Check entry
                if self.check_entry_signal(row, config, thresholds):
                    signal_count += 1
                    
                    raw_entry = row['close']
                    entry_slippage = config.slippage_per_share / 2
                    entry_price = raw_entry + entry_slippage
                    atr = row['atr']
                    
                    position = {
                        'entry_idx': idx,
                        'entry_time': df.index[idx],
                        'raw_entry': raw_entry,
                        'entry_price': entry_price,
                        'target': raw_entry + (config.target_atr * atr),
                        'stop': raw_entry - (config.stop_atr * atr),
                        'atr': atr
                    }
            else:
                # Manage position
                high = row['high']
                low = row['low']
                close = row['close']
                
                exit_signal = False
                exit_reason = None
                raw_exit = None
                
                if low <= position['stop']:
                    exit_signal = True
                    exit_reason = "STOP"
                    raw_exit = position['stop']
                elif high >= position['target']:
                    exit_signal = True
                    exit_reason = "TARGET"
                    raw_exit = position['target']
                elif idx - position['entry_idx'] >= config.max_hold_bars:
                    exit_signal = True
                    exit_reason = "TIME"
                    raw_exit = close
                
                if exit_signal:
                    exit_slippage = config.slippage_per_share / 2
                    exit_price = raw_exit - exit_slippage
                    
                    pnl_gross = raw_exit - position['raw_entry']
                    pnl_net = exit_price - position['entry_price']
                    risk = position['raw_entry'] - position['stop']
                    pnl_r = pnl_net / risk if risk > 0 else 0
                    
                    trades.append(Trade(
                        entry_time=position['entry_time'],
                        exit_time=df.index[idx],
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        atr=position['atr'],
                        pnl_gross=pnl_gross,
                        pnl_net=pnl_net,
                        pnl_r=pnl_r,
                        is_win=pnl_net > 0,
                        exit_reason=exit_reason
                    ))
                    position = None
        
        # Calculate signal frequency
        signal_freq = signal_count / len(df)
        print(f"  Signals: {signal_count:,} ({signal_freq:.1%} of bars)")
        
        return trades
    
    def analyze_results(self, trades: List[Trade], config: BacktestConfig,
                        total_bars: int) -> Dict:
        """Analyze backtest results."""
        
        if not trades:
            return {'error': 'No trades', 'config': config.name}
        
        df = pd.DataFrame([{
            'pnl_net': t.pnl_net,
            'pnl_r': t.pnl_r,
            'is_win': t.is_win,
            'exit_reason': t.exit_reason,
            'atr': t.atr
        } for t in trades])
        
        total = len(df)
        wins = df['is_win'].sum()
        hit_rate = wins / total
        
        avg_win_r = df[df['is_win']]['pnl_r'].mean() if wins > 0 else 0
        avg_loss_r = df[~df['is_win']]['pnl_r'].mean() if (total - wins) > 0 else 0
        expectancy_r = df['pnl_r'].mean()
        
        total_pnl = df['pnl_net'].sum()
        avg_pnl = df['pnl_net'].mean()
        
        # Equity curve metrics
        df['cum_pnl'] = df['pnl_net'].cumsum()
        df['max_pnl'] = df['cum_pnl'].cummax()
        df['drawdown'] = df['cum_pnl'] - df['max_pnl']
        max_dd = df['drawdown'].min()
        
        # Consecutive losses
        current_streak = 0
        max_streak = 0
        for is_win in df['is_win']:
            if not is_win:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        # Exit breakdown
        exit_breakdown = {}
        for reason in ['TARGET', 'STOP', 'TIME']:
            count = (df['exit_reason'] == reason).sum()
            reason_hr = df[df['exit_reason'] == reason]['is_win'].mean() if count > 0 else 0
            exit_breakdown[reason] = {'count': count, 'win_rate': reason_hr}
        
        # Trading frequency
        bars_per_day = 26  # 15-min bars in market hours
        bars_per_week = bars_per_day * 5
        signal_freq = total / total_bars
        trades_per_day = total / (total_bars / bars_per_day)
        trades_per_week = trades_per_day * 5
        
        return {
            'config_name': config.name,
            'total_trades': total,
            'wins': wins,
            'hit_rate': hit_rate,
            'avg_win_r': avg_win_r,
            'avg_loss_r': avg_loss_r,
            'expectancy_r': expectancy_r,
            'total_pnl': total_pnl,
            'avg_pnl_dollars': avg_pnl,
            'max_drawdown': max_dd,
            'max_consec_losses': max_streak,
            'signal_frequency': signal_freq,
            'trades_per_day': trades_per_day,
            'trades_per_week': trades_per_week,
            'exit_breakdown': exit_breakdown
        }
    
    def print_results(self, metrics: Dict):
        """Print formatted results."""
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {metrics['config_name']}")
        print(f"{'='*60}")
        
        print(f"\n--- PERFORMANCE ---")
        print(f"Total Trades:     {metrics['total_trades']:,}")
        print(f"Win Rate:         {metrics['hit_rate']:.1%}")
        print(f"Avg Win:          {metrics['avg_win_r']:.3f}R")
        print(f"Avg Loss:         {metrics['avg_loss_r']:.3f}R")
        print(f"NET EXPECTANCY:   {metrics['expectancy_r']:.3f}R")
        
        print(f"\n--- P&L ---")
        print(f"Total P&L:        ${metrics['total_pnl']:,.2f}")
        print(f"Avg P&L/Trade:    ${metrics['avg_pnl_dollars']:.2f}")
        print(f"Max Drawdown:     ${metrics['max_drawdown']:,.2f}")
        
        print(f"\n--- FREQUENCY ---")
        print(f"Signal Frequency: {metrics['signal_frequency']:.1%}")
        print(f"Trades/Day:       {metrics['trades_per_day']:.1f}")
        print(f"Trades/Week:      {metrics['trades_per_week']:.0f}")
        
        print(f"\n--- RISK ---")
        print(f"Max Consec Loss:  {metrics['max_consec_losses']}")
        
        print(f"\n--- EXIT BREAKDOWN ---")
        for reason, data in metrics['exit_breakdown'].items():
            print(f"  {reason:8s}: {data['count']:5d} | Win Rate: {data['win_rate']:.1%}")


def main():
    validator = DipBuyerValidator()
    
    # Load data
    df = validator.load_15min_data('SPY')
    df = validator.calculate_features(df)
    total_bars = len(df)
    
    print(f"\nTotal 15-min bars: {total_bars:,}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    # Define configurations
    configs = [
        BacktestConfig(
            name="CONFIG A: RAW BASELINE",
            target_atr=2.0,
            stop_atr=1.0,
            slippage_per_share=0.02,
            max_hold_bars=8,
            use_trend_filter=False,
            use_elite_thresholds=False
        ),
        BacktestConfig(
            name="CONFIG B: TREND FILTER (Close > SMA50)",
            target_atr=2.0,
            stop_atr=1.0,
            slippage_per_share=0.02,
            max_hold_bars=8,
            use_trend_filter=True,
            use_elite_thresholds=False
        ),
        BacktestConfig(
            name="CONFIG C: ELITE FILTER (Tight Thresholds)",
            target_atr=2.0,
            stop_atr=1.0,
            slippage_per_share=0.02,
            max_hold_bars=8,
            use_trend_filter=False,
            use_elite_thresholds=True,
            effort_result_threshold=-80,
            range_ratio_threshold=5.0
        )
    ]
    
    all_results = []
    
    for config in configs:
        trades = validator.run_backtest(df, config, 'SPY')
        metrics = validator.analyze_results(trades, config, total_bars)
        validator.print_results(metrics)
        all_results.append(metrics)
    
    # Final comparison
    print("\n" + "="*70)
    print("FINAL COMPARISON")
    print("="*70)
    
    print(f"\n{'Config':<35} {'Trades':<10} {'Win%':<8} {'Expect.':<10} {'Trades/Wk':<10}")
    print("-"*75)
    
    for m in all_results:
        name = m['config_name'].split(':')[1].strip()[:30]
        print(f"{name:<35} {m['total_trades']:<10,} {m['hit_rate']:.1%}{'':3} {m['expectancy_r']:.3f}R{'':4} {m['trades_per_week']:.0f}")
    
    print("-"*75)
    
    # Determine best
    profitable = [m for m in all_results if m['expectancy_r'] > 0]
    
    if profitable:
        # Score by expectancy * frequency (favor more trades if profitable)
        for m in profitable:
            m['score'] = m['expectancy_r'] * np.log(m['total_trades'] + 1)
        
        best = max(profitable, key=lambda x: x['score'])
        
        print(f"\n*** RECOMMENDED: {best['config_name']} ***")
        print(f"    Win Rate: {best['hit_rate']:.1%}")
        print(f"    Expectancy: {best['expectancy_r']:.3f}R")
        print(f"    Trades/Week: {best['trades_per_week']:.0f}")
        print(f"    Max Consecutive Losses: {best['max_consec_losses']}")
    else:
        print("\n*** WARNING: No profitable configuration found! ***")
    
    print("\n" + "="*70)
    print("DEPLOYMENT GUIDANCE")
    print("="*70)
    
    if profitable:
        print(f"""
Based on the analysis:

1. CONFIG A (Raw) shows if the base strategy works after slippage
2. CONFIG B (Trend Filter) reduces churn by only trading in uptrends  
3. CONFIG C (Elite) takes only the highest-conviction signals

NEXT STEPS:
- If all configs are profitable, start with CONFIG B (balance of frequency + edge)
- Paper trade for 2 weeks to verify execution
- Scale position size based on max consecutive losses
""")
    
    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)
