# Open Questions

## Critical (Blocking Progress)

None currently - core implementation is complete and all tests passing.

## Important (Affects Design)

### Backtesting & Validation

- [ ] **What backtest metrics should we use to validate the system?**
  - We need to define success: Lead time? False positive rate? Coverage of major drawdowns?
  - Should prioritize catching crashes vs minimizing false alarms?

- [ ] **Should we backtest with "as reported" or "revised" data?**
  - GDP and other indicators get revised. Using revised data = look-ahead bias.
  - FRED has real-time datasets for some series. Should we use those for accuracy?

- [ ] **What historical period should we validate against?**
  - 2000-2024 gives us 4 major events (tech bubble, GFC, COVID, 2022 bear)
  - Should we go further back (1990s) or would that overfit to different regime?

### Alert Thresholds

- [ ] **Should alert thresholds be dynamic or static?**
  - Current: Fixed thresholds (YELLOW≥6.5, RED≥8.0)
  - Alternative: Percentile-based (top 20% of historical distribution)
  - Trade-off: Static is simpler but may need re-calibration over time

- [ ] **How should we handle "alert fatigue" if risk stays elevated for months?**
  - Send repeat alerts? Weekly updates? Only on significant changes?
  - Need to balance staying informed vs inbox overload

### Indicator Selection

- [ ] **Should we include more timely indicators even if history is shorter?**
  - Example: High-frequency financial stress indexes
  - Trade-off: Better real-time signal vs less historical validation

- [ ] **How should we weight conflicting signals?**
  - What if recession risk is high but credit spreads are normal?
  - Current approach: Weighted average. Is this optimal?

## Nice to Know (Can Work Around)

### Data Quality

- [ ] **What's the typical lag for key FRED indicators?**
  - Most are updated with 1-2 day lag, some monthly with 2-week lag
  - Should document expected freshness for each indicator

- [ ] **How should we handle FRED API rate limits?**
  - Currently: Aggressive caching (24h TTL)
  - Is this sufficient for daily updates?

### User Experience

- [ ] **Should email alerts include charts/visualizations?**
  - Plain text vs HTML with embedded images
  - Trade-off: Richer content vs complexity and deliverability

- [ ] **What format should weekly non-alert status updates be?**
  - Brief email? Dashboard link? No updates unless alert?

### Performance

- [ ] **Is daily update latency acceptable?**
  - Currently: 30-60 seconds with caching, 2-3 minutes cold start
  - Could optimize if needed, but probably fine for daily batch

## Resolved

- [x] **Should we use velocity or levels for indicators?** - *2025-01-08*
  - **Decision:** Velocity (rate of change) is more predictive for leading indicators
  - **Rationale:** Unemployment rising from 3.5% to 4% is more significant than level at 4%
  - See: [decisions/2025-01-08-velocity-indicators.md](decisions/2025-01-08-velocity-indicators.md)

- [x] **What weight should each risk dimension have?** - *2025-01-08*
  - **Decision:** Recession 30%, Credit 25%, Valuation 20%, Liquidity 15%, Positioning 10%
  - **Rationale:** Recession and credit are most predictive of large drawdowns
  - See: [decisions/2025-01-08-dimension-weights.md](decisions/2025-01-08-dimension-weights.md)

- [x] **Should we add positioning/sentiment as a dimension?** - *2025-01-08*
  - **Decision:** Yes, added CFTC positioning as 5th dimension (10% weight)
  - **Rationale:** Extreme positioning can signal crowded trades and reversal risk
  - See: [decisions/2025-01-08-positioning-dimension.md](decisions/2025-01-08-positioning-dimension.md)

- [x] **What alert threshold levels should we use?** - *2025-01-08*
  - **Decision:** RED ≥8.0, YELLOW ≥6.5, or risk rising >1.0 in 4 weeks
  - **Rationale:** Targets 2-5 alerts per year, bias toward specificity over sensitivity
  - See: [decisions/2025-01-08-alert-thresholds.md](decisions/2025-01-08-alert-thresholds.md)

- [x] **Should we support multiple Python versions?** - *2025-01-08*
  - **Decision:** Yes, test on Python 3.9-3.12 across Ubuntu/Windows/macOS
  - **Rationale:** Broad compatibility, GitHub Actions matrix makes this easy
  - See: CI/CD configuration in `.github/workflows/ci.yml`

---

## Question Tracking Guidelines

**When to add questions:**
- Encountering uncertainty during development
- Making a trade-off that could be decided differently
- Before implementing a feature that has multiple approaches
- When backtest results are ambiguous

**When to move to Resolved:**
- Clear decision made
- ADR (Architecture Decision Record) created
- Implementation merged

**When to archive:**
- Question becomes irrelevant due to other changes
- Move to "Nice to Know" if no longer blocking
