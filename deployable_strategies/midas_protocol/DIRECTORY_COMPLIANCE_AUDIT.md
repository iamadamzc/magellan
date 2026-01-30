# Directory Structure Compliance Audit & Cleanup Plan

**Date**: January 30, 2026  
**Status**: VIOLATIONS FOUND - Action Required

---

## 🔍 **Audit Findings**

### **CRITICAL ISSUE #1: MIDAS Protocol in Wrong Directory**

**Current Location**: `/prod/midas_protocol/`  
**Expected Location (per DIRECTORY_STRUCTURE_RULES.md)**: `/deployable_strategies/midas_protocol/`

**Impact**:
- ❌ Violates directory structure standards
- ❌ Inconsistent with other strategies (bear_trap, daily_trend, hourly_swing)
- ⚠️ CI/CD workflow is currently configured for `/prod/` but should use `/deployable_strategies/`

---

### **CRITICAL ISSUE #2: Root Directory Pollution**

**Allowed files in root** (per DIRECTORY_STRUCTURE_RULES.md): **10 files only**
- .env, .env.template, .gitignore
- README.md, ARCHIVE_INDEX.md, DIRECTORY_STRUCTURE_RULES.md
- main.py, requirements.txt
- simulate_all_strategies_december.py
- Runtime logs: debug_vault.log, livetradelog.txt

**ACTUAL files in root**: **50+ markdown files** (MAJOR VIOLATION)

**Files that should be moved**:
```
Root → system_docs/operations/ or system_docs/session_logs/:
- AFTER_HOURS_MAINTENANCE.md
- AWS_DEPLOYMENT_OPERATIONS_GUIDE.md
- AWS_DEPLOYMENT_STRATEGY.md
- AWS_DEPLOYMENT_VERIFICATION.md
- CI_CD_GUIDE.md
- DEPLOYMENT_CHECKLIST.md
- MONITORING_GUIDE.md
- And 40+ more...
```

---

### **ISSUE #3: CI/CD Workflow Mismatch**

**Current CI/CD Workflow** (.github/workflows/deploy-strategies.yml):
- Expects strategies in: `/prod/{strategy}/`
- Systemd services named: `magellan-{strategy}.service`

**Directory Structure Rules** specify:
- Strategies should be in: `/deployable_strategies/{strategy}/`

**Status**: ⚠️ **CONFLICTING STANDARDS**

---

## 📋 **Recommended Actions**

### **Option A: Update Directory Structure (Align with Rules)**

Move MIDAS Protocol to comply with DIRECTORY_STRUCTURE_RULES.md:

```bash
# 1. Move MIDAS Protocol
git mv prod/midas_protocol deployable_strategies/midas_protocol

# 2. Update CI/CD workflow
# Change all references from prod/ to deployable_strategies/

# 3. Update systemd service paths on EC2

# 4. Clean up root directory
# Move all .md files to system_docs/
```

**Pros**:
- ✅ Complies with documented standards
- ✅ Consistent with stated rules
- ✅ Future-proof

**Cons**:
- ❌ Requires CI/CD workflow changes
- ❌ Requires EC2 service file updates
- ❌ Requires re-deployment

---

### **Option B: Update Rules (Align with Current Practice)**

Update DIRECTORY_STRUCTURE_RULES.md to match `/prod/` convention:

```markdown
# Change from:
/deployable_strategies/ - Production-Ready Strategy Code

# To:
/prod/ - Production-Ready Strategy Code
```

**Pros**:
- ✅ Minimal code changes
- ✅ Aligns with current deployment
- ✅ MIDAS already deployed successfully

**Cons**:
- ❌ Requires documentation updates
- ❌ Inconsistent naming (other strategies in deployable_strategies/)

---

### **Option C: Hybrid Approach (Recommended)**

**Keep `/prod/` as the production directory**, but:

1. **Update DIRECTORY_STRUCTURE_RULES.md** to reflect `/prod/` as standard
2. **Move other strategies** from `/deployable_strategies/` to `/prod/` for consistency
3. **Clean up root directory** (move all session docs to system_docs/)
4. **Update CI/CD guide** to reference `/prod/` consistently

**Pros**:
- ✅ Reflects actual practice
- ✅ Consistent deployment model
- ✅ MIDAS stays where deployed
- ✅ Clear separation: /prod/ = production, /deployable_strategies/ = staging

