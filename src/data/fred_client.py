"""
FRED (Federal Reserve Economic Data) API Client

Wrapper around fredapi library with caching, error handling,
and velocity calculations.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd

try:
    from fredapi import Fred
except ImportError:
    Fred = None

from src.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class FREDClient:
    """
    Client for fetching data from FRED API.

    Features:
    - Automatic caching to reduce API calls
    - Velocity calculations (YoY %, N-day rate of change)
    - Graceful error handling
    - Missing data interpolation
    """

    def __init__(self, config: Optional[ConfigManager] = None, cache_dir: Optional[str] = None):
        """
        Initialize FRED client.

        Args:
            config: ConfigManager instance. If None, creates new one.
            cache_dir: Directory for caching data. If None, uses data/cache/fred/
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        # Get API key
        self.api_key = config.get_secret('fred_api_key')
        if not self.api_key or self.api_key == 'your_fred_api_key_here':
            logger.warning("FRED API key not configured. Client will not work.")
            logger.warning("Get free key: https://fred.stlouisfed.org/docs/api/api_key.html")
            self.fred = None
        else:
            if Fred is None:
                raise ImportError("fredapi library not installed. Run: pip install fredapi")
            self.fred = Fred(api_key=self.api_key)
            logger.info("FRED client initialized")

        # Setup cache directory
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "data" / "cache" / "fred"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl_hours: int = 24
    ) -> Optional[pd.Series]:
        """
        Fetch a FRED series.

        Args:
            series_id: FRED series ID (e.g., "T10Y2Y", "UNRATE")
            start_date: Start date (YYYY-MM-DD). If None, gets last 5 years.
            end_date: End date (YYYY-MM-DD). If None, uses today.
            use_cache: Whether to use cached data
            cache_ttl_hours: Cache time-to-live in hours

        Returns:
            Pandas Series with data, or None if error
        """
        if self.fred is None:
            logger.error("FRED client not initialized (API key missing)")
            return None

        # Check cache
        if use_cache:
            cached_data = self._load_from_cache(series_id, cache_ttl_hours)
            if cached_data is not None:
                logger.debug(f"Loaded {series_id} from cache")
                return cached_data

        # Default date range: last 5 years
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')

        try:
            logger.info(f"Fetching FRED series: {series_id}")
            series = self.fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date
            )

            if series is None or len(series) == 0:
                logger.warning(f"No data returned for {series_id}")
                return None

            # Cache the data
            if use_cache:
                self._save_to_cache(series_id, series)

            logger.debug(f"Fetched {series_id}: {len(series)} observations")
            return series

        except Exception as e:
            logger.error(f"Failed to fetch {series_id}: {e}")
            return None

    def get_latest_value(self, series_id: str) -> Optional[float]:
        """
        Get the most recent value for a series.

        Args:
            series_id: FRED series ID

        Returns:
            Latest value or None
        """
        series = self.get_series(series_id)
        if series is None or len(series) == 0:
            return None

        return float(series.iloc[-1])

    def calculate_velocity(
        self,
        series_id: str,
        method: str = 'yoy_pct',
        lookback_days: int = 365
    ) -> Optional[float]:
        """
        Calculate rate of change (velocity) for a series.

        Args:
            series_id: FRED series ID
            method: Calculation method:
                - 'yoy_pct': Year-over-year percent change
                - 'rate': N-day rate of change (absolute)
                - 'pct_change': N-day percent change
            lookback_days: Number of days to look back (default 365 for YoY)

        Returns:
            Velocity value or None
        """
        series = self.get_series(series_id)
        if series is None or len(series) < 2:
            return None

        try:
            if method == 'yoy_pct':
                # Year-over-year percent change
                current = series.iloc[-1]
                year_ago_date = series.index[-1] - timedelta(days=lookback_days)

                # Find closest observation to year ago
                year_ago_series = series[series.index <= year_ago_date]
                if len(year_ago_series) == 0:
                    logger.warning(f"Not enough history for YoY calculation: {series_id}")
                    return None

                year_ago = year_ago_series.iloc[-1]
                velocity = ((current - year_ago) / year_ago) * 100

                logger.debug(f"{series_id} YoY velocity: {velocity:.2f}%")
                return float(velocity)

            elif method == 'rate':
                # N-day rate of change (absolute difference / days)
                current = series.iloc[-1]
                past_date = series.index[-1] - timedelta(days=lookback_days)
                past_series = series[series.index <= past_date]

                if len(past_series) == 0:
                    return None

                past_value = past_series.iloc[-1]
                actual_days = (series.index[-1] - past_series.index[-1]).days
                if actual_days == 0:
                    return None

                velocity = (current - past_value) / actual_days
                return float(velocity)

            elif method == 'pct_change':
                # N-day percent change
                current = series.iloc[-1]
                past_date = series.index[-1] - timedelta(days=lookback_days)
                past_series = series[series.index <= past_date]

                if len(past_series) == 0:
                    return None

                past_value = past_series.iloc[-1]
                if past_value == 0:
                    return None

                velocity = ((current - past_value) / past_value) * 100
                return float(velocity)

            else:
                logger.error(f"Unknown velocity method: {method}")
                return None

        except Exception as e:
            logger.error(f"Failed to calculate velocity for {series_id}: {e}")
            return None

    def get_value_as_of(
        self,
        series_id: str,
        as_of_date: str,
        max_days_old: int = 90
    ) -> Optional[float]:
        """
        Get series value as of a specific historical date.

        Args:
            series_id: FRED series ID
            as_of_date: Date to get value for (YYYY-MM-DD)
            max_days_old: Maximum days to look back for most recent value

        Returns:
            Value as of that date, or None if not available
        """
        # Fetch series with appropriate date range (disable cache to avoid stale data)
        target_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        start_date = (target_date - timedelta(days=max_days_old)).strftime('%Y-%m-%d')
        end_date = as_of_date

        series = self.get_series(series_id, start_date=start_date, end_date=end_date, use_cache=False)
        if series is None or len(series) == 0:
            return None

        try:
            # Get most recent value on or before target date
            series = series[series.index <= target_date]
            if len(series) == 0:
                return None

            # Drop NaN values and get most recent non-NaN
            series_clean = series.dropna()
            if len(series_clean) == 0:
                return None

            value = float(series_clean.iloc[-1])

            # Check if value is still NaN (edge case)
            if pd.isna(value):
                return None

            return value

        except Exception as e:
            logger.error(f"Failed to get {series_id} as of {as_of_date}: {e}")
            return None

    def calculate_velocity_as_of(
        self,
        series_id: str,
        as_of_date: str,
        method: str = 'yoy_pct',
        lookback_days: int = 365
    ) -> Optional[float]:
        """
        Calculate velocity as of a specific historical date.

        Args:
            series_id: FRED series ID
            as_of_date: Date to calculate velocity for (YYYY-MM-DD)
            method: Calculation method (same as calculate_velocity)
            lookback_days: Number of days to look back

        Returns:
            Velocity value or None
        """
        # Fetch series with enough history (disable cache to avoid stale data)
        target_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        start_date = (target_date - timedelta(days=lookback_days + 180)).strftime('%Y-%m-%d')
        end_date = as_of_date

        series = self.get_series(series_id, start_date=start_date, end_date=end_date, use_cache=False)
        if series is None or len(series) < 2:
            return None

        try:
            # Filter to data available as of target date
            series = series[series.index <= target_date]
            if len(series) < 2:
                return None

            if method == 'yoy_pct':
                current = series.iloc[-1]
                year_ago_date = series.index[-1] - timedelta(days=lookback_days)
                year_ago_series = series[series.index <= year_ago_date]

                if len(year_ago_series) == 0:
                    return None

                year_ago = year_ago_series.iloc[-1]
                if year_ago == 0:
                    return None
                velocity = ((current - year_ago) / year_ago) * 100
                return float(velocity)

            elif method == 'rate':
                current = series.iloc[-1]
                past_date = series.index[-1] - timedelta(days=lookback_days)
                past_series = series[series.index <= past_date]

                if len(past_series) == 0:
                    return None

                past_value = past_series.iloc[-1]
                actual_days = (series.index[-1] - past_series.index[-1]).days
                if actual_days == 0:
                    return None

                velocity = (current - past_value) / actual_days
                return float(velocity)

            elif method == 'pct_change':
                current = series.iloc[-1]
                past_date = series.index[-1] - timedelta(days=lookback_days)
                past_series = series[series.index <= past_date]

                if len(past_series) == 0:
                    return None

                past_value = past_series.iloc[-1]
                if past_value == 0:
                    return None

                velocity = ((current - past_value) / past_value) * 100
                return float(velocity)

            else:
                logger.error(f"Unknown velocity method: {method}")
                return None

        except Exception as e:
            logger.error(f"Failed to calculate velocity for {series_id} as of {as_of_date}: {e}")
            return None

    def get_moving_average(
        self,
        series_id: str,
        window: int = 4
    ) -> Optional[float]:
        """
        Get the current N-period moving average.

        Args:
            series_id: FRED series ID
            window: Number of periods for moving average

        Returns:
            Moving average value or None
        """
        series = self.get_series(series_id)
        if series is None or len(series) < window:
            return None

        try:
            ma = series.iloc[-window:].mean()
            return float(ma)
        except Exception as e:
            logger.error(f"Failed to calculate moving average for {series_id}: {e}")
            return None

    def _get_cache_path(self, series_id: str) -> Path:
        """Get cache file path for a series."""
        return self.cache_dir / f"{series_id}.csv"

    def _load_from_cache(self, series_id: str, ttl_hours: int) -> Optional[pd.Series]:
        """Load series from cache if fresh enough."""
        cache_path = self._get_cache_path(series_id)

        if not cache_path.exists():
            return None

        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(hours=ttl_hours):
            logger.debug(f"Cache expired for {series_id} (age: {cache_age})")
            return None

        try:
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            return df.squeeze()  # Convert DataFrame to Series
        except Exception as e:
            logger.warning(f"Failed to load cache for {series_id}: {e}")
            return None

    def _save_to_cache(self, series_id: str, series: pd.Series) -> None:
        """Save series to cache."""
        try:
            cache_path = self._get_cache_path(series_id)
            df = pd.DataFrame(series)
            df.to_csv(cache_path)
            logger.debug(f"Cached {series_id} to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache {series_id}: {e}")

    def get_multiple_series(self, series_ids: list[str]) -> Dict[str, pd.Series]:
        """
        Fetch multiple series at once.

        Args:
            series_ids: List of FRED series IDs

        Returns:
            Dict mapping series IDs to Series data
        """
        results = {}
        for series_id in series_ids:
            series = self.get_series(series_id)
            if series is not None:
                results[series_id] = series
        return results


