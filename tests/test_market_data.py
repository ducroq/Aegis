"""
Unit tests for Market Data Client (Yahoo Finance)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

from src.data.market_data import MarketDataClient


class TestMarketDataClient:
    """Test suite for MarketDataClient."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "yahoo_cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture
    def market_client(self, temp_cache_dir):
        """Create MarketDataClient with temp cache."""
        with patch('src.data.market_data.ConfigManager'):
            return MarketDataClient(cache_dir=str(temp_cache_dir))

    @pytest.fixture
    def mock_ticker_data(self):
        """Create mock ticker historical data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'Open': [4500 + i for i in range(100)],
            'High': [4550 + i for i in range(100)],
            'Low': [4450 + i for i in range(100)],
            'Close': [4500 + i for i in range(100)],
            'Volume': [1000000] * 100
        }, index=dates)
        return data

    def test_initialization(self, temp_cache_dir):
        """Test MarketDataClient initialization."""
        with patch('src.data.market_data.ConfigManager'):
            client = MarketDataClient(cache_dir=str(temp_cache_dir))
            assert client.cache_dir == temp_cache_dir
            assert client.cache_dir.exists()

    def test_initialization_default_cache_dir(self):
        """Test initialization with default cache directory."""
        with patch('src.data.market_data.ConfigManager'):
            client = MarketDataClient()
            assert 'yahoo' in str(client.cache_dir)

    def test_initialization_missing_yfinance(self, temp_cache_dir):
        """Test initialization fails gracefully without yfinance."""
        with patch('src.data.market_data.ConfigManager'), \
             patch('src.data.market_data.yf', None):
            with pytest.raises(ImportError, match="yfinance library not installed"):
                MarketDataClient(cache_dir=str(temp_cache_dir))

    def test_get_ticker_data_success(self, market_client, mock_ticker_data):
        """Test fetching ticker data successfully."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            data = market_client.get_ticker_data('^GSPC', period='1y', use_cache=False)

            assert data is not None
            assert len(data) == 100
            assert 'Close' in data.columns
            mock_ticker.history.assert_called_once_with(period='1y')

    def test_get_ticker_data_with_caching(self, market_client, mock_ticker_data):
        """Test ticker data caching mechanism."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            # First call - should fetch from API
            data1 = market_client.get_ticker_data('^GSPC', period='1y', use_cache=True)
            assert data1 is not None
            assert mock_ticker.history.call_count == 1

            # Second call - should use cache
            data2 = market_client.get_ticker_data('^GSPC', period='1y', use_cache=True, cache_ttl_hours=24)
            assert data2 is not None
            # history() should still be called only once (cached)
            assert mock_ticker.history.call_count == 1

    def test_get_ticker_data_cache_expiry(self, market_client, mock_ticker_data):
        """Test that expired cache is refreshed."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            # First call - populate cache
            data1 = market_client.get_ticker_data('^GSPC', period='1y', use_cache=True)
            assert data1 is not None

            # Manually expire the cache
            cache_file = market_client._get_cache_path('^GSPC', '1y')
            if cache_file.exists():
                old_time = (datetime.now() - timedelta(hours=25)).timestamp()
                import os
                os.utime(str(cache_file), (old_time, old_time))

                # Should fetch fresh data
                data2 = market_client.get_ticker_data('^GSPC', period='1y', use_cache=True, cache_ttl_hours=6)
                assert data2 is not None
                assert mock_ticker.history.call_count == 2  # Called again after expiry

    def test_get_ticker_data_no_data(self, market_client):
        """Test handling when no data is returned."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty

        with patch('yfinance.Ticker', return_value=mock_ticker):
            data = market_client.get_ticker_data('INVALID', use_cache=False)
            assert data is None

    def test_get_ticker_data_api_error(self, market_client):
        """Test handling of API errors."""
        mock_ticker = Mock()
        mock_ticker.history.side_effect = Exception("API Error")

        with patch('yfinance.Ticker', return_value=mock_ticker):
            data = market_client.get_ticker_data('^GSPC', use_cache=False)
            assert data is None

    def test_get_latest_price(self, market_client, mock_ticker_data):
        """Test getting latest closing price."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            price = market_client.get_latest_price('^GSPC')
            assert price is not None
            assert price == 4599.0  # Last close in mock data

    def test_get_latest_price_no_data(self, market_client):
        """Test get_latest_price with no data."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = None

        with patch('yfinance.Ticker', return_value=mock_ticker):
            price = market_client.get_latest_price('^GSPC')
            assert price is None

    def test_get_vix(self, market_client, mock_ticker_data):
        """Test getting VIX volatility index."""
        # Adjust mock data for VIX range (10-30 typical)
        vix_data = mock_ticker_data.copy()
        vix_data['Close'] = [15.0 + i*0.1 for i in range(100)]

        mock_ticker = Mock()
        mock_ticker.history.return_value = vix_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            vix = market_client.get_vix()
            assert vix is not None
            assert 10 < vix < 30  # Reasonable VIX range

    def test_get_sp500_price(self, market_client, mock_ticker_data):
        """Test getting S&P 500 price."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_ticker_data

        with patch('yfinance.Ticker', return_value=mock_ticker):
            sp500 = market_client.get_sp500_price()
            assert sp500 is not None
            assert sp500 > 4000  # Sanity check

    def test_get_forward_pe_with_forward_pe_key(self, market_client):
        """Test get_forward_pe when forwardPE is available."""
        mock_ticker = Mock()
        mock_ticker.info = {'forwardPE': 19.5}

        with patch('yfinance.Ticker', return_value=mock_ticker):
            pe = market_client.get_forward_pe('^GSPC')
            assert pe == 19.5

    def test_get_forward_pe_with_forward_eps(self, market_client):
        """Test get_forward_pe calculated from forwardEps and price."""
        mock_ticker = Mock()
        mock_ticker.info = {
            'forwardEps': 250.0,
            'price': 5000.0
        }

        with patch('yfinance.Ticker', return_value=mock_ticker):
            pe = market_client.get_forward_pe('^GSPC')
            assert pe == 20.0  # 5000 / 250

    def test_get_forward_pe_fallback_to_trailing(self, market_client):
        """Test get_forward_pe falls back to trailingPE."""
        mock_ticker = Mock()
        mock_ticker.info = {'trailingPE': 22.5}

        with patch('yfinance.Ticker', return_value=mock_ticker):
            pe = market_client.get_forward_pe('^GSPC')
            assert pe == 22.5

    def test_get_forward_pe_not_available(self, market_client):
        """Test get_forward_pe when no P/E data available."""
        mock_ticker = Mock()
        mock_ticker.info = {}

        with patch('yfinance.Ticker', return_value=mock_ticker):
            pe = market_client.get_forward_pe('^GSPC')
            assert pe is None

    def test_get_forward_pe_api_error(self, market_client):
        """Test get_forward_pe with API error."""
        mock_ticker = Mock()
        mock_ticker.info.side_effect = Exception("API Error")

        with patch('yfinance.Ticker', return_value=mock_ticker):
            pe = market_client.get_forward_pe('^GSPC')
            assert pe is None

    def test_get_sector_rotation_signal(self, market_client):
        """Test sector rotation signal calculation."""
        # Mock data for different sectors
        def create_sector_data(start_price, end_price):
            dates = pd.date_range('2024-01-01', periods=90, freq='D')
            prices = [start_price + (end_price - start_price) * i / 90 for i in range(90)]
            return pd.DataFrame({
                'Close': prices,
                'Volume': [1000000] * 90
            }, index=dates)

        # Defensive sectors up, cyclical down (risk-off)
        sector_data = {
            'XLV': create_sector_data(100, 110),  # Healthcare +10%
            'XLP': create_sector_data(100, 108),  # Staples +8%
            'XLU': create_sector_data(100, 106),  # Utilities +6%
            'XLY': create_sector_data(100, 95),   # Discretionary -5%
            'XLI': create_sector_data(100, 97),   # Industrials -3%
            'XLF': create_sector_data(100, 94),   # Financials -6%
        }

        def mock_ticker_factory(ticker):
            mock = Mock()
            mock.history.return_value = sector_data.get(ticker, pd.DataFrame())
            return mock

        with patch('yfinance.Ticker', side_effect=mock_ticker_factory):
            result = market_client.get_sector_rotation_signal()

            assert result is not None
            assert 'rotation_signal' in result

            rotation = result['rotation_signal']
            assert 'defensive_avg' in rotation
            assert 'cyclical_avg' in rotation
            assert 'spread' in rotation

            # Defensive should be positive, cyclical negative
            assert rotation['defensive_avg'] > 0
            assert rotation['cyclical_avg'] < 0
            # Spread should be positive (defensive outperforming)
            assert rotation['spread'] > 0

    def test_get_sector_rotation_signal_error(self, market_client):
        """Test sector rotation with API error."""
        # When get_ticker_data returns None for all tickers, we get empty results
        with patch.object(market_client, 'get_ticker_data', return_value=None):
            result = market_client.get_sector_rotation_signal()
            # Function returns dict with zeros rather than None on error
            assert result is not None
            assert 'rotation_signal' in result
            assert result['rotation_signal']['defensive_avg'] == 0.0

    def test_get_market_cap_to_gdp(self, market_client):
        """Test market cap to GDP (currently returns None, requires FRED)."""
        result = market_client.get_market_cap_to_gdp()
        assert result is None

    def test_cache_path_generation(self, market_client):
        """Test cache file path generation."""
        cache_path = market_client._get_cache_path('^GSPC', '1y')
        assert cache_path.parent == market_client.cache_dir
        assert '_GSPC_1y.csv' in str(cache_path)

    def test_cache_path_special_characters(self, market_client):
        """Test cache path handles special characters."""
        cache_path = market_client._get_cache_path('^VIX', '6mo')
        # Caret should be replaced with underscore
        assert '^' not in str(cache_path)
        assert '_VIX_6mo.csv' in str(cache_path)

    def test_load_cache_file_not_exists(self, market_client):
        """Test loading cache when file doesn't exist."""
        loaded_data = market_client._load_from_cache('^NONEXISTENT', '1y', ttl_hours=24)
        assert loaded_data is None

    def test_save_and_load_cache(self, market_client, mock_ticker_data):
        """Test cache save and load functionality."""
        # Save to cache
        market_client._save_to_cache('^GSPC', '1y', mock_ticker_data)

        # Load from cache
        loaded_data = market_client._load_from_cache('^GSPC', '1y', ttl_hours=24)

        assert loaded_data is not None
        assert len(loaded_data) == len(mock_ticker_data)
        assert list(loaded_data.columns) == list(mock_ticker_data.columns)
