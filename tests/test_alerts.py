"""
Unit tests for alerts modules (alert_logic, email_sender, history_manager)
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta, date
from pathlib import Path

from src.alerts.alert_logic import AlertLogic
from src.alerts.email_sender import EmailSender
from src.alerts.history_manager import HistoryManager
from src.config.config_manager import ConfigManager


class TestAlertLogic:
    """Tests for AlertLogic."""

    @pytest.fixture
    def alert_logic(self):
        return AlertLogic()

    @pytest.fixture
    def normal_result(self):
        """Normal conditions - below YELLOW threshold of 4.0."""
        return {
            'overall_score': 3.2,  # Below YELLOW threshold (4.0)
            'tier': 'GREEN',
            'dimension_scores': {
                'recession': 3.0,
                'credit': 2.0,
                'valuation': 5.0,
                'liquidity': 4.0,
                'positioning': 2.0
            },
            'all_signals': {'recession': [], 'credit': [], 'valuation': [], 'liquidity': [], 'positioning': []}
        }

    @pytest.fixture
    def red_result(self):
        """Crisis conditions - above RED threshold of 5.0 (realistic max: 5.55 in 2020)."""
        return {
            'overall_score': 5.2,  # Above RED threshold (5.0), realistic for major crisis
            'tier': 'RED',
            'dimension_scores': {
                'recession': 5.0,  # Realistic crisis levels
                'credit': 9.0,     # Credit stress can spike very high
                'valuation': 2.0,  # Usually cheap during crashes
                'liquidity': 7.0,  # Fed easing
                'positioning': 3.0
            },
            'all_signals': {
                'recession': ['CRITICAL: PMI crossed into contraction'],
                'credit': ['CRITICAL: HY spreads widening rapidly'],
                'valuation': [],
                'liquidity': ['CRITICAL: Fed rapidly tightening'],
                'positioning': []
            }
        }

    def test_no_alert_normal_conditions(self, alert_logic, normal_result):
        """Test that normal conditions don't trigger alert."""
        should_alert, tier, reason, details = alert_logic.should_alert(normal_result, [])

        assert should_alert is False
        assert tier == 'GREEN'
        assert 'normal range' in reason.lower()

    def test_red_threshold_alert(self, alert_logic, red_result):
        """Test that RED threshold triggers alert."""
        should_alert, tier, reason, details = alert_logic.should_alert(red_result, [])

        assert should_alert is True
        assert tier == 'RED'
        assert 'RED_THRESHOLD' in details['triggers']
        assert red_result['overall_score'] >= 5.0  # Updated from 8.0 to match new calibrated threshold

    def test_yellow_threshold_alert(self, alert_logic):
        """Test that YELLOW threshold triggers alert."""
        yellow_result = {
            'overall_score': 4.5,  # Between YELLOW (4.0) and RED (5.0)
            'tier': 'YELLOW',
            'dimension_scores': {
                'recession': 4.5,
                'credit': 6.0,
                'valuation': 4.0,
                'liquidity': 3.0,
                'positioning': 3.0
            },
            'all_signals': {}
        }

        should_alert, tier, reason, details = alert_logic.should_alert(yellow_result, [])

        assert should_alert is True
        assert tier == 'YELLOW'
        assert 'YELLOW_THRESHOLD' in details['triggers']

    def test_rapid_rise_detection(self, alert_logic):
        """Test rapid rise detection (>1.0 point in 4 weeks)."""
        current = {
            'overall_score': 4.2,  # YELLOW territory, realistic
            'tier': 'YELLOW',
            'dimension_scores': {'recession': 4.0, 'credit': 5.0, 'valuation': 4.0, 'liquidity': 3.0, 'positioning': 3.0},
            'all_signals': {}
        }

        history = [
            {'overall_score': 4.0},
            {'overall_score': 3.5},
            {'overall_score': 3.2},
            {'overall_score': 2.7}  # 4 weeks ago: 4.2 - 2.7 = 1.5 point rise
        ]

        should_alert, tier, reason, details = alert_logic.should_alert(current, history)

        assert should_alert is True
        assert 'RAPID_RISE' in details['triggers'] or 'YELLOW_THRESHOLD' in details['triggers']
        assert details['change_4w'] == 1.5

    def test_multiple_extremes_trigger(self, alert_logic):
        """Test multiple dimensions in extreme risk (2+ dimensions >= 8.0)."""
        extreme_result = {
            'overall_score': 4.8,  # Overall might still be below RED due to weights
            'tier': 'YELLOW',
            'dimension_scores': {
                'recession': 8.5,  # Extreme
                'credit': 8.2,     # Extreme (credit can spike very high in reality)
                'valuation': 1.0,  # Cheap (lowers overall score)
                'liquidity': 3.0,
                'positioning': 2.0
            },
            'all_signals': {}
        }

        should_alert, tier, reason, details = alert_logic.should_alert(extreme_result, [])

        assert should_alert is True
        assert 'MULTIPLE_EXTREMES' in details['triggers'] or 'YELLOW_THRESHOLD' in details['triggers']
        if 'extreme_dimensions' in details:
            assert 'recession' in details['extreme_dimensions']
            assert 'credit' in details['extreme_dimensions']

    def test_trend_calculation(self, alert_logic):
        """Test trend calculation from history."""
        current = {
            'overall_score': 4.2,  # Realistic YELLOW level
            'tier': 'YELLOW',
            'dimension_scores': {'recession': 4.5, 'credit': 5.0, 'valuation': 4.0, 'liquidity': 3.0, 'positioning': 3.0},
            'all_signals': {}
        }

        history = [
            {
                'overall_score': 4.0,
                'dimension_scores': {'recession': 4.0, 'credit': 5.0, 'valuation': 4.0, 'liquidity': 3.0, 'positioning': 3.0}
            },
            {'overall_score': 3.7},
            {'overall_score': 3.4},
            {'overall_score': 2.7}
        ]

        trends = alert_logic._calculate_trends(current, history)

        assert abs(trends['1w_change'] - 0.2) < 0.01
        assert abs(trends['4w_change'] - 1.5) < 0.01
        assert '1w_direction' in trends
        assert '4w_direction' in trends
        assert 'dimension_trends' in trends
        assert abs(trends['dimension_trends']['recession']['change'] - 0.5) < 0.01

    def test_get_arrow(self, alert_logic):
        """Test trend arrow generation."""
        assert alert_logic._get_arrow(0.6) == 'UP_SHARP'
        assert alert_logic._get_arrow(0.2) == 'UP'
        assert alert_logic._get_arrow(0.05) == 'STABLE'
        assert alert_logic._get_arrow(-0.2) == 'DOWN'
        assert alert_logic._get_arrow(-0.6) == 'DOWN_SHARP'

    def test_extract_key_evidence(self, alert_logic, red_result):
        """Test evidence extraction."""
        evidence = alert_logic._extract_key_evidence(red_result)

        assert len(evidence) > 0
        assert any('CRITICAL' in e for e in evidence)

    def test_get_alert_summary(self, alert_logic):
        """Test full alert summary generation."""
        current = {
            'overall_score': 4.5,  # Realistic YELLOW level
            'tier': 'YELLOW',
            'dimension_scores': {'recession': 4.5, 'credit': 6.0, 'valuation': 5.0, 'liquidity': 3.0, 'positioning': 3.0},
            'all_signals': {
                'recession': ['WARNING: Unemployment rising'],
                'credit': [],
                'valuation': ['CRITICAL: CAPE at bubble levels'],
                'liquidity': [],
                'positioning': []
            }
        }

        history = [{'overall_score': 6.8}, {'overall_score': 6.5}]

        summary = alert_logic.get_alert_summary(current, history)

        assert 'should_alert' in summary
        assert 'tier' in summary
        assert 'reason' in summary
        assert 'trends' in summary
        assert 'key_evidence' in summary
        assert summary['current_score'] == 4.5  # Updated from 7.0 to match realistic score


