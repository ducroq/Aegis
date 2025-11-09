"""
Backfill Historical Data - Generate Risk Scores for Past Dates

This script fetches historical economic indicators and calculates what the
risk scores would have been at each point in time. This enables backtesting
the system against known market crashes.

IMPORTANT: This uses point-in-time data where available, but some indicators
may use revised data, which could introduce look-ahead bias. Use results as
a guide, not absolute truth.

Usage:
    python scripts/backfill_history.py --start-date 2000-01-01 --end-date 2024-12-31 [--frequency weekly]

Options:
    --start-date    Start date for backfill (YYYY-MM-DD)
    --end-date      End date for backfill (YYYY-MM-DD)
    --frequency     Data frequency: daily, weekly (default), monthly
    --dry-run       Calculate but don't save to history
    --verbose       Enable verbose logging
"""

import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import csv
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.data.data_manager import DataManager
from src.scoring.aggregator import RiskAggregator


def setup_logging(verbose: bool = False):
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def generate_date_range(start_date: str, end_date: str, frequency: str) -> List[str]:
    """
    Generate list of dates to backfill.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        frequency: 'daily', 'weekly', or 'monthly'

    Returns:
        List of date strings (YYYY-MM-DD)
    """
    logger = logging.getLogger(__name__)

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    dates = []
    current = start

    if frequency == 'daily':
        delta = timedelta(days=1)
    elif frequency == 'weekly':
        delta = timedelta(weeks=1)
    elif frequency == 'monthly':
        # Approximate - will adjust to actual month boundaries
        delta = timedelta(days=30)
    else:
        raise ValueError(f"Invalid frequency: {frequency}")

    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))

        if frequency == 'monthly':
            # Move to same day next month
            month = current.month
            year = current.year
            month += 1
            if month > 12:
                month = 1
                year += 1
            try:
                current = current.replace(year=year, month=month)
            except ValueError:
                # Handle day overflow (e.g., Jan 31 -> Feb 31 doesn't exist)
                current = current.replace(year=year, month=month, day=1)
        else:
            current += delta

    logger.info(f"Generated {len(dates)} dates from {start_date} to {end_date} ({frequency})")
    return dates


def fetch_historical_indicators(date: str, data_manager: DataManager) -> dict:
    """
    Fetch indicators as they would have been on a specific date.

    Args:
        date: Target date (YYYY-MM-DD)
        data_manager: DataManager instance

    Returns:
        Dict with indicator data, or None if fetch fails
    """
    logger = logging.getLogger(__name__)

    try:
        # Fetch data as of the target date using historical methods
        data = data_manager.fetch_all_indicators_as_of(date)

        # Count failed indicators (None values)
        failed_count = 0
        total_count = 0
        for category in ['recession', 'credit', 'valuation', 'liquidity', 'positioning']:
            if category in data:
                for key, value in data[category].items():
                    total_count += 1
                    if value is None:
                        failed_count += 1

        # Allow up to 10 failures (we have ~25 total indicators, some are optional)
        if failed_count > 10:
            logger.warning(f"  {date}: Too many failed indicators ({failed_count}/{total_count})")
            return None

        return data

    except Exception as e:
        logger.error(f"  {date}: Failed to fetch indicators: {e}")
        return None


def calculate_historical_risk(indicators: dict, config: ConfigManager) -> dict:
    """
    Calculate risk scores for historical indicators.

    Args:
        indicators: Historical indicator data
        config: Configuration manager

    Returns:
        Dict with risk assessment
    """
    aggregator = RiskAggregator(config)
    result = aggregator.calculate_overall_risk(indicators)
    return result


