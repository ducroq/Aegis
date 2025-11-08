# FRED Client

**File:** `src/data/fred_client.py`

## Purpose

Fetch economic time series data from the Federal Reserve Economic Data (FRED) API with intelligent caching and velocity calculation capabilities. This is the primary data source for Aegis, providing ~80% of all indicators used in risk scoring.

## Public Interface

### Class: `FREDClient`

```python
class FREDClient:
    def __init__(self, config: ConfigManager, cache_dir: str = None)

    # Core data fetching
    def get_series(self, series_id: str,
                   start_date: str = None,
                   end_date: str = None,
                   use_cache: bool = True,
                   cache_ttl_hours: int = 24) -> pd.Series

    def get_latest_value(self, series_id: str) -> float

    def get_multiple_series(self, series_ids: List[str]) -> Dict[str, pd.Series]

    # Velocity calculations
    def calculate_velocity(self, series_id: str,
                          method: str = 'yoy_pct',
                          periods: int = None) -> float

    def get_moving_average(self, series_id: str, window: int = 12) -> float
```

### Key Methods

**`get_series(series_id, ...)`**
- Fetches time series from FRED
- Automatically caches to local CSV files
- Respects TTL for cache freshness
- Returns pandas Series with date index
- Defaults to last 5 years of data

**`get_latest_value(series_id)`**
- Quick accessor for most recent value
- Uses cached data if available
- Returns float or None

**`calculate_velocity(series_id, method, periods)`**
- **'yoy_pct':** Year-over-year percent change
- **'mom_change':** Month-over-month absolute change
- **'rate_of_change':** N-period rate of change
- Returns float representing velocity

**`get_moving_average(series_id, window)`**
- Calculates trailing moving average
- Default 12-period window
- Useful for smoothing noisy series

## Key Dependencies

- **fredapi:** Official FRED Python client
- **pandas:** Time series operations
- **pathlib:** Cache file management
- **datetime/timedelta:** Date handling

## Implementation Notes

### Current Approach

**Caching Strategy:**
- Files stored in `cache_dir/fred/{series_id}.csv`
- TTL checked using file modification time
- Cache hit rate >90% for daily updates
- Expired cache triggers fresh API fetch

**Velocity Calculations:**
- Year-over-year (YoY) most common for indicators
- Handles insufficient data gracefully (returns None)
- Uses last available value for most recent period

**Error Handling:**
- API failures return None (not exception)
- Logs errors but continues gracefully
- Allows system to function with partial data

### Gotchas

**⚠️ Cache Timestamp Precision**
- Windows filesystem has lower timestamp precision
- Tests using time-based cache expiry may be flaky on Windows
- Use `pytest.skip()` for platform-specific issues

**⚠️ FRED API Rate Limits**
- No official limit, but be reasonable
- Aggressive caching mitigates this
- ~50-100 requests per day typical

**⚠️ Data Revisions**
- FRED data gets revised (especially GDP, employment)
- Using current data in backtesting = look-ahead bias
- Consider using "real-time" datasets for accurate backtests

**⚠️ Series Discontinuation**
- Some FRED series get discontinued
- Always have fallback indicators
- Monitor logs for fetch failures

### TODOs

- [ ] Add support for FRED "real-time" datasets for backtesting
- [ ] Implement bulk download optimization
- [ ] Add retry logic with exponential backoff
- [ ] Create series metadata cache (names, descriptions)
- [ ] Add data quality checks (missing values, outliers)

## Usage Examples

### Basic Fetching

```python
from src.config.config_manager import ConfigManager
from src.data.fred_client import FREDClient

config = ConfigManager()
client = FREDClient(config)

# Get yield curve spread
yield_curve = client.get_series('T10Y2Y')
current_spread = client.get_latest_value('T10Y2Y')
```

### Velocity Calculation

```python
# Calculate year-over-year change in unemployment claims
claims_velocity = client.calculate_velocity('ICSA', method='yoy_pct')

# This is key for leading indicators - rate of change matters more than level
if claims_velocity > 10.0:
    print("⚠️ Unemployment claims rising rapidly")
```

### Batch Fetching

```python
series_ids = ['T10Y2Y', 'UNRATE', 'BAMLH0A0HYM2', 'M2SL']
data = client.get_multiple_series(series_ids)

for sid, series in data.items():
    print(f"{sid}: {len(series)} observations")
```

## Recent Changes

- **2025-01-08:** Initial implementation with caching and velocity
- **2025-01-08:** Added test suite with 26 unit tests
- **2025-01-08:** Fixed cache expiry test to handle Windows timing issues

## Related Components

- **DataManager** (`src/data/data_manager.py`) - Orchestrates FREDClient
- **All Scorers** (`src/scoring/*.py`) - Consume FRED data
- **ConfigManager** (`src/config/config_manager.py`) - Provides API key

## Performance Notes

- **Cold start:** 2-3 seconds (fetching multiple series)
- **Cached:** <100ms (reading local CSV files)
- **Memory:** ~5-10MB per series loaded
- **Disk:** ~500KB per cached series

## Testing

Tests are in `tests/test_fred_client.py` (26 tests)

**Key test scenarios:**
- API initialization and authentication
- Data fetching and caching
- Velocity calculations (YoY, MoM, RoC)
- Cache expiry and TTL
- Error handling (API failures, missing data)
- Edge cases (insufficient data for velocity)

**Run tests:**
```bash
pytest tests/test_fred_client.py -v
```
