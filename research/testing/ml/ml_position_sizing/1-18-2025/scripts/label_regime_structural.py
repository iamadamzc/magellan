"""
Structural Regime Labeling - No Look-Ahead Bias

Calculates regime labels based ONLY on entry-time structural features.
Labels describe the ENVIRONMENT, not the OUTCOME.

Principle: If you can't observe it before entry, you can't use it for labeling.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def calculate_structural_score(trade_row, all_trades_df=None):
    """
    Calculate structural regime score (0-15 points)
    Based ONLY on features observable at entry time
    
    Returns: dict with component scores and total
    """
    scores = {}
    
    # Component 1: Trend Strength (0-3 points)
    # Based on how trending the market was BEFORE entry
    trend_strength = trade_row.get('trend_strength', 0.5)  # From extraction
    if trend_strength > 0.7:
        scores['trend'] = 3
    elif trend_strength > 0.4:
        scores['trend'] = 2
    elif trend_strength > 0.2:
        scores['trend'] = 1
    else:
        scores['trend'] = 0
    
    # Component 2: Volatility Regime (0-3 points)
    # Stable volatility (ATR not expanding) is better for scaling
    atr_percentile = trade_row.get('atr_percentile', 0.5)
    if atr_percentile < 0.3:  # Low volatility (stable)
        scores['volatility'] = 3
    elif atr_percentile < 0.6:  # Normal volatility
        scores['volatility'] = 2
    elif atr_percentile < 0.8:  # Elevated volatility
        scores['volatility'] = 1
    else:  # Very high volatility (risky)
        scores['volatility'] = 0
    
    # Component 3: Volume Confirmation (0-3 points)
    # Strong volume at entry suggests conviction
    volume_ratio = trade_row.get('volume_ratio', 1.0)
    if volume_ratio > 2.0:
        scores['volume'] = 3
    elif volume_ratio > 1.5:
        scores['volume'] = 2
    elif volume_ratio > 1.2:
        scores['volume'] = 1
    else:
        scores['volume'] = 0
    
    # Component 4: Day Drop Severity (0-3 points)
    # For Bear Trap: Bigger drops often have bigger bounces
    day_change_pct = abs(trade_row.get('day_change_pct', -15))
    if day_change_pct > 25:  # Very severe drop (>-25%)
        scores['drop_severity'] = 3
    elif day_change_pct > 20:
        scores['drop_severity'] = 2
    elif day_change_pct > 15:
        scores['drop_severity'] = 1
    else:
        scores['drop_severity'] = 0
    
    # Component 5: Recent Strategy Performance (0-3 points)
    # If available, use recent win rate from all_trades_df
    # This is meta-level: is Bear Trap working well lately?
    if all_trades_df is not None:
        entry_date = pd.to_datetime(trade_row['entry_date'])
        # Get last 5 trades before this one
        prior_trades = all_trades_df[
            pd.to_datetime(all_trades_df['entry_date']) < entry_date
        ].tail(5)
        
        if len(prior_trades) >= 3:
            recent_wr = (prior_trades['r_multiple'] > 0).mean()
            if recent_wr > 0.7:
                scores['recent_performance'] = 3
            elif recent_wr > 0.5:
                scores['recent_performance'] = 2
            elif recent_wr > 0.3:
                scores['recent_performance'] = 1
            else:
                scores['recent_performance'] = 0
        else:
            scores['recent_performance'] = 1  # Neutral default
    else:
        scores['recent_performance'] = 1  # Neutral default
    
    # Total score (0-15 possible)
    total = scores['trend'] + scores['volatility'] + scores['volume'] + scores['drop_severity'] + scores['recent_performance']
    scores['total'] = total
    
    return scores

def map_score_to_label(total_score):
    """
    Map structural score to regime label
    
    Score ranges:
    - 11-15: ADD_ALLOWED (73-100% strong)
    - 7-10:  ADD_NEUTRAL (47-67% mixed)
    - 0-6:   NO_ADD (<47% weak)
    """
    if total_score >= 11:
        return 'ADD_ALLOWED'
    elif total_score >= 7:
        return 'ADD_NEUTRAL'
    else:
        return 'NO_ADD'

def validate_labels(df):
    """
    Validate that structural labels correlate with outcomes
    
    This is SEPARATE from labeling - we use outcomes to validate,
    not to create labels.
    
    Returns: dict with validation statistics
    """
    validation = {}
    
    for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
        subset = df[df['regime_label'] == label]
        
        if len(subset) > 0:
            validation[label] = {
                'count': len(subset),
                'avg_r_multiple': subset['r_multiple'].mean(),
                'win_rate': (subset['r_multiple'] > 0).mean() * 100,
                'avg_max_profit': subset['max_profit'].mean(),
                'avg_max_loss': subset['max_loss'].mean(),
                'stop_out_rate': (subset['exit_reason'] == 'stop').mean() * 100,
            }
        else:
            validation[label] = {
                'count': 0,
                'avg_r_multiple': 0,
                'win_rate': 0,
                'avg_max_profit': 0,
                'avg_max_loss': 0,
                'stop_out_rate': 0,
            }
    
    # Check if labeling makes sense
    add_allowed_r = validation['ADD_ALLOWED']['avg_r_multiple']
    no_add_r = validation['NO_ADD']['avg_r_multiple']
    
    validation['makes_sense'] = add_allowed_r > no_add_r
    validation['quality_score'] = add_allowed_r - no_add_r  # Higher is better
    
    return validation

def label_trades(input_csv, output_csv=None):
    """
    Main function: Label trades based on structural features
    
    Args:
        input_csv: Path to bear_trap_trades_2020_2024.csv
        output_csv: Path to save labeled data (optional)
    
    Returns:
        DataFrame with labels and validation stats
    """
    print("="*80)
    print("STRUCTURAL REGIME LABELING")
    print("="*80)
    print("Principle: Label by ENTRY CONDITIONS, not outcomes\n")
    
    # Load trades
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} trades from {input_csv}\n")
    
    # Sort by entry date (for recent performance calculation)
    df = df.sort_values('entry_date').reset_index(drop=True)
    
    # Calculate structural scores for each trade
    print("Calculating structural scores...")
    
    scores_list = []
    for idx, row in df.iterrows():
        scores = calculate_structural_score(row, df)
        scores_list.append(scores)
        
        if (idx + 1) % 100 == 0:
            print(f"  Processed {idx + 1}/{len(df)} trades")
    
    # Add scores to dataframe
    scores_df = pd.DataFrame(scores_list)
    df = pd.concat([df, scores_df], axis=1)
    
    # Map to labels
    df['regime_label'] = df['total'].apply(map_score_to_label)
    
    print(f"\n✓ Labeled {len(df)} trades")
    
    # Show label distribution
    print("\n" + "="*80)
    print("LABEL DISTRIBUTION")
    print("="*80)
    label_counts = df['regime_label'].value_counts()
    for label, count in label_counts.items():
        pct = (count / len(df)) * 100
        print(f"{label:15s}: {count:4d} trades ({pct:5.1f}%)")
    
    # Validate labels
    print("\n" + "="*80)
    print("VALIDATION: Do labels correlate with outcomes?")
    print("="*80)
    validation = validate_labels(df)
    
    for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
        stats = validation[label]
        print(f"\n{label}:")
        print(f"  Count: {stats['count']}")
        print(f"  Avg R-multiple: {stats['avg_r_multiple']:+.2f}")
        print(f"  Win rate: {stats['win_rate']:.1f}%")
        print(f"  Avg max profit: {stats['avg_max_profit']:.1f}%")
        print(f"  Avg max loss: {stats['avg_max_loss']:.1f}%")
        print(f"  Stop-out rate: {stats['stop_out_rate']:.1f}%")
    
    # Check if labeling makes sense
    print("\n" + "="*80)
    print("SANITY CHECK")
    print("="*80)
    if validation['makes_sense']:
        print("✅ PASS: ADD_ALLOWED has higher R-multiple than NO_ADD")
        print(f"   Quality score: {validation['quality_score']:+.2f} R")
        print("   → Structural features correctly identify favorable conditions")
    else:
        print("⚠️  WARNING: ADD_ALLOWED has LOWER R-multiple than NO_ADD")
        print(f"   Quality score: {validation['quality_score']:+.2f} R")
        print("   → Structural features may need revision")
        print("   → DO NOT relabel based on outcomes - fix features instead!")
    
    # Score component analysis
    print("\n" + "="*80)
    print("COMPONENT ANALYSIS")
    print("="*80)
    print("Average component scores by regime:\n")
    
    component_cols = ['trend', 'volatility', 'volume', 'drop_severity', 'recent_performance']
    for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
        subset = df[df['regime_label'] == label]
        if len(subset) > 0:
            print(f"{label}:")
            for comp in component_cols:
                avg = subset[comp].mean()
                print(f"  {comp:20s}: {avg:.2f} / 3.00")
            print()
    
    # Save labeled data
    if output_csv:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"\n✓ Saved labeled trades to: {output_path}")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Review validation results above")
    print("2. If quality score is positive → proceed to ML training")
    print("3. If quality score is negative → revise structural features")
    print("4. Never relabel based on outcomes - that defeats the purpose!")
    print("="*80)
    
    return df, validation

def main():
    # Paths
    input_csv = 'research/ml_position_sizing/data/bear_trap_trades_2020_2024.csv'
    output_csv = 'research/ml_position_sizing/data/labeled_regimes.csv'
    
    # Check if input exists
    if not Path(input_csv).exists():
        print(f"ERROR: Input file not found: {input_csv}")
        print("Run extract_bear_trap_trades.py first!")
        return
    
    # Label trades
    df, validation = label_trades(input_csv, output_csv)
    
    # Save validation report
    validation_report = Path('research/ml_position_sizing/data/validation_report.txt')
    validation_report.parent.mkdir(parents=True, exist_ok=True)
    with open(validation_report, 'w') as f:
        f.write("STRUCTURAL LABELING VALIDATION REPORT\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Total trades: {len(df)}\n\n")
        
        for label in ['ADD_ALLOWED', 'ADD_NEUTRAL', 'NO_ADD']:
            stats = validation[label]
            f.write(f"{label}:\n")
            f.write(f"  Count: {stats['count']}\n")
            f.write(f"  Avg R-multiple: {stats['avg_r_multiple']:+.2f}\n")
            f.write(f"  Win rate: {stats['win_rate']:.1f}%\n\n")
        
        f.write(f"\nQuality Score: {validation['quality_score']:+.2f} R\n")
        if validation['makes_sense']:
            f.write("✅ Labels correlate with outcomes\n")
        else:
            f.write("⚠️  Labels do NOT correlate - revise features!\n")
    
    print(f"\n✓ Validation report saved to: {validation_report}")

if __name__ == "__main__":
    main()
