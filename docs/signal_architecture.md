# Multi-Signal Architecture for Aegis

**Design Decision**: Build portfolio of independent signals with confidence scores for downstream aggregation

## Philosophy

Rather than seeking a single "perfect" indicator, Aegis uses multiple independent signals:
- Each signal captures different crash types
- Signals provide evidence that compounds
- More signals active = higher confidence in warning
- Dashboard displays all signals for nuanced decision-making

## Implemented Signals

### Signal #1: Valuation Warning
**Status**: ✓ IMPLEMENTED

**What it catches**: Bubble-driven crashes (Dot-com, COVID)

**Logic**:
- CAPE > 30 AND Buffett Indicator > 120%
- Fires 2-3 months before crash peaks

**Historical performance**:
- Dot-com: Warned 83 days before peak
- COVID: Warned 80 days before peak
- Financial Crisis: Missed (not a valuation bubble)
- 2022 Bear: Missed (data gap)

**Confidence levels**:
- EXTREME: CAPE > 40 AND Buffett > 180%
- HIGH: CAPE > 35 AND Buffett > 150%
- MODERATE: CAPE > 30 AND Buffett > 120% (current threshold)

**Code**: `src/scoring/aggregator.py::_check_valuation_warning()`

---

### Signal #2: Double Inversion Warning
**Status**: ✓ IMPLEMENTED

**What it catches**: Recession + credit stress combination

**Logic**:
- Yield curve 10Y-2Y < 0 (inverted) AND HY spreads > 5%
- Indicates both recession signal and funding stress

**Historical performance**:
- Dot-com: Warned 23 days before peak
- Financial Crisis: Missed (timing - curve uninverted before spreads widened)
- COVID: Missed
- 2022 Bear: Warned 8 months after peak (during crash)

**Why keep it despite overlap with valuation?**:
- Provides independent evidence (different mechanism)
- When BOTH fire, confidence is higher
- Catches credit+recession combos that aren't valuation-driven

**Confidence levels**:
- SEVERE: Both inverted AND spreads > 8%
- HIGH: Both inverted AND spreads > 5% (current threshold)

**Code**: `src/scoring/aggregator.py::_check_double_inversion()`

---

### Signal #3: Real Interest Rates Warning
**Status**: ✓ IMPLEMENTED

**What it catches**: Fed tightening cycles (2022 bear market, 1994, 1987)

**Logic**:
```python
real_rate = fed_funds_rate - cpi_inflation_yoy

if real_rate > 2.0 and fed_funds_velocity_6m > 3.0:
    # Rapid tightening into positive real rates
    return REAL_RATE_WARNING
```

**Why needed**:
- Catches Fed-driven selloffs that aren't crashes
- 2022 bear market (-25%) was pure rate-driven
- Complements other signals (orthogonal mechanism)

**Data added**:
- Fed funds rate: ✓ Already have (liquidity_fed_funds_rate)
- CPI inflation: ✓ Added FRED series CPIAUCSL + YoY calculation
- Fed funds velocity: ✓ Already have (liquidity_fed_funds_velocity_6m)

**Confidence levels**:
- HIGH: Real rate > 2.0% AND 6M velocity > 3.0% (rapid tightening)
- MODERATE: Real rate > 2.0% but velocity < 3.0% (high but stabilizing)

**Code**: `src/scoring/aggregator.py::_check_real_rate_warning()`

**Historical performance**: (Pending full backtest with CPI data)
- Expected to catch 2022 bear market early in tightening cycle
- Expected to warn before 1994 bond sell-off
- Expected to warn before 2018 Q4 selloff

---

---

## Signal Aggregation Framework

### Current Alert Logic (Priority Order):

1. **DOUBLE_INVERSION_WARNING** (highest priority - severe)
2. **VALUATION_WARNING** (leading indicator)
3. **RED alert** (macro score ≥ 5.0)
4. **YELLOW alert** (macro score ≥ 4.0)
5. **GREEN** (normal)

### Proposed Multi-Signal Dashboard:

| Signals Active | Risk Level | Confidence | Cash Target | Rationale |
|----------------|------------|------------|-------------|-----------|
| None | GREEN | N/A | 0-10% | Normal conditions |
| Valuation only | CAUTION | Medium | 20-30% | Bubble forming, watch for triggers |
| Real rates only | CAUTION | Medium | 20-30% | Fed headwind, reduce beta |
| Double inversion only | WARNING | High | 40-50% | Recession + credit stress |
| **Valuation + Real rates** | **WARNING** | **High** | **40-50%** | **Expensive + tightening** |
| **Valuation + Double inversion** | **DANGER** | **Very High** | **60-70%** | **Bubble + macro stress** |
| **Real rates + Double inversion** | **DANGER** | **Very High** | **60-70%** | **Tightening + credit stress** |
| **All 3 signals** | **EXTREME** | **Extreme** | **80%+** | **Multiple convergence** |

