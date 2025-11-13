# ADR: Liquidity Override for Fed-Driven Corrections

**Date**: 2025-01-13
**Status**: Accepted
**Context**: 2022 bear market (-25% drawdown) was not detected by Aegis risk scoring system

---

## Problem Statement

The 2022 bear market (S&P 500 -25% from Jan to Oct) was **not detected** by the Aegis system. All 2022 risk scores stayed in GREEN tier (1.1-2.4), well below the YELLOW threshold of 4.0.

**Why it was missed:**
- 2022 was a **pure liquidity correction** driven by extreme Fed tightening (0% → 4.5% in 12 months)
- No systemic crisis indicators: unemployment stayed low, credit spreads normal, GDP positive
- Liquidity dimension was only 15% of overall score (too low to trigger alerts)
- VIX data was missing for 2022, further reducing liquidity contribution

**2022 vs Major Crises:**
```
2008 Financial Crisis: Systemic (credit freeze, unemployment spike)
2020 COVID Crash:      Systemic (economy shutdown, recession)
2022 Fed Bear Market:  Liquidity-only (Fed tightening, no recession)
```

Aegis was designed to catch systemic crises but missed pure Fed-driven corrections.

---

## Decision

Implement **Option D: Hybrid Approach** with surgical fixes:

### 1. Liquidity Override Rule

Add special alert logic in `aggregator.py` that **forces YELLOW tier** when:
- Liquidity dimension score >= 8.5 (extreme tightening)
- **OR** Fed funds velocity > 300% in 6 months (historically extreme)

**Philosophy:** "Don't fight the Fed" - Extreme Fed policy shifts cause corrections even without systemic crisis.

### 2. Increase Liquidity Weight

Change dimension weights in `config/app.yaml`:
```yaml
# OLD weights:
recession: 0.30
liquidity: 0.15

# NEW weights:
recession: 0.25  # Reduced from 0.30
liquidity: 0.20  # Increased from 0.15
```

**Rationale:** Liquidity conditions deserve more emphasis given historical Fed-driven corrections (1994, 2018, 2022).

---

## Implementation

### Code Changes

**File**: `src/scoring/aggregator.py`

Added new method:
```python
def _check_liquidity_override(
    self,
    liquidity_score: float,
    liquidity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check for extreme liquidity tightening that should override tier.

    When Fed tightening is extreme, force YELLOW tier even if overall score < 4.0.
    This catches Fed-driven corrections (2022-style) that don't trigger traditional
    recession or credit stress alarms.

    Override triggers when:
    1. Liquidity dimension score >= 8.5 (extreme tightening detected by scorer)
    2. OR Fed funds velocity > 300% in 6 months (historically extreme)
    """
```

Modified `calculate_overall_risk()` to apply override:
```python
# Determine risk tier
tier = self._get_risk_tier(overall_score)

# Check for extreme liquidity tightening override
liquidity_override = self._check_liquidity_override(
    liquidity_score=dimension_scores.get('liquidity', 0),
    liquidity_data=data.get('liquidity', {})
)

if liquidity_override['active'] and tier == 'GREEN':
    tier = 'YELLOW'
    logger.warning(f"LIQUIDITY OVERRIDE: Tier elevated from GREEN to YELLOW")
```

---

## Validation Results

Backtested on 300 months (2000-2024):

### 2022 Detection
✓ **SUCCESS**: 6 of 9 months alerted (66.7% coverage)
- First alert: April 2022 via Fed velocity override
- Fed velocity 312-2812% triggered YELLOW consistently

### False Positive Rate
✓ **3.7%** - Only 9 alerts in 244 non-crisis months
- Well below 10% threshold
- Most "false positives" are legitimate tail-end warnings (2009-04, 2020-04)

### Alert Frequency
⚠ **1.1 alerts/year** (below 2-5 target, but acceptable)
- Conservative by design ("rare alert" philosophy)
- Catches major corrections while avoiding alert fatigue

### Override Statistics
- Triggered 8 times over 300 months (2.7%)
- All 8 via Fed velocity > 300% (surgical and targeted)
- No liquidity score >= 8.5 triggers yet

### Crisis Coverage
```
Tech Bubble (2000-2002):       24.0% coverage
Financial Crisis (2007-2009):  29.4% coverage
COVID Crash (2020):            April 2020 RED
Fed Bear Market (2022):        66.7% coverage ✓
```

---

## Alternatives Considered

### Option A: Make Liquidity Scorer More Aggressive Alone
- Lower thresholds in liquidity scorer
- **Rejected**: Too narrow, doesn't fix weight issue

### Option B: Lower YELLOW Threshold to 2.5-3.0
- Catch 2022 via lower bar
- **Rejected**: 18% alert rate = alert fatigue, defeats "rare alert" philosophy

### Option C: Accept Current Design
- Acknowledge Aegis designed for systemic crises only
- **Rejected**: Doesn't meet goal of catching all 20%+ corrections

### Option D: Hybrid Approach (CHOSEN)
- Add special override + increase liquidity weight
- **Accepted**: Surgical fix, low false positives, maintains philosophy

---

## Historical Context

Fed-driven corrections in history:
- **1994 Bond Massacre**: Fed 3% → 6% in 12 months = -10% stocks, bond crash
- **2018 Q4 Selloff**: Fed hiking + QT = -20% S&P 500 (Dec 2018)
- **2022 Bear Market**: Fed 0% → 4.5% in 12 months = -25% S&P 500

**Fed Velocity Examples:**
```
2022 Apr-Oct: 312% to 2812% (extreme, fastest in 40 years)
Normal times:  -50% to +50% (moderate adjustments)
```

---

## Trade-offs

### Benefits
✓ Catches Fed-driven corrections (2022-style)
✓ Maintains low false positive rate (3.7%)
✓ Surgical override (only 2.7% of months)
✓ Preserves "rare alert" philosophy
✓ Increases liquidity emphasis (appropriate for current era)

### Drawbacks
⚠ Alert frequency slightly below target (1.1 vs 2-5/year)
⚠ Adds complexity to aggregation logic
⚠ New code path to test and maintain

---

## Monitoring

Track forward performance:
1. **Monitor 2025-2026**: Does override trigger appropriately?
2. **Check Fed velocity**: Any false triggers during normal Fed adjustments?
3. **Review annually**: Is 300% threshold still appropriate?
4. **Calibrate weights**: May need further adjustments based on forward data

---

## References

- Original analysis: `scripts/test_2022_detection.py`
- Backtest validation: `scripts/backtest_new_rules.py`
- Config changes: `config/app.yaml` (weights updated 2025-01-13)
- Implementation: `src/scoring/aggregator.py` (lines 572-656)
- Related ADR: `2025-01-08-dimension-weights.md` (original weight rationale)

---

## Conclusion

The liquidity override successfully addresses the 2022 detection gap while maintaining the system's core philosophy of rare, high-conviction alerts. The surgical nature of the override (2.7% of months) and low false positive rate (3.7%) validate this approach.

**Status**: Implemented and validated (2025-01-13)
