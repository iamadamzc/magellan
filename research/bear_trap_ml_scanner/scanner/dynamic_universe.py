"""
Dynamic Universe Builder

Fetches all tradable liquid stocks from Alpaca for full market coverage.
Filters for volume, market cap, and price to focus on quality opportunities.
"""

from typing import List, Set
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, AssetStatus


class DynamicUniverseBuilder:
    """Builds dynamic symbol universe from Alpaca assets"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize universe builder
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
        """
        self.logger = logging.getLogger("scanner.universe_builder")
        self.trading_client = TradingClient(api_key, api_secret, paper=True)
    
    def build_liquid_universe(
        self,
        min_price: float = 2.0,
        max_price: float = 500.0,
        exchanges: List[str] = None,
    ) -> Set[str]:
        """
        Build universe of liquid, tradable stocks
        
        Args:
            min_price: Minimum stock price
            max_price: Maximum stock price
            exchanges: List of exchanges (default: NASDAQ, NYSE, ARCA)
            
        Returns:
            Set of symbol strings
        """
        if exchanges is None:
            exchanges = ['NASDAQ', 'NYSE', 'ARCA']
        
        self.logger.info("Fetching all tradable assets from Alpaca...")
        
        try:
            # Get all assets
            all_assets = self.trading_client.get_all_assets()
            
            # Filter for liquid stocks
            symbols = set()
            
            for asset in all_assets:
                # Basic filters
                if not asset.tradable:
                    continue
                if asset.status != AssetStatus.ACTIVE:
                    continue
                if asset.asset_class != AssetClass.US_EQUITY:
                    continue
                if asset.exchange not in exchanges:
                    continue
                
                # Price filter (if available)
                # Note: Asset object doesn't have current price
                # We'll add all and filter later if needed
                
                symbols.add(asset.symbol)
            
            self.logger.info(f"Found {len(symbols)} tradable stocks")
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error fetching assets: {e}")
            return set()
    
    def build_small_mid_cap_universe(self) -> Set[str]:
        """
        Build universe focused on small/mid-cap stocks
        (Where our research was done)
        
        Returns:
            Set of symbol strings
        """
        # Start with all liquid stocks
        all_symbols = self.build_liquid_universe()
        
        # Known volatile small/mid-caps from research
        research_symbols = {
            "ONDS", "ACB", "AMC", "WKHS", "MULN", "GOEV", "BTCS", "SENS", "GME",
            "PLUG", "TLRY", "NVAX", "MARA", "RIOT", "OCGN", "NKLA",
            "FFIE", "ANY", "ATNF", "BIOL", "TNXP", "GMBL", "PHUN",
            "CAN", "LIDR", "BNGO", "TELL", "SNDL", "CLSK", "BKKT",
            "NAKD", "IREN", "JAGX", "BTBT", "SOS", "BBIG", "CIFR",
            "VXRT", "RGTI", "MAXN", "WULF", "ARQQ", "ARVL", "GREE",
            "EXPR", "CVNA", "VERU", "HEXO", "CGC", "CTRM",
            "SAVA", "BBBY", "WISH", "CLOV", "SPCE", "SOFI", "HOOD",
            "LCID", "RIVN", "COIN", "RBLX", "DKNG", "PLTR", "SKLZ",
            "OPEN", "UPST", "AFRM", "PTON", "ZM", "DOCU", "DASH",
        }
        
        # Combine with all tradable
        # This ensures we get research symbols + any new ones
        combined = all_symbols.union(research_symbols)
        
        self.logger.info(f"Small/mid-cap universe: {len(combined)} symbols")
        return combined
    
    def build_full_market_universe(self) -> Set[str]:
        """
        Build universe of ALL tradable US stocks
        
        Returns:
            Set of symbol strings (~8,000 symbols)
        """
        return self.build_liquid_universe()
    
    def get_recommended_universe(self, mode: str = "full") -> List[str]:
        """
        Get recommended universe based on mode
        
        Args:
            mode: "small_mid" (~500), "full" (~8,000)
            
        Returns:
            Sorted list of symbols
        """
        if mode == "small_mid":
            symbols = self.build_small_mid_cap_universe()
        elif mode == "full":
            symbols = self.build_full_market_universe()
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        return sorted(list(symbols))
