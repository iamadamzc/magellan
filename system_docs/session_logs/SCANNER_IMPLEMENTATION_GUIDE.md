# Bear Trap Dynamic Scanner - Implementation Guide

**Date:** January 26, 2026  
**Scan Interval:** 15 minutes  
**Threshold:** -10% day change  
**Data Sources:** Alpaca (SIP feed) + FMP (optional)

---

## 📡 AVAILABLE DATA SOURCES

### **1. Alpaca Market Data Plus (SIP Feed)** ✅
**What You Have:**
- Real-time stock quotes
- 1-minute historical bars
- Snapshots (current price + day change)
- Premium SIP feed access

**API Client:**
```python
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockSnapshotRequest, StockBarsRequest

self.data_client = StockHistoricalDataClient(api_key, api_secret)
```

**Key Methods:**
- `get_stock_snapshot()` - Current price, volume, day change
- `get_stock_bars()` - Historical 1-min bars
- Feed: `feed="sip"` (already configured)

### **2. Financial Modeling Prep (FMP)** ✅
**What You Have:**
- Highest subscription tier
- Real-time stock screeners
- Market movers API
- Commodities/Forex data

**Endpoints Available:**
- `/api/v3/stock_market/losers` - Top losers by % change
- `/api/v3/stock_market/actives` - Most active stocks
- `/api/v3/quote/{symbol}` - Real-time quotes

---

## 🔧 SCANNER IMPLEMENTATION OPTIONS

### **Option 1: Alpaca Snapshots (RECOMMENDED)**

**Approach:** Batch-fetch snapshots for a pre-defined universe

**Pros:**
- ✅ Already integrated (using Alpaca)
- ✅ Real-time data
- ✅ No additional API setup
- ✅ Includes volume, spread, day change

