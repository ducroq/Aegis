# Backtesting Results

Track backtest performance metrics over time to validate methodology and tune thresholds.

## Current Status

**Status:** 🔴 Not Yet Run
**Last Updated:** 2025-01-08
**Data Range:** N/A (awaiting implementation)

---

## Backtest Methodology

### Test Period
- **Target:** 2000-01-01 to 2024-12-31 (24 years)
- **Rationale:** Captures 4 major market crashes and multiple bull/bear cycles

### Market Events to Test Against

| Event | Peak Date | Trough Date | Drawdown | Recovery Time |
|-------|-----------|-------------|----------|---------------|
| Tech Bubble | 2000-03-24 | 2002-10-09 | -49% | 7 years |
| Financial Crisis | 2007-10-09 | 2009-03-09 | -57% | 5.5 years |
| COVID Crash | 2020-02-19 | 2020-03-23 | -34% | 5 months |
| 2022 Bear Market | 2022-01-03 | 2022-10-12 | -25% | 1 year |

### Success Criteria

**Primary Goals:**
- Catch ≥3/4 major crashes (>20% drawdown)
- Lead time: 30-90 days average before peak
- False positive rate: <30% (≤7 false alarms over 24 years)
- Alert frequency: 2-5 per year average

**Metrics Tracked:**
- **True Positive (TP):** Alert → Drawdown >20% within 6 months
- **False Positive (FP):** Alert → No drawdown >20% within 6 months
- **False Negative (FN):** Drawdown >20% → No alert in prior 6 months
- **Lead Time:** Days between alert and market peak
- **Precision:** TP / (TP + FP)
- **Recall:** TP / (TP + FN)
- **F1 Score:** 2 × (Precision × Recall) / (Precision + Recall)

---

## Baseline Results (Awaiting Implementation)

### Overall Performance

```
Total Alerts: N/A
True Positives: N/A
False Positives: N/A
False Negatives: N/A

Precision: N/A
Recall: N/A
F1 Score: N/A
```

### Per-Event Performance

**2000 Tech Bubble**
- Alert Date: N/A
- Market Peak: 2000-03-24
- Lead Time: N/A days
- Max Risk Score: N/A
- Triggered By: N/A

**2007-2009 Financial Crisis**
- Alert Date: N/A
- Market Peak: 2007-10-09
- Lead Time: N/A days
- Max Risk Score: N/A
- Triggered By: N/A

**2020 COVID Crash**
- Alert Date: N/A
- Market Peak: 2020-02-19
- Lead Time: N/A days
- Max Risk Score: N/A
- Triggered By: N/A

**2022 Bear Market**
- Alert Date: N/A
- Market Peak: 2022-01-03
- Lead Time: N/A days
- Max Risk Score: N/A
- Triggered By: N/A

### False Positives Analysis

*(To be populated after backtest)*

---

## Threshold Tuning Experiments

### Experiment 1: Yellow Threshold Sensitivity

**Hypothesis:** Current YELLOW threshold (6.5) may be too sensitive or conservative

| Yellow Threshold | Red Threshold | Total Alerts | TP | FP | FN | F1 Score |
|------------------|---------------|--------------|----|----|----|----|
| 6.0 | 8.0 | N/A | N/A | N/A | N/A | N/A |
| 6.5 | 8.0 | N/A | N/A | N/A | N/A | N/A |
| 7.0 | 8.0 | N/A | N/A | N/A | N/A | N/A |
| 7.5 | 8.5 | N/A | N/A | N/A | N/A | N/A |

**Recommendation:** *(Awaiting results)*

### Experiment 2: Dimension Weight Sensitivity

**Hypothesis:** Test if alternative weightings improve performance

| Recession | Credit | Valuation | Liquidity | Positioning | F1 Score | Notes |
|-----------|--------|-----------|-----------|-------------|----------|-------|
| 30% | 25% | 20% | 15% | 10% | N/A | Baseline (current) |
| 35% | 25% | 15% | 15% | 10% | N/A | Higher recession weight |
| 25% | 30% | 20% | 15% | 10% | N/A | Higher credit weight |
| 25% | 25% | 25% | 15% | 10% | N/A | Higher valuation weight |
| 20% | 20% | 20% | 20% | 20% | N/A | Equal weights |

**Recommendation:** *(Awaiting results)*

### Experiment 3: Velocity vs Level Mix

**Hypothesis:** Test if different velocity/level ratios for credit improve accuracy

| Velocity Weight | Level Weight | F1 Score | Lead Time (avg) | Notes |
|-----------------|--------------|----------|-----------------|-------|
| 70% | 30% | N/A | N/A days | Baseline (current) |
| 50% | 50% | N/A | N/A days | Equal mix |
| 80% | 20% | N/A | N/A days | Higher velocity |
| 60% | 40% | N/A | N/A days | Moderate velocity |