def save_backfill_data(historical_data: List[dict], dry_run: bool = False):
    """
    Save backfilled data to history files.

    Args:
        historical_data: List of {date, indicators, risk_result} dicts
        dry_run: If True, don't actually save
    """
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("="*80)
        logger.info("DRY RUN - NOT SAVING TO HISTORY")
        logger.info("="*80)
        logger.info(f"Would save {len(historical_data)} records")
        return

    logger.info("="*80)
    logger.info("SAVING BACKFILLED DATA TO HISTORY")
    logger.info("="*80)

    history_dir = project_root / 'data' / 'history'
    history_dir.mkdir(parents=True, exist_ok=True)

    # Save risk scores
    scores_file = history_dir / 'risk_scores.csv'

    # Read existing data to avoid duplicates
    existing_dates = set()
    if scores_file.exists():
        with open(scores_file, 'r') as f:
            reader = csv.DictReader(f)
            existing_dates = {row['date'] for row in reader}

    # Filter out duplicates
    new_data = [d for d in historical_data if d['date'] not in existing_dates]

    if not new_data:
        logger.info("No new data to save (all dates already exist)")
        return

    # Append new data
    file_exists = scores_file.exists()

    with open(scores_file, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if new file
        if not file_exists:
            writer.writerow([
                'date', 'overall_risk', 'tier',
                'recession', 'credit', 'valuation', 'liquidity', 'positioning'
            ])

        # Write data rows
        for record in sorted(new_data, key=lambda x: x['date']):
            risk_result = record['risk_result']
            writer.writerow([
                record['date'],
                risk_result['overall_score'],
                risk_result['tier'],
                risk_result['dimension_scores']['recession'],
                risk_result['dimension_scores']['credit'],
                risk_result['dimension_scores']['valuation'],
                risk_result['dimension_scores']['liquidity'],
                risk_result['dimension_scores']['positioning']
            ])

    logger.info(f"Saved {len(new_data)} new records to {scores_file}")
    logger.info(f"Skipped {len(historical_data) - len(new_data)} existing records")

    # Save raw indicators
    indicators_file = history_dir / 'raw_indicators.csv'

    # Read existing dates
    existing_dates = set()
    if indicators_file.exists():
        with open(indicators_file, 'r') as f:
            reader = csv.DictReader(f)
            existing_dates = {row['date'] for row in reader}

    # Filter new data
    new_data = [d for d in historical_data if d['date'] not in existing_dates]

    if new_data:
        # Flatten indicators for CSV
        def flatten_indicators(indicators):
            flat = {}
            for category in ['recession', 'credit', 'valuation', 'liquidity', 'positioning']:
                for key, value in indicators[category].items():
                    flat[f"{category}_{key}"] = value
            return flat

        file_exists = indicators_file.exists()

        with open(indicators_file, 'a', newline='') as f:
            # Get fieldnames from first record
            first_flat = flatten_indicators(new_data[0]['indicators'])
            fieldnames = ['date'] + list(first_flat.keys())

            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header if new file
            if not file_exists:
                writer.writeheader()

            # Write data rows
            for record in sorted(new_data, key=lambda x: x['date']):
                flat = flatten_indicators(record['indicators'])
                row = {'date': record['date']}
                row.update(flat)
                writer.writerow(row)

        logger.info(f"Saved {len(new_data)} new indicator records to {indicators_file}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Backfill historical risk scores')
    parser.add_argument('--start-date', type=str, required=True,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--frequency', type=str, default='weekly',
                        choices=['daily', 'weekly', 'monthly'],
                        help='Data frequency (default: weekly)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Calculate but don\'t save to history')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("="*80)
        logger.info(f"HISTORICAL BACKFILL STARTING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        logger.info(f"Date range: {args.start_date} to {args.end_date}")
        logger.info(f"Frequency: {args.frequency}")

        # Initialize
        config = ConfigManager()
        data_manager = DataManager(config)

        # Generate date range
        dates = generate_date_range(args.start_date, args.end_date, args.frequency)

        # Process each date
        logger.info("="*80)
        logger.info("FETCHING HISTORICAL DATA")
        logger.info("="*80)

        historical_data = []
        successful = 0
        failed = 0

        for i, date in enumerate(dates, 1):
            logger.info(f"[{i}/{len(dates)}] Processing {date}...")

            # Note: Currently fetches latest data for each date
            # In a production system, would need to fetch data AS OF that date
            # This is a limitation - we're using current/revised data
            indicators = fetch_historical_indicators(date, data_manager)

            if indicators is None:
                failed += 1
                continue

            # Calculate risk scores
            risk_result = calculate_historical_risk(indicators, config)

            historical_data.append({
                'date': date,
                'indicators': indicators,
                'risk_result': risk_result
            })

            successful += 1

            logger.info(f"  Risk: {risk_result['overall_score']:.2f}/10 ({risk_result['tier']})")

            # Rate limiting - don't hammer APIs
            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{len(dates)} dates processed")
                import time
                time.sleep(2)  # 2 second pause every 10 requests

        # Summary
        logger.info("="*80)
        logger.info("FETCH SUMMARY")
        logger.info("="*80)
        logger.info(f"Successful: {successful}/{len(dates)}")
        logger.info(f"Failed: {failed}/{len(dates)}")

        if not historical_data:
            logger.error("No historical data collected - cannot save")
            return 1

        # Save to history
        save_backfill_data(historical_data, dry_run=args.dry_run)

        # Final summary
        logger.info("="*80)
        logger.info("BACKFILL COMPLETED")
        logger.info("="*80)
        logger.info(f"Processed {len(historical_data)} historical dates")

        if not args.dry_run:
            logger.info("Run backtest.py to validate against market crashes")

        return 0

    except Exception as e:
        logger.error(f"BACKFILL FAILED: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
