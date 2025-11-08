"""
Pytest configuration and shared fixtures for Aegis tests.

This module provides common fixtures and configuration for all test modules.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import yaml
import configparser
import pandas as pd

from src.config.config_manager import ConfigManager


# ============================================================================
# Session-level fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    return project_root / "tests" / "data"


# ============================================================================
# Configuration fixtures
# ============================================================================

@pytest.fixture
def temp_config_dir():
    """
    Create a temporary config directory with test configuration files.

    Yields the Path to the temporary directory. Automatically cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Create app.yaml
        app_config = {
            'app': {
                'name': 'Aegis Test',
                'version': '0.1.0'
            },
            'scoring': {
                'weights': {
                    'recession': 0.30,
                    'credit': 0.25,
                    'valuation': 0.20,
                    'liquidity': 0.15,
                    'positioning': 0.10
                }
            },
            'alerts': {
                'yellow_threshold': 6.5,
                'red_threshold': 8.0,
                'min_persistence_days': 2,
                'velocity_threshold': 1.0
            },
            'data': {
                'cache_ttl_hours': 24,
                'lookback_years': 5
            }
        }
        with open(config_dir / 'app.yaml', 'w') as f:
            yaml.dump(app_config, f)

        # Create indicators.yaml
        indicators_config = {
            'recession_indicators': {
                'unemployment_claims_velocity': {
                    'source': 'FRED',
                    'series_id': 'ICSA',
                    'description': 'Initial unemployment claims'
                },
                'ism_pmi': {
                    'source': 'FRED',
                    'series_id': 'NAPM',
                    'description': 'ISM Manufacturing PMI'
                }
            },
            'credit_indicators': {
                'hy_spread': {
                    'source': 'FRED',
                    'series_id': 'BAMLH0A0HYM2',
                    'description': 'ICE BofA US High Yield Index OAS'
                }
            },
            'valuation_indicators': {
                'shiller_cape': {
                    'source': 'Shiller',
                    'description': 'Shiller CAPE ratio'
                }
            },
            'liquidity_indicators': {
                'vix': {
                    'source': 'Yahoo',
                    'ticker': '^VIX',
                    'description': 'CBOE Volatility Index'
                }
            }
        }
        with open(config_dir / 'indicators.yaml', 'w') as f:
            yaml.dump(indicators_config, f)

        # Create regime_shifts.yaml
        regime_config = {
            'regime_shift_categories': {
                'financial_contagion': {
                    'score': 3.0,
                    'keywords': ['bank failure', 'contagion']
                }
            }
        }
        with open(config_dir / 'regime_shifts.yaml', 'w') as f:
            yaml.dump(regime_config, f)

        # Create credentials directory and secrets.ini
        creds_dir = config_dir / 'credentials'
        creds_dir.mkdir()

        secrets = configparser.ConfigParser()
        secrets['api_keys'] = {
            'fred_api_key': 'test_api_key_12345',
            'sendgrid_api_key': 'test_sendgrid_key'
        }
        secrets['email_credentials'] = {
            'sender_email': 'test@example.com',
            'sender_password': 'test_password',
            'recipient_email': 'recipient@example.com'
        }
        with open(creds_dir / 'secrets.ini', 'w') as f:
            secrets.write(f)

        yield config_dir


@pytest.fixture
def mock_config():
    """Create a mock ConfigManager for testing."""
    config = Mock(spec=ConfigManager)
    config.get_secret.return_value = 'test_api_key_12345'

    # Default config values
    config.get.side_effect = lambda path, default=None: {
        'app.scoring.weights.recession': 0.30,
        'app.scoring.weights.credit': 0.25,
        'app.scoring.weights.valuation': 0.20,
        'app.scoring.weights.liquidity': 0.15,
        'app.scoring.weights.positioning': 0.10,
        'app.alerts.yellow_threshold': 6.5,
        'app.alerts.red_threshold': 8.0,
        'app.data.cache_ttl_hours': 24,
    }.get(path, default)

    config.get_all_weights.return_value = {
        'recession': 0.30,
        'credit': 0.25,
        'valuation': 0.20,
        'liquidity': 0.15,
        'positioning': 0.10
    }

    config.get_alert_thresholds.return_value = {
        'yellow_threshold': 6.5,
        'red_threshold': 8.0
    }

    return config


# ============================================================================
# Cache directory fixtures
# ============================================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Sample data fixtures
# ============================================================================

@pytest.fixture
def sample_time_series():
    """Create a sample time series for testing."""
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
    values = range(100, 100 + len(dates))
    return pd.Series(values, index=dates, name='TEST_SERIES')


@pytest.fixture
def sample_fred_data():
    """Create sample FRED-style time series data."""
    dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='D')

    # Simulate different series
    return {
        'T10Y2Y': pd.Series([0.5 - (i * 0.001) for i in range(len(dates))], index=dates),  # Gradually inverting yield curve
        'UNRATE': pd.Series([3.5 + (i * 0.0001) for i in range(len(dates))], index=dates),  # Rising unemployment
        'ICSA': pd.Series([200000 + (i * 10) for i in range(len(dates))], index=dates),  # Rising claims
        'BAMLH0A0HYM2': pd.Series([350 + (i * 0.05) for i in range(len(dates))], index=dates),  # Widening spreads
    }


@pytest.fixture
def sample_market_data():
    """Create sample market data (Yahoo Finance style)."""
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')

    # Create OHLCV data
    df = pd.DataFrame({
        'Open': [4000 + i for i in range(len(dates))],
        'High': [4050 + i for i in range(len(dates))],
        'Low': [3950 + i for i in range(len(dates))],
        'Close': [4000 + i for i in range(len(dates))],
        'Volume': [100000000 + (i * 1000) for i in range(len(dates))]
    }, index=dates)

    return df


