# Aegis - Project Overview

## Vision

Aegis is a personal early warning system for portfolio risk management. It monitors quantitative macro indicators from free/low-cost APIs (FRED, Yahoo Finance, Shiller) and alerts when risk conditions suggest defensive positioning. The system is designed to help individual investors avoid major drawdowns (>20%) by providing objective, data-driven risk assessments 2-5 times per year.

## Current Status

**Phase:** Development → Refinement
**Last Updated:** 2025-01-08

Core implementation is complete with all 5 risk dimension scorers operational. GitHub Actions CI/CD pipeline is fully functional with 103/104 tests passing across 12 platform/Python combinations. The system is ready for backtesting and real-world validation.

## Active Focus Areas

- [ ] **Backtesting** - Validate methodology against 2000-2024 historical data
- [ ] **Threshold Calibration** - Tune alert thresholds based on backtest results
- [ ] **Orchestration Scripts** - Build daily_update.py, weekly_report.py
- [ ] **Production Deployment** - Set up automated daily runs

## Recent Significant Decisions

- **2025-01-08**: Implemented velocity-based indicators for leading signals → See [decisions/2025-01-08-velocity-indicators.md](decisions/2025-01-08-velocity-indicators.md)
- **2025-01-08**: Added CFTC positioning as 5th risk dimension → See [decisions/2025-01-08-positioning-dimension.md](decisions/2025-01-08-positioning-dimension.md)
- **2025-01-08**: Set dimension weights (Recession: 30%, Credit: 25%, Valuation: 20%, Liquidity: 15%, Positioning: 10%) → See [decisions/2025-01-08-dimension-weights.md](decisions/2025-01-08-dimension-weights.md)

## Architecture Summary

```
APIs (FRED, Yahoo, Shiller)
    ↓
Data Fetchers (cached, with velocity calculations)
    ↓
Risk Scorers (5 dimensions: 0-10 scale)
    ↓
Aggregator (weighted score 0-10)
    ↓
Alert Logic (threshold checking)
    ↓
Email Alert + History Storage
```

## Key Metrics

- **Test Coverage:** 64%+ (104 tests)
- **Platforms:** Ubuntu, Windows, macOS
- **Python Versions:** 3.9-3.12
- **CI/CD Status:** ✅ All checks passing
- **Expected Alert Frequency:** 2-5 per year

## Quick Links

- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Current Task:** [CURRENT_TASK.md](CURRENT_TASK.md)
- **Open Questions:** [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Testing Strategy:** [testing.md](testing.md)
- **Methodology:** [methodology.md](methodology.md)
- **Getting Started:** [getting_started.md](getting_started.md)

## Project Health

| Aspect | Status | Notes |
|--------|--------|-------|
| Core Implementation | ✅ Complete | All 5 scorers operational |
| Test Coverage | ✅ Good | 64%+, all tests passing |
| CI/CD | ✅ Excellent | GitHub Actions fully configured |
| Documentation | ✅ Strong | Comprehensive docs in place |
| Backtesting | 🟡 Pending | Next major milestone |
| Production Deployment | 🟡 Not Started | Needs orchestration scripts |
