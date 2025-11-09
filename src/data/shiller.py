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

    def get_cape_as_of(self, as_of_date: str, use_cache: bool = True, cache_ttl_days: int = 30) -> Optional[float]:
        """
        Get CAPE ratio as of a specific historical date.

        Args:
            as_of_date: Date to get CAPE for (YYYY-MM-DD)
            use_cache: Whether to use cached full dataset
            cache_ttl_days: Cache time-to-live for full dataset

        Returns:
            CAPE ratio as of that date, or None if unavailable
        """
        try:
            # Parse target date
            target_date = pd.to_datetime(as_of_date)

            # Load full historical dataset
            df = self._load_full_dataset(use_cache, cache_ttl_days)
            if df is None:
                return None

            # Filter to data available as of target date
            # CAPE is monthly data, so we look for the most recent month <= target
            df_filtered = df[df['Date'] <= target_date]

            if len(df_filtered) == 0:
                logger.warning(f"No CAPE data available before {as_of_date}")
                return None

            # Get CAPE value
            cape_value = df_filtered['CAPE'].iloc[-1]

            if pd.isna(cape_value):
                logger.warning(f"CAPE value is null for date near {as_of_date}")
                return None

            return float(cape_value)

        except Exception as e:
            logger.error(f"Failed to get CAPE as of {as_of_date}: {e}")
            return None

    def _load_full_dataset(self, use_cache: bool = True, cache_ttl_days: int = 30) -> Optional[pd.DataFrame]:
        """
        Load full Shiller CAPE historical dataset.

        Args:
            use_cache: Whether to use cached dataset
            cache_ttl_days: Cache time-to-live in days

        Returns:
            DataFrame with Date and CAPE columns, or None if error
        """
        # Check cache
        if use_cache:
            cached_df = self._load_dataset_from_cache(cache_ttl_days)
            if cached_df is not None:
                logger.debug(f"Loaded Shiller dataset from cache ({len(cached_df)} rows)")
                return cached_df

        # Fetch from web
        try:
            logger.info("Fetching full Shiller CAPE dataset from Yale...")

            # Download Excel file
            response = requests.get(self.DATA_URL, timeout=30)
            response.raise_for_status()

            # Save to temporary file
            temp_file = self.cache_dir / 'temp_download.xls'
            with open(temp_file, 'wb') as f:
                f.write(response.content)

            # Parse Excel file
            df = pd.read_excel(
                temp_file,
                sheet_name='Data',
                skiprows=7,
                na_values=['.', ''],
                engine='xlrd'
            )

            # Clean up temp file
            temp_file.unlink(missing_ok=True)

            # Find CAPE column
            cape_column = None
            for col in ['CAPE', 'Cyclically Adjusted PE Ratio', 'P/E10']:
                if col in df.columns:
                    cape_column = col
                    break

            if cape_column is None:
                logger.error(f"CAPE column not found. Available columns: {df.columns.tolist()}")
                return None

            # Find date column (usually first column or "Date")
            date_column = df.columns[0] if 'Date' not in df.columns else 'Date'

            # Parse dates - Shiller uses YYYY.MM format (e.g., 1871.01, 2023.12)
            def parse_shiller_date(date_val):
                """Convert Shiller's YYYY.MM format to datetime."""
                try:
                    if pd.isna(date_val):
                        return pd.NaT
                    year = int(date_val)
                    month = int(round((date_val - year) * 100))
                    if month == 0:
                        month = 1  # Handle cases like 1871.00
                    return pd.Timestamp(year=year, month=month, day=1)
                except:
                    return pd.NaT

            # Extract just Date and CAPE
            df_clean = pd.DataFrame({
                'Date': df[date_column].apply(parse_shiller_date),
                'CAPE': pd.to_numeric(df[cape_column], errors='coerce')
            })

            # Drop rows with invalid dates or CAPE
            df_clean = df_clean.dropna(subset=['Date'])

            # Sort by date
            df_clean = df_clean.sort_values('Date').reset_index(drop=True)

            logger.info(f"Fetched Shiller dataset: {len(df_clean)} observations from {df_clean['Date'].min()} to {df_clean['Date'].max()}")

            # Cache the dataset
            if use_cache:
                self._save_dataset_to_cache(df_clean)

            return df_clean

        except Exception as e:
            logger.error(f"Error loading Shiller dataset: {e}")
            return None

    def _get_dataset_cache_path(self) -> Path:
        """Get path to cached dataset file."""
        return self.cache_dir / 'cape_historical.csv'

    def _load_dataset_from_cache(self, ttl_days: int) -> Optional[pd.DataFrame]:
        """Load full dataset from cache if fresh enough."""
        cache_path = self._get_dataset_cache_path()

        if not cache_path.exists():
            return None

        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(days=ttl_days):
            logger.debug(f"Dataset cache expired (age: {cache_age.days} days)")
            return None

        try:
            df = pd.read_csv(cache_path, parse_dates=['Date'])
            return df
        except Exception as e:
            logger.warning(f"Failed to load dataset cache: {e}")
            return None

    def _save_dataset_to_cache(self, df: pd.DataFrame) -> None:
        """Save full dataset to cache."""
        try:
            cache_path = self._get_dataset_cache_path()
            df.to_csv(cache_path, index=False)
            logger.debug(f"Cached Shiller dataset: {len(df)} rows")
        except Exception as e:
            logger.warning(f"Failed to save dataset cache: {e}")

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