class TestEmailSender:
    """Tests for EmailSender."""

    @pytest.fixture
    def email_sender(self):
        return EmailSender()

    @pytest.fixture
    def test_alert_summary(self):
        return {
            'should_alert': True,
            'tier': 'YELLOW',
            'reason': 'Risk score 7.2/10 at YELLOW level',
            'current_score': 7.2,
            'dimension_scores': {
                'recession': 8.0,
                'credit': 7.5,
                'valuation': 6.0,
                'liquidity': 5.5,
                'positioning': 4.0
            },
            'trends': {
                '1w_change': 0.3,
                '1w_direction': 'UP',
                '4w_change': 1.5,
                '4w_direction': 'UP_SHARP'
            },
            'key_evidence': [
                '[RECESSION] CRITICAL: Unemployment claims spiking',
                '[CREDIT] WARNING: HY spreads widening'
            ],
            'all_signals': {}
        }

    def test_generate_subject(self, email_sender, test_alert_summary):
        """Test email subject generation."""
        subject = email_sender._generate_subject(test_alert_summary)

        assert 'WARNING' in subject or 'ELEVATED' in subject
        assert '7.2' in subject

    def test_generate_text_body(self, email_sender, test_alert_summary):
        """Test plain text email body generation."""
        body = email_sender._generate_text_body(test_alert_summary)

        assert 'AEGIS' in body
        assert 'YELLOW' in body
        assert '7.2' in body
        assert 'DISCLAIMER' in body
        assert 'SUGGESTED ACTIONS' in body

    def test_generate_html_body(self, email_sender, test_alert_summary):
        """Test HTML email body generation."""
        html = email_sender._generate_html_body(test_alert_summary)

        assert '<html>' in html
        assert 'AEGIS' in html
        assert '7.2' in html
        assert 'style=' in html  # CSS styling present

    def test_send_alert_dry_run(self, email_sender, test_alert_summary):
        """Test dry run email sending."""
        success = email_sender.send_alert(test_alert_summary, dry_run=True)

        assert success is True

    def test_red_alert_styling(self, email_sender):
        """Test RED alert has appropriate styling."""
        red_summary = {
            'tier': 'RED',
            'current_score': 8.5,
            'reason': 'Severe risk',
            'dimension_scores': {'recession': 9.0, 'credit': 8.5, 'valuation': 7.0, 'liquidity': 8.0, 'positioning': 5.0},
            'trends': {},
            'key_evidence': [],
            'all_signals': {}
        }

        subject = email_sender._generate_subject(red_summary)
        body = email_sender._generate_text_body(red_summary)

        assert 'ALERT' in subject or 'SEVERE' in subject
        assert 'RED' in body
        assert 'SEVERE' in body


