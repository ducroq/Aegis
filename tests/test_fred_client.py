"""
Unit tests for FRED Client
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from src.data.fred_client import FREDClient
from src.config.config_manager import ConfigManager


class TestFREDClient:
    """Test suite for FRED Client."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config with test API key."""
        config = Mock(spec=ConfigManager)
        config.get_secret.return_value = 'test_api_key_12345'
        return config

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_series_data(self):
        """Create sample time series data."""
        dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
        values = range(100, 100 + len(dates))
        return pd.Series(values, index=dates, name='TEST_SERIES')

    def test_initialization_with_valid_key(self, mock_config, temp_cache_dir):
        """Test initialization with valid API key."""
        with patch('src.data.fred_client.Fred') as mock_fred:
            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)

            assert client.api_key == 'test_api_key_12345'
            mock_fred.assert_called_once_with(api_key='test_api_key_12345')
            assert client.cache_dir == Path(temp_cache_dir)

    def test_initialization_without_key(self, temp_cache_dir):
        """Test initialization without API key."""
        config = Mock(spec=ConfigManager)
        config.get_secret.return_value = None

        client = FREDClient(config=config, cache_dir=temp_cache_dir)

        assert client.fred is None
        assert client.api_key is None

    def test_get_series_success(self, mock_config, temp_cache_dir, sample_series_data):
        """Test successful series fetch."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            result = client.get_series('T10Y2Y', use_cache=False)

            assert result is not None
            assert len(result) == len(sample_series_data)
            mock_fred.get_series.assert_called_once()

    def test_get_series_no_client(self, temp_cache_dir):
        """Test that get_series returns None when client not initialized."""
        config = Mock(spec=ConfigManager)
        config.get_secret.return_value = None

        client = FREDClient(config=config, cache_dir=temp_cache_dir)
        result = client.get_series('T10Y2Y')

        assert result is None

    def test_get_series_with_date_range(self, mock_config, temp_cache_dir, sample_series_data):
        """Test fetching series with custom date range."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            result = client.get_series(
                'T10Y2Y',
                start_date='2020-01-01',
                end_date='2024-01-01',
                use_cache=False
            )

            assert result is not None
            mock_fred.get_series.assert_called_once_with(
                'T10Y2Y',
                observation_start='2020-01-01',
                observation_end='2024-01-01'
            )

    def test_get_latest_value(self, mock_config, temp_cache_dir, sample_series_data):
        """Test getting latest value from series."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            result = client.get_latest_value('T10Y2Y')

            expected = float(sample_series_data.iloc[-1])
            assert result == expected

    def test_get_latest_value_empty_series(self, mock_config, temp_cache_dir):
        """Test getting latest value from empty series."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = pd.Series([])
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            result = client.get_latest_value('T10Y2Y')

            assert result is None

    def test_calculate_velocity_yoy_pct(self, mock_config, temp_cache_dir):
        """Test YoY percent change velocity calculation."""
        # Create series with known values for easy testing
        dates = pd.date_range(start='2022-01-01', end='2024-01-01', freq='D')
        # Value increases from 100 to 120 over 2 years = ~20% total, ~10% YoY at end
        values = [100 + (i * 20 / len(dates)) for i in range(len(dates))]
        series = pd.Series(values, index=dates)

        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = series
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            velocity = client.calculate_velocity('TEST', method='yoy_pct')

            assert velocity is not None
            # Should be approximately 9-10% YoY (value at end vs value 365 days ago)
            assert 8 < velocity < 12  # Allow some margin for daily granularity

    def test_calculate_velocity_rate(self, mock_config, temp_cache_dir):
        """Test N-day rate of change calculation."""
        # Create linear series
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        values = range(len(dates))  # Increases by 1 per day
        series = pd.Series(values, index=dates)

        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = series
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            velocity = client.calculate_velocity('TEST', method='rate', lookback_days=10)

            assert velocity is not None
            # Should be approximately 1.0 (increase of 1 per day)
            assert 0.9 < velocity < 1.1

    def test_calculate_velocity_insufficient_data(self, mock_config, temp_cache_dir):
        """Test velocity calculation with insufficient data."""
        # Very short series
        dates = pd.date_range(start='2024-01-01', end='2024-01-05', freq='D')
        series = pd.Series(range(len(dates)), index=dates)

        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = series
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            # Try to calculate YoY (365 days) with only 5 days of data
            velocity = client.calculate_velocity('TEST', method='yoy_pct')

            assert velocity is None

    def test_get_moving_average(self, mock_config, temp_cache_dir):
        """Test moving average calculation."""
        # Create series with known values
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        series = pd.Series(values, index=dates)

        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = series
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            ma = client.get_moving_average('TEST', window=4)

            # Last 4 values: 70, 80, 90, 100 → average = 85
            assert ma == 85.0

    def test_cache_save_and_load(self, mock_config, temp_cache_dir, sample_series_data):
        """Test that data is cached and loaded correctly."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)

            # First call - should fetch and cache
            result1 = client.get_series('T10Y2Y', use_cache=True, cache_ttl_hours=24)
            assert result1 is not None
            assert mock_fred.get_series.call_count == 1

            # Second call - should load from cache (no new API call)
            result2 = client.get_series('T10Y2Y', use_cache=True, cache_ttl_hours=24)
            assert result2 is not None
            assert mock_fred.get_series.call_count == 1  # Still only 1 call

            # Verify data is the same
            assert len(result1) == len(result2)

    def test_cache_expiry(self, mock_config, temp_cache_dir, sample_series_data):
        """Test that expired cache is not used."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)

            # First call - should fetch and cache
            result1 = client.get_series('T10Y2Y', use_cache=True, cache_ttl_hours=0)
            # With 0 TTL, cache should immediately expire

            # Second call - should fetch again due to expired cache
            result2 = client.get_series('T10Y2Y', use_cache=True, cache_ttl_hours=0)

            # Should have made 2 API calls
            assert mock_fred.get_series.call_count == 2

    def test_get_multiple_series(self, mock_config, temp_cache_dir, sample_series_data):
        """Test fetching multiple series at once."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.return_value = sample_series_data
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            series_ids = ['T10Y2Y', 'UNRATE', 'BAMLH0A0HYM2']
            results = client.get_multiple_series(series_ids)

            assert len(results) == 3
            assert all(sid in results for sid in series_ids)
            assert mock_fred.get_series.call_count == 3

    def test_error_handling(self, mock_config, temp_cache_dir):
        """Test that errors are handled gracefully."""
        with patch('src.data.fred_client.Fred') as mock_fred_class:
            mock_fred = MagicMock()
            mock_fred.get_series.side_effect = Exception("API Error")
            mock_fred_class.return_value = mock_fred

            client = FREDClient(config=mock_config, cache_dir=temp_cache_dir)
            result = client.get_series('INVALID_SERIES')

            # Should return None on error, not raise
            assert result is None
