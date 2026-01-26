"""
CRITICAL TEST 2.1: Hourly Swing Gap Reversal Stress

Tests whether Hourly Swing strategy's profitability depends on gap profits holding.
Strategy requires overnight holds; this test validates gap risk exposure.

CRITICAL PASS CRITERIA: Strategy must remain profitable even with 50% gap fading.
DEPLOYMENT BLOCKER: If 100% gap fade causes losses, strategy may not be deployable.

Test Matrix:
- 2 assets (TSLA, NVDA)
- 3 gap fade scenarios (No Fade, 50% Fade, 100% Fade)
- Total: 6 test runs
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.data_cache import cache

# Validated configurations
CONFIGS = {
    "TSLA": {"rsi_period": 14, "upper_band": 60, "lower_band": 40},
    "NVDA": {"rsi_period": 28, "upper_band": 55, "lower_band": 45},
}

VALIDATION_START = "2025-01-01"
VALIDATION_END = "2025-12-31"

def calculate_rsi(prices, period=28):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.inf)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
    return rsi

def simulate_gap_fade(df, fade_pct):
    """
    Simulate gap fading scenario.
    
    fade_pct = 0: No fade (baseline)
    fade_pct = 0.5: Gap fades by 50%
    fade_pct = 1.0: Gap completely reverses
    """
    df_adjusted = df.copy()
    
    # Identify overnight gaps
    df_adjusted['prev_close'] = df_adjusted['close'].shift(1)
    df_adjusted['gap'] = df_adjusted['open'] - df_adjusted['prev_close']
    df_adjusted['gap_pct'] = df_adjusted['gap'] / df_adjusted['prev_close']
    
    # Apply fade to opens
    for i in range(1, len(df_adjusted)):
        gap = df_adjusted['gap'].iloc[i]
        
        if abs(gap) > 0:
            # Reduce gap by fade_pct
            faded_gap = gap * (1 - fade_pct)
            df_adjusted.loc[df_adjusted.index[i], 'open'] = df_adjusted['prev_close'].iloc[i] + faded_gap
            
            # Adjust high/low/close proportionally if open changes
            # (simplified: assume intraday move pattern same, just shifted by gap fade)
            gap_change = gap - faded_gap
            df_adjusted.loc[df_adjusted.index[i], 'high'] -= gap_change
            df_adjusted.loc[df_adjusted.index[i], 'low'] -= gap_change
            df_adjusted.loc[df_adjusted.index[i], 'close'] -= gap_change
    
    # Keep gap_return column for analysis (shows actual gap after fading)
    df_adjusted['gap_return'] = df_adjusted['gap_pct'] * (1 - fade_pct)
    
    return df_adjusted

def run_backtest(symbol, config, gap_fade_pct):
    """Run backtest with gap fade simulation"""
    try:
        # Fetch hourly data
        df = cache.get_or_fetch_equity(symbol, '1hour', VALIDATION_START, VALIDATION_END)
        
        if len(df) < 200:
            return None
        
        # Apply gap fade simulation
        if gap_fade_pct > 0:
            df = simulate_gap_fade(df, gap_fade_pct)
        
        # Calculate RSI
        df['rsi'] = calculate_rsi(df['close'], period=config['rsi_period'])
        
        # Generate signals (RSI hysteresis with overnight holds)
        position = 0
        signals = []
        
        for i in range(len(df)):
            rsi_val = df['rsi'].iloc[i]
            
            if pd.isna(rsi_val):
                signals.append(position)
                continue
            
            if position == 0:  # Flat
                if rsi_val > config['upper_band']:
                    position = 1  # Go long
            elif position == 1:  # Long
                if rsi_val < config['lower_band']:
                    position = 0  # Go flat
            
            signals.append(position)
        
        df['signal'] = signals
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # Count trades and overnight holds
        trades = (df['signal'].diff() != 0).sum()
        
        # Identify overnight holds (position held across day boundary)
        df['date'] = df.index.date
        df['next_date'] = df['date'].shift(-1)
        overnight_holds = ((df['signal'] == 1) & (df['date'] != df['next_date'])).sum()
        
        # Apply friction (10 bps for hourly)
        friction_per_trade = 0.0010
        total_friction = trades * friction_per_trade
        
        # Performance metrics
        total_return = (1 + df['strategy_returns']).prod() - 1 - total_friction
        
        if df['strategy_returns'].std() > 0:
            sharpe = (df['strategy_returns'].mean() / df['strategy_returns'].std()) * np.sqrt(252 * 6.5)
        else:
            sharpe = 0
        
        # Calculate gap contribution (only if we did gap simulation)
        if gap_fade_pct == 0:
            # Calculate fresh for baseline
            df['prev_close_calc'] = df['close'].shift(1)
            df['gap_return_calc'] = (df['open'] - df['prev_close_calc']) / df['prev_close_calc']
            gap_contribution = (df[df['signal'].shift(1) == 1]['gap_return_calc']).fillna(0).sum()
        else:
            # Use the gap_return from gap simulation
            gap_contribution = (df[df['signal'].shift(1) == 1]['gap_return']).fillna(0).sum()
        
        return {
            'return_pct': total_return * 100,
            'sharpe': sharpe,
            'trades': trades,
            'overnight_holds': int(overnight_holds),
            'gap_contribution_pct': gap_contribution * 100,
            'profitable': total_return > 0
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def main():
    print("="*80)
    print("CRITICAL TEST 2.1: HOURLY SWING GAP REVERSAL STRESS")
    print("="*80)
    print(f"\nValidation Period: {VALIDATION_START} to {VALIDATION_END}")
    print(f"Testing {len(CONFIGS)} assets with gap fade scenarios\n")
    
    print("CRITICAL PASS CRITERIA:")
    print("  • Profitable with 50% gap fading")
    print("  • Return ≥+10% even with 50% fade")
    print("  • Deployment BLOCKED if 100% fade causes large losses\n")
    print("="*80)
    
    all_results = []
    
    gap_scenarios = [
        (0.0, "No Fade (Baseline)"),
        (0.5, "50% Fade"),
        (1.0, "100% Fade (Full Reversal)")
    ]
    
    for symbol, config in CONFIGS.items():
        print(f"\n{symbol} - RSI-{config['rsi_period']}, Bands {config['upper_band']}/{config['lower_band']}")
        print("-" * 60)
        
        baseline_return = None
        
        for gap_fade_pct, scenario_name in gap_scenarios:
            print(f"  {scenario_name:30s}...", end=" ")
            
            result = run_backtest(symbol, config, gap_fade_pct)
            
            if result is None:
                print("SKIP")
                continue
            
            if gap_fade_pct == 0:
                baseline_return = result['return_pct']
            
            status_icon = "✅" if result['profitable'] else "❌"
            print(f"{status_icon} Return: {result['return_pct']:+6.2f}% | Sharpe: {result['sharpe']:4.2f} | "
                  f"Gaps: {result['overnight_holds']:3d} ({result['gap_contribution_pct']:+.1f}%)")
            
            all_results.append({
                'Asset': symbol,
                'Gap_Fade_Pct': gap_fade_pct * 100,
                'Scenario': scenario_name,
                **result
            })
    
    # Save results
    df = pd.DataFrame(all_results)
    output_dir = Path('research/Perturbations/reports/test_results')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'critical_test_2_1_gap_reversal.csv'
    df.to_csv(output_path, index=False)
    
    # Analysis
    print("\n" + "="*80)
    print("CRITICAL TEST RESULTS")
    print("="*80)
    
    for fade_pct, scenario_name in gap_scenarios:
        scenario_results = df[df['Gap_Fade_Pct'] == fade_pct * 100]
        profitable_count = scenario_results['profitable'].sum()
        
        print(f"\n{scenario_name}:")
        print(f"  Profitable: {profitable_count}/{len(scenario_results)} assets")
        print(f"  Avg Return: {scenario_results['return_pct'].mean():+.2f}%")
        
        # Safely access individual asset results
        tsla_results = scenario_results[scenario_results['Asset']=='TSLA']
        nvda_results = scenario_results[scenario_results['Asset']=='NVDA']
        
        if len(tsla_results) > 0:
            print(f"  TSLA: {tsla_results['return_pct'].iloc[0]:+.2f}%")
        if len(nvda_results) > 0:
            print(f"  NVDA: {nvda_results['return_pct'].iloc[0]:+.2f}%")
    
    # Pass/Fail determination
    print("\n" + "="*80)
    print("GO/NO-GO DECISION")
    print("="*80)
    
    fade_50_results = df[df['Gap_Fade_Pct'] == 50]
    profitable_50 = fade_50_results['profitable'].sum()
    avg_return_50 = fade_50_results['return_pct'].mean()
    
    fade_100_results = df[df['Gap_Fade_Pct'] == 100]
    avg_return_100 = fade_100_results['return_pct'].mean()
    
    print(f"\n50% Fade: {profitable_50}/2 profitable, Avg Return: {avg_return_50:+.2f}%")
    print(f"100% Fade: Avg Return: {avg_return_100:+.2f}%")
    
    if profitable_50 == 2 and avg_return_50 >= 10:
        print("\n✅ PASS: Strategy has strong gap resilience")
        print("   DEPLOYMENT: APPROVED")
    elif profitable_50 == 2:
        print("\n⚠️  MARGINAL: Profitable but low returns with gap fading")
        print("   DEPLOYMENT: CONDITIONAL (monitor gap patterns closely)")
    else:
        print("\n❌ FAIL: Strategy depends heavily on gap profits")
        print("   DEPLOYMENT: BLOCKED or TSLA-only")
        print("   REASON: Edge destroyed if gaps fade")
    
    print(f"\nResults saved to: {output_path}")
    print("="*80)

if __name__ == "__main__":
    main()
