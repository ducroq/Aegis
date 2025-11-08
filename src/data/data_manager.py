"""
Data Manager - Orchestrates all data fetching

Coordinates FRED and Yahoo Finance clients to fetch all indicators
needed for risk scoring.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from src.config.config_manager import ConfigManager
from src.data.fred_client import FREDClient
from src.data.market_data import MarketDataClient


logger = logging.getLogger(__name__)


class DataManager:
    """
    Orchestrates data fetching from all sources.

    Provides a single interface to fetch all indicators needed for risk scoring.
    Handles errors gracefully - continues even if some indicators fail.
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize data manager.

        Args:
            config: ConfigManager instance. If None, creates new one.
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        # Initialize clients
        self.fred_client = FREDClient(config)
        self.market_client = MarketDataClient(config)

        logger.info("Data manager initialized")

    def fetch_all_indicators(self) -> Dict[str, Any]:
        """
        Fetch all economic indicators for risk scoring.

        Returns:
            Dict with all indicator data, organized by category:
            {
                'recession': {...},
                'credit': {...},
                'valuation': {...},
                'liquidity': {...},
                'positioning': {...},  # Stubbed for now
                'metadata': {...}
            }
        """
        logger.info("Fetching all indicators...")
        start_time = datetime.now()

        data = {
            'recession': self._fetch_recession_indicators(),
            'credit': self._fetch_credit_indicators(),
            'valuation': self._fetch_valuation_indicators(),
            'liquidity': self._fetch_liquidity_indicators(),
            'positioning': self._fetch_positioning_indicators(),
            'metadata': {
                'fetch_timestamp': datetime.now().isoformat(),
                'fetch_duration_seconds': 0  # Will update at end
            }
        }

        # Calculate fetch duration
        duration = (datetime.now() - start_time).total_seconds()
        data['metadata']['fetch_duration_seconds'] = duration

        logger.info(f"Fetch completed in {duration:.1f} seconds")

        # Log any failures
        self._log_fetch_summary(data)

        return data

    def _fetch_recession_indicators(self) -> Dict[str, Any]:
        """Fetch recession risk indicators."""
        logger.info("Fetching recession indicators...")

        return {
            # Unemployment claims velocity (YoY % change)
            'unemployment_claims': self.fred_client.get_latest_value('ICSA'),
            'unemployment_claims_4wk_avg': self.fred_client.get_moving_average('ICSA', window=4),
            'unemployment_claims_velocity_yoy': self.fred_client.calculate_velocity('ICSA', method='yoy_pct'),

            # ISM PMI (regime shift indicator)
            # Note: NAPM discontinued, using manufacturing employment as proxy
            'ism_pmi': self.fred_client.get_latest_value('MANEMP'),
            'ism_pmi_prev': self._get_previous_value('MANEMP'),  # For detecting crosses

            # Yield curves
            'yield_curve_10y2y': self.fred_client.get_latest_value('T10Y2Y'),
            'yield_curve_10y3m': self.fred_client.get_latest_value('T10Y3M'),

            # Consumer sentiment
            'consumer_sentiment': self.fred_client.get_latest_value('UMCSENT'),

            # Unemployment rate (lagging, but useful)
            'unemployment_rate': self.fred_client.get_latest_value('UNRATE'),
        }

    def _fetch_credit_indicators(self) -> Dict[str, Any]:
        """Fetch credit stress indicators."""
        logger.info("Fetching credit indicators...")

        return {
            # High-yield spreads (velocity + level)
            'hy_spread': self.fred_client.get_latest_value('BAMLH0A0HYM2'),
            'hy_spread_velocity_20d': self.fred_client.calculate_velocity(
                'BAMLH0A0HYM2', method='rate', lookback_days=20
            ),

            # Investment grade spreads
            'ig_spread_bbb': self.fred_client.get_latest_value('BAMLC0A4CBBB'),

            # TED spread (LIBOR - Treasury)
            'ted_spread': self.fred_client.get_latest_value('TEDRATE'),

            # Bank lending standards (quarterly, may be stale)
            'bank_lending_standards': self.fred_client.get_latest_value('DRTSCILM'),
        }

    def _fetch_valuation_indicators(self) -> Dict[str, Any]:
        """Fetch valuation indicators."""
        logger.info("Fetching valuation indicators...")

        return {
            # Market prices (use FRED instead of Yahoo Finance to avoid rate limits)
            'sp500_price': self.fred_client.get_latest_value('SP500'),
            'sp500_forward_pe': self.market_client.get_forward_pe('^GSPC'),  # Keep trying Yahoo

            # Shiller CAPE (would need separate scraper, stub for now)
            'shiller_cape': None,  # TODO: Implement Shiller scraper

            # Buffett indicator (Market Cap / GDP)
            # Note: Wilshire 5000 discontinued from FRED, using S&P 500 as proxy
            # For proper Buffett indicator, would need: (Wilshire 5000 / GDP) * 100
            # Using S&P 500 level as simpler proxy for now
            'sp500_level': self.fred_client.get_latest_value('SP500'),
            # Denominator: GDP (quarterly, may be stale)
            'gdp': self.fred_client.get_latest_value('GDP'),
        }

    def _fetch_liquidity_indicators(self) -> Dict[str, Any]:
        """Fetch liquidity condition indicators."""
        logger.info("Fetching liquidity indicators...")

        return {
            # Fed funds rate
            'fed_funds_rate': self.fred_client.get_latest_value('DFF'),
            'fed_funds_velocity_6m': self.fred_client.calculate_velocity(
                'DFF', method='rate', lookback_days=180
            ),

            # M2 money supply
            'm2_money_supply': self.fred_client.get_latest_value('M2SL'),
            'm2_velocity_yoy': self.fred_client.calculate_velocity('M2SL', method='yoy_pct'),

            # Fed balance sheet
            'fed_balance_sheet': self.fred_client.get_latest_value('WALCL'),

            # Margin debt (may need alternative source)
            'margin_debt': None,  # TODO: Add FINRA data source if needed

            # VIX (market volatility) - use FRED to avoid Yahoo Finance rate limits
            'vix': self.fred_client.get_latest_value('VIXCLS'),
        }

    def _fetch_positioning_indicators(self) -> Dict[str, Any]:
        """
        Fetch positioning/speculation indicators (CFTC data).

        Note: CFTC data requires separate implementation. Stubbed for now.
        """
        logger.info("Fetching positioning indicators (stubbed)...")

        return {
            # CFTC S&P 500 futures positioning
            'sp500_net_speculative': None,  # TODO: Implement CFTC client

            # CFTC Treasury futures positioning
            'treasury_net_speculative': None,  # TODO: Implement CFTC client

            # VIX futures positioning
            'vix_net_speculative': None,  # TODO: Implement CFTC client

            # For now, use VIX as a proxy for complacency (FRED instead of Yahoo)
            'vix_proxy': self.fred_client.get_latest_value('VIXCLS'),
        }

    def _get_previous_value(self, series_id: str, periods_back: int = 1) -> Optional[float]:
        """Get a previous value from a series (for detecting crosses)."""
        try:
            series = self.fred_client.get_series(series_id)
            if series is None or len(series) < periods_back + 1:
                return None
            return float(series.iloc[-(periods_back + 1)])
        except Exception as e:
            logger.error(f"Failed to get previous value for {series_id}: {e}")
            return None

    def _log_fetch_summary(self, data: Dict[str, Any]) -> None:
        """Log summary of fetch results."""
        total_indicators = 0
        successful_indicators = 0
        failed_indicators = []

        for category in ['recession', 'credit', 'valuation', 'liquidity', 'positioning']:
            if category not in data:
                continue

            for indicator, value in data[category].items():
                total_indicators += 1
                if value is not None:
                    successful_indicators += 1
                else:
                    failed_indicators.append(f"{category}.{indicator}")

        success_rate = (successful_indicators / total_indicators * 100) if total_indicators > 0 else 0

        logger.info(f"Fetch summary: {successful_indicators}/{total_indicators} indicators ({success_rate:.0f}%)")

        if failed_indicators:
            logger.warning(f"Failed indicators: {', '.join(failed_indicators)}")


def main():
    """Test data manager."""
    import sys
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Data Manager...\n")

    try:
        manager = DataManager()

        print("[TEST] Fetching all indicators...")
        data = manager.fetch_all_indicators()

        print("\n" + "="*50)
        print("FETCH RESULTS")
        print("="*50)

        for category in ['recession', 'credit', 'valuation', 'liquidity', 'positioning']:
            print(f"\n{category.upper()}:")
            for indicator, value in data[category].items():
                if value is not None:
                    if isinstance(value, float):
                        print(f"  [OK] {indicator}: {value:.2f}")
                    else:
                        print(f"  [OK] {indicator}: {value}")
                else:
                    print(f"  [MISSING] {indicator}")

        print(f"\nMetadata:")
        print(f"  Fetch time: {data['metadata']['fetch_timestamp']}")
        print(f"  Duration: {data['metadata']['fetch_duration_seconds']:.1f}s")

        print("\n" + "="*50)
        print("Data Manager test PASSED")
        print("="*50)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
