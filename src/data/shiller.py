"""
Shiller CAPE (Cyclically Adjusted Price-to-Earnings) Data Scraper

Fetches CAPE ratio data from Robert Shiller's website at Yale.
Data source: http://www.econ.yale.edu/~shiller/data.htm
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
from io import StringIO

logger = logging.getLogger(__name__)


class ShillerDataClient:
    """
    Client for fetching Shiller CAPE ratio data.

    Data is updated monthly by Professor Robert Shiller at Yale.
    """

    # Shiller's Excel file URL (updated monthly)
    DATA_URL = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize Shiller data client.

        Args:
            cache_dir: Directory for caching downloaded data
        """
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "data" / "cache" / "shiller"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Shiller data client initialized")

    def get_latest_cape(self, use_cache: bool = True, cache_ttl_days: int = 7) -> Optional[float]:
        """
        Get the most recent CAPE ratio value.

        Args:
            use_cache: Whether to use cached data
            cache_ttl_days: Cache time-to-live in days (default 7, since data updates monthly)

        Returns:
            Latest CAPE ratio or None if unavailable
        """
        try:
            # Try cache first
            if use_cache:
                cached_cape = self._load_from_cache(cache_ttl_days)
                if cached_cape is not None:
                    logger.debug(f"Loaded CAPE from cache: {cached_cape:.2f}")
                    return cached_cape

            # Fetch fresh data
            logger.info("Fetching Shiller CAPE data from Yale...")
            cape_value = self._fetch_cape_from_web()

            if cape_value is not None and use_cache:
                self._save_to_cache(cape_value)

            return cape_value

        except Exception as e:
            logger.error(f"Failed to fetch Shiller CAPE: {e}")
            return None

    def _fetch_cape_from_web(self) -> Optional[float]:
        """
        Fetch CAPE data from Shiller's website.

        Note: The Excel file format may change. This implementation
        attempts to be robust but may need updates.
        """
        try:
            # Download Excel file
            response = requests.get(self.DATA_URL, timeout=30)
            response.raise_for_status()

            # Save to temporary file (pandas needs a file path for XLS format)
            temp_file = self.cache_dir / 'temp_download.xls'
            with open(temp_file, 'wb') as f:
                f.write(response.content)

            # Parse Excel file using xlrd engine for .xls files
            # Shiller's file has data starting around row 8
            # Columns: Date, S&P Composite, Dividend, Earnings, CPI, etc., CAPE
            df = pd.read_excel(
                temp_file,
                sheet_name='Data',
                skiprows=7,  # Skip header rows
                na_values=['.', ''],
                engine='xlrd'
            )

            # Clean up temp file
            temp_file.unlink(missing_ok=True)

            # CAPE is typically in column 'CAPE' or 'Cyclically Adjusted PE Ratio'
            # Try different possible column names
            cape_column = None
            for col in ['CAPE', 'Cyclically Adjusted PE Ratio', 'P/E10']:
                if col in df.columns:
                    cape_column = col
                    break

            if cape_column is None:
                logger.error(f"CAPE column not found. Available columns: {df.columns.tolist()}")
                return None

            # Get most recent non-null value
            cape_series = df[cape_column].dropna()
            if len(cape_series) == 0:
                logger.warning("No CAPE data found in file")
                return None

            latest_cape = float(cape_series.iloc[-1])
            logger.info(f"Fetched Shiller CAPE: {latest_cape:.2f}")
            return latest_cape

        except Exception as e:
            logger.error(f"Error parsing Shiller data: {e}")
            return None

    def _get_cache_path(self) -> Path:
        """Get path to cache file."""
        return self.cache_dir / 'cape_latest.txt'

    def _load_from_cache(self, ttl_days: int) -> Optional[float]:
        """Load CAPE from cache if fresh enough."""
        cache_path = self._get_cache_path()

        if not cache_path.exists():
            return None

        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(days=ttl_days):
            logger.debug(f"Cache expired (age: {cache_age.days} days)")
            return None

        try:
            with open(cache_path, 'r') as f:
                cape_value = float(f.read().strip())
            return cape_value
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, cape_value: float) -> None:
        """Save CAPE to cache."""
        try:
            cache_path = self._get_cache_path()
            with open(cache_path, 'w') as f:
                f.write(f"{cape_value:.2f}")
            logger.debug(f"Cached CAPE: {cape_value:.2f}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


def main():
    """Test Shiller CAPE fetcher."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Shiller CAPE Data Fetcher...\n")

    try:
        client = ShillerDataClient()

        print("[TEST] Fetching latest CAPE ratio...")
        cape = client.get_latest_cape(use_cache=False)

        if cape is not None:
            print(f"[OK] Current Shiller CAPE: {cape:.2f}")

            # Interpretation
            print(f"\nInterpretation:")
            if cape > 30:
                print(f"  EXPENSIVE: CAPE {cape:.2f} > 30 (bubble territory)")
            elif cape > 25:
                print(f"  ELEVATED: CAPE {cape:.2f} > 25 (overvalued)")
            elif cape > 20:
                print(f"  NORMAL: CAPE {cape:.2f} in normal range (15-25)")
            else:
                print(f"  CHEAP: CAPE {cape:.2f} < 20 (undervalued)")

            print(f"\n[OK] Test PASSED")
        else:
            print("[ERROR] Failed to fetch CAPE")
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