# ============================================================================
# Indicator data fixtures
# ============================================================================

@pytest.fixture
def normal_recession_indicators():
    """Normal economic conditions - recession indicators."""
    return {
        'unemployment_claims_velocity_yoy': 2.0,
        'ism_pmi': 54.0,
        'ism_pmi_prev': 53.5,
        'yield_curve_10y2y': 0.3,
        'yield_curve_10y3m': 0.5,
        'consumer_sentiment': 95.0
    }


@pytest.fixture
def warning_recession_indicators():
    """Warning-level recession indicators."""
    return {
        'unemployment_claims_velocity_yoy': 12.0,
        'ism_pmi': 48.5,
        'ism_pmi_prev': 51.0,
        'yield_curve_10y2y': -0.6,
        'yield_curve_10y3m': -0.4,
        'consumer_sentiment': 72.0
    }


@pytest.fixture
def normal_credit_indicators():
    """Normal credit conditions."""
    return {
        'hy_spread': 350,
        'hy_spread_velocity_20d': 1.0,
        'ig_spread_bbb': 120,
        'ted_spread': 0.3,
        'bank_lending_standards': 5.0
    }


@pytest.fixture
def crisis_credit_indicators():
    """Credit crisis conditions."""
    return {
        'hy_spread': 900,
        'hy_spread_velocity_20d': 15.0,
        'ig_spread_bbb': 450,
        'ted_spread': 2.5,
        'bank_lending_standards': 40.0
    }


@pytest.fixture
def normal_valuation_indicators():
    """Normal valuation levels."""
    return {
        'shiller_cape': 18.0,
        'wilshire_5000': 28000,
        'gdp': 28000,
        'sp500_forward_pe': 18.0
    }


@pytest.fixture
def bubble_valuation_indicators():
    """Bubble-level valuations."""
    return {
        'shiller_cape': 38.0,
        'wilshire_5000': 60000,
        'gdp': 28000,
        'sp500_forward_pe': 28.0
    }


@pytest.fixture
def normal_liquidity_indicators():
    """Normal liquidity conditions."""
    return {
        'fed_funds_rate': 3.0,
        'fed_funds_velocity_6m': 0.3,
        'm2_velocity_yoy': 6.0,
        'vix': 15.0
    }


@pytest.fixture
def tight_liquidity_indicators():
    """Tight liquidity conditions."""
    return {
        'fed_funds_rate': 5.5,
        'fed_funds_velocity_6m': 2.5,
        'm2_velocity_yoy': -1.0,
        'vix': 35.0
    }


# ============================================================================
# Historical data fixtures
# ============================================================================

@pytest.fixture
def historical_risk_scores():
    """Sample historical risk scores for alert testing."""
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='D')

    # Simulate gradually increasing risk
    scores = [5.0 + (i * 0.1) for i in range(len(dates))]

    return pd.DataFrame({
        'date': dates,
        'overall_risk': scores,
        'recession': [s * 0.3 for s in scores],
        'credit': [s * 0.25 for s in scores],
        'valuation': [s * 0.20 for s in scores],
        'liquidity': [s * 0.15 for s in scores],
        'positioning': [s * 0.10 for s in scores],
        'tier': ['GREEN'] * len(dates)
    })


# ============================================================================
# Mock API clients
# ============================================================================

@pytest.fixture
def mock_fred_client(sample_fred_data):
    """Create a mock FRED client."""
    from src.data.fred_client import FREDClient

    client = Mock(spec=FREDClient)
    client.get_series.side_effect = lambda series_id, **kwargs: sample_fred_data.get(series_id)
    client.get_latest_value.side_effect = lambda series_id: float(sample_fred_data[series_id].iloc[-1]) if series_id in sample_fred_data else None
    client.calculate_velocity.return_value = 5.0
    client.get_moving_average.return_value = 100.0

    return client


@pytest.fixture
def mock_market_client(sample_market_data):
    """Create a mock market data client."""
    from src.data.market_data import MarketDataClient

    client = Mock(spec=MarketDataClient)
    client.get_ticker_data.return_value = sample_market_data
    client.get_latest_price.return_value = float(sample_market_data['Close'].iloc[-1])
    client.get_sp500_price.return_value = 4500.0
    client.get_vix.return_value = 15.0
    client.get_forward_pe.return_value = 20.0

    return client


# ============================================================================
# Pytest markers and configuration
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests across components")
    config.addinivalue_line("markers", "slow: Tests that take significant time")
    config.addinivalue_line("markers", "api: Tests that hit external APIs")
    config.addinivalue_line("markers", "requires_secrets: Tests requiring API keys")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "backtest: Backtesting tests")


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name."""
    for item in items:
        # Mark unit tests
        if "test_unit" in item.nodeid or "/unit/" in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Mark integration tests
        if "test_integration" in item.nodeid or "/integration/" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark API tests
        if "api" in item.name.lower() or "fred" in item.name.lower() or "yahoo" in item.name.lower():
            item.add_marker(pytest.mark.api)

        # Mark slow tests
        if "backtest" in item.name.lower() or "historical" in item.name.lower():
            item.add_marker(pytest.mark.slow)


# ============================================================================
# Environment setup/teardown
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """
    Automatically set up test environment for each test.

    This fixture:
    - Sets PYTHONPATH
    - Creates temporary directories
    - Cleans up after test
    """
    # Set PYTHONPATH to project root
    project_root = Path(__file__).parent.parent
    monkeypatch.setenv('PYTHONPATH', str(project_root))

    # Create temp directories
    temp_data = tmp_path / "data"
    temp_cache = temp_data / "cache"
    temp_cache.mkdir(parents=True, exist_ok=True)

    yield

    # Cleanup happens automatically with tmp_path
