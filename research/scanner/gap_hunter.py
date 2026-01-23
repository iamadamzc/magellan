import pandas as pd
import requests
import os
from dotenv import load_dotenv
import concurrent.futures
from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockSnapshotRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
import logging

# Load Env for FMP Key
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")

# FMP Stable URL
FMP_STABLE_URL = "https://financialmodelingprep.com/stable"

# Import intraday analysis
try:
    from intraday_analysis import get_opening_drive_strength
except ImportError:
    get_opening_drive_strength = None

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets/v2" # Trading Client URL
DATA_URL = "https://data.alpaca.markets/v2" # Data Client URL (IEX is default for paper)


class AlpacaScanner:
    def __init__(self):
        self.trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
        self.data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
        
        # Strategy Parameters (Defaults from TRADING_STRATEGY.md)
        self.MIN_PRICE = 1.00
        self.MAX_PRICE = 20.00
        self.MIN_DOLLAR_VOLUME = 2_000_000
        self.MIN_RVOL = 2.0
        self.MAX_FLOAT = 80_000_000
        self.MIN_DAY_CHANGE_PCT = 0.02 # 2%
        
        # Candidate tracking
        self.candidates = {}  # {symbol: {'data': row_dict, 'first_seen': datetime}}
        
    def get_universe(self):
        """Fetches active, tradable, shortable, marginable US equities."""
        logger.info("Fetching universe from Alpaca...")
        req = GetAssetsRequest(
            status=AssetStatus.ACTIVE,
            asset_class=AssetClass.US_EQUITY
        )
        assets = self.trading_client.get_all_assets(req)
        
        # Filter for tradable, shortable, marginable
        universe = [
            a.symbol for a in assets 
            if a.tradable and a.shortable and a.marginable
        ]
        logger.info(f"Universe size: {len(universe)} symbols")
        return universe

    def get_snapshots(self, symbols):
        """Fetches snapshots and applies pre-filters (Price, Dollar Vol)."""
        logger.info(f"Fetching snapshots for {len(symbols)} symbols...")
        
        # Alpaca allows max 1000 symbols per request? Chunking is safer.
        chunk_size = 1000
        candidates = []
        
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i+chunk_size]
            try:
                req = StockSnapshotRequest(symbol_or_symbols=chunk)
                snapshots = self.data_client.get_stock_snapshot(req)
                
                for symbol, snapshot in snapshots.items():
                    if not snapshot.latest_trade or not snapshot.daily_bar:
                        continue
                        
                    price = snapshot.latest_trade.price
                    # Handle cases where daily_bar volume might be None (early morning)
                    vol = snapshot.daily_bar.volume if snapshot.daily_bar.volume else 0
                    dollar_vol = price * vol
                    
                    # Hard Filter: Price & Dollar Volume
                    if self.MIN_PRICE <= price <= self.MAX_PRICE and dollar_vol >= self.MIN_DOLLAR_VOLUME:
                        # Calculate % change from TODAY'S OPEN
                        daily_bar = snapshot.daily_bar
                        open_price = daily_bar.open if daily_bar and daily_bar.open else price
                        change_pct = (price - open_price) / open_price if open_price > 0 else 0
                        
                        if change_pct >= self.MIN_DAY_CHANGE_PCT:
                            candidates.append({
                                'Ticker': symbol,
                                'Price': price,
                                'Volume': vol,
                                'DollarVol': dollar_vol,
                                'Gap%': change_pct * 100, # Store as percentage
                                'Snapshot': snapshot
                            })
            except Exception as e:
                logger.error(f"Error fetching snapshots for chunk {i}: {e}")
                
        df = pd.DataFrame(candidates)
        if not df.empty:
            # Sort by Gap% initially to prioritize processing
            df = df.sort_values(by='Gap%', ascending=False)
            
            # Enrich with FMP real-time quotes for accuracy
            if FMP_API_KEY:
                logger.info("Enriching with FMP real-time quotes...")
                df = self.enrich_fmp_realtime(df)
            
        logger.info(f"Pre-filter candidates: {len(df)}")
        return df
    
    def enrich_fmp_realtime(self, df):
        """Enriches with FMP real-time quotes for more accurate volume/price."""
        if df.empty:
            return df
        
        tickers = df['Ticker'].tolist()[:50]  # Limit to top 50
        tickers_str = ",".join(tickers)
        
        try:
            url = f"{FMP_STABLE_URL}/quote?symbol={tickers_str}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                fmp_data = response.json()
                fmp_map = {item['symbol']: item for item in fmp_data}
                
                for idx, row in df.iterrows():
                    ticker = row['Ticker']
                    if ticker in fmp_map:
                        fmp_quote = fmp_map[ticker]
                        # Update with FMP real-time data
                        df.at[idx, 'Price'] = fmp_quote.get('price', row['Price'])
                        df.at[idx, 'Volume'] = fmp_quote.get('volume', row['Volume'])
                        df.at[idx, 'DollarVol'] = df.at[idx, 'Price'] * df.at[idx, 'Volume']
                        
                        # Calculate % change from TODAY'S OPEN (not previous close)
                        open_price = fmp_quote.get('open', row['Price'])
                        if open_price > 0:
                            df.at[idx, 'Gap%'] = ((df.at[idx, 'Price'] - open_price) / open_price) * 100
        except Exception as e:
            logger.error(f"Error enriching with FMP real-time: {e}")
        
        return df

    def get_rvol_threshold(self):
        """Determines RVOL threshold based on current market time (CST)."""
        now = datetime.now()
        # Market Open is 8:30 AM CST (9:30 AM EST)
        market_open = now.replace(hour=8, minute=30, second=0, microsecond=0)
        # Market Close is 3:00 PM CST (4:00 PM EST)
        market_close = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        if now < market_open or now > market_close:
            logger.info("Market Status: PRE/POST MARKET. Using lower RVOL threshold (0.1).")
            return 0.1
        else:
            logger.info("Market Status: OPEN. Using standard RVOL threshold (2.0).")
            return self.MIN_RVOL

    def get_history_and_rvol(self, candidates_df):
        """Fetches history for top candidates to calc RVOL and check warmup."""
        if candidates_df.empty:
            return candidates_df
            
        # Limit to top 50 to avoid rate limits and speed up (Strategy Spec 1.3)
        top_candidates = candidates_df.head(50).copy()
        symbols = top_candidates['Ticker'].tolist()
        
        logger.info(f"Fetching history for top {len(symbols)} candidates...")
        
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=60) # Fetch enough for 40 trading days
        
        req = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=start_dt,
            end=end_dt
        )
        
        bars = self.data_client.get_stock_bars(req)
        
        rvol_map = {}
        warmup_map = {}
        
        logger.info(f"Fetched bars for {len(bars.data)} symbols.")
        
        # Determine dynamic threshold
        current_rvol_threshold = self.get_rvol_threshold()
        
        for symbol in symbols:
            if symbol in bars.data:
                symbol_bars = bars.data[symbol]
                # Check Warmup (Min 20 bars)
                if len(symbol_bars) < 20:
                    logger.debug(f"{symbol}: Insufficient history ({len(symbol_bars)} bars)")
                    warmup_map[symbol] = False
                    rvol_map[symbol] = 0
                    continue
                
                warmup_map[symbol] = True
                
                # Calculate RVOL
                recent_bars = symbol_bars[:-1] 
                if len(recent_bars) < 20:
                     avg_vol = sum(b.volume for b in recent_bars) / len(recent_bars)
                else:
                     avg_vol = sum(b.volume for b in recent_bars[-20:]) / 20
                
                current_vol = top_candidates.loc[top_candidates['Ticker'] == symbol, 'Volume'].values[0]
                
                rvol = current_vol / avg_vol if avg_vol > 0 else 0
                rvol_map[symbol] = rvol
                
                if rvol < current_rvol_threshold:
                    logger.debug(f"{symbol}: Low RVOL ({rvol:.2f} < {current_rvol_threshold})")
            else:
                logger.debug(f"{symbol}: No bars data found")
                warmup_map[symbol] = False
                rvol_map[symbol] = 0
                
        top_candidates['RVOL'] = top_candidates['Ticker'].map(rvol_map)
        top_candidates['Warmup'] = top_candidates['Ticker'].map(warmup_map)
        
        # Filter: Min RVOL & Warmup
        before_len = len(top_candidates)
        top_candidates = top_candidates[
            (top_candidates['RVOL'] >= current_rvol_threshold) & 
            (top_candidates['Warmup'] == True)
        ]
        logger.info(f"History Filter: {before_len} -> {len(top_candidates)} candidates")
        
        return top_candidates

    def check_economic_calendar(self):
        """Checks for high-impact economic events in the next 2 hours."""
        if not FMP_API_KEY:
            return None
            
        try:
            url = f"{FMP_STABLE_URL}/economic-calendar?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                events = response.json()
                now = datetime.now()
                warning_window = now + timedelta(hours=2)
                
                high_impact = ['CPI', 'NFP', 'FOMC', 'GDP', 'Unemployment', 'Fed']
                
                for event in events[:50]:  # Check next 50 events
                    event_date_str = event.get('date', '')
                    if event_date_str:
                        try:
                            event_dt = datetime.strptime(event_date_str, '%Y-%m-%d %H:%M:%S')
                            if now <= event_dt <= warning_window:
                                event_name = event.get('event', '')
                                if any(keyword in event_name for keyword in high_impact):
                                    return {
                                        'event': event_name,
                                        'time': event_date_str,
                                        'impact': event.get('impact', 'Unknown')
                                    }
                        except:
                            continue
        except Exception as e:
            logger.error(f"Error checking economic calendar: {e}")
        return None

    def enrich_float(self, df):
        """Enriches with Float data using FMP API (Batch Request)."""
        if df.empty:
            return df
            
        tickers = df['Ticker'].tolist()
        logger.info(f"Enriching float for {len(tickers)} symbols via FMP...")
        
        float_map = {}
        
        try:
            # Batch Request using stable endpoint
            tickers_str = ",".join(tickers)
            if not FMP_API_KEY:
                logger.error("FMP_API_KEY not found in environment!")
            else:
                url = f"{FMP_STABLE_URL}/quote?symbol={tickers_str}&apikey={FMP_API_KEY}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        sym = item.get('symbol')
                        # Calculate shares from market cap / price
                        market_cap = item.get('marketCap')
                        price = item.get('price')
                        if market_cap and price and price > 0:
                            shares = market_cap / price
                            float_map[sym] = float(shares)
                            logger.debug(f"{sym}: Float = {shares/1_000_000:.2f}M (from marketCap={market_cap}, price={price})")
                else:
                    logger.error(f"FMP API Error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error fetching float from FMP: {e}")

        # Map results (Default to 0 if not found)
        df['Float'] = df['Ticker'].map(float_map).fillna(0)
        
        # Convert to Millions for display/logic consistency
        df['Float (M)'] = df['Float'] / 1_000_000
        
        # Filter Max Float
        df = df[df['Float'] <= self.MAX_FLOAT]
        
        return df

    def enrich_institutional_ownership(self, df):
        """Enriches with Institutional Ownership % using FMP."""
        if df.empty or not FMP_API_KEY:
            df['Institutional%'] = 0
            return df
            
        tickers = df['Ticker'].tolist()
        logger.info(f"Enriching institutional ownership for {len(tickers)} symbols...")
        
        inst_map = {}
        
        # Get current quarter (approximate)
        now = datetime.now()
        year = now.year if now.month > 3 else now.year - 1
        quarter = ((now.month - 1) // 3) if now.month > 3 else 4
        
        for ticker in tickers:
            try:
                url = f"{FMP_STABLE_URL}/institutional-ownership/symbol-positions-summary?symbol={ticker}&year={year}&quarter={quarter}&apikey={FMP_API_KEY}"
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        # Calculate institutional ownership %
                        total_shares = data[0].get('numberOf13Fshares', 0)
                        # Approximate: institutional shares / typical float
                        # For simplicity, we'll use a normalized score
                        inst_map[ticker] = min(total_shares / 1_000_000, 100)  # Cap at 100
                else:
                    inst_map[ticker] = 0
            except Exception as e:
                logger.debug(f"Error fetching institutional data for {ticker}: {e}")
                inst_map[ticker] = 0
        
        df['Institutional%'] = df['Ticker'].map(inst_map).fillna(0)
        return df

    def enrich_opening_drive(self, df):
        """Enriches top candidates with Opening Drive Strength (1-min intraday analysis)."""
        if df.empty or not get_opening_drive_strength:
            df['OpenDrive'] = "N/A"
            return df
        
        # Only analyze top 10 to avoid rate limits
        top_10 = df.head(10).copy()
        other = df.iloc[10:].copy() if len(df) > 10 else pd.DataFrame()
        
        logger.info(f"Analyzing opening drive for top {len(top_10)} candidates...")
        
        drive_map = {}
        for ticker in top_10['Ticker'].tolist():
            result = get_opening_drive_strength(ticker)
            if result:
                drive_map[ticker] = result['verdict']
            else:
                drive_map[ticker] = "N/A"
        
        top_10['OpenDrive'] = top_10['Ticker'].map(drive_map)
        
        if not other.empty:
            other['OpenDrive'] = "N/A"
            df = pd.concat([top_10, other], ignore_index=True)
        else:
            df = top_10
        
        return df

    def score_candidates(self, df):
        """Applies Algo-Shadow scoring formula with Smart Money boost."""
        if df.empty:
            df['Score'] = 0
            return df
            
        def calculate_score(row):
            # Base Score = RVOL
            score = row['RVOL']
            
            # Float Rotation Boost
            # float_rot = (current_vol / float_val)
            float_val = row['Float']
            if float_val > 0:
                float_rot = row['Volume'] / float_val
                # Boost: 1.0 + min(float_rot, 5.0)
                score *= (1.0 + min(float_rot, 5.0))
            
            # Ideal RVOL Boost (3.0 <= rvol <= 6.0) -> 1.5x
            if 3.0 <= row['RVOL'] <= 6.0:
                score *= 1.5
                
            # Tiny Float Boost (< 10M) -> 1.5x
            if row['Float'] <= 10_000_000:
                score *= 1.5
                
            # Ideal Day Change Boost (5% <= change <= 20%) -> 1.25x
            if 5.0 <= row['Gap%'] <= 20.0:
                score *= 1.25
            
            # Smart Money Boost (Institutional Ownership > 50) -> 1.3x
            if row.get('Institutional%', 0) > 50:
                score *= 1.3
                
            return score
            
        df['Score'] = df.apply(calculate_score, axis=1)
        return df.sort_values(by='Score', ascending=False)

    def run_scan(self):
        """
        Three-Stage Scan with News Filter
        
        Stage 1: Broad filter (Price, Volume, RVOL)
        Stage 2: News check (HARD FILTER - must have news in last 24h)
        Stage 3: Deep enrichment (Float, Institutional, Opening Drive)
        """
        # Import news checker
        try:
            from news_bot import has_recent_news
        except ImportError:
            logger.error("news_bot module not found - news filtering disabled")
            has_recent_news = None
        
        # Check for high-impact economic events
        econ_warning = self.check_economic_calendar()
        if econ_warning:
            logger.warning(f"⚠️ HIGH IMPACT EVENT: {econ_warning['event']} at {econ_warning['time']}")
        
        # STAGE 1: Broad Filter
        logger.info("=== STAGE 1: BROAD FILTER ===")
        universe = self.get_universe()
        if not universe:
            return pd.DataFrame()
            
        df = self.get_snapshots(universe)
        if df.empty:
            return pd.DataFrame()
            
        df = self.get_history_and_rvol(df)
        if df.empty:
            return pd.DataFrame()
        
        logger.info(f"Stage 1 complete: {len(df)} candidates")
        
        # STAGE 2: News Filter (CRITICAL FOR MOMENTUM SCALPING)
        logger.info("=== STAGE 2: NEWS FILTER ===")
        if has_recent_news:
            candidates_with_news = []
            for idx, row in df.iterrows():
                ticker = row['Ticker']
                if has_recent_news(ticker, hours=24):
                    candidates_with_news.append(row)
                    logger.info(f"✓ {ticker}: Has recent news")
                else:
                    logger.debug(f"✗ {ticker}: No recent news - FILTERED OUT")
            
            if not candidates_with_news:
                logger.info("No candidates with recent news")
                return pd.DataFrame()
            
            df = pd.DataFrame(candidates_with_news)
            logger.info(f"Stage 2 complete: {len(df)} candidates WITH NEWS")
        else:
            logger.warning("News filtering disabled - skipping Stage 2")
        
        # STAGE 3: Deep Enrichment
        logger.info("=== STAGE 3: DEEP ENRICHMENT ===")
        df = self.enrich_float(df)
        if df.empty:
            return pd.DataFrame()
        
        df = self.enrich_institutional_ownership(df)
        df = self.enrich_opening_drive(df)
        df = self.score_candidates(df)
        
        logger.info(f"Stage 3 complete: {len(df)} final candidates")
        
        # Update candidate tracking
        now = datetime.now()
        current_symbols = set(df['Ticker'].tolist())
        
        for _, row in df.iterrows():
            symbol = row['Ticker']
            if symbol not in self.candidates:
                # New candidate
                self.candidates[symbol] = {
                    'first_seen': now,
                    'data': row.to_dict()
                }
            else:
                # Update existing
                self.candidates[symbol]['data'] = row.to_dict()
                self.candidates[symbol]['last_updated'] = now
        
        # Remove stale candidates (not in current scan)
        stale = [s for s in self.candidates.keys() if s not in current_symbols]
        for symbol in stale:
            del self.candidates[symbol]
        
        # Add first_seen to dataframe
        df['FirstSeen'] = df['Ticker'].map(
            lambda s: self.candidates[s]['first_seen'] if s in self.candidates else now
        )
        
        # Final formatting
        final_cols = ['Ticker', 'Price', 'Gap%', 'Volume', 'RVOL', 'Float (M)', 'Institutional%', 'OpenDrive', 'Score', 'FirstSeen']
        # Ensure columns exist
        for col in final_cols:
            if col not in df.columns:
                df[col] = 0 if col not in ['OpenDrive', 'FirstSeen'] else ("N/A" if col == 'OpenDrive' else now)
                
        return df[final_cols]


# --- Wrapper for app.py compatibility ---
def fetch_market_gainers(min_price=1.0, max_price=20.0, min_gap_percent=2.0, max_float_million=80.0, min_rvol=2.0):
    """
    Wrapper function to maintain compatibility with app.py, 
    but using the new AlpacaScanner logic.
    Overrides default params with arguments if provided, though Scanner has its own defaults.
    """
    scanner = AlpacaScanner()
    
    # Override scanner config with UI inputs
    scanner.MIN_PRICE = min_price
    scanner.MAX_PRICE = max_price
    scanner.MIN_DAY_CHANGE_PCT = min_gap_percent / 100.0
    scanner.MAX_FLOAT = max_float_million * 1_000_000
    scanner.MIN_RVOL = min_rvol
    
    return scanner.run_scan()

if __name__ == "__main__":
    print("Starting Algo-Shadow Alpaca Scanner...")
    df = fetch_market_gainers()
    print(f"Found {len(df)} candidates.")
    if not df.empty:
        print(df.head(10))
