"""
Selloff Scanner Package

Real-time detection and prioritization of intraday selloff opportunities.
"""

__version__ = "1.0.0"

from .selloff_detector import SelloffDetector
from .universe_manager import UniverseManager
from .priority_scorer import PriorityScorer
from .alert_manager import AlertManager

__all__ = [
    "SelloffDetector",
    "UniverseManager", 
    "PriorityScorer",
    "AlertManager",
]
