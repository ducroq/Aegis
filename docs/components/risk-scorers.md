# Risk Scorers

**Files:** `src/scoring/*.py`

## Purpose

Transform raw economic and market indicators into standardized risk scores (0-10 scale) across five dimensions. Each scorer analyzes its specific risk domain and returns both an overall score and detailed breakdown of contributing factors.

## Architecture

All scorers follow a common interface pattern:

```python
class [Dimension]Scorer:
    def __init__(self, config: ConfigManager)

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns:
        {
            'score': float (0-10),
            'breakdown': {
                'signal_1': float,
                'signal_2': float,
                ...
            },
            'signals': [
                {'name': str, 'value': float, 'threshold': float, 'triggered': bool},
                ...
            ],
            'reasoning': str
        }
        """
```

---

## 1. Recession Scorer

**File:** `src/scoring/recession.py`
**Weight:** 30% (highest)
**Purpose:** Detect early signs of economic recession

### Key Signals

| Signal | Weight | Threshold | Rationale |
|--------|--------|-----------|-----------|
| **Unemployment Claims Velocity** | 4.0 | >20% YoY | Rapid job loss is strongest recession signal |
| **ISM PMI Regime Cross** | 3.0 | <48 (from >50) | Manufacturing contraction signals recession |
| **Yield Curve (10Y-2Y)** | 2.0 | Inverted (<0) | Most reliable recession predictor (6-18 month lead) |
| **Yield Curve (10Y-3M)** | 1.0 | Inverted (<0) | Confirmation signal |

### Velocity Focus

**Why velocity matters:**
- Unemployment rising 3.5% → 4.0% is more alarming than stable 4.5%
- Rate of change predicts turning points better than levels
- Allows for early warning before indicators reach extreme levels

### Implementation Notes

```python
def calculate_score(self, indicators):
    score = 0.0

    # Unemployment velocity (YoY % change)
    velocity = indicators.get('unemployment_claims_velocity_yoy')
    if velocity > 20:
        score += 4.0  # Extreme spike
    elif velocity > 10:
        score += 2.0  # Significant rise
    elif velocity > 5:
        score += 1.0  # Rising

    # ISM PMI regime shift detection
    current_pmi = indicators.get('ism_pmi')
    prev_pmi = indicators.get('ism_pmi_prev')

    if current_pmi < 48:
        score += 3.0  # Deep contraction
    elif current_pmi < 50 and prev_pmi >= 50:
        score += 2.0  # Just crossed into contraction
    elif current_pmi < 50:
        score += 1.0  # Mild contraction

    # Yield curve inversion
    yc_10y2y = indicators.get('yield_curve_10y2y')
    if yc_10y2y < -0.5:
        score += 2.0  # Deep inversion
    elif yc_10y2y < 0:
        score += 1.0  # Shallow inversion

    return {'score': min(score, 10.0), ...}
```

### Gotchas

- PMI data is monthly (released first week of month)
- Unemployment claims are weekly but volatile (use moving average)
- Yield curve can stay inverted for months before recession

---

## 2. Credit Scorer

**File:** `src/scoring/credit.py`
**Weight:** 25%
**Purpose:** Detect credit market stress and systemic risk

### Key Signals

| Signal | Weight | Threshold | Rationale |
|--------|--------|-----------|-----------|
| **HY Spread Velocity** | 4.0 | >10% widening | Rapid spread widening = credit crunch |
| **HY Spread Level** | 2.0 | >600 bps | Absolute level indicates stress |
| **IG BBB Spreads** | 2.0 | >250 bps | Investment grade stress = serious |
| **TED Spread** | 1.0 | >100 bps | Interbank funding stress |
| **Bank Lending Standards** | 1.0 | >20% net tightening | Credit availability shrinking |

### Hybrid Approach: Velocity + Level

**Why both?**
- **Velocity (70%):** Early warning of deterioration
- **Level (30%):** Confirms stress reached dangerous territory
- Together: Catch both rapid changes and extreme absolutes

### Implementation Notes

