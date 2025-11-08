"""
Unit tests for DataManager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.data.data_manager import DataManager
from src.config.config_manager import ConfigManager


class TestDataManager:
    """Test suite for DataManager."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Mock(spec=ConfigManager)
        return config

    @pytest.fixture
    def mock_clients(self):
        """Create mock FRED and market data clients."""
        fred_client = MagicMock()
        market_client = MagicMock()

        # Setup default return values
        fred_client.get_latest_value.return_value = 100.0
        fred_client.get_moving_average.return_value = 95.0
        fred_client.calculate_velocity.return_value = 5.0
        market_client.get_sp500_price.return_value = 4500.0
        market_client.get_vix.return_value = 15.0
        market_client.get_forward_pe.return_value = 20.0

        return fred_client, market_client

    def test_initialization(self, mock_config):
        """Test DataManager initialization."""
        with patch('src.data.data_manager.FREDClient'), \
             patch('src.data.data_manager.MarketDataClient'):
            manager = DataManager(config=mock_config)
            assert manager.config == mock_config
            assert manager.fred_client is not None
            assert manager.market_client is not None

    def test_fetch_all_indicators_structure(self, mock_config, mock_clients):
        """Test that fetch_all_indicators returns correct structure."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager.fetch_all_indicators()

            # Check top-level structure
            assert 'recession' in data
            assert 'credit' in data
            assert 'valuation' in data
            assert 'liquidity' in data
            assert 'positioning' in data
            assert 'metadata' in data

            # Check metadata
            assert 'fetch_timestamp' in data['metadata']
            assert 'fetch_duration_seconds' in data['metadata']

    def test_fetch_recession_indicators(self, mock_config, mock_clients):
        """Test fetching recession indicators."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager._fetch_recession_indicators()

            # Check expected keys
            assert 'unemployment_claims' in data
            assert 'ism_pmi' in data
            assert 'yield_curve_10y2y' in data
            assert 'consumer_sentiment' in data

            # Verify FRED client was called
            assert fred_client.get_latest_value.called
            assert fred_client.calculate_velocity.called

    def test_fetch_credit_indicators(self, mock_config, mock_clients):
        """Test fetching credit indicators."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager._fetch_credit_indicators()

            # Check expected keys
            assert 'hy_spread' in data
            assert 'hy_spread_velocity_20d' in data
            assert 'ig_spread_bbb' in data
            assert 'ted_spread' in data

    def test_fetch_valuation_indicators(self, mock_config, mock_clients):
        """Test fetching valuation indicators."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager._fetch_valuation_indicators()

            # Check expected keys
            assert 'sp500_price' in data
            assert 'sp500_forward_pe' in data
            assert 'wilshire_5000' in data
            assert 'gdp' in data

            # Verify both clients were called
            assert fred_client.get_latest_value.called
            assert market_client.get_sp500_price.called

    def test_fetch_liquidity_indicators(self, mock_config, mock_clients):
        """Test fetching liquidity indicators."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager._fetch_liquidity_indicators()

            # Check expected keys
            assert 'fed_funds_rate' in data
            assert 'm2_money_supply' in data
            assert 'vix' in data

    def test_fetch_positioning_indicators(self, mock_config, mock_clients):
        """Test fetching positioning indicators (stubbed)."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager._fetch_positioning_indicators()

            # CFTC data is stubbed, so should have None values
            assert 'sp500_net_speculative' in data
            assert data['sp500_net_speculative'] is None

            # But should have VIX proxy
            assert 'vix_proxy' in data

    def test_graceful_failure_handling(self, mock_config):
        """Test that DataManager continues even if some indicators fail."""
        fred_client = MagicMock()
        market_client = MagicMock()

        # Make some calls return None (failure)
        fred_client.get_latest_value.return_value = None
        fred_client.get_moving_average.return_value = None
        fred_client.calculate_velocity.return_value = None
        market_client.get_sp500_price.return_value = None
        market_client.get_vix.return_value = None
        market_client.get_forward_pe.return_value = None

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)

            # Should not raise, even with failures
            data = manager.fetch_all_indicators()

            # Should still return data structure
            assert data is not None
            assert 'recession' in data
            assert 'metadata' in data

    def test_fetch_duration_tracking(self, mock_config, mock_clients):
        """Test that fetch duration is tracked."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)
            data = manager.fetch_all_indicators()

            # Duration should be tracked
            assert data['metadata']['fetch_duration_seconds'] >= 0
            assert isinstance(data['metadata']['fetch_duration_seconds'], float)

    def test_log_fetch_summary(self, mock_config, mock_clients):
        """Test that fetch summary is logged."""
        fred_client, market_client = mock_clients

        # Mix of successful and failed fetches
        fred_client.get_latest_value.side_effect = [100.0, None, 50.0, 75.0, None]

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)

            # Create sample data with some None values
            test_data = {
                'recession': {'ind1': 100.0, 'ind2': None, 'ind3': 50.0},
                'credit': {'ind4': None, 'ind5': 75.0}
            }

            # This should not raise
            manager._log_fetch_summary(test_data)

    def test_get_previous_value(self, mock_config):
        """Test getting previous value for detecting crosses."""
        import pandas as pd

        fred_client = MagicMock()
        market_client = MagicMock()

        # Create sample series with multiple values
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        series = pd.Series([45, 48, 51, 52, 49, 47, 50, 52, 51, 48], index=dates)
        fred_client.get_series.return_value = series

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)

            # Get previous value (should be second to last)
            prev_value = manager._get_previous_value('NAPM', periods_back=1)

            assert prev_value == 51.0  # Second to last value

    def test_get_previous_value_insufficient_data(self, mock_config):
        """Test getting previous value with insufficient data."""
        import pandas as pd

        fred_client = MagicMock()
        market_client = MagicMock()

        # Create very short series
        dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='D')
        series = pd.Series([50, 51], index=dates)
        fred_client.get_series.return_value = series

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):
            manager = DataManager(config=mock_config)

            # Try to get value 5 periods back with only 2 data points
            prev_value = manager._get_previous_value('NAPM', periods_back=5)

            assert prev_value is None
