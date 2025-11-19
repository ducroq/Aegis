"""
Daily Update Script - Fetch Data and Calculate Risk Scores

This script is intended to be run daily (e.g., via cron or Task Scheduler).
It:
1. Fetches latest economic indicators from FRED, Yahoo Finance, and Shiller
2. Calculates risk scores for each dimension
3. Calculates overall aggregated risk score
4. Stores results in CSV history files for tracking over time
5. Logs all operations

Usage:
    python scripts/daily_update.py [--dry-run] [--verbose]

Options:
    --dry-run    Fetch and calculate but don't save to history
    --verbose    Enable verbose logging output
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.data.data_manager import DataManager
from src.scoring.recession import RecessionScorer
from src.scoring.credit import CreditScorer
from src.scoring.valuation import ValuationScorer
from src.scoring.liquidity import LiquidityScorer
from src.scoring.positioning import PositioningScorer
from src.scoring.aggregator import RiskAggregator


def setup_logging(verbose: bool = False):
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / 'data' / 'logs' / 'daily_update.log')
        ]
    )


def ensure_directories():
    """Ensure required directories exist."""
    (project_root / 'data' / 'history').mkdir(parents=True, exist_ok=True)
    (project_root / 'data' / 'logs').mkdir(parents=True, exist_ok=True)


def fetch_indicators(data_manager: DataManager) -> dict:
    """
    Fetch all economic indicators.

    Returns:
        Dict with all indicator data organized by category
    """
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("FETCHING ECONOMIC INDICATORS")
    logger.info("="*60)

    data = data_manager.fetch_all_indicators()

    logger.info(f"Fetch completed in {data['metadata']['fetch_duration_seconds']:.1f}s")

    return data


def calculate_risk_scores(indicators: dict, config: ConfigManager) -> dict:
    """
    Calculate risk scores for all dimensions and overall risk.

    Args:
        indicators: Dict with all indicator data from DataManager
        config: Configuration manager

    Returns:
        Dict with overall risk assessment including dimension scores
    """
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("CALCULATING RISK SCORES")
    logger.info("="*60)

    # Use aggregator which handles all scoring internally
    aggregator = RiskAggregator(config)
    result = aggregator.calculate_overall_risk(indicators)

    # Log dimension scores
    logger.info("  Dimension Scores:")
    for dimension, score in result['dimension_scores'].items():
        logger.info(f"    {dimension.capitalize():12s}: {score:.2f}/10")

    logger.info(f"\n  Overall Risk Score: {result['overall_score']:.2f}/10")
    logger.info(f"  Risk Tier: {result['tier']}")

    return result


def save_to_history(indicators: dict, risk_result: dict, dry_run: bool = False):
    """
    Save results to CSV history files.

    Args:
        indicators: Raw indicator data
        risk_result: Overall risk assessment with dimension scores
        dry_run: If True, don't actually save
    """
    logger = logging.getLogger(__name__)

    if dry_run:
        logger.info("="*60)
        logger.info("DRY RUN - NOT SAVING TO HISTORY")
        logger.info("="*60)
        return

    logger.info("="*60)
    logger.info("SAVING TO HISTORY")
    logger.info("="*60)

    history_dir = project_root / 'data' / 'history'
    timestamp = datetime.now().strftime('%Y-%m-%d')

    # Save risk scores
    scores_file = history_dir / 'risk_scores.csv'
    file_exists = scores_file.exists()

    with open(scores_file, 'a', newline='') as f:
        writer = csv.writer(f)

        # Write header if new file
        if not file_exists:
            writer.writerow([
                'date', 'overall_risk',
                'recession', 'credit', 'valuation', 'liquidity', 'positioning',
                'tier', 'alerted'
            ])

        # Write data
        writer.writerow([
            timestamp,
            risk_result['overall_score'],
            risk_result['dimension_scores']['recession'],
            risk_result['dimension_scores']['credit'],
            risk_result['dimension_scores']['valuation'],
            risk_result['dimension_scores']['liquidity'],
            risk_result['dimension_scores']['positioning'],
            risk_result['tier'],
            risk_result.get('alerted', False)  # Whether alert was triggered
        ])

    logger.info(f"  Saved risk scores to {scores_file}")

    # Save raw indicators (optional, for backtesting)
    indicators_file = history_dir / 'raw_indicators.csv'
    file_exists = indicators_file.exists()

    # Flatten indicators for CSV
    flat_indicators = {}
    for category in ['recession', 'credit', 'valuation', 'liquidity', 'positioning']:
        for key, value in indicators[category].items():
            flat_indicators[f"{category}_{key}"] = value

    # Add metadata fields
    flat_indicators['metadata_fetch_timestamp'] = indicators['metadata']['fetch_timestamp']
    flat_indicators['metadata_as_of_date'] = indicators['metadata'].get('as_of_date', timestamp)
    flat_indicators['metadata_fetch_duration_seconds'] = indicators['metadata']['fetch_duration_seconds']

    # Determine field names - read from existing file if it exists, otherwise use current order
    if file_exists:
        # Read existing header to maintain column order
        with open(indicators_file, 'r', newline='') as f:
            reader = csv.reader(f)
            existing_header = next(reader)
            fieldnames = existing_header
    else:
        # New file - define the canonical column order
        fieldnames = ['date'] + list(flat_indicators.keys())

    with open(indicators_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')

        # Write header if new file
        if not file_exists:
            writer.writeheader()

        # Write data
        row = {'date': timestamp}
        row.update(flat_indicators)
        writer.writerow(row)

    logger.info(f"  Saved raw indicators to {indicators_file}")

    # Copy to dashboard folder for Netlify deployment
    dashboard_dir = project_root / 'dashboard' / 'data'
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(scores_file, dashboard_dir / 'risk_scores.csv')
    shutil.copy2(indicators_file, dashboard_dir / 'raw_indicators.csv')

    logger.info(f"  Copied files to dashboard/data/ for Netlify")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Daily risk score update')
    parser.add_argument('--dry-run', action='store_true',
                        help='Fetch and calculate but don\'t save to history')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Setup (ensure directories first, before logging tries to write)
    ensure_directories()
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("="*60)
        logger.info(f"DAILY UPDATE STARTING - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        # Initialize
        config = ConfigManager()
        data_manager = DataManager(config)

        # Fetch data
        indicators = fetch_indicators(data_manager)

        # Calculate risk scores (dimensions + overall)
        risk_result = calculate_risk_scores(indicators, config)

        # Save to history
        save_to_history(indicators, risk_result, dry_run=args.dry_run)

        # Summary
        logger.info("="*60)
        logger.info("DAILY UPDATE COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        logger.info(f"Overall Risk: {risk_result['overall_score']:.2f}/10 ({risk_result['tier']})")

        # Print key signals
        if risk_result['all_signals']:
            logger.info("\nKey Signals:")
            for signal in risk_result['all_signals']:
                logger.info(f"  - {signal}")

        return 0

    except Exception as e:
        logger.error(f"DAILY UPDATE FAILED: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
