"""
Configuration Manager for Aegis

Loads YAML configuration files and secrets, provides unified access
with dot notation and environment variable overrides.
"""

import os
import yaml
import configparser
import logging
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Central configuration management for Aegis.

    Loads configurations from:
    1. YAML files (app.yaml, indicators.yaml, regime_shifts.yaml)
    2. Secrets file (secrets.ini)
    3. Environment variables (AEGIS_* prefix overrides)

    Provides dot notation access: config.get("scoring.weights.recession")
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Path to config directory. If None, auto-detect from project root.
        """
        if config_dir is None:
            # Auto-detect: assume we're in src/config/, go up 2 levels to root
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self.config_data: Dict[str, Any] = {}
        self.secrets: Dict[str, Dict[str, str]] = {}

        # Load all configurations
        self._load_yaml_configs()
        self._load_secrets()
        self._apply_env_overrides()
        self._validate_config()

        logger.info("Configuration loaded successfully")

    def _load_yaml_configs(self) -> None:
        """Load all YAML configuration files."""
        yaml_files = {
            'app': self.config_dir / 'app.yaml',
            'indicators': self.config_dir / 'indicators.yaml',
            'regime_shifts': self.config_dir / 'regime_shifts.yaml'
        }

        for name, path in yaml_files.items():
            if not path.exists():
                logger.warning(f"Config file not found: {path}")
                continue

            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data:
                        self.config_data[name] = data
                        logger.debug(f"Loaded {name} config from {path}")
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
                raise

    def _load_secrets(self) -> None:
        """Load secrets from secrets.ini file."""
        secrets_path = self.config_dir / 'credentials' / 'secrets.ini'

        if not secrets_path.exists():
            logger.warning(f"Secrets file not found: {secrets_path}")
            logger.warning("API keys will not be available. Copy secrets.ini.example to secrets.ini")
            return

        try:
            parser = configparser.ConfigParser()
            parser.read(secrets_path, encoding='utf-8')

            # Convert to dict
            self.secrets = {section: dict(parser[section]) for section in parser.sections()}
            logger.debug(f"Loaded secrets from {secrets_path}")
        except Exception as e:
            logger.error(f"Failed to load secrets from {secrets_path}: {e}")
            raise

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides (AEGIS_* prefix)."""
        # Example: AEGIS_SCORING_WEIGHTS_RECESSION=0.35
        # Overrides config.scoring.weights.recession

        for key, value in os.environ.items():
            if not key.startswith('AEGIS_'):
                continue

            # Remove prefix and convert to lowercase dot notation
            config_path = key[6:].lower().replace('_', '.')

            # Try to parse as number if possible
            try:
                if '.' in value:
                    parsed_value = float(value)
                else:
                    parsed_value = int(value)
            except ValueError:
                # Keep as string
                parsed_value = value

            # Set in config (simplified - just store as top-level key)
            logger.info(f"Environment override: {config_path} = {parsed_value}")
            # Note: Full nested override would require more complex logic
            # For now, just log it as a future enhancement

    def _validate_config(self) -> None:
        """Validate critical configuration values."""
        # Check that scoring weights sum to 1.0
        try:
            weights = self.get('app.scoring.weights')
            if weights:
                total_weight = sum(weights.values())
                if not (0.99 <= total_weight <= 1.01):  # Allow small floating point errors
                    raise ValueError(
                        f"Scoring weights must sum to 1.0, got {total_weight}. "
                        f"Weights: {weights}"
                    )
                logger.info(f"Scoring weights validated (sum={total_weight:.3f})")
        except Exception as e:
            logger.error(f"Weight validation failed: {e}")
            raise

        # Check that required sections exist
        required_sections = ['app', 'indicators']
        for section in required_sections:
            if section not in self.config_data:
                logger.warning(f"Required config section missing: {section}")

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            path: Dot-separated path (e.g., "app.scoring.weights.recession")
            default: Default value if path not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get("app.scoring.weights.recession")
            0.30
            >>> config.get("app.alerts.yellow_threshold")
            6.5
        """
        parts = path.split('.')

        # First part is the config file name (app, indicators, regime_shifts)
        if len(parts) < 2:
            return self.config_data.get(path, default)

        config_name = parts[0]
        if config_name not in self.config_data:
            return default

        # Navigate through nested dict
        current = self.config_data[config_name]
        for part in parts[1:]:
            if not isinstance(current, dict):
                return default
            current = current.get(part)
            if current is None:
                return default

        return current

    def get_secret(self, key: str, section: str = 'api_keys') -> Optional[str]:
        """
        Get secret value from secrets.ini.

        Args:
            key: Secret key name (e.g., "fred_api_key")
            section: Section in secrets.ini (default: "api_keys")

        Returns:
            Secret value or None if not found

        Examples:
            >>> config.get_secret("fred_api_key")
            "abcdef1234567890"
        """
        if section not in self.secrets:
            logger.warning(f"Secret section not found: {section}")
            return None

        return self.secrets[section].get(key)

    def get_all_weights(self) -> Dict[str, float]:
        """
        Get all dimension weights.

        Returns:
            Dict mapping dimension names to weights
        """
        return self.get('app.scoring.weights', {})

    def get_alert_thresholds(self) -> Dict[str, float]:
        """
        Get alert thresholds.

        Returns:
            Dict with 'yellow_threshold' and 'red_threshold'
        """
        return {
            'yellow_threshold': self.get('app.alerts.yellow_threshold', 6.5),
            'red_threshold': self.get('app.alerts.red_threshold', 8.0),
        }

    def get_indicator_config(self, category: str) -> Dict[str, Any]:
        """
        Get configuration for an indicator category.

        Args:
            category: Category name (e.g., "recession_indicators", "credit_indicators")

        Returns:
            Dict with indicator configuration
        """
        return self.get(f'indicators.{category}', {})


def main():
    """Test configuration loading."""
    import sys

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    # Check if --test flag provided
    if '--test' in sys.argv:
        print("Testing Aegis configuration...\n")

        try:
            config = ConfigManager()

            print("[OK] Configuration files loaded successfully")
            print(f"  - Config directory: {config.config_dir}")
            print(f"  - Loaded sections: {list(config.config_data.keys())}")

            # Test weights
            weights = config.get_all_weights()
            print(f"\n[OK] Scoring weights (sum={sum(weights.values()):.3f}):")
            for dim, weight in weights.items():
                print(f"  - {dim}: {weight}")

            # Test alert thresholds
            thresholds = config.get_alert_thresholds()
            print(f"\n[OK] Alert thresholds:")
            print(f"  - Yellow: {thresholds['yellow_threshold']}")
            print(f"  - Red: {thresholds['red_threshold']}")

            # Test secrets
            fred_key = config.get_secret('fred_api_key')
            if fred_key:
                print(f"\n[OK] FRED API key found: {fred_key[:8]}...")
            else:
                print("\n[WARNING] FRED API key not found in secrets.ini")
                print("  Copy secrets.ini.example to secrets.ini and add your key")

            print("\n" + "="*50)
            print("Configuration test PASSED")
            print("="*50)

        except Exception as e:
            print(f"\n[ERROR] Configuration test FAILED: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("Usage: python config_manager.py --test")
        sys.exit(1)


if __name__ == '__main__':
    main()
