"""
Incremental Historical Backfill - One Month at a Time

This script carefully fetches missing historical data month-by-month,
validating each step before proceeding. It respects API rate limits
and stops on errors.

Usage:
    python scripts/incremental_backfill.py --target-month 2020-02-01
    python scripts/incremental_backfill.py --fill-gaps 2000-01-01 2020-02-01
"""

import sys
import logging
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
import csv
from typing import List, Dict, Any, Optional
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.data.data_manager import DataManager
from src.scoring.aggregator import RiskAggregator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_existing_data(csv_path: Path) -> pd.DataFrame:
    """Load existing historical data from CSV."""
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} existing rows from {csv_path.name}")
        return df
    else:
        logger.info(f"No existing data found at {csv_path}")
        return pd.DataFrame()


def month_already_exists(date_str: str, existing_df: pd.DataFrame) -> bool:
    """Check if a month already exists in the data."""
    if existing_df.empty:
        return False
    return date_str in existing_df['date'].values


def fetch_single_month(
    target_date: str,
    config: ConfigManager,
    data_manager: DataManager,
    aggregator: RiskAggregator
) -> Dict[str, Any]:
    """
    Fetch all indicators for a single month and calculate risk score.

    Returns:
        Dictionary with 'raw_indicators' and 'risk_scores' or None on failure
    """
    logger.info(f"=" * 70)
    logger.info(f"FETCHING DATA FOR: {target_date}")
    logger.info(f"=" * 70)

    try:
        # Fetch all indicators as of target date
        logger.info(f"Fetching all indicators as of {target_date}...")
        start_time = time.time()

        data = data_manager.fetch_all_indicators_as_of(target_date)

        fetch_time = time.time() - start_time
        logger.info(f"Fetch completed in {fetch_time:.1f} seconds")

        # Count successful fetches
        total_indicators = 0
        successful_indicators = 0

        for category, indicators in data.items():
            if isinstance(indicators, dict):
                for key, value in indicators.items():
                    total_indicators += 1
                    if value is not None:
                        successful_indicators += 1

        logger.info(f"Successfully fetched {successful_indicators}/{total_indicators} indicators")

        # Calculate risk score
        logger.info("Calculating risk score...")
        result = aggregator.calculate_overall_risk(data)

        overall_score = result['overall_score']
        tier = result['tier']
        dimension_scores = result['dimension_scores']

        logger.info(f"Overall risk score: {overall_score:.2f}/10 ({tier})")
        logger.info(f"  - Recession: {dimension_scores['recession']:.2f}/10")
        logger.info(f"  - Credit: {dimension_scores['credit']:.2f}/10")
        logger.info(f"  - Valuation: {dimension_scores['valuation']:.2f}/10")
        logger.info(f"  - Liquidity: {dimension_scores['liquidity']:.2f}/10")
        logger.info(f"  - Positioning: {dimension_scores['positioning']:.2f}/10")

        # Prepare raw indicators row
        raw_row = {'date': target_date}
        for category, indicators in data.items():
            if isinstance(indicators, dict):
                for key, value in indicators.items():
                    col_name = f"{category}_{key}"
                    raw_row[col_name] = value

        # Prepare risk scores row
        risk_row = {
            'date': target_date,
            'overall_risk': overall_score,
            'tier': tier,
            'recession': dimension_scores['recession'],
            'credit': dimension_scores['credit'],
            'valuation': dimension_scores['valuation'],
            'liquidity': dimension_scores['liquidity'],
            'positioning': dimension_scores['positioning']
        }

        return {
            'raw_indicators': raw_row,
            'risk_scores': risk_row,
            'success': True,
            'indicators_count': successful_indicators,
            'total_count': total_indicators
        }

    except Exception as e:
        logger.error(f"FAILED to fetch data for {target_date}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def append_to_csv(row: Dict[str, Any], csv_path: Path, is_first_row: bool = False):
    """Append a single row to CSV file."""
    file_exists = csv_path.exists() and csv_path.stat().st_size > 0

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())

        if not file_exists or is_first_row:
            writer.writeheader()

        writer.writerow(row)

    logger.info(f"[OK] Appended row to {csv_path.name}")


def verify_csv_integrity(csv_path: Path) -> bool:
    """Verify CSV can be read and has valid data."""
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"[OK] CSV verified: {len(df)} rows, {len(df.columns)} columns")
        return True
    except Exception as e:
        logger.error(f"[FAIL] CSV verification failed: {e}")
        return False


