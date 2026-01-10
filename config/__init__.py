"""
Magellan Configuration Module
Provides ticker-specific parameter loading from JSON configuration files.
"""

import os
import json
from typing import Dict, Any, Optional


# Default configuration used when no ticker-specific config exists
DEFAULT_CONFIG = {
    "ticker": "DEFAULT",
    "description": "Default configuration for unconfigured tickers",
    
    "alpha_weights": {
        "rsi_14": 0.4,
        "volume_zscore": 0.3,
        "sentiment": 0.3
    },
    
    "sentry_gate": {
        "enabled": False,
        "type": None,
        "threshold": None,
        "description": "No gate applied"
    },
    
    "ic_horizons": [5, 15, 60],
    
    "validation": {
        "walk_forward_split": 0.70,
        "horizon_bars": 15,
        "min_hit_rate": 0.51
    },
    
    "stress_test": {
        "days": 15,
        "in_sample_days": 3,
        "initial_capital": 100000.0
    }
}


def get_config_path(ticker: str) -> str:
    """Get the path to a ticker's configuration file."""
    config_dir = os.path.dirname(__file__)
    return os.path.join(config_dir, 'nodes', f'{ticker}.json')


def load_ticker_config(ticker: str) -> Dict[str, Any]:
    """
    Load ticker-specific configuration from JSON file.
    
    Args:
        ticker: Stock symbol (e.g., 'SPY', 'QQQ')
        
    Returns:
        Configuration dictionary with all node parameters
        
    Falls back to DEFAULT_CONFIG if no ticker-specific config exists.
    """
    config_path = get_config_path(ticker)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"[CONFIG] Loaded configuration for {ticker}")
            return config
        except json.JSONDecodeError as e:
            print(f"[CONFIG] WARNING: Invalid JSON in {config_path}: {e}")
            print(f"[CONFIG] Falling back to default configuration")
            return DEFAULT_CONFIG.copy()
    else:
        print(f"[CONFIG] No config found for {ticker}, using defaults")
        return DEFAULT_CONFIG.copy()


def get_alpha_weights(ticker: str) -> Dict[str, float]:
    """
    Get alpha weights for a specific ticker.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with 'rsi_14', 'volume_zscore', 'sentiment' weights
    """
    config = load_ticker_config(ticker)
    return config['alpha_weights']


def get_sentry_gate(ticker: str) -> Dict[str, Any]:
    """
    Get sentry gate configuration for a specific ticker.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with 'enabled', 'type', 'threshold', 'description'
    """
    config = load_ticker_config(ticker)
    return config['sentry_gate']


def get_validation_params(ticker: str) -> Dict[str, Any]:
    """
    Get validation parameters for a specific ticker.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with 'walk_forward_split', 'horizon_bars', 'min_hit_rate'
    """
    config = load_ticker_config(ticker)
    return config['validation']


def get_stress_test_params(ticker: str) -> Dict[str, Any]:
    """
    Get stress test parameters for a specific ticker.
    
    Args:
        ticker: Stock symbol
        
    Returns:
        Dict with 'days', 'in_sample_days', 'initial_capital'
    """
    config = load_ticker_config(ticker)
    return config['stress_test']


def list_configured_tickers() -> list:
    """
    List all tickers that have dedicated configuration files.
    
    Returns:
        List of ticker symbols with JSON configs in config/nodes/
    """
    nodes_dir = os.path.join(os.path.dirname(__file__), 'nodes')
    tickers = []
    
    if os.path.exists(nodes_dir):
        for filename in os.listdir(nodes_dir):
            if filename.endswith('.json'):
                tickers.append(filename.replace('.json', ''))
    
    return sorted(tickers)