**Cons:**
- ⚠️ Need to define universe (can't scan "entire market")
- ⚠️ Limited to ~500 symbols per batch

**Implementation:**
```python
from alpaca.data.requests import StockSnapshotRequest

def scan_universe_for_crashes(self):
    """Scan pre-defined universe for stocks down -10%+"""
    
    # Universe: Top 200 liquid small-caps
    universe = self.config.get('scanner', {}).get('base_universe', [])
    
    # Batch fetch snapshots
    request = StockSnapshotRequest(symbol_or_symbols=universe)
    snapshots = self.data_client.get_stock_snapshot(request)
    
    candidates = []
    for symbol, snapshot in snapshots.items():
        # Calculate day change
        if snapshot.daily_bar:
            day_change_pct = (
                (snapshot.latest_trade.price - snapshot.daily_bar.open) / 
                snapshot.daily_bar.open * 100
            )
            
            # Filter criteria
            if (day_change_pct <= -10.0 and
                snapshot.latest_trade.price > 0.50 and
                snapshot.latest_trade.price < 100 and
                snapshot.daily_bar.volume > 100000):
                
                candidates.append({
                    'symbol': symbol,
                    'day_change': day_change_pct,
                    'price': snapshot.latest_trade.price,
                    'volume': snapshot.daily_bar.volume
                })
    
    return candidates
```

---

### **Option 2: FMP Stock Screener**

**Approach:** Use FMP's built-in screener for market losers

**Pros:**
- ✅ Scans entire market automatically
- ✅ Pre-sorted by % change
- ✅ No universe maintenance needed

**Cons:**
- ⚠️ Need to set up FMP client
- ⚠️ Additional API integration

**Implementation:**
```python
import requests

def scan_market_with_fmp(self):
    """Use FMP to find top losers"""
    
    fmp_api_key = self.config.get('fmp_api_key')
    url = f"https://financialmodelingprep.com/api/v3/stock_market/losers?apikey={fmp_api_key}"
    
    response = requests.get(url)
    losers = response.json()
    
    candidates = []
    for stock in losers[:50]:  # Top 50 losers
        if (stock['changesPercentage'] <= -10.0 and
            stock['price'] > 0.50 and
            stock['price'] < 100 and
            stock['volume'] > 100000):
            
            candidates.append({
                'symbol': stock['symbol'],
                'day_change': stock['changesPercentage'],
                'price': stock['price'],
                'volume': stock['volume']
            })
    
    return candidates
```

---

### **Option 3: Hybrid (BEST FOR YOU)**

**Approach:** Use FMP to discover, Alpaca to validate

**Why This Works:**
1. FMP finds the losers (entire market scan)
2. Alpaca validates liquidity (spread, volume)
3. Best of both worlds

**Implementation:**
```python
def scan_market_hybrid(self):
    """Hybrid: FMP discovers, Alpaca validates"""
    
    # Step 1: Get top losers from FMP
    fmp_losers = self._get_fmp_losers(limit=100)
    
    # Step 2: Validate with Alpaca snapshots
    symbols_to_check = [stock['symbol'] for stock in fmp_losers]
    
    request = StockSnapshotRequest(symbol_or_symbols=symbols_to_check)
    snapshots = self.data_client.get_stock_snapshot(request)
    
    validated_candidates = []
    for symbol, snapshot in snapshots.items():
        # Check liquidity via Alpaca
        spread = snapshot.latest_quote.ask_price - snapshot.latest_quote.bid_price
        spread_pct = spread / snapshot.latest_trade.price
        
        if (spread_pct < 0.05 and  # Max 5% spread
            snapshot.daily_bar.volume > 100000):
            
            validated_candidates.append({
                'symbol': symbol,
                'day_change': self._calc_day_change(snapshot),
                'price': snapshot.latest_trade.price,
                'volume': snapshot.daily_bar.volume,
                'spread_pct': spread_pct
            })
    
    return validated_candidates
```

---

## 📋 RECOMMENDED IMPLEMENTATION

### **Use Option 1 (Alpaca Snapshots) for Simplicity**

**Base Universe (200 symbols):**
```python
SMALL_CAP_UNIVERSE = [
    # Meme/Volatile (20)
    "AMC", "GME", "ONDS", "SNDL", "KOSS", "EXPR", "BBBY", "CLOV",
    "WISH", "SOFI", "PLTR", "NIO", "LCID", "RIVN", "HOOD", "COIN",
    "DKNG", "PENN", "FUBO", "SKLZ",
    
    # Crypto-Related (15)
    "RIOT", "MARA", "BTBT", "BTCS", "CAN", "EBON", "SOS", "GREE",
    "CIFR", "HIVE", "HUT", "BITF", "ARBK", "CLSK", "CORZ",
    
    # Cannabis (10)
    "TLRY", "ACB", "CGC", "SNDL", "CRON", "HEXO", "OGI", "CURLF",
    "GTBIF", "TCNNF",
    
    # Biotech/Pharma (30)
    "OCGN", "SENS", "GEVO", "BNGO", "NVAX", "NTLA", "CRSP", "EDIT",
    "BEAM", "VERV", "BLUE", "FATE", "SGMO", "CRBU", "IONS",
    "SRPT", "RARE", "BMRN", "ALNY", "VRTX", "REGN", "BIIB",
    "GILD", "AMGN", "CELG", "MYL", "TEVA", "ABBV", "LLY", "PFE",
    
    # EV/Battery (15)
    "WKHS", "PLUG", "FCEL", "BLNK", "CHPT", "QS", "NKLA", "GOEV",
    "ARVL", "FSR", "RIDE", "HYLN", "SOLO", "AYRO", "ELMS",
    
    # Tech/Small-Cap (30)
    "DNUT", "CVNA", "UPST", "AFRM", "OPEN", "RDFN", "Z", "ZG",
    "PTON", "BYND", "OATLY", "DASH", "UBER", "LYFT", "ABNB",
    "SNOW", "DDOG", "CRWD", "ZS", "OKTA", "MDB", "NET", "FSLY",
    "TWLO", "DOCU", "ZM", "TEAM", "WDAY", "NOW", "VEEV",
    
    # Energy/Commodities (10)
    "DVLT", "TELL", "CLNE", "BKEP", "USWS", "PTEN", "RIG", "VAL",
    "HP", "NBR",
    
    # SPACs/Recent IPOs (20)
    "SPCE", "OPEN", "MTTR", "IONQ", "RKLB", "BROS", "RIVN", "LCID",
    "HOOD", "COIN", "RBLX", "ABNB", "DASH", "SNOW", "U", "PLTR",
    "WISH", "CLOV", "SOFI", "DKNG",
    
    # Other Volatile (50)
    # Add more as needed...
]
```

---

## 🚀 IMPLEMENTATION STEPS

### **Step 1: Add Scanner to Strategy (1 hour)**

**File:** `deployable_strategies/bear_trap/strategy.py`

**Add after line 68:**
```python
# Scanner state
self.scanner_enabled = config.get('scanner', {}).get('enabled', False)
self.scan_interval = config.get('scanner', {}).get('scan_interval_seconds', 900)  # 15 min
self.base_universe = config.get('scanner', {}).get('base_universe', [])
self.watch_list = set(self.base_universe)
self.last_scan_time = None

self.logger.info(f"Scanner: {'enabled' if self.scanner_enabled else 'disabled'}")
```

**Add scanner method:**
```python
def _should_scan(self):
    """Check if it's time to scan"""
    if not self.scanner_enabled:
        return False
    
    if self.last_scan_time is None:
        return True
    
    elapsed = (datetime.now() - self.last_scan_time).total_seconds()
    return elapsed >= self.scan_interval

def _update_watch_list(self):
    """Scan market for stocks down -10%+"""
    self.logger.info("🔍 Scanning market for candidates...")
    
    try:
        # Fetch snapshots for universe
        request = StockSnapshotRequest(symbol_or_symbols=self.base_universe)
        snapshots = self.data_client.get_stock_snapshot(request)
        
        candidates = set(self.base_universe)  # Always include base
        
        for symbol, snapshot in snapshots.items():
            if not snapshot.daily_bar:
                continue
            
            # Calculate day change
            day_change = (
                (snapshot.latest_trade.price - snapshot.daily_bar.open) / 
                snapshot.daily_bar.open * 100
            )
            
            # Add if down -10%+ with good liquidity
            if (day_change <= -10.0 and
                snapshot.latest_trade.price > 0.50 and
                snapshot.daily_bar.volume > 100000):
                candidates.add(symbol)
        
        self.watch_list = candidates
        self.last_scan_time = datetime.now()
        
        self.logger.info(f"✓ Watch list updated: {len(self.watch_list)} symbols")
        
    except Exception as e:
        self.logger.error(f"Scanner error: {e}")
```

**Update process_market_data (line 70):**
```python
def process_market_data(self):
    """Fetch and process 1-minute bars for all symbols"""
    
    # Update watch list if scanner enabled
    if self._should_scan():
        self._update_watch_list()
    
    # Process current watch list
    for symbol in self.watch_list:
        try:
            # ... existing code ...
```

---

### **Step 2: Update Config**

**File:** `deployed/bear_trap/config.json`

**Add scanner section:**
```json
{
    "scanner": {
        "enabled": true,
        "scan_interval_seconds": 900,
        "min_day_change_pct": -10.0,
        "base_universe": [
            "ONDS", "AMC", "WKHS", "ACB", "SENS", "BTCS",
            "PLUG", "MARA", "RIOT", "OCGN", "GME", "TLRY",
            "SNDL", "KOSS", "EXPR", "CLOV", "SOFI", "PLTR",
            "NIO", "LCID", "RIVN", "HOOD", "COIN", "DKNG"
        ],
        "filters": {
            "min_volume": 100000,
            "min_price": 0.50,
            "max_price": 100
        }
    }
}
```

**Update entry threshold:**
```json
{
    "entry_criteria": {
        "min_day_change_pct": -10.0
    }
}
```

---

### **Step 3: Test Locally**

```powershell
# Set environment
$env:ALPACA_API_KEY="your_paper_key"
$env:ALPACA_API_SECRET="your_paper_secret"
$env:ENVIRONMENT="testing"

# Run
cd a:\1\Magellan
python deployable_strategies/bear_trap/runner.py
```

**Expected Output:**
```
🔍 Scanning market for candidates...
✓ Watch list updated: 24 symbols
Processing ONDS... day_change: -2.3%
Processing AMC... day_change: -11.5% ← Candidate!
Processing GME... day_change: +3.1%
...
```

---

## ✅ NEXT STEPS

1. **I'll implement the scanner** (1 hour)
2. **Update config** (5 minutes)
3. **Test locally** (15 minutes)
4. **Deploy after hours** (5 minutes)
5. **Monitor tomorrow** (see trades!)

**Ready to proceed?**
