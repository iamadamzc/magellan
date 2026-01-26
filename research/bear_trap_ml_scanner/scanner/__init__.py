"""
Selloff Scanner Package

Real-time detection and prioritization of intraday selloff opportunities.
"""

__version__ = "2.0.0"

from .selloff_detector import SelloffDetector
from .universe_manager import UniverseManager
from .priority_scorer import PriorityScorer
from .alert_manager import AlertManager
from .websocket_scanner import WebSocketScanner
from .dynamic_universe import DynamicUniverseBuilder

__all__ = [
    "SelloffDetector",
    "UniverseManager",
    "PriorityScorer",
    "AlertManager",
    "WebSocketScanner",
    "DynamicUniverseBuilder",
]