High-yield spreads are the most important credit indicator:
- Normal: 300-400 bps
- Elevated: 500-600 bps
- Stress: 700+ bps
- Crisis: 1000+ bps (2008, 2020)

Velocity calculation:
```python
# 20-day rate of change
hy_spread_20d_ago = get_historical_value(20)
hy_spread_velocity = ((current - hy_spread_20d_ago) / hy_spread_20d_ago) * 100
```

### Gotchas

- Spreads can gap wider in hours during crisis
- Daily updates may miss intraday spikes
- OAS (Option-Adjusted Spread) is better than nominal spread

---

## 3. Valuation Scorer

**File:** `src/scoring/valuation.py`
**Weight:** 20%
**Purpose:** Identify overvaluation that increases downside risk

### Key Signals

| Signal | Weight | Threshold | Rationale |
|--------|--------|-----------|-----------|
| **Shiller CAPE** | 4.0 | >30 | P/E >30 historically precedes poor returns |
| **Buffett Indicator** | 3.0 | >150% | Market cap / GDP ratio |
| **Forward P/E** | 3.0 | >22 | Forward estimates less volatile than trailing |

### Historical Context

| Metric | Normal | Elevated | Extreme | Historical Peaks |
|--------|--------|----------|---------|------------------|
| CAPE | 15-20 | 25-30 | 30+ | 44 (1999), 33 (2021) |
| Buffett | 75-100% | 120-150% | 150%+ | 195% (1999), 215% (2021) |
| Forward P/E | 15-18 | 20-22 | 22+ | 28 (1999), 24 (2021) |

### Implementation Notes

Valuation is a **slow-moving** indicator:
- Markets can stay expensive for years (1996-2000, 2017-2021)
- High valuation doesn't cause crashes, but amplifies them
- Use as risk modifier, not timing signal

```python
def calculate_score(self, indicators):
    score = 0.0

    cape = indicators.get('shiller_cape')
    if cape > 35:
        score += 4.0  # Extreme bubble territory
    elif cape > 30:
        score += 3.0  # Elevated
    elif cape > 25:
        score += 1.5  # Slightly high

    # Similar logic for Buffett indicator and Forward P/E

    return {'score': min(score, 10.0), ...}
```

### Gotchas

- Shiller CAPE updated monthly (2-week lag)
- "This time is different" = famous last words
- Valuation can stay elevated for years (dot-com: 1996-2000)

---

## 4. Liquidity Scorer

**File:** `src/scoring/liquidity.py`
**Weight:** 15%
**Purpose:** Assess monetary conditions and market liquidity

### Key Signals

| Signal | Weight | Threshold | Rationale |
|--------|--------|-----------|-----------|
| **Fed Funds Rate Velocity** | 3.0 | >200 bps in 6mo | Rapid tightening = liquidity drain |
| **M2 Velocity** | 2.0 | <0% YoY | Money supply contracting = tight conditions |
| **VIX Level** | 3.0 | >30 | Elevated volatility = liquidity premium |
| **Margin Debt** | 2.0 | Sharp decline | Forced deleveraging = selling pressure |

### Fed Policy Regimes

**Easy Money (Risk Off):**
- Rates: 0-2%
- M2: Growing >5% YoY
- VIX: <15
- Score: 0-3

**Neutral:**
- Rates: 2-4%
- M2: Growing 2-5% YoY
- VIX: 15-20
- Score: 3-6

**Tight Money (Risk On):**
- Rates: 4%+
- M2: Growing <2% or contracting
- VIX: >25
- Score: 6-10

### Implementation Notes

Focus on **rate of change** in Fed policy:
```python
# 6-month change in Fed Funds rate
fed_funds_6m_ago = get_historical_value(180)
velocity = current_rate - fed_funds_6m_ago

if velocity > 2.0:  # Raised 200+ bps in 6 months
    score += 3.0  # Aggressive tightening
```

### Gotchas

- VIX spikes can be short-lived (1-2 days)
- Use moving average for VIX to reduce noise
- M2 data has 2-week lag

