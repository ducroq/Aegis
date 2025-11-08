# Aegis Test Suite

Comprehensive test suite for the Aegis Real-Time Macro Defense system.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [CI/CD Integration](#cicd-integration)
- [Coverage Requirements](#coverage-requirements)
- [Writing New Tests](#writing-new-tests)

## Overview

The Aegis test suite is designed to ensure reliability, correctness, and maintainability of the risk assessment system. Tests are organized by component and include unit tests, integration tests, and smoke tests.

**Coverage Goal:** 85%+

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and pytest configuration
├── test_config.py           # Configuration loading tests
├── test_fred_client.py      # FRED API client tests
├── test_data_manager.py     # Data manager integration tests
├── test_scoring.py          # Risk scoring logic tests
├── test_alerts.py           # Alert system tests
├── test_integration.py      # End-to-end integration tests
└── README.md               # This file
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scoring.py

# Run specific test
pytest tests/test_scoring.py::TestRecessionScorer::test_normal_conditions
```

### Test Markers

Tests are organized using pytest markers for selective execution:

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Tests that don't require external APIs
pytest -m "not api and not requires_secrets"

# Smoke tests (quick validation)
pytest -m smoke

# Slow tests (backtesting, historical data)
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Common Test Scenarios

```bash
# Local development (fast feedback loop)
pytest -m "unit and not api" -v

# Pre-commit checks (without API calls)
pytest -m "not api and not requires_secrets" --cov=src --cov-fail-under=85

# Full test suite (requires API keys)
pytest --cov=src --cov-report=html

# Integration tests only
pytest -m integration -v

# Run tests in parallel (faster)
pytest -n auto
```

## Test Categories

### Unit Tests (`-m unit`)

Fast, isolated tests for individual components:

- **Configuration:** `test_config.py`
  - Config file loading
  - Secret management
  - Weight validation

- **Data Clients:** `test_fred_client.py`, `test_market_data.py`
  - API client functionality
  - Data caching
  - Velocity calculations

- **Scoring Logic:** `test_scoring.py`
  - Recession scoring
  - Credit scoring
  - Valuation scoring
  - Liquidity scoring
  - Positioning scoring
  - Risk aggregation

- **Alerts:** `test_alerts.py`
  - Alert logic
  - Email formatting
  - History management

### Integration Tests (`-m integration`)

End-to-end tests across multiple components:

- **Full Pipeline:** Data fetching → Scoring → Aggregation
- **Component Interaction:** Verify data flows correctly
- **Config Integration:** Test config usage throughout system
- **Missing Data Handling:** Graceful degradation

### Smoke Tests (`-m smoke`)

Quick sanity checks for basic functionality:

- System can start
- Configuration loads
- Basic calculations work
- No import errors

### API Tests (`-m api`)

Tests that require external API calls:

- **Note:** These tests are marked and can be skipped in CI when API keys are not available
- Requires valid FRED API key in `config/credentials/secrets.ini`
- Tests actual API responses and data quality

## CI/CD Integration

### GitHub Actions Workflows

#### 1. Main CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push and pull request:

- **Lint:** Code quality checks (Black, isort, Flake8, MyPy)
- **Unit Tests:** Runs across Python 3.9-3.12 and Linux/Windows/macOS
- **Integration Tests:** Full pipeline validation
- **Coverage:** Generates coverage reports
- **Security:** Dependency and security scanning

**Matrix Strategy:**
- 3 operating systems (Ubuntu, Windows, macOS)
- 4 Python versions (3.9, 3.10, 3.11, 3.12)
- Fail-fast disabled for comprehensive results

#### 2. Coverage Report (`.github/workflows/coverage-report.yml`)

Generates detailed coverage reports:

- HTML coverage report
- XML for Codecov integration
- Coverage badges
- PR comments with coverage changes

### Required Secrets for CI

Configure these in GitHub repository settings:

```
FRED_API_KEY (optional)        # For running API tests
CODECOV_TOKEN (optional)       # For Codecov integration
```

### Status Checks

Pull requests must pass:

- ✅ Lint checks
- ✅ Unit tests (all platforms)
- ⚠️ Integration tests (optional without API keys)
- ✅ Coverage ≥ 85%
- ✅ Security scan

## Coverage Requirements

### Overall Coverage: 85%+

**Component-Level Targets:**

| Component | Target | Priority |
|-----------|--------|----------|
| Config Manager | 95%+ | Critical |
| Data Clients | 90%+ | High |
| Scoring Logic | 95%+ | Critical |
| Alert System | 90%+ | High |
| Aggregator | 95%+ | Critical |
| Dashboard | 60%+ | Low (optional) |

### Coverage Exclusions

Lines excluded from coverage (configured in `pytest.ini`):

- `if __name__ == '__main__':`
- `def __repr__`
- `def __str__`
- `raise NotImplementedError`
- `@abstractmethod`
- Dashboard code (lower priority)

### Viewing Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
# Windows:
start htmlcov/index.html

# Mac:
open htmlcov/index.html

# Linux:
xdg-open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing
```

## Writing New Tests

### Test File Naming

- `test_<module>.py` for unit tests
- `test_<feature>_integration.py` for integration tests

### Test Class Naming

```python
class TestComponentName:
    """Tests for ComponentName."""
    pass
```

### Test Method Naming

```python
def test_<behavior>_<condition>(self):
    """Test that <expected behavior> when <condition>."""
    pass
```

**Examples:**
```python
def test_calculate_score_normal_conditions(self):
    """Test that score is low under normal conditions."""

def test_fetch_series_returns_none_on_error(self):
    """Test that fetch_series returns None when API error occurs."""
```

### Fixture Usage

Use shared fixtures from `conftest.py`:

```python
def test_with_config(self, mock_config):
    """Test using mock configuration."""
    # mock_config is provided by conftest.py
    assert mock_config.get_secret('fred_api_key') is not None

def test_with_temp_cache(self, temp_cache_dir):
    """Test using temporary cache directory."""
    client = FREDClient(cache_dir=temp_cache_dir)
    # Temp directory auto-cleaned after test
```

### Common Fixtures

| Fixture | Description |
|---------|-------------|
| `mock_config` | Mock ConfigManager |
| `temp_config_dir` | Temporary config directory |
| `temp_cache_dir` | Temporary cache directory |
| `sample_time_series` | Sample pandas Series |
| `sample_fred_data` | Mock FRED data |
| `normal_recession_indicators` | Normal recession indicators |
| `warning_recession_indicators` | Warning-level indicators |
| `mock_fred_client` | Mock FRED client |
| `mock_market_client` | Mock market data client |

### Test Patterns

#### Pattern 1: Arrange-Act-Assert

```python
def test_score_calculation(self):
    """Test score calculation."""
    # Arrange
    scorer = RecessionScorer()
    indicators = {'unemployment_velocity': 5.0, 'ism_pmi': 52.0}

    # Act
    result = scorer.calculate_score(indicators)

    # Assert
    assert result['score'] > 0
    assert result['score'] < 10
```

#### Pattern 2: Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("velocity,expected_score", [
    (20.0, 4.0),  # Extreme spike
    (10.0, 2.0),  # Moderate spike
    (5.0, 1.0),   # Rising
    (1.0, 0.0),   # Stable
])
def test_unemployment_velocity_scoring(self, velocity, expected_score):
    """Test unemployment velocity scoring thresholds."""
    scorer = RecessionScorer()
    score, _ = scorer._score_unemployment_velocity(velocity)
    assert score == expected_score
```

#### Pattern 3: Mock External Dependencies

```python
@patch('src.data.fred_client.Fred')
def test_fred_client_initialization(self, mock_fred_class):
    """Test FRED client initializes correctly."""
    mock_config = Mock()
    mock_config.get_secret.return_value = 'test_key'

    client = FREDClient(config=mock_config)

    mock_fred_class.assert_called_once_with(api_key='test_key')
    assert client.api_key == 'test_key'
```

### Adding Test Markers

```python
@pytest.mark.unit
def test_basic_functionality(self):
    """Quick unit test."""
    pass

@pytest.mark.integration
def test_full_pipeline(self):
    """Integration test across components."""
    pass

@pytest.mark.api
@pytest.mark.requires_secrets
def test_live_fred_api(self):
    """Test that requires live FRED API."""
    pass

@pytest.mark.slow
def test_backtest_2000_2024(self):
    """Slow backtest over 24 years of data."""
    pass
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$PWD
pytest

# Or use pytest's built-in path resolution
pytest --import-mode=importlib
```

#### 2. Missing Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-mock black isort flake8 mypy
```

#### 3. API Tests Failing

```bash
# Skip API tests
pytest -m "not api"

# Or add dummy API key
echo "[api_keys]" > config/credentials/secrets.ini
echo "fred_api_key = dummy_key_for_testing" >> config/credentials/secrets.ini
```

#### 4. Coverage Below Threshold

```bash
# See which lines are missing coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML report for detailed view
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

#### 5. Tests Hanging

```bash
# Add timeout
pytest --timeout=300

# Run with verbose output
pytest -vv -s
```

## Best Practices

### DO

✅ Write descriptive test names that explain what is being tested
✅ Use fixtures for setup and teardown
✅ Test edge cases and error conditions
✅ Use markers to categorize tests
✅ Keep tests independent (no shared state)
✅ Mock external dependencies (APIs, file I/O)
✅ Assert on specific values, not just "not None"
✅ Test both success and failure paths

### DON'T

❌ Write tests that depend on external services without mocking
❌ Use hardcoded paths (use fixtures with temp directories)
❌ Test implementation details (test behavior, not internals)
❌ Write tests that take minutes to run (mark as `slow`)
❌ Commit test data to repository (generate in fixtures)
❌ Use `sleep()` for timing (use mocks)
❌ Test third-party libraries (trust they work)

## Continuous Improvement

### Adding Tests for Bugs

When fixing a bug:

1. **Write a failing test** that reproduces the bug
2. **Fix the bug**
3. **Verify the test passes**
4. **Commit both** the test and the fix

```python
def test_regression_issue_42(self):
    """Test for bug #42: YoY calculation fails with leap years."""
    # Arrange: Data that caused the bug
    dates = pd.date_range(start='2020-02-29', end='2024-02-29', freq='D')
    series = pd.Series(range(len(dates)), index=dates)

    # Act: This should not raise
    velocity = calculate_velocity(series, method='yoy_pct')

    # Assert: Should return valid number
    assert velocity is not None
    assert -100 < velocity < 1000  # Reasonable range
```

### Monitoring Test Health

```bash
# Check test execution time
pytest --durations=10

# Check flaky tests
pytest --count=10  # Run each test 10 times

# Profile test coverage
pytest --cov=src --cov-report=html
# Look for red lines in htmlcov/
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Getting Help

Issues with tests? Check:

1. **This README** for common patterns
2. **conftest.py** for available fixtures
3. **Existing tests** for examples
4. **GitHub Issues** for known problems
5. **CI logs** for detailed error messages

---

**Note:** Keep tests fast, focused, and valuable. Every test should have a clear purpose and test one specific behavior.