**Cons**:
- ⚠️ Requires documentation updates
- ⚠️ Need to decide fate of /deployable_strategies/

---

## 🎯 **Immediate Action Plan (Hybrid Approach)**

### Phase 1: Clarify Directory Standards ✅

**Decision**: Use `/prod/` as the production-ready directory.

**Rationale**:
- MIDAS Protocol successfully deployed from `/prod/`
- CI/CD workflow configured for `/prod/`
- Clearer naming than "deployable_strategies"
- Logical: `/prod/` = production, `/deployable_strategies/` = pre-production staging

### Phase 2: Update Documentation

1. **Update DIRECTORY_STRUCTURE_RULES.md**:
   - Change `/deployable_strategies/` section to `/prod/`
   - Add `/deployable_strategies/` as optional staging area

2. **Update CI_CD_GUIDE.md**:
   - Ensure all references use `/prod/`
   - Document staging vs production workflow

3. **Update AWS_DEPLOYMENT_OPERATIONS_GUIDE.md**:
   - Reflect `/prod/` standard

### Phase 3: Clean Up Root Directory 🚨 URGENT

Move all markdown files to appropriate locations:

```bash
# Session logs and summaries
mv *SESSION*.md system_docs/session_logs/
mv *DEPLOYMENT*.md system_docs/operations/
mv *HANDOFF*.md system_docs/session_logs/

# Operational guides
mv AWS_DEPLOYMENT_*.md system_docs/operations/
mv CI_CD_GUIDE.md system_docs/operations/
mv MONITORING_GUIDE.md system_docs/operations/

# Analysis documents
mv *ANALYSIS*.md system_docs/session_logs/

# Strategy-specific docs
mv BEAR_TRAP_*.md system_docs/session_logs/

# Move remaining to appropriate locations
```

### Phase 4: Verify MIDAS Protocol Structure

Ensure `/prod/midas_protocol/` follows standards:

```
/prod/midas_protocol/
├── strategy.py                  ✅ Main implementation
├── runner.py                    ✅ Production runner
├── config.json                  ✅ Configuration
├── README.md                    ✅ Strategy overview
├── tests/
│   └── test_strategy.py         ✅ Unit tests
├── deployment/
│   └── systemd/
│       └── magellan-midas-protocol.service  ✅ Service file
└── docs/
    ├── DEPLOYMENT_CHECKLIST.md  ✅ Deployment guide
    └── STRATEGY_SPECIFICATION.md ✅ Complete spec
```

**Status**: ✅ **COMPLIANT** (once we update rules to use /prod/)

---

## 📊 **Compliance Summary**

| Item | Current State | Compliant? | Action Needed |
|------|--------------|------------|---------------|
| MIDAS Protocol location | `/prod/` | ⚠️ | Update rules to specify `/prod/` |
| Root directory | 50+ files | ❌ | Move to system_docs/ |
| CI/CD workflow | Uses `/prod/` | ✅ | No change needed |
| Strategy structure | Complete | ✅ | No change needed |
| Systemd service | Deployed | ✅ | No change needed |
| Documentation | In strategy | ✅ | No change needed |

---

## ⚡ **Next Steps**

### Immediate (Today):
1. ✅ Audit complete (this document)
2. ⏳ Get user approval on Option C (Hybrid Approach)
3. ⏳ Clean up root directory

### Soon (This Week):
4. ⏳ Update DIRECTORY_STRUCTURE_RULES.md
5. ⏳ Update CI_CD_GUIDE.md
6. ⏳ Move existing deployable_strategies to /prod/

### Later (As Needed):
7. ⏳ Establish /deployable_strategies/ as staging area
8. ⏳ Create promotion workflow from staging → prod

---

## 📝 **Recommendation**

**I recommend Option C (Hybrid Approach)**:

1. **Accept `/prod/` as the standard** for production strategies
2. **Update documentation** to reflect this decision
3. **Clean up root directory** immediately (critical)
4. **Use `/deployable_strategies/` as staging** for pre-production testing

This approach:
- ✅ Reflects actual practice
- ✅ Minimal disruption to deployed MIDAS Protocol
- ✅ Provides clear staging → production pathway
- ✅ Maintains deployment consistency

---

**Ready to proceed with cleanup?**
