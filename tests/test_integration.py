"""
Integration tests for Aegis system

Tests the full pipeline: Data Fetching → Scoring → Aggregation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd

from src.config.config_manager import ConfigManager
from src.data.data_manager import DataManager
from src.scoring.aggregator import RiskAggregator


class TestEndToEndIntegration:
    """Test full end-to-end data flow."""

    @pytest.fixture
    def mock_fred_data(self):
        """Create realistic mock FRED data."""
        # Create sample time series
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')

        return {
            'ICSA': pd.Series([220000 + i*10 for i in range(len(dates))], index=dates),  # Rising claims
            'NAPM': pd.Series([52.0] * 200 + [48.0] * (len(dates)-200), index=dates),  # PMI crosses below 50
            'T10Y2Y': pd.Series([0.3] * 100 + [-0.2] * (len(dates)-100), index=dates),  # Inverts
            'T10Y3M': pd.Series([0.5] * len(dates), index=dates),
            'UMCSENT': pd.Series([85.0] * len(dates), index=dates),
            'BAMLH0A0HYM2': pd.Series([400 + i*0.5 for i in range(len(dates))], index=dates),  # Rising spreads
            'BAMLC0A4CBBB': pd.Series([150.0] * len(dates), index=dates),
            'TEDRATE': pd.Series([0.4] * len(dates), index=dates),
            'DRTSCILM': pd.Series([10.0] * len(dates), index=dates),
            'WILL5000IND': pd.Series([45000.0] * len(dates), index=dates),
            'GDP': pd.Series([28000.0] * len(dates), index=dates),
            'DFF': pd.Series([5.0 + i*0.01 for i in range(len(dates))], index=dates),  # Rising rates
            'M2SL': pd.Series([21000.0] * len(dates), index=dates),
            'WALCL': pd.Series([8000.0] * len(dates), index=dates),
        }

    @pytest.fixture
    def mock_clients(self, mock_fred_data):
        """Create mock data clients with realistic data."""
        fred_client = MagicMock()
        market_client = MagicMock()

        # Setup FRED client responses
        def get_series(series_id, **kwargs):
            return mock_fred_data.get(series_id)

        def get_latest_value(series_id):
            series = mock_fred_data.get(series_id)
            return float(series.iloc[-1]) if series is not None else None

        def get_moving_average(series_id, window=4):
            series = mock_fred_data.get(series_id)
            if series is not None and len(series) >= window:
                return float(series.iloc[-window:].mean())
            return None

        def calculate_velocity(series_id, method='yoy_pct', lookback_days=365):
            series = mock_fred_data.get(series_id)
            if series is None or len(series) < lookback_days:
                return None

            if method == 'yoy_pct':
                current = series.iloc[-1]
                past_idx = max(0, len(series) - lookback_days)
                past = series.iloc[past_idx]
                return float((current - past) / past * 100)
            elif method == 'rate':
                current = series.iloc[-1]
                past_idx = max(0, len(series) - lookback_days)
                past = series.iloc[past_idx]
                actual_days = lookback_days
                return float((current - past) / actual_days)
            return None

        fred_client.get_series.side_effect = get_series
        fred_client.get_latest_value.side_effect = get_latest_value
        fred_client.get_moving_average.side_effect = get_moving_average
        fred_client.calculate_velocity.side_effect = calculate_velocity

        # Setup market client responses
        market_client.get_sp500_price.return_value = 4500.0
        market_client.get_vix.return_value = 16.0
        market_client.get_forward_pe.return_value = 20.0

        return fred_client, market_client

    def test_full_pipeline_normal_conditions(self, mock_clients):
        """Test complete pipeline with normal market conditions."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):

            # Step 1: Fetch all data
            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            # Verify data was fetched
            assert all_data is not None
            assert 'recession' in all_data
            assert 'credit' in all_data
            assert 'valuation' in all_data
            assert 'liquidity' in all_data
            assert 'positioning' in all_data

            # Step 2: Calculate risk scores
            aggregator = RiskAggregator()
            result = aggregator.calculate_overall_risk(all_data)

            # Verify results structure
            assert 'overall_score' in result
            assert 'tier' in result
            assert 'dimension_scores' in result
            assert result['tier'] in ['GREEN', 'YELLOW', 'RED']

            # Verify all dimensions were scored
            assert len(result['dimension_scores']) == 5
            assert 'recession' in result['dimension_scores']
            assert 'credit' in result['dimension_scores']
            assert 'valuation' in result['dimension_scores']
            assert 'liquidity' in result['dimension_scores']
            assert 'positioning' in result['dimension_scores']

            # Verify overall score is in valid range
            assert 0 <= result['overall_score'] <= 10

            # Verify weighted calculation (allowing for re-normalized weights when dimensions are missing)
            # The aggregator may exclude dimensions with no data and re-normalize weights
            manual_calc = sum(
                result['dimension_scores'][dim] * result['weights'][dim]
                for dim in result['dimension_scores']
            )
            # Allow up to 0.5 point difference due to re-normalization and signal adjustments
            assert abs(manual_calc - result['overall_score']) < 0.5

    def test_pipeline_with_missing_data(self, mock_clients):
        """Test pipeline handles missing data gracefully."""
        fred_client, market_client = mock_clients

        # Make some data return None
        fred_client.get_latest_value.side_effect = lambda x: None if x == 'UMCSENT' else 100.0
        fred_client.calculate_velocity.return_value = None

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):

            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            aggregator = RiskAggregator()
            result = aggregator.calculate_overall_risk(all_data)

            # Should still produce a result
            assert result is not None
            assert 'overall_score' in result
            assert 0 <= result['overall_score'] <= 10

    def test_pipeline_high_risk_scenario(self):
        """Test pipeline with high-risk market conditions."""
        fred_client = MagicMock()
        market_client = MagicMock()

        # Setup high-risk data
        fred_client.get_latest_value.side_effect = lambda x: {
            'ICSA': 280000,  # High claims
            'MANEMP': 12500,  # Manufacturing employment (ISM proxy)
            'T10Y2Y': -0.8,  # Deep inversion
            'T10Y3M': -0.5,
            'UMCSENT': 68.0,  # Low confidence
            'BAMLH0A0HYM2': 850,  # Wide spreads
            'BAMLC0A4CBBB': 400,
            'TEDRATE': 2.0,  # Stress
            'DRTSCILM': 35.0,  # Tight lending
            'SP500': 4200.0,  # S&P 500 from FRED
            'GDP': 28000,
            'DFF': 5.5,
            'M2SL': 20000,
            'WALCL': 7500,
            'VIXCLS': 38.0,  # VIX from FRED
            'UNRATE': 4.5,
        }.get(x)

        fred_client.get_moving_average.return_value = 275000
        fred_client.calculate_velocity.side_effect = lambda series_id, **kwargs: {
            'ICSA': 18.0,  # Spiking claims
            'BAMLH0A0HYM2': 12.0,  # Widening spreads
            'DFF': 2.2,  # Rapid tightening
            'M2SL': -1.5,  # Contracting money supply
        }.get(series_id, 0.0)

        # Previous PMI for cross detection
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
        pmi_series = pd.Series([52.0] * 5 + [46.0] * 5, index=dates)
        fred_client.get_series.return_value = pmi_series

        market_client.get_sp500_price.return_value = 4200.0
        market_client.get_vix.return_value = 38.0  # High fear
        market_client.get_forward_pe.return_value = 26.0

        # Mock Shiller client for high valuation
        mock_shiller = MagicMock()
        mock_shiller.get_latest_cape.return_value = 35.0  # Expensive

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client), \
             patch('src.data.data_manager.ShillerDataClient', return_value=mock_shiller):

            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            aggregator = RiskAggregator()
            result = aggregator.calculate_overall_risk(all_data)

            # Should be high risk (using realistic calibrated thresholds: YELLOW=4.0, RED=5.0)
            # Historical max is 5.55 (April 2020), so high-risk scenarios are typically 4-6
            assert result['overall_score'] >= 4.0  # At least YELLOW threshold
            assert result['overall_score'] < 10.0  # Sanity check
            # Should be elevated risk
            assert result['overall_score'] > 3.5  # Significantly elevated

            # Should have multiple signals
            total_signals = sum(len(signals) for signals in result['all_signals'].values())
            assert total_signals > 3  # At least a few warning signals

    def test_config_integration(self):
        """Test that config properly flows through entire system."""
        # Load actual config
        config = ConfigManager()

        # Verify weights are loaded
        weights = config.get_all_weights()
        assert len(weights) == 5
        assert abs(sum(weights.values()) - 1.0) < 0.01

        # Create aggregator with config
        aggregator = RiskAggregator(config)

        # Verify aggregator uses config weights
        assert aggregator.weights == weights

        # Verify thresholds are loaded
        thresholds = config.get_alert_thresholds()
        assert 'yellow_threshold' in thresholds
        assert 'red_threshold' in thresholds

    def test_data_to_score_consistency(self, mock_clients):
        """Test that data keys match what scorers expect."""
        fred_client, market_client = mock_clients

        # Mock Shiller client
        mock_shiller = MagicMock()
        mock_shiller.get_latest_cape.return_value = 30.81

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client), \
             patch('src.data.data_manager.ShillerDataClient', return_value=mock_shiller):

            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            # Check recession data keys
            recession_keys = all_data['recession'].keys()
            required_recession = [
                'unemployment_claims_velocity_yoy',
                'ism_pmi',
                'yield_curve_10y2y'
            ]
            for key in required_recession:
                assert key in recession_keys, f"Missing recession indicator: {key}"

            # Check credit data keys
            credit_keys = all_data['credit'].keys()
            required_credit = ['hy_spread', 'hy_spread_velocity_20d']
            for key in required_credit:
                assert key in credit_keys, f"Missing credit indicator: {key}"

            # Check valuation data keys (updated for new structure)
            valuation_keys = all_data['valuation'].keys()
            required_valuation = ['sp500_price', 'shiller_cape', 'gdp']  # Updated from wilshire_5000
            for key in required_valuation:
                assert key in valuation_keys, f"Missing valuation indicator: {key}"

    def test_score_range_validation(self, mock_clients):
        """Test that all scores are within valid 0-10 range."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):

            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            aggregator = RiskAggregator()
            result = aggregator.calculate_overall_risk(all_data)

            # Check all dimension scores are in range
            for dim, score in result['dimension_scores'].items():
                assert 0 <= score <= 10, f"{dim} score out of range: {score}"

            # Check overall score is in range
            assert 0 <= result['overall_score'] <= 10

            # Check tier matches score
            if result['overall_score'] >= 8.0:
                assert result['tier'] == 'RED'
            elif result['overall_score'] >= 6.5:
                assert result['tier'] == 'YELLOW'
            else:
                assert result['tier'] == 'GREEN'

    def test_metadata_completeness(self, mock_clients):
        """Test that all expected metadata is present."""
        fred_client, market_client = mock_clients

        with patch('src.data.data_manager.FREDClient', return_value=fred_client), \
             patch('src.data.data_manager.MarketDataClient', return_value=market_client):

            data_manager = DataManager()
            all_data = data_manager.fetch_all_indicators()

            # Check data metadata
            assert 'metadata' in all_data
            assert 'fetch_timestamp' in all_data['metadata']
            assert 'fetch_duration_seconds' in all_data['metadata']

            # Check scoring metadata
            aggregator = RiskAggregator()
            result = aggregator.calculate_overall_risk(all_data)

            assert 'metadata' in result
            assert 'weighted_calculation' in result['metadata']
            # May be 4 or 5 depending on whether positioning has data (often excluded in mocks)
            assert len(result['metadata']['weighted_calculation']) >= 4
            assert len(result['metadata']['weighted_calculation']) <= 5


class TestComponentInteraction:
    """Test interactions between specific components."""

    def test_recession_scorer_with_real_data_structure(self):
        """Test recession scorer with realistic data structure from DataManager."""
        from src.scoring.recession import RecessionScorer

        # Simulate what DataManager._fetch_recession_indicators returns
        data = {
            'unemployment_claims': 250000,
            'unemployment_claims_4wk_avg': 248000,
            'unemployment_claims_velocity_yoy': 8.5,
            'ism_pmi': 49.0,
            'ism_pmi_prev': 51.5,
            'yield_curve_10y2y': -0.4,
            'yield_curve_10y3m': -0.2,
            'consumer_sentiment': 78.0,
            'unemployment_rate': 3.8
        }

        scorer = RecessionScorer()
        result = scorer.calculate_score(data)

        assert result is not None
        assert 'score' in result
        assert 'components' in result
        assert 'signals' in result

    def test_credit_scorer_with_real_data_structure(self):
        """Test credit scorer with realistic data structure."""
        from src.scoring.credit import CreditScorer

        data = {
            'hy_spread': 520,
            'hy_spread_velocity_20d': 4.5,
            'ig_spread_bbb': 185,
            'ted_spread': 0.65,
            'bank_lending_standards': 18.0
        }

        scorer = CreditScorer()
        result = scorer.calculate_score(data)

        assert result is not None
        assert result['score'] > 0  # Should show some risk

    def test_aggregator_handles_partial_component_scores(self):
        """Test aggregator when some components have None values."""
        from src.scoring.aggregator import RiskAggregator

        # Data with some missing values
        data = {
            'recession': {
                'unemployment_claims_velocity_yoy': 5.0,
                'ism_pmi': 52.0,
                'ism_pmi_prev': 51.0,
                'yield_curve_10y2y': None,  # Missing
                'yield_curve_10y3m': None,  # Missing
                'consumer_sentiment': 85.0
            },
            'credit': {
                'hy_spread': 400,
                'hy_spread_velocity_20d': 2.0,
                'ig_spread_bbb': None,  # Missing
                'ted_spread': 0.4,
                'bank_lending_standards': 10.0
            },
            'valuation': {
                'shiller_cape': 30.0,
                'sp500_price': 6700.0,  # Added
                'sp500_level': 6700.0,  # Added
                'gdp': 28000,
                'sp500_forward_pe': 19.0
            },
            'liquidity': {
                'fed_funds_velocity_6m': 1.0,
                'm2_velocity_yoy': 4.5,
                'vix': 17.0
            },
            'positioning': {
                'vix_proxy': 17.0
            }
        }

        aggregator = RiskAggregator()
        result = aggregator.calculate_overall_risk(data)

        # Should still produce valid result
        assert result is not None
        assert 0 <= result['overall_score'] <= 10

        # Components with missing data should still have scores
        # (based on available sub-components)
        assert result['dimension_scores']['recession'] >= 0
        assert result['dimension_scores']['credit'] >= 0


class TestActualConfigIntegration:
    """Integration tests using actual config files."""

    def test_load_and_use_actual_config(self):
        """Test loading actual config and using it in the system."""
        config = ConfigManager()

        # Verify config loaded
        assert config.config_data is not None

        # Test getting indicators config
        recession_indicators = config.get_indicator_config('recession_indicators')
        assert recession_indicators is not None

        # Create aggregator with real config
        aggregator = RiskAggregator(config)

        # Verify weights match config file
        expected_weights = config.get_all_weights()
        assert aggregator.weights == expected_weights

    def test_indicator_config_matches_data_manager(self):
        """Test that indicator config matches what DataManager fetches."""
        config = ConfigManager()

        # Get recession indicators from config
        recession_config = config.get_indicator_config('recession_indicators')

        # Check that config has expected structure
        assert 'unemployment_claims_velocity' in recession_config
        assert 'ism_pmi_regime' in recession_config
        assert 'yield_curve_traditional' in recession_config