**Recommendation:** *(Awaiting results)*

---

## Historical Risk Score Timeline

*(To be populated with backtest data)*

### Annual Risk Statistics

| Year | Avg Score | Max Score | Alerts | Market Return | Max Drawdown |
|------|-----------|-----------|--------|---------------|--------------|
| 2000 | N/A | N/A | N/A | -9.1% | -49% |
| 2001 | N/A | N/A | N/A | -11.9% | -29% |
| 2002 | N/A | N/A | N/A | -22.1% | -33% |
| 2003 | N/A | N/A | N/A | +28.7% | -6% |
| ... | ... | ... | ... | ... | ... |

### Dimension Breakdown During Major Events

**2008 Financial Crisis (Peak: Oct 2007)**

| Date | Overall | Recession | Credit | Valuation | Liquidity | Positioning |
|------|---------|-----------|--------|-----------|-----------|-------------|
| 2007-01 | N/A | N/A | N/A | N/A | N/A | N/A |
| 2007-04 | N/A | N/A | N/A | N/A | N/A | N/A |
| 2007-07 | N/A | N/A | N/A | N/A | N/A | N/A |
| 2007-10 | N/A | N/A | N/A | N/A | N/A | N/A |

---

## Indicator Contribution Analysis

### Most Predictive Indicators

*(Ranked by contribution to successful alerts)*

| Rank | Indicator | Dimension | Lead Time | Contribution |
|------|-----------|-----------|-----------|--------------|
| 1 | N/A | N/A | N/A days | N/A |
| 2 | N/A | N/A | N/A days | N/A |
| 3 | N/A | N/A | N/A days | N/A |
| 4 | N/A | N/A | N/A days | N/A |
| 5 | N/A | N/A | N/A days | N/A |

### Least Predictive Indicators

*(Candidates for removal)*

| Rank | Indicator | Dimension | False Signals | Notes |
|------|-----------|-----------|---------------|-------|
| 1 | N/A | N/A | N/A | N/A |
| 2 | N/A | N/A | N/A | N/A |

---

## Lessons Learned

### What Worked Well

*(To be populated after backtest)*

1. TBD
2. TBD
3. TBD

### What Didn't Work

*(To be populated after backtest)*

1. TBD
2. TBD
3. TBD

### Methodology Changes Made

*(Track all changes to scoring methodology over time)*

| Date | Change | Rationale | Impact on F1 | ADR Link |
|------|--------|-----------|--------------|----------|
| 2025-01-08 | Added Positioning dimension (10% weight) | Capture sentiment extremes | N/A (baseline) | [ADR](decisions/2025-01-08-positioning-dimension.md) |
| 2025-01-08 | Velocity-first approach (70/30 for credit) | Earlier turning point detection | N/A (baseline) | [ADR](decisions/2025-01-08-velocity-indicators.md) |

---

## Forward Testing

### Real-Time Performance Tracking

**Start Date:** TBD (when system goes live)
**Current Date:** N/A
**Days Tracked:** N/A

| Date | Risk Score | Tier | Alert Sent | S&P 500 | Notes |
|------|-----------|------|------------|---------|-------|
| TBD | N/A | N/A | No | N/A | Awaiting deployment |

### Alerts Issued

*(Track all real-time alerts for future validation)*

| Alert # | Date | Score | Tier | Reason | Outcome (6mo) | Validated? |
|---------|------|-------|------|--------|---------------|------------|
| TBD | N/A | N/A | N/A | N/A | Pending | Pending |

---

## Next Steps

**Before First Backtest:**
1. ✅ Complete all configuration files
2. ✅ Implement data fetchers (FRED, Yahoo Finance)
3. ✅ Implement all 5 risk scorers
4. ✅ Implement aggregator
5. ✅ Write `scripts/backtest.py`

**After First Backtest:**
1. Populate this document with results
2. Identify threshold adjustments needed
3. Test alternative weight combinations
4. Validate indicator selections
5. Create ADRs for any methodology changes

**Ongoing (Post-Deployment):**
1. Update forward testing section weekly
2. Validate alerts after 6-month waiting period
3. Re-run backtest quarterly with updated data
4. Adjust methodology based on real-world performance

---

## References

- `scripts/backtest.py` - Backtesting script
- `docs/decisions/` - Architecture Decision Records
- `docs/METHODOLOGY_EVOLUTION.md` - Timeline of changes
- `config/indicators.yaml` - Current indicator configuration

---

**Template Version:** 1.0
**Last Updated:** 2025-01-08
**Next Review:** After first backtest completion