### Signal Combination Examples:

**Scenario 1: Dot-com Peak (Mar 2000)**
- Valuation: ✓ (83 days before)
- Double inversion: ✓ (23 days before)
- Real rates: (need to backtest)
- **Combination**: At least 2 signals = DANGER level

**Scenario 2: 2007 Financial Crisis Peak**
- Valuation: ✗ (CAPE only 27)
- Double inversion: ✗ (timing issue)
- Real rates: (need to backtest - Fed was cutting)
- **Combination**: Macro score would trigger (coincident)

**Scenario 3: 2022 Bear Market**
- Valuation: ✗ (data gap)
- Double inversion: ✓ (8 months late)
- Real rates: ✓ (expected - Fed tightening)
- **Combination**: Real rates would provide early warning

---

## Implementation Roadmap

### Phase 1: Completed ✓
- [x] Valuation warning system
- [x] Double inversion warning
- [x] Alert integration
- [x] Documentation

### Phase 2: Completed ✓
- [x] Add CPI data to DataManager
- [x] Implement real interest rates warning
- [x] Update aggregator to return all signals
- [x] Integrate into alert_logic.py
- [ ] Complete backtest on 2022 bear market (pending CPI data backfill)

### Phase 3: Dashboard (Future)
- [ ] Create signal dashboard view
- [ ] Visual indicators for each signal
- [ ] Signal combination heatmap
- [ ] Historical signal backtest visualization

### Phase 4: Confidence Weighting (Future)
- [ ] Implement signal confidence scores
- [ ] Weighted aggregation logic
- [ ] Dynamic cash allocation recommendation
- [ ] Track signal accuracy over time

---

## Signal Design Principles

1. **Independence**: Each signal uses different data/mechanisms
2. **Transparency**: Clear thresholds, no black boxes
3. **Backtestable**: All signals validated on historical data
4. **Actionable**: Each signal maps to specific actions
5. **Complementary**: Signals catch different crash types

---

## Future Signal Ideas (Backlog)

### Signal #4: Earnings Recession
**What**: Forward EPS estimates declining
**Catches**: Economic slowdowns before they hit stocks
**Data**: FRED forward P/E (can derive EPS)

### Signal #5: Housing Bubble
**What**: New home sales declining + affordability crisis
**Catches**: Housing-led crises (2007)
**Data**: FRED housing indicators

### Signal #6: Market Breadth Deterioration
**What**: % of S&P 500 above 200-day MA declining
**Catches**: Tops forming even without extreme valuations
**Data**: Yahoo Finance (harder to get)

### Signal #7: Margin Debt Peak
**What**: Margin debt as % of GDP at extremes
**Catches**: Speculative excess
**Data**: FRED (we have this data)

---

## Code Architecture

### Signal Return Format (Standard):

```python
{
    'active': bool,           # Is warning currently active?
    'level': str,            # 'EXTREME', 'SEVERE', 'HIGH', 'MODERATE', None
    'confidence': float,      # 0-100% confidence score (future)
    'message': str,          # Human-readable explanation
    'values': dict,          # Actual indicator values
    'threshold': dict        # Threshold values for reference
}
```

### Aggregator Integration:

All signals checked in `RiskAggregator.calculate_overall_risk()`:
1. Call each signal check method
2. Add results to return dict
3. Alert logic consumes signals in priority order
4. Dashboard displays all signals (future)

---

## Documentation

- **Implementation**: `src/scoring/aggregator.py`
- **Alert logic**: `src/alerts/alert_logic.py`
- **Backtest results**: `docs/backtest_results.md`
- **Valuation system**: `docs/valuation_warnings.md`
- **Quick reference**: `docs/quick_reference.md`

---

## Summary

Aegis uses a **multi-signal portfolio** rather than single indicator:

**Current signals**:
1. ✓ Valuation warning (catches bubbles)
2. ✓ Double inversion (recession + credit)
3. ⏳ Real interest rates (Fed tightening) - next to implement

**Future expansion**: 4-7 more signals for comprehensive coverage

**Advantage**: Multiple independent evidence sources → higher confidence warnings → better decision-making
