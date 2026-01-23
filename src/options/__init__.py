"""
Magellan Options Trading Module

Provides options-specific functionality for trend-following strategies:
- Options data fetching (chains, quotes, Greeks)
- Options feature engineering (IV, delta selection, DTE management)
- Options execution logic (signal translation, position management)
- Options P&L tracking and reporting

Architecture:
- data_handler.py: Alpaca Options API client
- features.py: Greeks calculations, IV analysis, strike selection
- executor.py: Signal → options position translation
- utils.py: Symbol formatting, helpers
"""

__version__ = "1.0.0"
__author__ = "Magellan Trading System"

from .data_handler import AlpacaOptionsClient
from .features import OptionsFeatureEngineer
from .utils import build_option_symbol, parse_option_symbol, calculate_dte

__all__ = [
    "AlpacaOptionsClient",
    "OptionsFeatureEngineer",
    "build_option_symbol",
    "parse_option_symbol",
    "calculate_dte",
]