---

## 5. Positioning Scorer

**File:** `src/scoring/positioning.py`
**Weight:** 10% (lowest, but important)
**Purpose:** Detect extreme positioning that signals crowded trades

### Key Signals

| Signal | Weight | Threshold | Rationale |
|--------|--------|-----------|-----------|
| **CFTC S&P 500 Net Long** | 4.0 | >80th percentile | Extreme bullishness = reversal risk |
| **CFTC Treasury Net Short** | 3.0 | >80th percentile | Crowded short = squeeze risk |
| **VIX Futures Positioning** | 3.0 | Short interest high | Complacency measure |

### Contrarian Logic

**Extreme bullish positioning = Risk:**
- When everyone is long, who's left to buy?
- Forced unwinding amplifies selloffs
- "Be fearful when others are greedy"

**Extreme bearish positioning = Opportunity:**
- Short squeezes can be violent
- Pessimism often overdone
- Contrarian indicators

### Implementation Notes

CFTC data:
- Updated weekly (Fridays)
- Measures speculative positioning in futures/options
- Net long/short as percentage of open interest

```python
def calculate_score(self, indicators):
    score = 0.0

    # S&P 500 net positioning (contrarian)
    sp_positioning = indicators.get('cftc_sp500_net_long_pct')

    if sp_positioning > 80:  # 80th percentile = very bullish
        score += 4.0  # Crowded long = risk
    elif sp_positioning > 60:
        score += 2.0  # Elevated bullishness

    return {'score': min(score, 10.0), ...}
```

### Gotchas

- CFTC data is backward-looking (1-week lag)
- Positioning can stay extreme for weeks
- Use percentile ranks, not absolute levels (context matters)

---

## Common Patterns Across All Scorers

### Score Capping

All scorers cap at 10.0:
```python
return {'score': min(calculated_score, 10.0), ...}
```

### Graceful Degradation

Missing data handled gracefully:
```python
value = indicators.get('key', None)
if value is None:
    # Skip this signal, continue with others
    pass
```

### Breakdown Transparency

All scorers return detailed breakdown:
```python
return {
    'score': 7.5,
    'breakdown': {
        'unemployment_velocity': 4.0,
        'ism_pmi': 2.0,
        'yield_curve': 1.5
    },
    'signals': [
        {'name': 'Unemployment Claims YoY', 'value': 15.2, 'threshold': 10.0, 'triggered': True},
        ...
    ],
    'reasoning': 'Recession risk elevated due to rapid unemployment increase...'
}
```

---

## Testing

Each scorer has comprehensive unit tests in `tests/test_scoring.py`:

**Test scenarios:**
- Normal conditions (score 0-3)
- Elevated conditions (score 4-6)
- Warning conditions (score 7-8)
- Crisis conditions (score 9-10)
- Edge cases (missing data, extreme values)

**Run tests:**
```bash
pytest tests/test_scoring.py -v
pytest tests/test_scoring.py::TestRecessionScorer -v
```

---

## Tuning Guidelines

When adjusting thresholds:

1. **Backtest first:** Always validate changes against historical data
2. **Document rationale:** Create ADR explaining why threshold changed
3. **Track performance:** Monitor alert accuracy over time
4. **Iterate slowly:** Change one threshold at a time

**Good reasons to adjust:**
- Backtest shows too many false positives
- Missed a significant market event
- New research suggests different threshold

**Bad reasons to adjust:**
- "Feels too sensitive" without data
- Want to suppress current alert
- Overfitting to recent data

---

## Related Components

- **RiskAggregator** (`src/scoring/aggregator.py`) - Combines all scorer outputs
- **DataManager** (`src/data/data_manager.py`) - Provides indicator dict
- **ConfigManager** (`src/config/config_manager.py`) - Provides thresholds from config

---

## Recent Changes

- **2025-01-08:** Initial implementation of all 5 scorers
- **2025-01-08:** Added 32 comprehensive unit tests
- **2025-01-08:** Documented velocity-based approach
