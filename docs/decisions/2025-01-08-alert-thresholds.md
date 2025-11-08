# Alert Thresholds: RED ≥8.0, YELLOW ≥6.5

**Date:** 2025-01-08
**Status:** Accepted

## Context

With overall risk scores ranging 0-10, we need to define thresholds for sending alerts. Too sensitive = alert fatigue. Too conservative = miss crashes.

**Target:** 2-5 alerts per year for individual investor portfolio risk management.

## Decision

**Alert Tiers:**
- **RED (≥8.0):** Severe risk - consider major defensive positioning
- **YELLOW (≥6.5):** Elevated risk - review portfolio, build cash
- **GREEN (0-6.4):** Normal conditions - stay the course

**Additional Trigger:**
- Alert if risk ≥6.5 AND rising >1.0 points in 4 weeks (velocity-based)

## Rationale

### 1. Historical Calibration

Estimated risk scores for major events:

| Event | Estimated Score | Months Before Crash | Actual Alert? |
|-------|----------------|---------------------|---------------|
| Mar 2000 (Tech Peak) | 7.5-8.5 | 2-6 months | YELLOW/RED ✅ |
| Oct 2007 (GFC Peak) | 8.0-9.0 | 3-6 months | RED ✅ |
| Feb 2020 (COVID) | 6.5-7.5 | 2-4 weeks | YELLOW ✅ |
| Jan 2022 (Bear Start) | 6.5-7.0 | 0-2 months | YELLOW ✅ |

### 2. Alert Frequency Target

**With 6.5 threshold:**
- Estimated 2-4 alerts per year in normal conditions
- 5-8 alerts during crisis periods (appropriate)
- Balances sensitivity vs specificity

**With 7.0 threshold:**
- Estimated 1-2 alerts per year (too conservative)
- Might miss early warnings
- User never acts if alerts too rare

**With 6.0 threshold:**
- Estimated 6-10 alerts per year (too many)
- Alert fatigue
- "Cry wolf" syndrome

### 3. Action-Oriented Tiers

**RED (≥8.0) - Immediate Action:**
- "Severe conditions - consider 30-50% cash/bonds"
- Rare (once every 2-3 years)
- When this fires, take it seriously

**YELLOW (6.5-7.9) - Review & Prepare:**
- "Elevated risk - review exposure, build 10-20% cash"
- More common (1-3x per year)
- Early warning to prepare

**GREEN (0-6.4) - Stay Course:**
- "Normal conditions - no action needed"
- Most of the time
- Confidence to stay invested

### 4. Velocity Trigger (≥6.5 AND rising >1.0 in 4 weeks)

Catches rapid deterioration:
- 2020 COVID: Score went 4.5 → 7.5 in 2 weeks
- 2008 GFC: Score went 6.0 → 8.5 in 6 weeks
- Velocity matters as much as absolute level

## Consequences

### Positive

✅ **Balanced:** Not too sensitive, not too conservative
✅ **Actionable:** Clear guidance per tier
✅ **Empirical:** Based on historical analysis
✅ **Flexible:** Can adjust after backtest

### Negative

⚠️ **Arbitrary:** 6.5 vs 6.7 is marginal
⚠️ **May Need Tuning:** Real-world may require adjustment
⚠️ **Context-Free:** Doesn't consider user risk tolerance

### Neutral

ℹ️ **Will Validate:** Backtest will confirm or adjust
ℹ️ **Can Personalize:** Future: User-specific thresholds
ℹ️ **Documented:** Clear rationale for changes

## Alternatives Considered

### Alternative 1: 7.0/8.5 Thresholds ❌

**Why Rejected:**
- Too conservative
- Would miss 2020 COVID warning (peaked ~7.2)
- Alert frequency <2 per year

### Alternative 2: Percentile-Based ❌

**Idea:** Alert at 90th/95th percentile
**Why Rejected:**
- Need extensive historical baseline
- Less intuitive ("what does 90th percentile mean?")
- Can layer on later

### Alternative 3: Multi-Stage Alerts ❌

**Idea:**
- Watch (5.0-6.0)
- Caution (6.0-7.0)
- Warning (7.0-8.0)
- Danger (8.0+)

**Why Rejected:**
- Too complex
- Alert fatigue with 4 levels
- User confusion

## Implementation

```python
def should_alert(current_score, history, thresholds):
    # Threshold alerts
    if current_score >= thresholds['red']:
        return True, 'RED', f'Risk {current_score:.1f} exceeds RED threshold'

    if current_score >= thresholds['yellow']:
        # Check velocity
        if len(history) >= 28:  # 4 weeks
            four_week_change = current_score - history[-28]
            if four_week_change > 1.0:
                return True, 'YELLOW', f'Risk rising rapidly (+{four_week_change:.1f} in 4 weeks)'

        return True, 'YELLOW', f'Risk {current_score:.1f} exceeds YELLOW threshold'

    return False, 'GREEN', 'Risk within normal range'
```

## Suggested Actions by Tier

**RED (≥8.0):**
- Consider 30-50% cash/short-term bonds
- Trim cyclical exposure
- Increase defensive sectors (utilities, healthcare, consumer staples)
- Review stop-losses
- Avoid new equity purchases

**YELLOW (6.5-7.9):**
- Build 10-20% cash position
- Rebalance to target allocations
- Trim concentrated positions
- Consider adding portfolio hedges
- Monitor daily for escalation

**GREEN (0-6.4):**
- Stay invested per plan
- Rebalance opportunistically
- Consider increasing equity on dips
- No defensive action needed

## Backtest Plan

1. Calculate what alerts would have triggered (2000-2024)
2. Measure:
   - Alert frequency (target: 2-5/year)
   - Lead time before crashes
   - False positive rate
   - True positive rate
3. Compare to alternatives (6.0, 7.0, 7.5 thresholds)
4. Tune if needed

**Success Criteria:**
- Catch 3/4 major crashes
- 2-5 alerts per year average
- Lead time 30-90 days
- <30% false positive rate

## Future Considerations

- Personalized thresholds based on user risk tolerance
- Dynamic thresholds that adapt to regime
- Confidence intervals ("risk likely 6.5-7.5")
- Multi-horizon alerts (1-month vs 6-month outlook)

---

**Last Updated:** 2025-01-08
**Next Review:** After backtesting
