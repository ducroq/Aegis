"""
History Manager

Stores and retrieves historical risk scores and raw indicator data.

Storage format:
- data/history/risk_scores.csv: Overall risk scores and dimension scores
- data/history/raw_indicators.csv: Raw indicator values
"""

import logging
import os
import csv
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pathlib import Path


logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manage historical risk score and indicator data storage.
    """

    def __init__(self, data_dir: str = "data/history"):
        """
        Initialize history manager.

        Args:
            data_dir: Directory for historical data storage
        """
        self.data_dir = Path(data_dir)
        self.risk_scores_file = self.data_dir / "risk_scores.csv"
        self.raw_indicators_file = self.data_dir / "raw_indicators.csv"

        # Create directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"History manager initialized: {self.data_dir}")

    def save_risk_score(
        self,
        result: Dict[str, Any],
        alert_sent: bool = False,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Save risk score result to history.

        Args:
            result: Risk assessment result from RiskAggregator
            alert_sent: Whether an alert was sent
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Prepare row data
        row = {
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S'),
            'overall_risk': result['overall_score'],
            'tier': result['tier'],
            'recession': result['dimension_scores']['recession'],
            'credit': result['dimension_scores']['credit'],
            'valuation': result['dimension_scores']['valuation'],
            'liquidity': result['dimension_scores']['liquidity'],
            'positioning': result['dimension_scores']['positioning'],
            'alerted': alert_sent
        }

        # Check if file exists
        file_exists = self.risk_scores_file.exists()

        # Write to CSV
        with open(self.risk_scores_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'date', 'time', 'overall_risk', 'tier',
                'recession', 'credit', 'valuation', 'liquidity', 'positioning',
                'alerted'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header if new file
            if not file_exists:
                writer.writeheader()
                logger.info(f"Created new risk scores file: {self.risk_scores_file}")

            writer.writerow(row)

        logger.info(
            f"Saved risk score: {result['overall_score']:.1f}/10 ({result['tier']}) "
            f"[Alert: {alert_sent}]"
        )

    def save_raw_indicators(
        self,
        indicators: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Save raw indicator data to history.

        Args:
            indicators: Dict of indicator values from DataManager
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Flatten nested dict
        flattened = {
            'date': timestamp.strftime('%Y-%m-%d'),
            'time': timestamp.strftime('%H:%M:%S')
        }

        # Flatten dimension data
        for dimension, data in indicators.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    flattened[f"{dimension}.{key}"] = value
            else:
                flattened[dimension] = data

        # Check if file exists
        file_exists = self.raw_indicators_file.exists()

        # Write to CSV
        with open(self.raw_indicators_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = sorted(flattened.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Write header if new file
            if not file_exists:
                writer.writeheader()
                logger.info(f"Created new raw indicators file: {self.raw_indicators_file}")

            writer.writerow(flattened)

        logger.debug(f"Saved {len(flattened)-2} raw indicators")

    def get_recent_scores(self, num_records: int = 12) -> List[Dict[str, Any]]:
        """
        Get recent risk scores from history.

        Args:
            num_records: Number of recent records to retrieve

        Returns:
            List of risk score dicts (most recent first)
        """
        if not self.risk_scores_file.exists():
            logger.warning("No risk score history found")
            return []

        # Read all records
        records = []
        with open(self.risk_scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                record = {
                    'date': row['date'],
                    'time': row['time'],
                    'overall_score': float(row['overall_risk']),
                    'tier': row['tier'],
                    'dimension_scores': {
                        'recession': float(row['recession']),
                        'credit': float(row['credit']),
                        'valuation': float(row['valuation']),
                        'liquidity': float(row['liquidity']),
                        'positioning': float(row['positioning'])
                    },
                    'alerted': row['alerted'].lower() == 'true'
                }
                records.append(record)

        # Return most recent N records (reverse order)
        recent = records[-num_records:] if len(records) > num_records else records
        recent.reverse()

        logger.info(f"Retrieved {len(recent)} recent risk scores")
        return recent

    def get_scores_by_date_range(
        self,
        start_date: date,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get risk scores within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive), defaults to today

        Returns:
            List of risk score dicts
        """
        if end_date is None:
            end_date = date.today()

        if not self.risk_scores_file.exists():
            logger.warning("No risk score history found")
            return []

        records = []
        with open(self.risk_scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_date = datetime.strptime(row['date'], '%Y-%m-%d').date()

                if start_date <= row_date <= end_date:
                    record = {
                        'date': row['date'],
                        'time': row['time'],
                        'overall_score': float(row['overall_risk']),
                        'tier': row['tier'],
                        'dimension_scores': {
                            'recession': float(row['recession']),
                            'credit': float(row['credit']),
                            'valuation': float(row['valuation']),
                            'liquidity': float(row['liquidity']),
                            'positioning': float(row['positioning'])
                        },
                        'alerted': row['alerted'].lower() == 'true'
                    }
                    records.append(record)

        logger.info(
            f"Retrieved {len(records)} risk scores from {start_date} to {end_date}"
        )
        return records

    def get_alert_history(self, num_records: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts from history.

        Args:
            num_records: Number of recent alerts to retrieve

        Returns:
            List of alert records (most recent first)
        """
        if not self.risk_scores_file.exists():
            logger.warning("No risk score history found")
            return []

        alerts = []
        with open(self.risk_scores_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['alerted'].lower() == 'true':
                    record = {
                        'date': row['date'],
                        'time': row['time'],
                        'overall_score': float(row['overall_risk']),
                        'tier': row['tier']
                    }
                    alerts.append(record)

        # Return most recent N alerts (reverse order)
        recent_alerts = alerts[-num_records:] if len(alerts) > num_records else alerts
        recent_alerts.reverse()

        logger.info(f"Retrieved {len(recent_alerts)} recent alerts")
        return recent_alerts

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored history.

        Returns:
            Dict with history statistics
        """
        stats = {
            'risk_scores_exist': self.risk_scores_file.exists(),
            'raw_indicators_exist': self.raw_indicators_file.exists(),
            'risk_scores_count': 0,
            'raw_indicators_count': 0,
            'alerts_count': 0,
            'date_range': None
        }

        if self.risk_scores_file.exists():
            with open(self.risk_scores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                stats['risk_scores_count'] = len(rows)

                if rows:
                    stats['date_range'] = {
                        'start': rows[0]['date'],
                        'end': rows[-1]['date']
                    }
                    stats['alerts_count'] = sum(
                        1 for row in rows if row['alerted'].lower() == 'true'
                    )

        if self.raw_indicators_file.exists():
            with open(self.raw_indicators_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                stats['raw_indicators_count'] = len(list(reader))

        return stats


def main():
    """Test history manager."""
    import sys
    from datetime import timedelta

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing History Manager...\n")
    print("=" * 60)

    # Use test directory
    test_dir = "data/history_test"
    history = HistoryManager(test_dir)

    # Test 1: Save risk scores
    print("\nTEST 1: Save Risk Scores")
    print("-" * 60)

    test_result = {
        'overall_score': 6.5,
        'tier': 'YELLOW',
        'dimension_scores': {
            'recession': 5.0,
            'credit': 7.0,
            'valuation': 8.0,
            'liquidity': 4.0,
            'positioning': 3.0
        }
    }

    # Save multiple records with different dates
    base_date = datetime.now() - timedelta(days=7)
    for i in range(8):
        timestamp = base_date + timedelta(days=i)
        test_result['overall_score'] = 6.5 + (i * 0.2)
        history.save_risk_score(test_result, alert_sent=(i >= 5), timestamp=timestamp)

    print(f"Saved 8 risk score records")

    # Test 2: Save raw indicators
    print("\n" + "=" * 60)
    print("TEST 2: Save Raw Indicators")
    print("-" * 60)

    test_indicators = {
        'recession': {
            'unemployment_claims_velocity_yoy': 5.2,
            'ism_pmi': 51.3,
            'yield_curve_10y2y': -0.3
        },
        'credit': {
            'hy_spread': 450,
            'hy_spread_velocity_20d': 3.5
        }
    }

    history.save_raw_indicators(test_indicators)
    print("Saved raw indicators")

    # Test 3: Get recent scores
    print("\n" + "=" * 60)
    print("TEST 3: Get Recent Scores")
    print("-" * 60)

    recent = history.get_recent_scores(num_records=5)
    print(f"Retrieved {len(recent)} recent scores:")
    for record in recent:
        print(f"  {record['date']}: {record['overall_score']:.1f}/10 ({record['tier']}) "
              f"[Alerted: {record['alerted']}]")

    # Test 4: Get alert history
    print("\n" + "=" * 60)
    print("TEST 4: Get Alert History")
    print("-" * 60)

    alerts = history.get_alert_history()
    print(f"Retrieved {len(alerts)} alerts:")
    for alert in alerts:
        print(f"  {alert['date']} {alert['time']}: {alert['overall_score']:.1f}/10 ({alert['tier']})")

    # Test 5: Get date range
    print("\n" + "=" * 60)
    print("TEST 5: Get Scores by Date Range")
    print("-" * 60)

    start = (datetime.now() - timedelta(days=3)).date()
    end = datetime.now().date()
    range_scores = history.get_scores_by_date_range(start, end)
    print(f"Retrieved {len(range_scores)} scores from {start} to {end}")

    # Test 6: Get stats
    print("\n" + "=" * 60)
    print("TEST 6: Get History Statistics")
    print("-" * 60)

    stats = history.get_stats()
    print(f"Risk scores exist: {stats['risk_scores_exist']}")
    print(f"Total risk scores: {stats['risk_scores_count']}")
    print(f"Total alerts: {stats['alerts_count']}")
    print(f"Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")

    print("\n" + "=" * 60)
    print("History Manager tests PASSED")
    print("=" * 60)
    print(f"\nTest data saved to: {history.data_dir}")


if __name__ == '__main__':
    main()
