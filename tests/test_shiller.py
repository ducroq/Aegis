"""
Unit tests for Shiller CAPE data scraper
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import requests

from src.data.shiller import ShillerDataClient


class TestShillerDataClient:
    """Test suite for Shiller CAPE scraper."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "shiller_cache"
        cache_dir.mkdir()
        return cache_dir

    @pytest.fixture
    def shiller_client(self, temp_cache_dir):
        """Create ShillerDataClient with temp cache."""
        return ShillerDataClient(cache_dir=str(temp_cache_dir))

    @pytest.fixture
    def mock_excel_data(self):
        """Create mock Excel data that mimics Shiller's format."""
        # Create sample data matching Shiller's structure
        data = {
            'Date': pd.date_range('2020-01', periods=12, freq='MS'),
            'S&P Composite': [3200 + i*50 for i in range(12)],
            'CAPE': [30.0 + i*0.5 for i in range(12)]
        }
        return pd.DataFrame(data)

    def test_initialization(self, temp_cache_dir):
        """Test ShillerDataClient initialization."""
        client = ShillerDataClient(cache_dir=str(temp_cache_dir))

        assert client.cache_dir == temp_cache_dir
        assert client.cache_dir.exists()

    def test_initialization_default_cache_dir(self):
        """Test initialization with default cache directory."""
        client = ShillerDataClient()

        # Should create cache dir in project/data/cache/shiller
        assert 'shiller' in str(client.cache_dir)

    def test_get_latest_cape_from_web(self, shiller_client, mock_excel_data, temp_cache_dir):
        """Test fetching CAPE from web successfully."""
        # Mock the requests.get call
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=mock_excel_data):

            cape = shiller_client.get_latest_cape(use_cache=False)

            assert cape is not None
            assert cape == 35.5  # Last value in mock data (30.0 + 11*0.5)

    def test_get_latest_cape_with_caching(self, shiller_client, mock_excel_data):
        """Test CAPE caching mechanism."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=mock_excel_data):

            # First call - should fetch from web
            cape1 = shiller_client.get_latest_cape(use_cache=True)
            assert cape1 == 35.5

            # Second call - should use cache (requests.get shouldn't be called again)
            with patch('requests.get', side_effect=Exception("Should not call API")) as mock_get:
                cape2 = shiller_client.get_latest_cape(use_cache=True, cache_ttl_days=7)
                assert cape2 == 35.5  # Same value from cache
                mock_get.assert_not_called()

    def test_cache_expiry(self, shiller_client, mock_excel_data):
        """Test that expired cache is refreshed."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=mock_excel_data):

            # First call - populate cache
            cape1 = shiller_client.get_latest_cape(use_cache=True)
            assert cape1 == 35.5

            # Manually expire the cache by setting old timestamp
            cache_file = shiller_client._get_cache_path()
            if cache_file.exists():
                old_time = (datetime.now() - timedelta(days=10)).timestamp()
                cache_file.touch()
                import os
                os.utime(str(cache_file), (old_time, old_time))

                # Should fetch fresh data
                cape2 = shiller_client.get_latest_cape(use_cache=True, cache_ttl_days=7)
                assert cape2 == 35.5

    def test_get_latest_cape_network_error(self, shiller_client):
        """Test handling of network errors."""
        with patch('requests.get', side_effect=requests.RequestException("Network error")):
            cape = shiller_client.get_latest_cape(use_cache=False)
            assert cape is None

    def test_get_latest_cape_parsing_error(self, shiller_client):
        """Test handling of Excel parsing errors."""
        mock_response = Mock()
        mock_response.content = b'invalid excel content'
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', side_effect=Exception("Parse error")):

            cape = shiller_client.get_latest_cape(use_cache=False)
            assert cape is None

    def test_get_latest_cape_no_cape_column(self, shiller_client):
        """Test handling when CAPE column is missing."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        # DataFrame without CAPE column
        bad_data = pd.DataFrame({
            'Date': pd.date_range('2020-01', periods=12, freq='MS'),
            'S&P Composite': [3200 + i*50 for i in range(12)]
        })

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=bad_data):

            cape = shiller_client.get_latest_cape(use_cache=False)
            assert cape is None

    def test_get_latest_cape_empty_dataframe(self, shiller_client):
        """Test handling of empty dataframe."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        # Empty DataFrame
        empty_data = pd.DataFrame({
            'Date': [],
            'CAPE': []
        })

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=empty_data):

            cape = shiller_client.get_latest_cape(use_cache=False)
            assert cape is None

    def test_cache_path_generation(self, shiller_client):
        """Test cache file path generation."""
        cache_path = shiller_client._get_cache_path()

        assert cache_path.parent == shiller_client.cache_dir
        assert cache_path.name == 'cape_latest.txt'

    def test_save_and_load_cache(self, shiller_client):
        """Test cache save and load functionality."""
        test_cape = 32.45

        # Save to cache
        shiller_client._save_to_cache(test_cape)

        # Load from cache
        loaded_cape = shiller_client._load_from_cache(ttl_days=7)

        assert loaded_cape == test_cape

    def test_load_cache_file_not_exists(self, shiller_client):
        """Test loading cache when file doesn't exist."""
        loaded_cape = shiller_client._load_from_cache(ttl_days=7)
        assert loaded_cape is None

    def test_load_cache_corrupted_file(self, shiller_client):
        """Test loading corrupted cache file."""
        # Create corrupted cache file
        cache_file = shiller_client._get_cache_path()
        with open(cache_file, 'w') as f:
            f.write("not a number")

        loaded_cape = shiller_client._load_from_cache(ttl_days=7)
        assert loaded_cape is None

    def test_alternative_cape_column_names(self, shiller_client):
        """Test that alternative CAPE column names are recognized."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        # Try 'Cyclically Adjusted PE Ratio' column name
        alt_data = pd.DataFrame({
            'Date': pd.date_range('2020-01', periods=12, freq='MS'),
            'Cyclically Adjusted PE Ratio': [30.0 + i*0.5 for i in range(12)]
        })

        with patch('requests.get', return_value=mock_response), \
             patch('pandas.read_excel', return_value=alt_data):

            cape = shiller_client.get_latest_cape(use_cache=False)
            assert cape == 35.5  # Should find the alternative column name

    def test_fetch_with_timeout(self, shiller_client):
        """Test that timeout is set for requests."""
        mock_response = Mock()
        mock_response.content = b'mock excel content'
        mock_response.raise_for_status = Mock()

        mock_excel_data = pd.DataFrame({
            'Date': pd.date_range('2020-01', periods=12, freq='MS'),
            'CAPE': [30.0 + i*0.5 for i in range(12)]
        })

        with patch('requests.get', return_value=mock_response) as mock_get, \
             patch('pandas.read_excel', return_value=mock_excel_data):

            shiller_client.get_latest_cape(use_cache=False)

            # Verify timeout was passed to requests.get
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] == 30
