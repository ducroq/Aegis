"""
Backtest Script - Historical Validation of Risk Scoring System

This script validates the Aegis risk scoring system against historical data.
It checks if the system would have warned before major market drawdowns.

Major events to test against:
- 2000-2002: Dot-com bubble crash (-49%)
- 2007-2009: Financial crisis (-57%)
- 2020: COVID crash (-34%)
- 2022: Bear market (-25%)

Usage:
    python scripts/backtest.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]

Options:
    --start-date    Start date for backtest (default: earliest in history)
    --end-date      End date for backtest (default: latest in history)
    --verbose       Enable verbose logging
"""

import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import csv
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.alerts.alert_logic import AlertLogic


# Known market crashes for validation
MAJOR_CRASHES = [
    {
        'name': '2000-2002 Dot-com Bubble',
        'peak_date': '2000-03-24',
        'trough_date': '2002-10-09',
        'drawdown': -49.1,
        'warning_window_days': 90  # Should warn within 90 days before peak
    },
    {
        'name': '2007-2009 Financial Crisis',
        'peak_date': '2007-10-09',
        'trough_date': '2009-03-09',
        'drawdown': -56.8,
        'warning_window_days': 90
    },
    {
        'name': '2020 COVID Crash',
        'peak_date': '2020-02-19',
        'trough_date': '2020-03-23',
        'drawdown': -33.9,
        'warning_window_days': 30  # Faster crash
    },
    {
        'name': '2022 Bear Market',
        'peak_date': '2022-01-03',
        'trough_date': '2022-10-13',
        'drawdown': -25.4,
        'warning_window_days': 60
    }
]


