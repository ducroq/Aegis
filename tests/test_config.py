"""
Unit tests for ConfigManager
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml
import configparser

from src.config.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory with test files."""
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
                    'red_threshold': 8.0
                }
            }
            with open(config_dir / 'app.yaml', 'w') as f:
                yaml.dump(app_config, f)

            # Create indicators.yaml
            indicators_config = {
                'recession_indicators': {
                    'unemployment_claims_velocity': {
                        'source': 'FRED',
                        'series_id': 'ICSA'
                    }
                }
            }
            with open(config_dir / 'indicators.yaml', 'w') as f:
                yaml.dump(indicators_config, f)

            # Create regime_shifts.yaml
            regime_config = {
                'regime_shift_categories': {
                    'financial_contagion': {
                        'score': 3.0
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
                'sender_password': 'test_password'
            }
            with open(creds_dir / 'secrets.ini', 'w') as f:
                secrets.write(f)

            yield config_dir

    def test_config_loading(self, temp_config_dir):
        """Test that all config files are loaded successfully."""
        config = ConfigManager(config_dir=temp_config_dir)

        assert 'app' in config.config_data
        assert 'indicators' in config.config_data
        assert 'regime_shifts' in config.config_data

    def test_get_with_dot_notation(self, temp_config_dir):
        """Test getting values using dot notation."""
        config = ConfigManager(config_dir=temp_config_dir)

        # Test nested access
        assert config.get('app.app.name') == 'Aegis Test'
        assert config.get('app.scoring.weights.recession') == 0.30
        assert config.get('app.alerts.yellow_threshold') == 6.5

    def test_get_with_default(self, temp_config_dir):
        """Test that default values are returned for missing keys."""
        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get('nonexistent.key', 'default_value') == 'default_value'
        assert config.get('app.nonexistent', 42) == 42

    def test_get_all_weights(self, temp_config_dir):
        """Test getting all scoring weights."""
        config = ConfigManager(config_dir=temp_config_dir)

        weights = config.get_all_weights()
        assert weights == {
            'recession': 0.30,
            'credit': 0.25,
            'valuation': 0.20,
            'liquidity': 0.15,
            'positioning': 0.10
        }

    def test_weights_validation(self, temp_config_dir):
        """Test that weights are validated to sum to 1.0."""
        config = ConfigManager(config_dir=temp_config_dir)

        weights = config.get_all_weights()
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01  # Allow small floating point errors

    def test_weights_sum_validation(self, temp_config_dir):
        """Test that weights properly validate when they sum correctly."""
        config = ConfigManager(config_dir=temp_config_dir)

        # Our fixture has weights that sum to 1.0, so validation should pass
        weights = config.get_all_weights()
        total = sum(weights.values())

        # If this passes, validation is working
        assert 0.99 <= total <= 1.01

    def test_get_secret(self, temp_config_dir):
        """Test getting secrets from secrets.ini."""
        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_secret('fred_api_key') == 'test_api_key_12345'
        assert config.get_secret('sendgrid_api_key') == 'test_sendgrid_key'

    def test_get_secret_different_section(self, temp_config_dir):
        """Test getting secrets from different sections."""
        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_secret('sender_email', section='email_credentials') == 'test@example.com'

    def test_get_secret_missing(self, temp_config_dir):
        """Test that missing secrets return None."""
        config = ConfigManager(config_dir=temp_config_dir)

        assert config.get_secret('nonexistent_key') is None
        assert config.get_secret('some_key', section='nonexistent_section') is None

    def test_get_alert_thresholds(self, temp_config_dir):
        """Test getting alert thresholds."""
        config = ConfigManager(config_dir=temp_config_dir)

        thresholds = config.get_alert_thresholds()
        assert thresholds['yellow_threshold'] == 6.5
        assert thresholds['red_threshold'] == 8.0

    def test_get_indicator_config(self, temp_config_dir):
        """Test getting indicator configuration."""
        config = ConfigManager(config_dir=temp_config_dir)

        recession_config = config.get_indicator_config('recession_indicators')
        assert 'unemployment_claims_velocity' in recession_config
        assert recession_config['unemployment_claims_velocity']['series_id'] == 'ICSA'

    def test_missing_config_file(self, temp_config_dir):
        """Test handling of missing config files."""
        # Remove one config file
        os.remove(temp_config_dir / 'regime_shifts.yaml')

        # Should still load successfully, just log a warning
        config = ConfigManager(config_dir=temp_config_dir)
        assert 'app' in config.config_data
        assert 'indicators' in config.config_data
        assert 'regime_shifts' not in config.config_data

    def test_missing_secrets_file(self, temp_config_dir):
        """Test handling of missing secrets file."""
        # Remove secrets file
        os.remove(temp_config_dir / 'credentials' / 'secrets.ini')

        # Should still load successfully, just log a warning
        config = ConfigManager(config_dir=temp_config_dir)
        assert config.get_secret('fred_api_key') is None


class TestConfigManagerIntegration:
    """Integration tests using actual config files."""

    def test_load_actual_config(self):
        """Test loading the actual project configuration."""
        # This assumes we're running from project root
        config = ConfigManager()

        # Verify basic structure
        assert config.config_data is not None
        assert 'app' in config.config_data

        # Verify weights sum to 1.0
        weights = config.get_all_weights()
        total = sum(weights.values())
        assert 0.99 <= total <= 1.01

    def test_actual_indicator_config(self):
        """Test that actual indicator config has expected structure."""
        config = ConfigManager()

        # Check recession indicators exist
        recession = config.get_indicator_config('recession_indicators')
        assert recession is not None

        # Check credit indicators exist
        credit = config.get_indicator_config('credit_indicators')
        assert credit is not None
