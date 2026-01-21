# 🧪 TEST - Validation & Staging

This folder contains strategies undergoing final validation before production deployment.

## Purpose

- Final validation testing
- Walk-forward analysis
- Perturbation testing
- Production code structure
- Pre-deployment staging

## Rules

- ✅ Production-ready code structure
- ✅ Comprehensive tests required
- ✅ Uses cached data for testing
- ✅ Full documentation required

## Promotion Criteria

To move from `test/` to `prod/`:

- ✅ All validation tests pass
- ✅ Walk-forward analysis complete
- ✅ Perturbation tests pass
- ✅ Code meets production standards
- ✅ Documentation complete
- ✅ Approved for deployment

## Structure

```
test/
├── strategy_name/
│   ├── strategy.py          # Core logic
│   ├── runner.py            # Universal runner
│   ├── config.json          # Configuration
│   ├── tests/               # Unit tests
│   │   ├── test_strategy.py
│   │   └── test_integration.py
│   ├── validation_report.md # Validation results
│   └── docs/                # Documentation
│       ├── README.md
│       └── parameters.md
```

## Current Strategies

(None - all validated strategies have been promoted to prod/)