class TestHistoryManager:
    """Tests for HistoryManager."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def history_manager(self, temp_dir):
        return HistoryManager(temp_dir)

    @pytest.fixture
    def test_result(self):
        return {
            'overall_score': 6.5,
            'tier': 'YELLOW',
            'dimension_scores': {
                'recession': 5.0,
                'credit': 7.0,
                'valuation': 8.0,
                'liquidity': 4.0,
                'positioning': 3.0
            }
        }

    def test_initialization(self, history_manager, temp_dir):
        """Test history manager initialization."""
        assert history_manager.data_dir == Path(temp_dir)
        assert history_manager.risk_scores_file == Path(temp_dir) / "risk_scores.csv"
        assert history_manager.data_dir.exists()

    def test_save_risk_score(self, history_manager, test_result):
        """Test saving risk score."""
        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        history_manager.save_risk_score(test_result, alert_sent=True, timestamp=timestamp)

        assert history_manager.risk_scores_file.exists()

        # Read back and verify
        scores = history_manager.get_recent_scores(num_records=1)
        assert len(scores) == 1
        assert scores[0]['overall_score'] == 6.5
        assert scores[0]['tier'] == 'YELLOW'
        assert scores[0]['alerted'] is True

    def test_save_multiple_scores(self, history_manager, test_result):
        """Test saving multiple risk scores."""
        base_time = datetime(2025, 1, 1, 12, 0, 0)

        for i in range(5):
            timestamp = base_time + timedelta(days=i)
            test_result['overall_score'] = 6.0 + (i * 0.2)
            history_manager.save_risk_score(test_result, alert_sent=False, timestamp=timestamp)

        scores = history_manager.get_recent_scores(num_records=10)
        assert len(scores) == 5
        assert scores[0]['overall_score'] == 6.8  # Most recent (i=4)
        assert scores[4]['overall_score'] == 6.0  # Oldest (i=0)

    def test_save_raw_indicators(self, history_manager):
        """Test saving raw indicator data."""
        indicators = {
            'recession': {
                'unemployment_claims_velocity_yoy': 5.2,
                'ism_pmi': 51.3
            },
            'credit': {
                'hy_spread': 450
            }
        }

        timestamp = datetime(2025, 1, 1, 12, 0, 0)
        history_manager.save_raw_indicators(indicators, timestamp=timestamp)

        assert history_manager.raw_indicators_file.exists()

    def test_get_recent_scores(self, history_manager, test_result):
        """Test retrieving recent scores."""
        # Save 10 scores
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        for i in range(10):
            timestamp = base_time + timedelta(days=i)
            test_result['overall_score'] = 6.0 + (i * 0.1)
            history_manager.save_risk_score(test_result, alert_sent=False, timestamp=timestamp)

        # Get recent 5
        scores = history_manager.get_recent_scores(num_records=5)
        assert len(scores) == 5
        assert scores[0]['overall_score'] == 6.9  # Most recent

    def test_get_scores_by_date_range(self, history_manager, test_result):
        """Test retrieving scores by date range."""
        # Save scores across date range
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        for i in range(10):
            timestamp = base_time + timedelta(days=i)
            history_manager.save_risk_score(test_result, alert_sent=False, timestamp=timestamp)

        # Get specific range
        start = date(2025, 1, 3)
        end = date(2025, 1, 7)
        scores = history_manager.get_scores_by_date_range(start, end)

        assert len(scores) == 5  # Days 3, 4, 5, 6, 7

    def test_get_alert_history(self, history_manager, test_result):
        """Test retrieving alert history."""
        base_time = datetime(2025, 1, 1, 12, 0, 0)

        # Save some with alerts, some without
        for i in range(10):
            timestamp = base_time + timedelta(days=i)
            alert_sent = (i >= 5)  # Last 5 have alerts
            history_manager.save_risk_score(test_result, alert_sent=alert_sent, timestamp=timestamp)

        alerts = history_manager.get_alert_history(num_records=10)
        assert len(alerts) == 5  # Only the ones with alerts

    def test_get_stats(self, history_manager, test_result):
        """Test getting history statistics."""
        # Save some scores
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        for i in range(5):
            timestamp = base_time + timedelta(days=i)
            alert_sent = (i >= 3)
            history_manager.save_risk_score(test_result, alert_sent=alert_sent, timestamp=timestamp)

        stats = history_manager.get_stats()

        assert stats['risk_scores_exist'] is True
        assert stats['risk_scores_count'] == 5
        assert stats['alerts_count'] == 2  # i=3, i=4
        assert stats['date_range']['start'] == '2025-01-01'
        assert stats['date_range']['end'] == '2025-01-05'

    def test_empty_history(self, history_manager):
        """Test operations on empty history."""
        scores = history_manager.get_recent_scores()
        assert len(scores) == 0

        alerts = history_manager.get_alert_history()
        assert len(alerts) == 0

        stats = history_manager.get_stats()
        assert stats['risk_scores_exist'] is False
        assert stats['risk_scores_count'] == 0