def main():
    """Test FRED client."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing FRED Client...\n")

    try:
        client = FREDClient()

        if client.fred is None:
            print("[ERROR] FRED client not initialized")
            print("Please add your FRED API key to config/credentials/secrets.ini")
            sys.exit(1)

        # Test fetching a series
        print("[TEST] Fetching 10Y-2Y Treasury spread (T10Y2Y)...")
        spread = client.get_latest_value('T10Y2Y')
        if spread is not None:
            print(f"[OK] Current spread: {spread:.2f}%")
        else:
            print("[ERROR] Failed to fetch spread")

        # Test velocity calculation
        print("\n[TEST] Calculating unemployment claims velocity (ICSA)...")
        velocity = client.calculate_velocity('ICSA', method='yoy_pct')
        if velocity is not None:
            print(f"[OK] YoY velocity: {velocity:+.1f}%")
        else:
            print("[WARNING] Not enough data for velocity calculation")

        # Test multiple series
        print("\n[TEST] Fetching multiple series...")
        series_ids = ['T10Y2Y', 'UNRATE', 'BAMLH0A0HYM2']
        results = client.get_multiple_series(series_ids)
        print(f"[OK] Fetched {len(results)}/{len(series_ids)} series:")
        for sid in results:
            print(f"  - {sid}: {len(results[sid])} observations")

        print("\n" + "="*50)
        print("FRED Client test PASSED")
        print("="*50)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
