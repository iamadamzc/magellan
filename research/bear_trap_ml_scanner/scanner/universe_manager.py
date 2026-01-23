"""
Universe Manager - Symbol List Management

Manages the universe of symbols to scan for selloff opportunities.
Supports static lists and dynamic expansion.
"""

from typing import List, Set
from pathlib import Path
import json


class UniverseManager:
    """Manages the symbol universe for scanning"""
    
    def __init__(self, mode: str = "static_50"):
        """
        Initialize universe manager
        
        Args:
            mode: Universe selection mode
                - "static_50": 50 validated symbols
                - "static_250": Full 250 research symbols
                - "custom": Load from custom file
        """
        self.mode = mode
        self.symbols: Set[str] = set()
        self._load_universe()
    
    def _load_universe(self):
        """Load symbol universe based on mode"""
        if self.mode == "static_50":
            self.symbols = self._get_static_50()
        elif self.mode == "static_250":
            self.symbols = self._get_static_250()
        elif self.mode == "custom":
            self.symbols = self._load_custom()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def _get_static_50(self) -> Set[str]:
        """Get 50-symbol validated universe"""
        return {
            "ONDS", "ACB", "AMC", "WKHS", "MULN", "GOEV", "BTCS", "SENS", "GME",
            "PLUG", "TLRY", "NVAX", "MARA", "RIOT", "OCGN", "NKLA",
            "FFIE", "ANY", "ATNF", "BIOL", "TNXP", "GMBL", "PHUN",
            "CAN", "LIDR", "BNGO", "TELL", "SNDL", "CLSK", "BKKT",
            "NAKD", "IREN", "JAGX", "BTBT", "SOS", "BBIG", "CIFR",
            "VXRT", "RGTI", "MAXN", "WULF", "ARQQ", "ARVL", "GREE",
            "EXPR", "CVNA", "VERU", "HEXO", "CGC", "CTRM"
        }
    
    def _get_static_250(self) -> Set[str]:
        """Get full 250-symbol research universe"""
        # This would load from the research data
        # For now, start with 50 and expand
        base = self._get_static_50()
        
        # Add more volatile small-caps
        additional = {
            "SAVA", "BBBY", "WISH", "CLOV", "SPCE", "SOFI", "HOOD",
            "LCID", "RIVN", "COIN", "RBLX", "DKNG", "PLTR", "SKLZ",
            "OPEN", "UPST", "AFRM", "PTON", "ZM", "DOCU", "DASH",
            # Add more as needed...
        }
        
        return base.union(additional)
    
    def _load_custom(self) -> Set[str]:
        """Load custom symbol list from file"""
        custom_path = Path("research/bear_trap_ml_scanner/scanner/custom_universe.json")
        if custom_path.exists():
            with open(custom_path) as f:
                data = json.load(f)
                return set(data.get("symbols", []))
        return self._get_static_50()
    
    def get_symbols(self) -> List[str]:
        """Get list of symbols to scan"""
        return sorted(list(self.symbols))
    
    def add_symbol(self, symbol: str):
        """Add symbol to universe"""
        self.symbols.add(symbol.upper())
    
    def remove_symbol(self, symbol: str):
        """Remove symbol from universe"""
        self.symbols.discard(symbol.upper())
    
    def get_count(self) -> int:
        """Get number of symbols in universe"""
        return len(self.symbols)
    
    def save_custom(self, filepath: str):
        """Save current universe to custom file"""
        with open(filepath, 'w') as f:
            json.dump({"symbols": sorted(list(self.symbols))}, f, indent=2)
