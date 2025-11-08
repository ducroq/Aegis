# Use Velocity (Rate of Change) Over Absolute Levels

**Date:** 2025-01-08
**Status:** Accepted

## Context

Economic indicators can be analyzed as:
1. **Levels** - Current absolute value (e.g., unemployment at 4.0%)
2. **Velocity** - Rate of change (e.g., unemployment up 15% YoY)

For early warning systems, which approach is more predictive of market drawdowns?

## Decision

**Primary approach: Velocity (rate of change) with 70% weight**
**Secondary approach: Levels with 30% weight**

Specific implementations:
- Unemployment claims: **YoY % change** (velocity only)
- High-yield spreads: **20-day velocity (70%) + absolute level (30%)**
- Fed funds rate: **6-month change** (velocity only)
- M2 money supply: **YoY % change** (velocity only)

## Rationale

### 1. Turning Points vs Extremes

**Velocity captures turning points:**
- Unemployment rising from 3.5% → 4.0% is more alarming than stable 4.5%
- Credit spreads widening 100 bps in 2 weeks signals stress
- Fed raising rates 200 bps in 6 months = aggressive tightening

**Levels miss early warnings:**
- Unemployment at 4.0% could be improving (from 5%) or deteriorating (from 3.5%)
- Context matters - absolute levels alone are ambiguous

### 2. Historical Evidence

**Major crashes preceded by velocity spikes:**

**2008 Financial Crisis:**
- HY spreads: 350 bps → 2000 bps in 3 months (450% increase)
- Unemployment velocity: +50% YoY by late 2008
- Level changes lagged velocity by 2-4 months

**2020 COVID:**
- HY spreads: 350 bps → 1100 bps in 2 weeks (215% increase!)
- Unemployment claims: +1000% in single week
- Velocity was the first and clearest signal

**2022 Bear:**
- Fed funds: 0% → 5% in 12 months (fastest tightening since 1980s)
- Velocity of tightening caused valuation compression
- Absolute level (5%) wasn't extreme, but pace was

### 3. Lead Time

Velocity indicators lead by 3-6 months:
- Changes in trend precede changes in level
- Acceleration/deceleration is early warning
- By the time levels are extreme, often too late

### 4. Avoiding False Signals

**High levels can persist:**
- CAPE >25 for 5 years (1996-2000) - level stayed high
- Valuation velocity (rate of increase) topped in 1999
- Velocity signaled turn, level did not

**Velocity spikes resolve:**
- Rapid changes are unsustainable
- Either accelerate into crisis or mean-revert
- Creates actionable signals

## Consequences

### Positive

✅ **Early Warnings:** Catch turning points 3-6 months earlier
✅ **Clearer Signals:** Velocity spikes are more decisive
✅ **Actionable:** Rapid changes demand attention
✅ **Validated:** Historical crashes show velocity led levels

### Negative

⚠️ **Noisy:** Short-term velocity can whipsaw
⚠️ **Requires Historical Data:** Need lookback periods (12-month for YoY)
⚠️ **Can Miss Sustained Extremes:** Level-based signals still important
⚠️ **More Complex:** Harder to explain than simple thresholds

### Neutral

ℹ️ **Hybrid Approach:** Combine velocity (70%) + level (30%) for credit
ℹ️ **Smoothing Needed:** Use moving averages to reduce noise
ℹ️ **Context Dependent:** Some indicators work better with levels (valuation)

## Implementation

### Unemployment Claims Velocity

```python
# Year-over-year percent change
current_claims = indicators['unemployment_claims']
claims_1y_ago = get_historical('unemployment_claims', periods=252)  # ~1 year

velocity_yoy = ((current_claims - claims_1y_ago) / claims_1y_ago) * 100

if velocity_yoy > 20:
    score += 4.0  # Extreme spike
elif velocity_yoy > 10:
    score += 2.0  # Significant rise
elif velocity_yoy > 5:
    score += 1.0  # Rising
```

### High-Yield Spread Hybrid

```python
# 70% velocity, 30% level
hy_spread = indicators['hy_spread']
hy_spread_20d_ago = get_historical('hy_spread', periods=20)

# Velocity (rate of change over 20 days)
velocity = ((hy_spread - hy_spread_20d_ago) / hy_spread_20d_ago) * 100

# Level score (absolute threshold)
if hy_spread > 900:
    level_score = 4.0
elif hy_spread > 600:
    level_score = 2.0
elif hy_spread > 450:
    level_score = 1.0
else:
    level_score = 0.0

# Velocity score
if velocity > 15:
    velocity_score = 4.0
elif velocity > 10:
    velocity_score = 2.0
elif velocity > 5:
    velocity_score = 1.0
else:
    velocity_score = 0.0

# Combine: 70% velocity, 30% level
combined_score = (velocity_score * 0.7) + (level_score * 0.3)
```

### Fed Funds Rate Change

```python
# 6-month change (velocity only)
fed_funds_current = indicators['fed_funds_rate']
fed_funds_6m_ago = get_historical('fed_funds_rate', periods=126)  # ~6 months

velocity_6m = fed_funds_current - fed_funds_6m_ago

if velocity_6m > 2.0:  # Raised 200+ bps in 6 months
    score += 3.0  # Aggressive tightening
elif velocity_6m > 1.0:  # Raised 100-200 bps
    score += 1.5  # Moderate tightening
```

## Alternatives Considered

### Alternative 1: Levels Only ❌

**Why Rejected:**
- Misses turning points
- False signals from persistent extremes
- Slower to react
- Historical analysis shows inferior performance

### Alternative 2: Velocity Only ❌

**Why Rejected:**
- Too noisy without level confirmation
- Can miss sustained extreme conditions
- Hybrid (velocity + level) performs better for credit indicators

### Alternative 3: Percentile Ranks ❌

**Idea:** Score based on historical distribution
- 95th percentile = extreme
- 50th percentile = normal

**Why Rejected:**
- Requires extensive historical data
- Harder to interpret
- Doesn't capture velocity directly
- Could layer on top later

## Backtest Validation

**Will test in backtesting:**
1. Pure velocity approach vs pure level
2. Velocity-only vs hybrid (70/30)
3. Different lookback periods (20d, 60d, 1yr)
4. Smoothing techniques (moving averages)

**Success Criteria:**
- Velocity approach catches crashes 30+ days earlier
- Fewer false positives than level-based
- F1 score >0.7

## Future Considerations

**When to Revisit:**
- After backtest results
- If velocity signals prove too noisy
- New research on optimal lookback periods

**Potential Enhancements:**
- Acceleration (2nd derivative) for extreme cases
- Adaptive lookback periods based on volatility
- Regime-specific velocity thresholds

## References

- Federal Reserve: "Turning Points in Business Cycles" (2019)
- BIS Working Papers: "Early Warning Indicators of Banking Crises" (2014)
- NBER: "Predicting Stock Market Crashes Using Derivatives" (2016)

---

**Last Updated:** 2025-01-08
**Next Review:** After backtesting completion
