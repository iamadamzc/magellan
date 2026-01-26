"""
Engine Configuration Loader (Singleton)
Provides centralized access to engine parameters from JSON config files.
"""

import json
import os
from typing import Any, Optional


class EngineConfig:
    """
    Singleton class for loading and accessing engine configuration parameters.

    Usage:
        config = EngineConfig()  # Uses default path
        config = EngineConfig('/custom/path/config.json')  # Custom path

        value = config.get('RETRAIN_INTERVAL')  # Returns None if missing
        value = config.get('RETRAIN_INTERVAL', strict=True)  # Raises ValueError if missing
    """

    _instance: Optional["EngineConfig"] = None
    _config: dict = {}
    _config_path: str = ""
    _initialized: bool = False

    def __new__(cls, config_path: Optional[str] = None) -> "EngineConfig":
        """
        Create or return singleton instance.

        Args:
            config_path: Optional path to JSON config file.
                         Defaults to 'src/configs/mag7_default.json'
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize config loader with specified or default path.

        Args:
            config_path: Optional path to JSON config file.
                         Defaults to 'src/configs/mag7_default.json'
        """
        # Only load once (singleton pattern)
        if EngineConfig._initialized:
            return

        # Determine config path
        if config_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "src", "configs", "mag7_default.json")

        EngineConfig._config_path = config_path

        # Load configuration
        self._load_config(config_path)
        EngineConfig._initialized = True

    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to JSON config file
        """
        print(f"[INFO] ENGINE: Loading config from {config_path}")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            EngineConfig._config = json.load(f)

    def get(self, key: str, strict: bool = False) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Configuration parameter name
            strict: If True, raise ValueError when key is missing.
                    If False, return None for missing keys.

        Returns:
            Configuration value or None (if not strict)

        Raises:
            ValueError: If strict=True and key is not found
        """
        if key in EngineConfig._config:
            return EngineConfig._config[key]

        if strict:
            available_keys = list(EngineConfig._config.keys())
            raise ValueError(f"Missing required config key: '{key}'. " f"Available keys: {available_keys}")

        return None

    @classmethod
    def reset(cls) -> None:
        """
        Reset singleton instance (for testing purposes).
        """
        cls._instance = None
        cls._config = {}
        cls._config_path = ""
        cls._initialized = False

    @property
    def config_path(self) -> str:
        """Return the active configuration file path."""
        return EngineConfig._config_path

    @property
    def all_keys(self) -> list:
        """Return all available configuration keys."""
        return list(EngineConfig._config.keys())
