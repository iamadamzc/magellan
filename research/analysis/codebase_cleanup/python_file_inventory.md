# Python File Inventory and Classification

**Date**: 2026-01-18  
**Total Python Files**: 326

---

## Executive Summary

**Test/Debug/Analysis Scripts**: 120 files (36.8%)  
**Core Source Code**: 21 files (6.4%)  
**Strategy Implementations**: 10 files (3.1%)  
**Other**: 175 files (53.7%)

---

## Detailed Breakdown by Category

| Category | Count | % of Total | Description |
|----------|-------|------------|-------------|
| **OTHER** | 171 | 52.5% | Scripts, utilities, main files, etc. |
| **TEST** | 78 | 23.9% | test_*.py files |
| **CORE_SRC** | 21 | 6.4% | Production infrastructure in src/ |
| **ANALYZE** | 12 | 3.7% | analyze_*.py files |
| **STRATEGY** | 10 | 3.1% | Strategy implementations |
| **BATCH** | 9 | 2.8% | batch_*.py files |
| **DEBUG** | 7 | 2.1% | debug_*.py files |
| **CHECK** | 6 | 1.8% | check_*.py files |
| **FETCH** | 4 | 1.2% | fetch_*.py data retrieval scripts |
| **VERIFY** | 3 | 0.9% | verify_*.py validation scripts |
| **DIAGNOSE** | 3 | 0.9% | diagnose_*.py diagnostic scripts |
| **INSPECT** | 2 | 0.6% | inspect_*.py inspection scripts |

---

## Analysis: Test & Development Scripts

**Total Development/Testing Scripts**: ~120 files (36.8%)

These are clearly temporary development artifacts:
- 78 `test_*.py` files
- 12 `analyze_*.py` files  
- 9 `batch_*.py` files
- 7 `debug_*.py` files
- 6 `check_*.py` files
- 3 `verify_*.py` files
- 3 `diagnose_*.py` files
- 2 `inspect_*.py` files

**Recommendation**: Archive all test/debug/analysis scripts except:
- Tests in `research/Perturbations/` (validated strategy tests)
- Core tests if they exist in a proper test framework

---

## Next Steps

1. **List all `test_*.py` files** by location
2. **Identify which tests are validated/deployment-related**
3. **Archive the rest** (likely 70+ test files)
4. **Do the same** for analyze/debug/check files
5. **Focus on the "OTHER" category** - what's in there?

---

**Ready to generate detailed file lists?**
