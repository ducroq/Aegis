"""
AAII Sentiment Data Handler

Reads and processes AAII (American Association of Individual Investors) sentiment survey data.
This is a contrarian indicator - extreme bullishness often precedes corrections,
extreme bearishness often marks bottoms.
"""

import os
import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SentimentDataManager:
    """
    Manages AAII sentiment survey data.

    Data source: https://www.aaii.com/sentimentsurvey/sent_results
    Format: CSV with columns [Date, Bullish%, Neutral%, Bearish%]

    User must manually download CSV weekly and save to data/external/aaii_sentiment.csv
    """

    def __init__(self, csv_path: str = 'data/external/aaii_sentiment.csv'):
        """
        Initialize sentiment data manager.

        Args:
            csv_path: Path to AAII sentiment CSV file
        """
        self.csv_path = csv_path
        self.data = None

    def load_data(self) -> bool:
        """
        Load AAII sentiment data from CSV.

        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        if not os.path.exists(self.csv_path):
            logger.warning(
                f"AAII sentiment CSV not found at {self.csv_path}. "
                f"Download from https://www.aaii.com/sentimentsurvey/sent_results"
            )
            return False

        try:
            # Read CSV - AAII format has header row
            self.data = pd.read_csv(self.csv_path, parse_dates=['Date'])

            # Standardize column names (remove any whitespace)
            self.data.columns = [col.strip() for col in self.data.columns]

            # Sort by date ascending
            self.data = self.data.sort_values('Date')

            logger.info(
                f"Loaded {len(self.data)} weeks of AAII sentiment data "
                f"({self.data['Date'].min().date()} to {self.data['Date'].max().date()})"
            )
            return True

        except Exception as e:
            logger.error(f"Error loading AAII sentiment data: {e}")
            return False

    def get_latest_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Get most recent sentiment reading.

        Returns:
            Dict with keys: date, bulls_percent, neutrals_percent, bears_percent
            or None if data not available
        """
        if self.data is None:
            if not self.load_data():
                return None

        if len(self.data) == 0:
            logger.warning("AAII sentiment data is empty")
            return None

        latest = self.data.iloc[-1]

        return {
            'date': latest['Date'],
            'bulls_percent': float(latest['Bullish%']),
            'neutrals_percent': float(latest['Neutral%']),
            'bears_percent': float(latest['Bearish%'])
        }

    def get_sentiment_at_date(self, target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        Get sentiment reading closest to target date (for backtesting).

        Args:
            target_date: Date to look up

        Returns:
            Dict with sentiment data or None if not available
        """
        if self.data is None:
            if not self.load_data():
                return None

        if len(self.data) == 0:
            return None

        # Find closest date (AAII is weekly, so within 7 days is acceptable)
        self.data['date_diff'] = abs((self.data['Date'] - target_date).dt.days)
        closest_idx = self.data['date_diff'].idxmin()
        closest_row = self.data.loc[closest_idx]

        # If closest date is more than 30 days away, data is stale
        if closest_row['date_diff'] > 30:
            logger.warning(
                f"AAII sentiment data is stale for {target_date.date()}. "
                f"Closest data is from {closest_row['Date'].date()} "
                f"({closest_row['date_diff']} days away)"
            )
            return None

        return {
            'date': closest_row['Date'],
            'bulls_percent': float(closest_row['Bullish%']),
            'neutrals_percent': float(closest_row['Neutral%']),
            'bears_percent': float(closest_row['Bearish%'])
        }

    def get_sentiment_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get historical sentiment data for a date range.

        Args:
            start_date: Start date (inclusive), None for all data
            end_date: End date (inclusive), None for all data

        Returns:
            DataFrame with columns: Date, Bullish%, Neutral%, Bearish%
        """
        if self.data is None:
            if not self.load_data():
                return pd.DataFrame()

        df = self.data.copy()

        if start_date is not None:
            df = df[df['Date'] >= start_date]

        if end_date is not None:
            df = df[df['Date'] <= end_date]

        # Remove temporary column if it exists
        if 'date_diff' in df.columns:
            df = df.drop(columns=['date_diff'])

        return df

    def get_historical_percentiles(self, lookback_years: int = 5) -> Dict[str, float]:
        """
        Calculate historical percentiles for bulls_percent (for context).

        Args:
            lookback_years: Years of history to use for percentile calculation

        Returns:
            Dict with keys: p10, p20, p50, p80, p90 (percentile values for bulls%)
        """
        if self.data is None:
            if not self.load_data():
                return {}

        # Get data from last N years
        cutoff_date = datetime.now() - pd.DateOffset(years=lookback_years)
        recent_data = self.data[self.data['Date'] >= cutoff_date]

        if len(recent_data) == 0:
            return {}

        bulls = recent_data['Bullish%']

        return {
            'p10': float(bulls.quantile(0.10)),
            'p20': float(bulls.quantile(0.20)),
            'p50': float(bulls.quantile(0.50)),  # Median
            'p80': float(bulls.quantile(0.80)),
            'p90': float(bulls.quantile(0.90))
        }


def create_sample_csv(output_path: str = 'data/external/aaii_sentiment.csv'):
    """
    Create a sample CSV file with instructions for the user.

    This creates a template file showing the expected format.
    User should replace with actual data from AAII website.

    Args:
        output_path: Where to save sample CSV
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    sample_data = pd.DataFrame({
        'Date': pd.date_range(start='2024-01-01', periods=10, freq='W'),
        'Bullish%': [45.2, 43.8, 42.1, 40.5, 38.9, 37.2, 35.8, 34.1, 32.5, 31.0],
        'Neutral%': [30.0, 31.2, 32.5, 33.0, 34.1, 35.2, 36.0, 37.5, 38.2, 39.0],
        'Bearish%': [24.8, 25.0, 25.4, 26.5, 27.0, 27.6, 28.2, 28.4, 29.3, 30.0]
    })

    sample_data.to_csv(output_path, index=False)

    print(f"Sample AAII sentiment CSV created at: {output_path}")
    print()
    print("INSTRUCTIONS:")
    print("1. Visit https://www.aaii.com/sentimentsurvey/sent_results")
    print("2. Download the full historical CSV (may require free AAII membership)")
    print("3. Replace the sample file with the downloaded CSV")
    print("4. Ensure columns are named: Date, Bullish%, Neutral%, Bearish%")
    print("5. Update weekly to keep data current")


if __name__ == '__main__':
    # Test/demo code
    import argparse

    parser = argparse.ArgumentParser(description='AAII Sentiment Data Manager')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample CSV template')
    parser.add_argument('--test', action='store_true',
                       help='Test loading existing CSV')
    args = parser.parse_args()

    if args.create_sample:
        create_sample_csv()

    if args.test:
        manager = SentimentDataManager()
        if manager.load_data():
            print("\n✓ Data loaded successfully")

            latest = manager.get_latest_sentiment()
            if latest:
                print(f"\nLatest sentiment ({latest['date'].date()}):")
                print(f"  Bulls:    {latest['bulls_percent']:.1f}%")
                print(f"  Neutrals: {latest['neutrals_percent']:.1f}%")
                print(f"  Bears:    {latest['bears_percent']:.1f}%")

            percentiles = manager.get_historical_percentiles()
            if percentiles:
                print(f"\nHistorical percentiles (5-year):")
                print(f"  10th: {percentiles['p10']:.1f}%")
                print(f"  50th: {percentiles['p50']:.1f}%")
                print(f"  90th: {percentiles['p90']:.1f}%")
        else:
            print("\n✗ Failed to load data")
            print("Run with --create-sample to create template CSV")
