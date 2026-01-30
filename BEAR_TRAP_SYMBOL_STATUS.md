# Bear Trap Symbol Status - January 26, 2026

## DELISTED / INACTIVE SYMBOLS (REMOVE FROM CONFIG)

### 1. **NKLA (Nikola Corporation)** ❌ DELISTED
- **Status:** Delisted from Nasdaq in April 2025
- **Current:** Trading OTC as NKLAQ at ~$0.18
- **Reason:** Chapter 11 bankruptcy, delisted Feb 26, 2025
- **Action:** REMOVE from bear_trap config

### 2. **MULN (Mullen Automotive / Bollinger Innovations)** ❌ DELISTED  
- **Status:** Delisted from Nasdaq in October 2025
- **Current:** May trade OTC under limited volume
- **Reason:** Failed to maintain minimum bid price
- **Action:** REMOVE from bear_trap config

### 3. **GOEV (Canoo Inc.)** ❌ DELISTED
- **Status:** Delisted from Nasdaq on January 29, 2025
- **Current:** Chapter 7 bankruptcy
- **Reason:** Bankruptcy, compliance failure
- **Action:** REMOVE from bear_trap config

---

## ACTIVE SYMBOLS (KEEP IN CONFIG)

### ✅ Still Trading on Major Exchanges:

1. **ONDS** - ✅ Active
2. **ACB** - ✅ Active  
3. **AMC** - ✅ Active
4. **WKHS** - ✅ Active
5. **BTCS** - ✅ Active (confirmed trading Jan 2026)
6. **SENS** - ✅ Active
7. **DNUT** - ✅ Active
8. **CVNA** - ✅ Active
9. **PLUG** - ✅ Active
10. **KOSS** - ✅ Active
11. **TLRY** - ✅ Active
12. **DVLT** - ✅ Active (confirmed trading Jan 2026)
13. **NVAX** - ✅ Active
14. **NTLA** - ✅ Active
15. **MARA** - ✅ Active
16. **RIOT** - ✅ Active
17. **OCGN** - ✅ Active
18. **GME** - ✅ Active

---

## RECOMMENDED CONFIG UPDATE

### Current Config (21 symbols):
```json
"symbols": [
    "ONDS", "ACB", "AMC", "WKHS", "MULN",    // MULN delisted
    "GOEV", "BTCS", "SENS", "DNUT", "CVNA",  // GOEV delisted
    "PLUG", "KOSS", "TLRY", "DVLT", "NVAX",
    "NTLA", "MARA", "RIOT", "OCGN", "NKLA",  // NKLA delisted
    "GME"
]
```

### Updated Config (18 symbols):
```json
"symbols": [
    "ONDS", "ACB", "AMC", "WKHS",
    "BTCS", "SENS", "DNUT", "CVNA",
    "PLUG", "KOSS", "TLRY", "DVLT",
    "NVAX", "NTLA", "MARA", "RIOT",
    "OCGN", "GME"
]
```

**Removed:** NKLA, MULN, GOEV (3 delisted symbols)  
**Remaining:** 18 active symbols

---

## Why "No Data" Warnings

The logs showing "No data for NKLA" are **expected and correct** because:
1. NKLA is delisted from Nasdaq
2. Alpaca's SIP feed doesn't include OTC stocks
3. Strategy correctly handles missing data without crashing

**This is not a bug** - it's the strategy gracefully skipping symbols that don't have data.

---

## Action Required

Update the deployed config to remove delisted symbols:

**File:** `deployed/bear_trap/config.json`

**Change:** Remove NKLA, MULN, GOEV from symbols array

**Benefit:**
- Cleaner logs (no more "No data" warnings)
- Faster execution (skip API calls for dead symbols)
- Focus on tradeable opportunities

---

## Deployment Steps

```bash
# 1. Update local config
# Edit: deployed/bear_trap/config.json
# Remove: "NKLA", "MULN", "GOEV"

# 2. Commit and push
git add deployed/bear_trap/config.json
git commit -m "fix: Remove delisted symbols from bear_trap (NKLA, MULN, GOEV)"
git push origin deployment/aws-paper-trading-setup

# 3. CI/CD will auto-deploy
# 4. Service will restart with updated config
```

---

## Summary

- **3 symbols delisted:** NKLA, MULN, GOEV
- **18 symbols active:** All others confirmed trading
- **Current behavior:** Working correctly, just logging warnings for dead symbols
- **Recommended:** Update config to clean up symbol list
