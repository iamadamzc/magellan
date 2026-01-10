# FMP API Migration Summary

## Problem
Received 403 Forbidden errors from legacy FMP endpoints (v3/v4) requiring migration to the modern **Stable** API.

## Solution ✅ (Updated 2026-01-09)
Migrated to FMP **Stable** endpoints as the primary API route. Legacy v3 is now an opt-in fallback only.

---

## Implemented Endpoints

### News Sentiment
- **Stable (Primary)**: `https://financialmodelingprep.com/stable/news/stock?symbols={symbol}&limit=50`
- **Legacy v3 (Opt-in)**: `/api/v3/stock_news?tickers={symbol}&limit=50`
- **Parameter difference**: Stable uses `symbols=` (plural), legacy uses `tickers=`

### Quote / Fundamental Metrics
- **Stable (Primary)**: `https://financialmodelingprep.com/stable/quote?symbol={symbol}`
- **Legacy v3 (Opt-in)**: `/api/v3/quote/{symbol}` (path param)
- **Parameter difference**: Stable uses query param, legacy uses path param

### Other Stable Endpoints (Available)
- **Profile**: `https://financialmodelingprep.com/stable/profile?symbol={symbol}`
- **Ratios**: `https://financialmodelingprep.com/stable/ratios?symbol={symbol}`
- **Key Metrics**: `https://financialmodelingprep.com/stable/key-metrics?symbol={symbol}`

---

## Key Features

### 1. Stable-First Fallback Strategy
- **Primary**: Always try stable endpoints first
- **Fallback**: Legacy v3 only if explicitly enabled via `use_legacy_fallback=True`
- **Removed**: v4 endpoint attempts (was redundant)

### 2. FMPDataClient Constructor
```python
# Default: Stable only (recommended)
fmp_client = FMPDataClient()

# With legacy fallback (only if your account has v3 access)
fmp_client = FMPDataClient(use_legacy_fallback=True)
```

### 3. Proxy Sentiment Calculation
Implemented two-tier sentiment calculation:
1. Average article `sentiment` fields when available
2. Use news frequency as engagement proxy when sentiment unavailable

### 4. Enhanced Debugging
- Endpoint-specific logging (`[FMP] Attempting STABLE news endpoint...`)
- Masked URL display (shows first 4 chars of API key)
- Clear fallback indication (`trying next endpoint...`)

### 5. Robust Error Handling
- Separate handling for HTTP, network, and parse errors
- Graceful defaults (sentiment=0 on failure)
- Informative console output for troubleshooting

---

## Testing Instructions

Run the pipeline:
```powershell
python main.py
```

Expected console output (successful stable):
```
[FMP] Attempting STABLE news endpoint: https://...?symbols=SPY&limit=50&apikey=XXXX...
[FMP] Successfully fetched from STABLE
[FMP] Processed 50 articles, proxy sentiment: 0.XXXX
```

Expected console output (stable fails, legacy enabled):
```
[FMP] Attempting STABLE news endpoint: https://...
[FMP] 403 Forbidden on STABLE, trying next endpoint...
[FMP] Attempting V3-LEGACY news endpoint: https://...
[FMP] Successfully fetched from V3-LEGACY
```

If all endpoints fail:
```
[FMP] All endpoints failed for SPY, defaulting to sentiment=0
```

---

## Migration Checklist

- [x] Replace v3/v4 base URLs with `/stable`
- [x] Update news endpoint path: `/news/stock` (stable) vs `/stock_news` (legacy)
- [x] Update parameter names: `symbols` (stable) vs `tickers` (legacy)  
- [x] Update quote endpoint: query param (stable) vs path param (legacy)
- [x] Remove v4 as fallback (not needed)
- [x] Make legacy fallback opt-in only
- [x] Handle both list and dict responses for quote endpoint

---

## Files Changed
- `src/data_handler.py` - Migrated to stable endpoints, removed v4, made v3 opt-in
- `FMP_MIGRATION.md` - Updated documentation

**Status**: ✅ Stable API Migration Complete
