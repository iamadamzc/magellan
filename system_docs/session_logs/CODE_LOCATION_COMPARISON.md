# Code Location Comparison: /deployed vs /deployable_strategies

**Date:** January 26, 2026  
**Question:** Are /deployed and /deployable_strategies the same code?

---

## **ANSWER: NO - They serve DIFFERENT purposes**

---

## Directory Structure Comparison

### `/deployed/` - **Configuration & Service Definitions ONLY**

```
deployed/
├── bear_trap/
│   ├── config.json                          # Live production config
│   └── magellan-bear-trap.service           # Systemd service file
├── hourly_swing/
│   ├── config.json                          # Live production config
│   └── magellan-hourly-swing.service        # Systemd service file
└── daily_trend/
    ├── config.json                          # Live production config
    └── magellan-daily-trend.service         # Systemd service file
```

❌ **NO PYTHON CODE** - Only config and service files  
✅ **Purpose:** Store LIVE configuration and systemd service definitions

---

### `/deployable_strategies/` - **Actual Strategy Code**

```
deployable_strategies/
├── bear_trap/
│   ├── strategy.py          # ← THE ACTUAL STRATEGY IMPLEMENTATION
│   ├── runner.py            # ← THE EXECUTION RUNNER
│   ├── config.json          # ← DEFAULT/TEMPLATE CONFIG
│   ├── README.md
│   ├── docs/
│   ├── tests/
│   ├── deployment/
│   └── __pycache__/
├── hourly_swing/
│   ├── strategy.py          # ← THE ACTUAL STRATEGY IMPLEMENTATION
│   ├── runner.py            # ← THE EXECUTION RUNNER
│   ├── config.json          # ← DEFAULT/TEMPLATE CONFIG
│   ├── README.md
│   ├── docs/
│   ├── tests/
│   ├── deployment/
│   └── __pycache__/
└── daily_trend/
    └── (similar structure)
```

✅ **HAS ALL PYTHON CODE** - strategy.py, runner.py, tests, docs  
✅ **Purpose:** Immutable, production-ready code (the "gold master")

---

## How They Work Together

### Architecture Pattern: **Code Separation from Configuration**

```
On EC2 Instance:
/home/ssm-user/magellan/
├── deployable_strategies/      ← CODE (immutable)
│   └── bear_trap/
│       ├── strategy.py         ← Order execution logic lives HERE
│       └── runner.py           ← Entry point that loads config
│
└── deployed/                   ← CONFIG (environment-specific)
    └── bear_trap/
        ├── config.json         ← Account ID, symbols, thresholds
        └── *.service           ← Points to runner.py above
```

### Service File Connection

**File:** `deployed/bear_trap/magellan-bear-trap.service` (line 19)
```bash
ExecStart=/home/ssm-user/magellan/.venv/bin/python \
          /home/ssm-user/magellan/deployable_strategies/bear_trap/runner.py
          #                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          #                     RUNS CODE FROM deployable_strategies/
```

**Environment Variable:** (line 16)
```bash
Environment="CONFIG_PATH=/home/ssm-user/magellan/deployed/bear_trap/config.json"
#                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                        LOADS CONFIG FROM deployed/
```

**Result:**
- **Code** comes from `deployable_strategies/bear_trap/runner.py`
- **Config** comes from `deployed/bear_trap/config.json`
- They are **separate** but work together

---

## Why This Matters for Your Issue

### The Bug is in `/deployable_strategies/` NOT `/deployed/`

**The broken code:**
- Location: `deployable_strategies/bear_trap/runner.py` (lines 179-181)
- Problem: Calls methods that don't exist in `strategy.py`
- Fix needed: Edit `deployable_strategies/bear_trap/runner.py`

**NOT a config issue:**
- The configs in `deployed/bear_trap/config.json` are fine
- The bug is in the Python code itself

---

## What's Actually on EC2 Right Now?

Based on the CI/CD deployment workflow:

```yaml
# .github/workflows/deploy-strategies.yml (lines 151-155)
git fetch --all
git reset --hard origin/deployment/aws-paper-trading-setup
git clean -fd
source .venv/bin/activate
pip install -r requirements.txt
```

**On EC2 `/home/ssm-user/magellan/`:**
- ✅ Has `deployable_strategies/` with all code (including the bug)
- ✅ Has `deployed/` with config files
- ✅ Has `src/` with shared libraries
- ✅ Code matches `deployment/aws-paper-trading-setup` branch on GitHub

---

## Summary Table

| Directory | Contains | Purpose | Has Bug? |
|-----------|----------|---------|----------|
| `/deployed/` | config.json<br>.service files | Live production configuration | ❌ No |
| `/deployable_strategies/` | strategy.py<br>runner.py<br>tests/<br>docs/ | Production-ready strategy code | ✅ **YES** |

---

## To Fix the Issue

### Step 1: Edit the CODE (not the config)
```bash
# Fix this file:
a:\1\Magellan\deployable_strategies\bear_trap\runner.py

# Remove lines 179-181:
# strategy.evaluate_entries()
# strategy.manage_positions()
# strategy.check_risk_gates()
```

### Step 2: Deploy the CODE (not the config)
```bash
git add deployable_strategies/bear_trap/runner.py
git commit -m "fix: Remove non-existent method calls from bear_trap runner"
git push origin deployment/aws-paper-trading-setup
```

### Step 3: CI/CD automatically deploys to EC2
- GitHub Actions workflow triggers
- Pulls latest code to EC2
- Restarts services
- Fixed code now running

---

## Verification Commands

```bash
# Check what files are in each directory locally:
ls -R deployed/bear_trap
ls -R deployable_strategies/bear_trap

# Check what's on EC2:
aws ssm start-session --target i-0cd785630b55dd9a2
cd /home/ssm-user/magellan
ls -lh deployed/bear_trap/
ls -lh deployable_strategies/bear_trap/
```

---

## Conclusion

**NO**, `/deployed/` and `/deployable_strategies/` are **NOT** the same code.

- `/deployed/` = Configuration only (no Python code)
- `/deployable_strategies/` = Actual strategy code (has the bug)

**The fix must be applied to `/deployable_strategies/bear_trap/runner.py`**
