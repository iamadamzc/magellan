"""
Alpha Discovery Module
Calculates Information Coefficient (IC) to test feature predictive power.
"""

import pandas as pd
from scipy.stats import spearmanr


def calculate_ic(
    df: pd.DataFrame,
    feature_col: str,
    target_col: str = 'log_return',
    horizon: int = 15
) -> float:
    """
    Calculate Information Coefficient (Spearman Rank Correlation) between
    a feature and forward returns.
    
    Args:
        df: DataFrame containing the feature and target columns
        feature_col: Name of the feature column (e.g., 'sentiment')
        target_col: Name of the target column (default: 'log_return')
        horizon: Number of periods to look ahead (default: 15)
    
    Returns:
        Spearman correlation coefficient between feature and forward returns.
        Returns NaN if insufficient data.
    """
    # Create a copy to avoid modifying the original
    working_df = df[[feature_col, target_col]].copy()
    
    # Create forward returns by shifting target backward by horizon periods
    # Shifting backward means: for each row, we get the return from 'horizon' periods in the future
    working_df['forward_return'] = working_df[target_col].shift(-horizon)
    
    # Drop NaN values (last 'horizon' rows will have NaN forward returns)
    valid_data = working_df.dropna()
    
    # Need at least 10 observations for meaningful correlation
    if len(valid_data) < 10:
        return float('nan')
    
    # Calculate Spearman rank correlation
    correlation, _ = spearmanr(valid_data[feature_col], valid_data['forward_return'])
    
    return correlation
