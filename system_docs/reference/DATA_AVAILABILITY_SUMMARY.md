# Data Availability Summary for Strategy Testing

**Generated:** 2026-01-18  
**Purpose:** Quick reference for available cached data

---

## ✅ Confirmed Available Data

### Strategy 1: Daily Trend Hysteresis
- **SPY**: ✅ Daily data (2018-2026) - 7 files including recent data
- **QQQ**: Need to verify  
- **IWM**: Need to verify
- **GLD**: Need to verify

### Strategy 2: Hourly Swing
- **TSLA**: Need to verify
- **NVDA**: Need to verify

### Strategy 5: Bear Trap (1-minute data required)
- **AMC**: ✅ Excellent coverage (2022-2025) - 11 files
- **MULN**: Need to verify
- **ONDS**: Need to verify  
- **NKLA**: Need to verify
- **SENS**: Need to verify
- **ACB**: Need to verify
- **GOEV**: Need to verify
- **BTCS**: Need to verify
- **WKHS**: Need to verify

### Strategy 6: GSB (Futures)
- **NG (Natural Gas)**: ✅ Hourly data (2022-2025) - 3 files
- **SB (Sugar)**: Need to verify

---

## 📋 Data Check Commands

Run this to see ALL available symbols:

```powershell
# Check equities
Get-ChildItem data\cache\equities\*.parquet | ForEach-Object { $_.Name -replace '_.*' } | Sort-Object -Unique

# Check futures  
Get-ChildItem data\cache\futures\*.parquet | ForEach-Object { $_.Name -replace '_.*' } | Sort-Object -Unique
```

---

## 🔍 Detailed Data Verification

### For Daily Trend (ETFs):
```powershell
foreach ($sym in @('SPY','QQQ','IWM','GLD')) {
    Write-Host "`n$sym Daily Data:"
    Get-ChildItem "data\cache\equities\${sym}_1day_*.parquet" | Select-Object Name, Length, LastWriteTime
}
```

### For Hourly Swing (Tech):
```powershell
foreach ($sym in @('TSLA','NVDA')) {
    Write-Host "`n$sym Hourly Data:"
    Get-ChildItem "data\cache\equities\${sym}_1hour_*.parquet" | Select-Object Name, Length, LastWriteTime
}
```

### For Bear Trap (Small-caps - 1-min):
```powershell
foreach ($sym in @('MULN','ONDS','NKLA','AMC','SENS','ACB','GOEV','BTCS','WKHS')) {
    Write-Host "`n$sym 1-Minute Data:"
    $files = Get-ChildItem "data\cache\equities\${sym}_1min_*.parquet" -ErrorAction SilentlyContinue
    if ($files) {
        $files | Select-Object Name, @{N='Size MB';E={[math]::Round($_.Length/1MB,2)}}
    } else {
        Write-Host "  NO DATA FOUND" -ForegroundColor Red
    }
}
```

### For GSB (Futures):
```powershell
Write-Host "`nNatural Gas:"
Get-ChildItem "data\cache\futures\NG*.parquet" | Select-Object Name

Write-Host "`nSugar:"
Get-ChildItem "data\cache\futures\SB*.parquet" | Select-Object Name
```

---

## 🚨 If Data is Missing

### Option 1: Use scripts/fetch_data.py
```powershell
# Example for missing daily data
python scripts\fetch_data.py --symbol QQQ --timeframe 1day --start 2024-01-01 --end 2024-12-31

# Example for missing 1-minute data
python scripts\fetch_data.py --symbol MULN --timeframe 1min --start 2024-12-01 --end 2024-12-31
```

### Option 2: Check if there's a prefetch script
```powershell
ls scripts\*prefetch*.py
ls scripts\*download*.py
```

### Option 3: Use existing test scripts
Many test scripts in `research/Perturbations/` automatically fetch data if missing.

---

## 📊 Key Findings

Based on sample checks:

1. **SPY has excellent coverage** (2018-2026) - Daily Trend Strategy ready
2. **AMC has full 1-minute data** (2022-2025) - Bear Trap can be tested on AMC
3. **NG (Natural Gas) has hourly data** - GSB partially testable (might need 1-min)

**Next Steps:**
1. Run the comprehensive data check commands above
2. Identify which symbols need data downloads
3. Use `scripts/fetch_data.py` to fill gaps
4. Then proceed with testing using `STRATEGY_TESTING_GUIDE.md`

---

**Status:** Partial verification complete  
**Action Required:** Full data inventory check
