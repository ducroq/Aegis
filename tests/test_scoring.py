"""
Unit tests for scoring modules
"""

import pytest
from src.scoring.recession import RecessionScorer
from src.scoring.credit import CreditScorer
from src.scoring.valuation import ValuationScorer
from src.scoring.liquidity import LiquidityScorer
from src.scoring.positioning import PositioningScorer
from src.scoring.aggregator import RiskAggregator


class TestRecessionScorer:
    """Tests for RecessionScorer."""

    @pytest.fixture
    def scorer(self):
        return RecessionScorer()

    def test_normal_conditions(self, scorer):
        """Test scoring under normal economic conditions."""
        indicators = {
            'unemployment_claims_velocity_yoy': 2.0,
            'ism_pmi': 54.0,
            'ism_pmi_prev': 53.5,
            'yield_curve_10y2y': 0.3,
            'yield_curve_10y3m': 0.5,
            'consumer_sentiment': 95.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 0.0
        assert result['components']['unemployment_velocity'] == 0.0
        assert result['components']['pmi_regime'] == 0.0
        assert len(result['signals']) == 0

    def test_recession_warning_conditions(self, scorer):
        """Test scoring under recession warning conditions."""
        indicators = {
            'unemployment_claims_velocity_yoy': 12.0,  # Spiking
            'ism_pmi': 48.5,  # Contraction
            'ism_pmi_prev': 51.0,  # Just crossed
            'yield_curve_10y2y': -0.6,  # Inverted
            'yield_curve_10y3m': -0.4,
            'consumer_sentiment': 72.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] > 7.0  # Should be high risk
        assert result['components']['unemployment_velocity'] == 2.0
        assert result['components']['pmi_regime'] == 3.0
        assert len(result['signals']) > 0

    def test_unemployment_velocity_scoring(self, scorer):
        """Test unemployment velocity scoring thresholds."""
        # Extreme spike
        score, signal = scorer._score_unemployment_velocity(20.0)
        assert score == 4.0
        assert 'CRITICAL' in signal

        # Moderate spike
        score, signal = scorer._score_unemployment_velocity(10.0)
        assert score == 2.0
        assert 'WARNING' in signal

        # Rising
        score, signal = scorer._score_unemployment_velocity(5.0)
        assert score == 1.0
        assert 'WATCH' in signal

        # Stable
        score, signal = scorer._score_unemployment_velocity(1.0)
        assert score == 0.0

    def test_pmi_regime_cross(self, scorer):
        """Test PMI regime cross detection."""
        # Cross into contraction
        score, signal = scorer._score_pmi_regime(48.0, 51.0)
        assert score == 3.0
        assert 'CRITICAL' in signal

        # Already in deep contraction
        score, signal = scorer._score_pmi_regime(42.0, 43.0)
        assert score == 2.5

        # Healthy expansion
        score, signal = scorer._score_pmi_regime(55.0, 54.0)
        assert score == 0.0

    def test_yield_curve_inversion(self, scorer):
        """Test yield curve inversion scoring."""
        # Dual deep inversion
        score, signal = scorer._score_yield_curve(-1.0, -0.5)
        assert score >= 2.0  # Should be at least 2.0 (capped at 2.0 total)
        assert 'CRITICAL' in signal

        # Normal (positive spreads)
        score, signal = scorer._score_yield_curve(0.5, 0.8)
        assert score == 0.0

    def test_missing_data_handling(self, scorer):
        """Test that missing data is handled gracefully."""
        indicators = {
            'unemployment_claims_velocity_yoy': None,
            'ism_pmi': 50.0,
            'ism_pmi_prev': None,
            'yield_curve_10y2y': None,
            'yield_curve_10y3m': None,
            'consumer_sentiment': None
        }
        result = scorer.calculate_score(indicators)

        # Should not raise, should return partial score
        assert result['score'] >= 0
        assert result['components']['unemployment_velocity'] is None
        assert result['components']['pmi_regime'] is not None


class TestCreditScorer:
    """Tests for CreditScorer."""

    @pytest.fixture
    def scorer(self):
        return CreditScorer()

    def test_normal_conditions(self, scorer):
        """Test scoring under normal credit conditions."""
        indicators = {
            'hy_spread': 350,
            'hy_spread_velocity_20d': 1.0,
            'ig_spread_bbb': 120,
            'ted_spread': 0.3,
            'bank_lending_standards': 5.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 0.0
        assert len(result['signals']) == 0

    def test_crisis_conditions(self, scorer):
        """Test scoring under credit crisis conditions."""
        indicators = {
            'hy_spread': 900,
            'hy_spread_velocity_20d': 15.0,
            'ig_spread_bbb': 450,
            'ted_spread': 2.5,
            'bank_lending_standards': 40.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] > 8.0  # Should be very high
        assert len(result['signals']) >= 3

    def test_hy_spread_velocity_weighting(self, scorer):
        """Test that HY spread velocity is weighted more than level."""
        # High velocity, normal level
        score1, _ = scorer._score_hy_spread(350, 12.0)

        # Normal velocity, high level
        score2, _ = scorer._score_hy_spread(800, 1.0)

        # Velocity should contribute more to score
        assert score1 > score2

    def test_hy_spread_scoring(self, scorer):
        """Test HY spread scoring thresholds."""
        # Rapid widening
        score, signal = scorer._score_hy_spread(500, 12.0)
        assert score > 4.0
        assert 'CRITICAL' in signal or 'WARNING' in signal

        # Stable, normal level
        score, signal = scorer._score_hy_spread(350, 0.5)
        assert score == 0.0

    def test_ted_spread_crisis_levels(self, scorer):
        """Test TED spread at 2008 crisis levels."""
        score, signal = scorer._score_ted_spread(2.5)
        assert score == 1.0
        assert 'CRITICAL' in signal


class TestValuationScorer:
    """Tests for ValuationScorer."""

    @pytest.fixture
    def scorer(self):
        return ValuationScorer()

    def test_normal_valuations(self, scorer):
        """Test scoring with normal valuations."""
        indicators = {
            'shiller_cape': 18.0,
            'wilshire_5000': 28000,
            'gdp': 28000,  # 100% ratio
            'sp500_forward_pe': 18.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] <= 1.0

    def test_bubble_valuations(self, scorer):
        """Test scoring with bubble-level valuations."""
        indicators = {
            'shiller_cape': 38.0,  # Dot-com levels
            'wilshire_5000': 60000,
            'gdp': 28000,  # >200% ratio
            'sp500_forward_pe': 28.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] > 8.0
        assert len(result['signals']) >= 2

    def test_missing_cape(self, scorer):
        """Test handling when CAPE is missing."""
        indicators = {
            'shiller_cape': None,
            'wilshire_5000': 28000,
            'gdp': 28000,
            'sp500_forward_pe': 18.0
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['cape'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_missing_buffett_indicator(self, scorer):
        """Test handling when Buffett indicator data is missing."""
        indicators = {
            'shiller_cape': 25.0,
            'wilshire_5000': None,
            'gdp': None,
            'sp500_forward_pe': 18.0
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['buffett_indicator'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_missing_forward_pe(self, scorer):
        """Test handling when forward P/E is missing."""
        indicators = {
            'shiller_cape': 25.0,
            'wilshire_5000': 28000,
            'gdp': 28000,
            'sp500_forward_pe': None
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['forward_pe'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_cape_scoring(self, scorer):
        """Test CAPE ratio scoring."""
        # Bubble levels
        score, signal = scorer._score_cape(38.0)
        assert score == 4.0
        assert 'CRITICAL' in signal

        # Normal levels
        score, signal = scorer._score_cape(17.0)
        assert score == 0.0

    def test_buffett_indicator(self, scorer):
        """Test Buffett Indicator (Market Cap / GDP)."""
        # Extreme overvaluation (>200%)
        score, signal = scorer._score_buffett_indicator(60000, 28000)
        assert score == 4.0
        assert 'CRITICAL' in signal

        # Fair value (~100%)
        score, signal = scorer._score_buffett_indicator(28000, 28000)
        assert score == 0.0


class TestLiquidityScorer:
    """Tests for LiquidityScorer."""

    @pytest.fixture
    def scorer(self):
        return LiquidityScorer()

    def test_normal_liquidity(self, scorer):
        """Test scoring under normal liquidity conditions."""
        indicators = {
            'fed_funds_velocity_6m': 0.3,
            'm2_velocity_yoy': 6.0,
            'vix': 15.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] <= 1.0

    def test_tight_liquidity(self, scorer):
        """Test scoring under tight liquidity conditions."""
        indicators = {
            'fed_funds_velocity_6m': 2.5,  # Rapid tightening
            'm2_velocity_yoy': -1.0,  # Contracting
            'vix': 35.0  # Fear
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] > 7.0

    def test_missing_fed_velocity(self, scorer):
        """Test handling when Fed funds velocity is missing."""
        indicators = {
            'fed_funds_velocity_6m': None,
            'm2_velocity_yoy': 5.0,
            'vix': 15.0
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['fed_trajectory'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_missing_m2_velocity(self, scorer):
        """Test handling when M2 velocity is missing."""
        indicators = {
            'fed_funds_velocity_6m': 0.3,
            'm2_velocity_yoy': None,
            'vix': 15.0
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['m2_growth'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_missing_vix(self, scorer):
        """Test handling when VIX is missing."""
        indicators = {
            'fed_funds_velocity_6m': 0.3,
            'm2_velocity_yoy': 5.0,
            'vix': None
        }
        result = scorer.calculate_score(indicators)

        assert result['components']['vix'] is None
        # Should still score with other indicators
        assert result['score'] >= 0

    def test_fed_tightening(self, scorer):
        """Test Fed tightening trajectory scoring."""
        # Rapid tightening
        score, signal = scorer._score_fed_trajectory(2.5)
        assert score == 4.0
        assert 'CRITICAL' in signal

        # Stable
        score, signal = scorer._score_fed_trajectory(0.2)
        assert score == 0.0

    def test_m2_contraction(self, scorer):
        """Test M2 contraction scoring."""
        # Contraction (rare and concerning)
        score, signal = scorer._score_m2_growth(-2.0)
        assert score == 3.0
        assert 'CRITICAL' in signal

        # Normal growth
        score, signal = scorer._score_m2_growth(6.0)
        assert score == 0.0

    def test_vix_panic_levels(self, scorer):
        """Test VIX at panic levels."""
        # Panic
        score, signal = scorer._score_vix(45.0)
        assert score == 3.0
        assert 'CRITICAL' in signal

        # Normal
        score, signal = scorer._score_vix(15.0)
        assert score == 0.0


class TestPositioningScorer:
    """Tests for PositioningScorer."""

    @pytest.fixture
    def scorer(self):
        return PositioningScorer()

    def test_normal_positioning(self, scorer):
        """Test scoring with normal VIX levels."""
        indicators = {
            'vix_proxy': 16.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 0.0

    def test_extreme_complacency(self, scorer):
        """Test scoring with extreme complacency (very low VIX)."""
        indicators = {
            'vix_proxy': 10.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 10.0  # Maximum score
        assert 'CRITICAL' in result['signals'][0]

    def test_cftc_stub(self, scorer):
        """Test that CFTC data absence is noted."""
        indicators = {
            'sp500_net_speculative': None,
            'treasury_net_speculative': None,
            'vix_proxy': 15.0
        }
        result = scorer.calculate_score(indicators)

        # Should have note about CFTC not implemented
        assert any('CFTC' in signal for signal in result['signals'])

    def test_missing_vix_data(self, scorer):
        """Test handling when VIX data is missing."""
        indicators = {
            'vix_proxy': None
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 0.0
        assert result['components']['vix_positioning'] is None
        # Check for CFTC note (since VIX is missing, CFTC data is also None)
        assert any('CFTC' in signal for signal in result['signals'])

    def test_very_low_vix(self, scorer):
        """Test scoring with very low VIX (complacency)."""
        indicators = {
            'vix_proxy': 12.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 5.0
        assert any('WARNING' in signal for signal in result['signals'])

    def test_low_vix(self, scorer):
        """Test scoring with low VIX (some complacency)."""
        indicators = {
            'vix_proxy': 14.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 2.0
        assert any('WATCH' in signal for signal in result['signals'])

    def test_extreme_fear_vix(self, scorer):
        """Test scoring with extreme high VIX (panic)."""
        indicators = {
            'vix_proxy': 45.0
        }
        result = scorer.calculate_score(indicators)

        assert result['score'] == 3.0
        assert any('extreme' in signal.lower() for signal in result['signals'])


class TestRiskAggregator:
    """Tests for RiskAggregator."""

    @pytest.fixture
    def aggregator(self):
        return RiskAggregator()

    def test_weight_validation(self, aggregator):
        """Test that weights sum to 1.0."""
        weights = aggregator.weights
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01

    def test_overall_risk_calculation(self, aggregator):
        """Test overall risk score calculation."""
        test_data = {
            'recession': {
                'unemployment_claims_velocity_yoy': 2.0,
                'ism_pmi': 54.0,
                'ism_pmi_prev': 53.5,
                'yield_curve_10y2y': 0.3,
                'yield_curve_10y3m': 0.5,
                'consumer_sentiment': 95.0
            },
            'credit': {
                'hy_spread': 350,
                'hy_spread_velocity_20d': 1.0,
                'ig_spread_bbb': 120,
                'ted_spread': 0.3,
                'bank_lending_standards': 5.0
            },
            'valuation': {
                'shiller_cape': 18.0,
                'wilshire_5000': 28000,
                'gdp': 28000,
                'sp500_forward_pe': 18.0
            },
            'liquidity': {
                'fed_funds_velocity_6m': 0.3,
                'm2_velocity_yoy': 6.0,
                'vix': 15.0
            },
            'positioning': {
                'vix_proxy': 15.0
            }
        }

        result = aggregator.calculate_overall_risk(test_data)

        assert 'overall_score' in result
        assert 0 <= result['overall_score'] <= 10
        assert result['tier'] in ['GREEN', 'YELLOW', 'RED']
        assert 'dimension_scores' in result
        assert len(result['dimension_scores']) == 5

    def test_risk_tier_classification(self, aggregator):
        """Test risk tier classification."""
        # GREEN
        assert aggregator._get_risk_tier(5.0) == 'GREEN'

        # YELLOW
        assert aggregator._get_risk_tier(7.0) == 'YELLOW'

        # RED
        assert aggregator._get_risk_tier(9.0) == 'RED'

    def test_weighted_calculation(self, aggregator):
        """Test that weighted calculation is correct."""
        # Create data where we know exact scores
        test_data = {
            'recession': {
                'unemployment_claims_velocity_yoy': 20.0,  # Should give 4.0
                'ism_pmi': 55.0,  # Should give 0.0
                'ism_pmi_prev': 54.0,
                'yield_curve_10y2y': 0.5,  # Should give 0.0
                'yield_curve_10y3m': 0.5,
                'consumer_sentiment': 100.0  # Should give 0.0
            },
            'credit': {
                'hy_spread': 350,
                'hy_spread_velocity_20d': 0.5,
                'ig_spread_bbb': 120,
                'ted_spread': 0.3,
                'bank_lending_standards': 5.0
            },
            'valuation': {
                'shiller_cape': 17.0,
                'wilshire_5000': 28000,
                'gdp': 28000,
                'sp500_forward_pe': 18.0
            },
            'liquidity': {
                'fed_funds_velocity_6m': 0.2,
                'm2_velocity_yoy': 6.0,
                'vix': 15.0
            },
            'positioning': {
                'vix_proxy': 15.0
            }
        }

        result = aggregator.calculate_overall_risk(test_data)

        # Recession score should be 4.0, weighted by 0.30 = 1.2
        # Others should be near 0
        # Total should be close to 1.2
        assert result['dimension_scores']['recession'] == 4.0
        assert result['overall_score'] > 1.0
        assert result['overall_score'] < 2.0

    def test_signal_aggregation(self, aggregator):
        """Test that signals from all dimensions are collected."""
        test_data = {
            'recession': {
                'unemployment_claims_velocity_yoy': 15.0,  # Will generate signal
                'ism_pmi': 54.0,
                'ism_pmi_prev': 53.5,
                'yield_curve_10y2y': 0.3,
                'yield_curve_10y3m': 0.5,
                'consumer_sentiment': 95.0
            },
            'credit': {
                'hy_spread': 850,  # Will generate signal
                'hy_spread_velocity_20d': 1.0,
                'ig_spread_bbb': 120,
                'ted_spread': 0.3,
                'bank_lending_standards': 5.0
            },
            'valuation': {
                'shiller_cape': 18.0,
                'wilshire_5000': 28000,
                'gdp': 28000,
                'sp500_forward_pe': 18.0
            },
            'liquidity': {
                'fed_funds_velocity_6m': 0.3,
                'm2_velocity_yoy': 6.0,
                'vix': 15.0
            },
            'positioning': {
                'vix_proxy': 15.0
            }
        }

        result = aggregator.calculate_overall_risk(test_data)

        # Should have signals from recession and credit at least
        assert len(result['all_signals']['recession']) > 0
        assert len(result['all_signals']['credit']) > 0