def generate_missing_months(start_date: str, end_date: str, existing_df: pd.DataFrame) -> List[str]:
    """Generate list of missing months between start and end date."""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    missing_months = []
    current = start

    while current <= end:
        date_str = current.strftime('%Y-%m-%d')

        if not month_already_exists(date_str, existing_df):
            missing_months.append(date_str)

        # Move to first day of next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

    return missing_months


def main():
    parser = argparse.ArgumentParser(description='Incremental historical backfill')
    parser.add_argument('--target-month', type=str, help='Single month to fetch (YYYY-MM-DD)')
    parser.add_argument('--fill-gaps', nargs=2, metavar=('START', 'END'),
                        help='Fill all missing months between START and END dates')
    parser.add_argument('--delay', type=int, default=2,
                        help='Seconds to wait between fetches (default: 2)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Fetch but don\'t save to files')

    args = parser.parse_args()

    if not args.target_month and not args.fill_gaps:
        parser.error("Must specify either --target-month or --fill-gaps")

    # Initialize components
    logger.info("Initializing configuration and data managers...")
    config = ConfigManager()
    data_manager = DataManager(config)
    aggregator = RiskAggregator(config)

    # Setup paths
    history_dir = project_root / 'data' / 'history'
    history_dir.mkdir(parents=True, exist_ok=True)

    raw_indicators_path = history_dir / 'raw_indicators.csv'
    risk_scores_path = history_dir / 'risk_scores.csv'

    # Load existing data
    existing_raw = load_existing_data(raw_indicators_path)
    existing_scores = load_existing_data(risk_scores_path)

    # Determine which months to fetch
    if args.target_month:
        months_to_fetch = [args.target_month]
    else:
        start_date, end_date = args.fill_gaps
        months_to_fetch = generate_missing_months(start_date, end_date, existing_scores)

    if not months_to_fetch:
        logger.info("No missing months found. Data is complete!")
        return 0

    logger.info(f"Will fetch {len(months_to_fetch)} missing months")
    logger.info(f"First: {months_to_fetch[0]}, Last: {months_to_fetch[-1]}")

    # Fetch each month
    success_count = 0
    fail_count = 0

    for i, target_month in enumerate(months_to_fetch, 1):
        logger.info(f"\n[{i}/{len(months_to_fetch)}] Processing {target_month}...")

        # Check if already exists (safety check)
        if month_already_exists(target_month, existing_scores):
            logger.info(f"Month {target_month} already exists. Skipping.")
            continue

        # Fetch data for this month
        result = fetch_single_month(target_month, config, data_manager, aggregator)

        if result is None or not result['success']:
            logger.error(f"[FAIL] FAILED to fetch {target_month}")
            fail_count += 1

            # Stop on first failure
            logger.error("Stopping due to error. Fix the issue and re-run.")
            break

        # Save to CSV files
        if not args.dry_run:
            try:
                # Append to raw indicators
                append_to_csv(result['raw_indicators'], raw_indicators_path)

                # Append to risk scores
                append_to_csv(result['risk_scores'], risk_scores_path)

                # Verify integrity
                if not verify_csv_integrity(raw_indicators_path):
                    logger.error("CSV integrity check failed! Stopping.")
                    break

                if not verify_csv_integrity(risk_scores_path):
                    logger.error("CSV integrity check failed! Stopping.")
                    break

                logger.info(f"[OK] SUCCESS: {target_month} saved and verified")
                success_count += 1

            except Exception as e:
                logger.error(f"[FAIL] FAILED to save {target_month}: {e}")
                fail_count += 1
                break
        else:
            logger.info(f"[OK] DRY-RUN SUCCESS: {target_month} (not saved)")
            success_count += 1

        # Rate limiting: wait between fetches
        if i < len(months_to_fetch):
            logger.info(f"Waiting {args.delay} seconds before next fetch...")
            time.sleep(args.delay)

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("INCREMENTAL BACKFILL COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Successfully fetched: {success_count} months")
    logger.info(f"Failed: {fail_count} months")

    if fail_count == 0:
        logger.info("[OK] All fetches completed successfully!")
        return 0
    else:
        logger.error("[FAIL] Some fetches failed. Please review errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