def setup_logging(verbose: bool = False):
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def load_historical_scores(start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    Load historical risk scores from CSV.

    Args:
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        List of score records sorted by date
    """
    logger = logging.getLogger(__name__)
    history_file = project_root / 'data' / 'history' / 'risk_scores.csv'

    if not history_file.exists():
        logger.error(f"History file not found: {history_file}")
        logger.error("Run daily_update.py to create historical data")
        return []

    records = []
    with open(history_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert to proper types
            record = {
                'date': row['date'],
                'overall_score': float(row['overall_risk']),
                'tier': row['tier'],
                'dimension_scores': {
                    'recession': float(row['recession']),
                    'credit': float(row['credit']),
                    'valuation': float(row['valuation']),
                    'liquidity': float(row['liquidity']),
                    'positioning': float(row['positioning'])
                }
            }

            # Apply date filters
            if start_date and record['date'] < start_date:
                continue
            if end_date and record['date'] > end_date:
                continue

            records.append(record)

    logger.info(f"Loaded {len(records)} historical records")
    if records:
        logger.info(f"  Date range: {records[0]['date']} to {records[-1]['date']}")

    return records


def identify_alerts(records: List[Dict], alert_logic: AlertLogic) -> List[Dict]:
    """
    Identify when alerts would have been triggered.

    Args:
        records: Historical score records
        alert_logic: AlertLogic instance

    Returns:
        List of alert events
    """
    logger = logging.getLogger(__name__)
    logger.info("Identifying historical alerts...")

    alerts = []

    # Need at least 4 weeks of history for trend detection
    for i in range(4, len(records)):
        current = records[i]
        # Get last 4 weeks for trend analysis
        history = records[max(0, i-4):i]

        # Check if alert would have triggered
        triggered, tier, reason, details = alert_logic.should_alert(current, history)

        if triggered:
            alert = {
                'date': current['date'],
                'score': current['overall_score'],
                'tier': tier,
                'reason': reason,
                'dimension_scores': current['dimension_scores']
            }
            alerts.append(alert)
            logger.debug(f"  Alert on {current['date']}: {reason}")

    logger.info(f"Found {len(alerts)} alerts in historical data")

    return alerts


def validate_against_crashes(alerts: List[Dict], crashes: List[Dict]) -> Dict:
    """
    Validate if alerts occurred before major crashes.

    Args:
        alerts: List of historical alerts
        crashes: List of known market crashes

    Returns:
        Dict with validation results
    """
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("VALIDATING AGAINST MAJOR MARKET CRASHES")
    logger.info("="*80)

    results = {
        'total_crashes': len(crashes),
        'crashes_with_warnings': 0,
        'false_positives': 0,
        'crash_details': []
    }

    # Check each crash
    for crash in crashes:
        logger.info(f"\n{crash['name']}:")
        logger.info(f"  Peak: {crash['peak_date']}, Drawdown: {crash['drawdown']:.1f}%")

        # Find alerts in warning window before peak
        peak_date = datetime.strptime(crash['peak_date'], '%Y-%m-%d')
        warning_start = peak_date - timedelta(days=crash['warning_window_days'])

        relevant_alerts = [
            a for a in alerts
            if warning_start.strftime('%Y-%m-%d') <= a['date'] <= crash['peak_date']
        ]

        crash_result = {
            'crash': crash['name'],
            'warned': len(relevant_alerts) > 0,
            'alerts_count': len(relevant_alerts),
            'lead_time_days': None,
            'max_score': None
        }

        if relevant_alerts:
            results['crashes_with_warnings'] += 1

            # Calculate lead time (days before peak)
            first_alert_date = datetime.strptime(relevant_alerts[0]['date'], '%Y-%m-%d')
            lead_time = (peak_date - first_alert_date).days

            # Find max score
            max_score = max(a['score'] for a in relevant_alerts)

            crash_result['lead_time_days'] = lead_time
            crash_result['max_score'] = max_score

            logger.info(f"  [OK] WARNING ISSUED")
            logger.info(f"    - {len(relevant_alerts)} alert(s) in warning window")
            logger.info(f"    - First alert: {relevant_alerts[0]['date']} ({lead_time} days before peak)")
            logger.info(f"    - Max risk score: {max_score:.2f}/10")
        else:
            logger.warning(f"  [X] NO WARNING")
            logger.warning(f"    - No alerts in {crash['warning_window_days']}-day window before peak")

        results['crash_details'].append(crash_result)

    # Calculate false positives (alerts not followed by crashes)
    # Simplified: count alerts not within any crash warning window
    alert_dates = {a['date'] for a in alerts}
    crash_warning_dates = set()

    for crash in crashes:
        peak_date = datetime.strptime(crash['peak_date'], '%Y-%m-%d')
        warning_start = peak_date - timedelta(days=crash['warning_window_days'])

        current_date = warning_start
        while current_date <= peak_date:
            crash_warning_dates.add(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    false_positive_dates = alert_dates - crash_warning_dates
    results['false_positives'] = len(false_positive_dates)

    return results


def calculate_metrics(results: Dict) -> None:
    """
    Calculate and display backtest metrics.

    Args:
        results: Validation results
    """
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("BACKTEST METRICS")
    logger.info("="*80)

    # Detection rate
    detection_rate = (results['crashes_with_warnings'] / results['total_crashes'] * 100
                     if results['total_crashes'] > 0 else 0)

    logger.info(f"\nCrash Detection:")
    logger.info(f"  Total crashes analyzed: {results['total_crashes']}")
    logger.info(f"  Crashes with warnings: {results['crashes_with_warnings']}")
    logger.info(f"  Detection rate: {detection_rate:.1f}%")

    # Lead time stats
    lead_times = [c['lead_time_days'] for c in results['crash_details']
                  if c['lead_time_days'] is not None]

    if lead_times:
        avg_lead_time = sum(lead_times) / len(lead_times)
        logger.info(f"\nLead Time:")
        logger.info(f"  Average: {avg_lead_time:.0f} days")
        logger.info(f"  Range: {min(lead_times)}-{max(lead_times)} days")

    # False positives
    logger.info(f"\nFalse Positives:")
    logger.info(f"  Alerts not near crashes: {results['false_positives']}")

    # Overall assessment
    logger.info("\n" + "="*80)
    logger.info("ASSESSMENT")
    logger.info("="*80)

    if detection_rate >= 75:
        logger.info("[OK] EXCELLENT: System detected most major crashes")
    elif detection_rate >= 50:
        logger.info("[OK] GOOD: System detected half of major crashes")
    else:
        logger.warning("[X] NEEDS IMPROVEMENT: Low detection rate")

    if lead_times and avg_lead_time >= 30:
        logger.info(f"[OK] GOOD LEAD TIME: Average {avg_lead_time:.0f} days advance warning")
    elif lead_times:
        logger.info(f"[OK] SHORT LEAD TIME: Only {avg_lead_time:.0f} days advance warning")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Backtest risk scoring system')
    parser.add_argument('--start-date', type=str,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                        help='End date (YYYY-MM-DD)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Setup
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        logger.info("="*80)
        logger.info(f"AEGIS BACKTEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)

        # Initialize
        config = ConfigManager()
        alert_logic = AlertLogic(config)

        # Load historical data
        records = load_historical_scores(args.start_date, args.end_date)

        if not records:
            logger.error("No historical data available for backtesting")
            logger.error("Run daily_update.py over time to accumulate history")
            return 1

        if len(records) < 30:
            logger.warning(f"Limited data: only {len(records)} records")
            logger.warning("Backtest results may not be reliable with < 30 days of data")

        # Identify alerts
        alerts = identify_alerts(records, alert_logic)

        # Validate against known crashes
        results = validate_against_crashes(alerts, MAJOR_CRASHES)

        # Calculate metrics
        calculate_metrics(results)

        logger.info("\n" + "="*80)
        logger.info("BACKTEST COMPLETED")
        logger.info("="*80)

        return 0

    except Exception as e:
        logger.error(f"BACKTEST FAILED: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
