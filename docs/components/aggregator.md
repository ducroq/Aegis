# Risk Aggregator

**File:** `src/scoring/aggregator.py`

## Purpose

Combine individual risk dimension scores (0-10) into a single overall risk score (0-10) using weighted averaging. Determines risk tier (GREEN/YELLOW/RED) and provides transparent breakdown of which dimensions are elevated.

## Public Interface

### Class: `RiskAggregator`

```python
class RiskAggregator:
    def __init__(self, config: ConfigManager)

    def calculate_overall_risk(self, dimension_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Args:
            dimension_scores: {
                'recession': 7.5,
                'credit': 6.0,
                'valuation': 8.5,
                'liquidity': 4.0,
                'positioning': 5.5
            }

        Returns:
            {
                'score': 7.2,
                'tier': 'YELLOW',
                'breakdown': dimension_scores,
                'weights': dimension_weights,
                'elevated_dimensions': ['recession', 'valuation'],
                'reasoning': str
            }
        ```
    def validate_weights(self, weights: Dict[str, float]) -> bool
    def get_tier(self, score: float) -> str
```

## Key Methods

**`calculate_overall_risk(dimension_scores)`**
- Takes 5 dimension scores (must all be present)
- Applies configured weights (default: 30%, 25%, 20%, 15%, 10%)
- Returns weighted average + metadata
- Identifies which dimensions are >7.0 (elevated)

**`validate_weights(weights)`**
- Ensures weights sum to 1.0 (within 0.001 tolerance)
- Raises ValueError if invalid
- Called during initialization

**`get_tier(score)`**
- **GREEN:** 0.0 - 6.4 (normal conditions)
- **YELLOW:** 6.5 - 7.9 (elevated risk)
- **RED:** 8.0 - 10.0 (severe risk)

## Weighting Rationale

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| Recession | 30% | Most predictive of large drawdowns |
| Credit | 25% | Credit crises cause systemic risk |
| Valuation | 20% | Amplifies downsides but slow-moving |
| Liquidity | 15% | Fed policy and volatility matter |
| Positioning | 10% | Contrarian signal, helpful but noisy |

**Why These Weights?**

Based on historical analysis of major market crashes:
- **2008 GFC:** Credit (extreme), Recession (high), Liquidity (high)
- **2000 Tech Bubble:** Valuation (extreme), Recession (moderate)
- **2020 COVID:** All dimensions elevated rapidly
- **2022 Bear:** Valuation (high), Liquidity (high), Recession (moderate)

Recession and Credit have highest weights because they:
1. Predict largest drawdowns (>30%)
2. Give earliest warnings (6-12 month lead time)
3. Have clearest actionable signals

See [decisions/2025-01-08-dimension-weights.md](../decisions/2025-01-08-dimension-weights.md) for full analysis.

## Implementation Notes

### Current Approach

Simple weighted average:

```python
def calculate_overall_risk(self, dimension_scores):
    # Validate all dimensions present
    required = ['recession', 'credit', 'valuation', 'liquidity', 'positioning']
    for dim in required:
        if dim not in dimension_scores:
            raise ValueError(f"Missing dimension: {dim}")

    # Get weights from config
    weights = self.config.get_all_weights()

    # Calculate weighted average
    overall = sum(dimension_scores[dim] * weights[dim] for dim in required)

    # Determine tier
    if overall >= 8.0:
        tier = 'RED'
    elif overall >= 6.5:
        tier = 'YELLOW'
    else:
        tier = 'GREEN'

    # Identify elevated dimensions
    elevated = [dim for dim, score in dimension_scores.items() if score >= 7.0]

    return {
        'score': round(overall, 2),
        'tier': tier,
        'breakdown': dimension_scores,
        'weights': weights,
        'elevated_dimensions': elevated,
        'reasoning': self._generate_reasoning(overall, elevated)
    }
```

### Transparency Features

**Breakdown Included:**
- All individual dimension scores
- Weights used
- Which dimensions are elevated
- Human-readable reasoning

**Example Output:**
```python
{
    'score': 7.2,
    'tier': 'YELLOW',
    'breakdown': {
        'recession': 7.5,
        'credit': 6.0,
        'valuation': 8.5,
        'liquidity': 4.0,
        'positioning': 5.5
    },
    'weights': {
        'recession': 0.30,
        'credit': 0.25,
        'valuation': 0.20,
        'liquidity': 0.15,
        'positioning': 0.10
    },
    'elevated_dimensions': ['recession', 'valuation'],
    'reasoning': 'Risk elevated (7.2/10) due to recession concerns and high valuations. Credit and liquidity conditions remain stable.'
}
```

### Gotchas

**⚠️ All Dimensions Required**
- Aggregator fails if any dimension missing
- This is intentional - partial scoring would be misleading
- DataManager must provide all indicators

**⚠️ Weight Changes Break Comparisons**
- Historical scores calculated with old weights
- Changing weights invalidates past comparisons
- Document weight changes in ADRs

**⚠️ Linear Combination May Miss Interactions**
- Simple weighted average assumes independence
- Reality: Dimensions interact (credit + recession → systemic crisis)
- Future: Could add "amplification factor" for multiple elevated dimensions

## Alternative Approaches Considered

### 1. Non-Linear Combination ❌

**Idea:** Amplify when multiple dimensions elevated
```python
if len(elevated_dimensions) >= 3:
    overall *= 1.2  # 20% boost
