# After-Hours Maintenance - Bear Trap Symbol Cleanup

**Scheduled:** After market close (4:00 PM ET / 3:00 PM CT)  
**Priority:** Low (cosmetic cleanup, not urgent)  
**Estimated Time:** 5 minutes

---

## Task: Remove Delisted Symbols from Bear Trap Config

### Symbols to Remove:
- **NKLA** (delisted April 2025)
- **MULN** (delisted October 2025)
- **GOEV** (delisted January 2025)

### File to Update:
`deployed/bear_trap/config.json`

---

## Step-by-Step Instructions

### 1. Update Config File

**File:** `a:\1\Magellan\deployed\bear_trap\config.json`

**Current symbols array (lines 16-38):**
```json
"symbols": [
    "ONDS",
    "ACB",
    "AMC",
    "WKHS",
    "MULN",    // ← REMOVE
    "GOEV",    // ← REMOVE
    "BTCS",
    "SENS",
    "DNUT",
    "CVNA",
    "PLUG",
    "KOSS",
    "TLRY",
    "DVLT",
    "NVAX",
    "NTLA",
    "MARA",
    "RIOT",
    "OCGN",
    "NKLA",    // ← REMOVE
    "GME"
]
```

**Updated symbols array (18 symbols):**
```json
"symbols": [
    "ONDS",
    "ACB",
    "AMC",
    "WKHS",
    "BTCS",
    "SENS",
    "DNUT",
    "CVNA",
    "PLUG",
    "KOSS",
    "TLRY",
    "DVLT",
    "NVAX",
    "NTLA",
    "MARA",
    "RIOT",
    "OCGN",
    "GME"
]
```

### 2. Commit and Deploy

```powershell
# Navigate to repo
cd a:\1\Magellan

# Stage changes
git add deployed/bear_trap/config.json

# Commit with descriptive message
git commit -m "fix: Remove delisted symbols from bear_trap config

Removed 3 delisted symbols:
- NKLA (delisted April 2025, bankruptcy)
- MULN (delisted October 2025, now OTC)
- GOEV (delisted January 2025, bankruptcy)

Remaining: 18 active symbols
Impact: Cleaner logs, no 'No data' warnings for dead symbols"

# Push to deployment branch
git push origin deployment/aws-paper-trading-setup
```

### 3. Monitor Deployment

```powershell
# Set AWS profile
$env:AWS_PAGER=""
$env:AWS_PROFILE="magellan_admin"

# Wait 2-3 minutes for CI/CD to deploy, then verify
aws ssm send-command --instance-ids i-0cd785630b55dd9a2 `
  --document-name "AWS-RunShellScript" `
  --parameters 'commands=["sudo systemctl status magellan-bear-trap","sudo journalctl -u magellan-bear-trap -n 20"]' `
  --region us-east-2
```

### 4. Verification Checklist

After deployment completes:

- [ ] Service restarted successfully
- [ ] No "No data for NKLA" warnings in logs
- [ ] No "No data for MULN" warnings in logs
- [ ] No "No data for GOEV" warnings in logs
- [ ] Strategy processing remaining 18 symbols
- [ ] No errors or crashes

---

## Expected Impact

### Before (21 symbols):
```
2026-01-26 15:45:32 - WARNING - No data for NKLA
2026-01-26 15:45:32 - WARNING - No data for MULN
2026-01-26 15:45:32 - WARNING - No data for GOEV
```

### After (18 symbols):
```
(Clean logs, no warnings for delisted symbols)
```

---

## Rollback Plan (if needed)

If any issues arise:

```powershell
# Connect to EC2
$env:AWS_PROFILE="magellan_admin"
aws ssm start-session --target i-0cd785630b55dd9a2 --region us-east-2

# On EC2:
cd /home/ssm-user/magellan
git log --oneline -3
git reset --hard HEAD~1  # Revert to previous commit
sudo systemctl restart magellan-bear-trap
```

---

## Notes

- **Timing:** Do this after 4:00 PM ET when market is closed
- **Risk:** Very low - just removing dead symbols
- **Benefit:** Cleaner logs, slightly faster execution
- **No impact on trading:** These symbols weren't tradeable anyway

---

## Current Status (as of 9:51 AM CT)

✅ Bear Trap is running successfully  
✅ AttributeError bug is fixed  
✅ Strategy is operational and monitoring for signals  
⚠️ Minor log warnings for 3 delisted symbols (cosmetic only)

**Action:** Wait until after market close to clean up config

---

**Created:** 2026-01-26 09:51 CT  
**Scheduled:** After 4:00 PM ET (3:00 PM CT)  
**Status:** Pending