```

**Why Rejected:**
- Adds complexity
- Hard to explain
- Linear approach performs well in backtests
- Can revisit if needed

### 2. Dynamic Weights ❌

**Idea:** Adjust weights based on current regime
- Recession threatening? → Increase recession weight
- Credit crisis? → Increase credit weight

**Why Rejected:**
- Introduces look-ahead bias
- Makes system less stable
- Hard to backtest reliably
- Prefer fixed weights for consistency

### 3. Percentile-Based Scoring ❌

**Idea:** Score based on historical percentiles
- 80th percentile = 8.0 score
- 50th percentile = 5.0 score

**Why Rejected:**
- Requires extensive historical data
- Harder to interpret ("what does 7.2 mean?")
- Current absolute thresholds more intuitive
- Can add percentile context to alerts

## TODOs

- [ ] Add "amplification factor" for multiple elevated dimensions (>= 3)
- [ ] Track weight changes over time in metadata
- [ ] Add percentile context to output (e.g., "95th percentile historically")
- [ ] Create visualization of dimension contributions
- [ ] Consider regime-specific weights (expansion vs contraction)

## Usage Examples

### Basic Usage

```python
from src.config.config_manager import ConfigManager
from src.scoring.aggregator import RiskAggregator

config = ConfigManager()
aggregator = RiskAggregator(config)

# Dimension scores from individual scorers
dimension_scores = {
    'recession': 7.5,
    'credit': 6.0,
    'valuation': 8.5,
    'liquidity': 4.0,
    'positioning': 5.5
}

result = aggregator.calculate_overall_risk(dimension_scores)

print(f"Overall Risk: {result['score']}/10 ({result['tier']})")
print(f"Elevated: {result['elevated_dimensions']}")
```

### Weight Validation

```python
# Weights must sum to 1.0
weights = {
    'recession': 0.30,
    'credit': 0.25,
    'valuation': 0.20,
    'liquidity': 0.15,
    'positioning': 0.10
}

aggregator.validate_weights(weights)  # Passes

weights['recession'] = 0.40  # Now sums to 1.1
aggregator.validate_weights(weights)  # Raises ValueError
```

### Interpreting Tiers

```python
def interpret_tier(tier):
    if tier == 'RED':
        return "⛔ SEVERE RISK: Consider major defensive positioning"
    elif tier == 'YELLOW':
        return "⚠️ ELEVATED RISK: Review portfolio, build cash"
    else:
        return "✅ NORMAL CONDITIONS: Stay the course"
```

## Testing

Tests are in `tests/test_scoring.py`:

**Test scenarios:**
- Normal risk (all dimensions 0-3)
- Single elevated dimension
- Multiple elevated dimensions
- Extreme risk (all dimensions 8-10)
- Weight validation (sum != 1.0)
- Missing dimensions (error handling)
- Tier classification

**Run tests:**
```bash
pytest tests/test_scoring.py::TestRiskAggregator -v
```

## Performance Notes

- **Execution Time:** <1ms (simple arithmetic)
- **Memory:** Negligible (<1KB)
- **Bottleneck:** None (dimension scoring is the slow part)

## Related Components

- **All Scorers** (`src/scoring/*.py`) - Provide dimension scores
- **AlertLogic** (`src/alerts/alert_logic.py`) - Consumes overall risk score
- **ConfigManager** (`src/config/config_manager.py`) - Provides weights

## Recent Changes

- **2025-01-08:** Initial implementation with 5 dimensions
- **2025-01-08:** Added weight validation and tier classification
- **2025-01-08:** Documented weighting rationale
- **2025-01-08:** Added comprehensive test coverage

## Decision Records

Key decisions related to aggregation:
- [Dimension Weights](../decisions/2025-01-08-dimension-weights.md) - Why 30/25/20/15/10
- [Alert Thresholds](../decisions/2025-01-08-alert-thresholds.md) - Why YELLOW≥6.5, RED≥8.0
