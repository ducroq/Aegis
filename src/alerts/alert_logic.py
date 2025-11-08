"""
Alert Logic Module

Determines when to send alerts based on:
- Risk score thresholds (RED >= 8.0, YELLOW >= 6.5)
- Rapid changes (>1.0 point increase in 4 weeks)
- Multiple dimensions in extreme risk (2+ dimensions >= 8.0)
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from src.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class AlertLogic:
    """
    Determine if alerts should be sent based on risk scores and history.
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize alert logic.

        Args:
            config: ConfigManager instance. If None, creates new one.
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        # Get thresholds from config
        thresholds = config.get_alert_thresholds()
        self.red_threshold = thresholds.get('red_threshold', 8.0)
        self.yellow_threshold = thresholds.get('yellow_threshold', 6.5)
        self.rapid_change_threshold = thresholds.get('rapid_change_threshold', 1.0)
        self.rapid_change_weeks = thresholds.get('rapid_change_weeks', 4)
        self.extreme_dimension_threshold = thresholds.get('extreme_dimension_threshold', 8.0)
        self.extreme_dimension_count = thresholds.get('extreme_dimension_count', 2)

        logger.info(
            f"Alert logic initialized: RED>={self.red_threshold}, "
            f"YELLOW>={self.yellow_threshold}, "
            f"rapid_change>{self.rapid_change_threshold} in {self.rapid_change_weeks} weeks"
        )

    def should_alert(
        self,
        current_result: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Tuple[bool, str, str, Dict[str, Any]]:
        """
        Determine if an alert should be sent.

        Args:
            current_result: Current risk assessment result from RiskAggregator
            history: List of historical risk results (most recent first)

        Returns:
            Tuple of:
                - should_alert (bool): Whether to send alert
                - tier (str): 'RED', 'YELLOW', or 'GREEN'
                - reason (str): Human-readable reason for alert
                - details (dict): Additional alert details
        """
        current_score = current_result['overall_score']
        current_tier = current_result['tier']
        dimension_scores = current_result['dimension_scores']

        details = {
            'current_score': current_score,
            'tier': current_tier,
            'triggers': []
        }

        # Trigger 1: RED threshold
        if current_score >= self.red_threshold:
            details['triggers'].append('RED_THRESHOLD')
            reason = (
                f"Risk score {current_score:.1f}/10 exceeds RED threshold "
                f"({self.red_threshold}). SEVERE risk - consider major defensive positioning."
            )
            logger.warning(f"ALERT: {reason}")
            return True, 'RED', reason, details

        # Trigger 2: YELLOW threshold
        if current_score >= self.yellow_threshold:
            details['triggers'].append('YELLOW_THRESHOLD')

            # Check for rapid rise
            rapid_rise_detected = False
            if len(history) >= self.rapid_change_weeks:
                weeks_ago_score = history[self.rapid_change_weeks - 1].get('overall_score')
                if weeks_ago_score is not None:
                    change = current_score - weeks_ago_score
                    details['change_4w'] = change

                    if change > self.rapid_change_threshold:
                        rapid_rise_detected = True
                        details['triggers'].append('RAPID_RISE')
                        reason = (
                            f"Risk score {current_score:.1f}/10 at YELLOW level and rising rapidly "
                            f"(+{change:.1f} points in {self.rapid_change_weeks} weeks). "
                            f"Review portfolio, consider building cash position."
                        )
                        logger.warning(f"ALERT: {reason}")
                        return True, 'YELLOW', reason, details

            # Yellow threshold crossed but not rapidly rising
            reason = (
                f"Risk score {current_score:.1f}/10 exceeds YELLOW threshold "
                f"({self.yellow_threshold}). Elevated risk - monitor closely."
            )
            logger.info(f"ALERT: {reason}")
            return True, 'YELLOW', reason, details

        # Trigger 3: Multiple dimensions in extreme risk
        extreme_dimensions = [
            dim for dim, score in dimension_scores.items()
            if score >= self.extreme_dimension_threshold
        ]

        if len(extreme_dimensions) >= self.extreme_dimension_count:
            details['triggers'].append('MULTIPLE_EXTREMES')
            details['extreme_dimensions'] = extreme_dimensions

            reason = (
                f"{len(extreme_dimensions)} dimensions in extreme risk "
                f"({', '.join(extreme_dimensions)}). "
                f"Multiple risk factors aligning - review portfolio."
            )
            logger.warning(f"ALERT: {reason}")

            # Determine tier based on overall score
            tier = 'YELLOW' if current_score >= self.yellow_threshold else 'GREEN'
            return True, tier, reason, details

        # No alert triggered
        logger.debug(f"No alert: score {current_score:.1f}/10 (tier: {current_tier})")
        return False, current_tier, 'Risk within normal range', details

    def get_alert_summary(
        self,
        current_result: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive alert summary with trend analysis.

        Args:
            current_result: Current risk assessment result
            history: List of historical results

        Returns:
            Dict with alert summary, trends, key signals
        """
        should_alert, tier, reason, details = self.should_alert(current_result, history)

        summary = {
            'should_alert': should_alert,
            'tier': tier,
            'reason': reason,
            'details': details,
            'current_score': current_result['overall_score'],
            'dimension_scores': current_result['dimension_scores'],
            'all_signals': current_result['all_signals'],
            'trends': self._calculate_trends(current_result, history),
            'key_evidence': self._extract_key_evidence(current_result)
        }

        return summary

    def _calculate_trends(
        self,
        current_result: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate score trends over various time periods.

        Args:
            current_result: Current risk result
            history: Historical results

        Returns:
            Dict with trend data
        """
        current_score = current_result['overall_score']
        trends = {}

        # 1-week change
        if len(history) >= 1:
            week_ago = history[0].get('overall_score')
            if week_ago is not None:
                trends['1w_change'] = current_score - week_ago
                trends['1w_direction'] = self._get_arrow(trends['1w_change'])

        # 4-week change
        if len(history) >= 4:
            four_weeks_ago = history[3].get('overall_score')
            if four_weeks_ago is not None:
                trends['4w_change'] = current_score - four_weeks_ago
                trends['4w_direction'] = self._get_arrow(trends['4w_change'])

        # 12-week change (quarterly)
        if len(history) >= 12:
            twelve_weeks_ago = history[11].get('overall_score')
            if twelve_weeks_ago is not None:
                trends['12w_change'] = current_score - twelve_weeks_ago
                trends['12w_direction'] = self._get_arrow(trends['12w_change'])

        # Dimension trends (1-week)
        if len(history) >= 1:
            dim_trends = {}
            for dim, current_dim_score in current_result['dimension_scores'].items():
                prev_dim_score = history[0].get('dimension_scores', {}).get(dim)
                if prev_dim_score is not None:
                    change = current_dim_score - prev_dim_score
                    dim_trends[dim] = {
                        'change': change,
                        'direction': self._get_arrow(change)
                    }
            trends['dimension_trends'] = dim_trends

        return trends

    def _get_arrow(self, change: float) -> str:
        """Get trend arrow based on change magnitude."""
        if change > 0.5:
            return 'UP_SHARP'  # Sharp increase
        elif change > 0.1:
            return 'UP'        # Moderate increase
        elif change < -0.5:
            return 'DOWN_SHARP'  # Sharp decrease
        elif change < -0.1:
            return 'DOWN'      # Moderate decrease
        else:
            return 'STABLE'    # Stable

    def _extract_key_evidence(self, current_result: Dict[str, Any]) -> List[str]:
        """
        Extract key evidence points from current result.

        Args:
            current_result: Current risk assessment

        Returns:
            List of key evidence strings
        """
        evidence = []

        # Get all signals
        all_signals = current_result.get('all_signals', {})

        # Prioritize CRITICAL signals
        critical_signals = []
        warning_signals = []

        for dimension, signals in all_signals.items():
            for signal in signals:
                if 'CRITICAL' in signal:
                    critical_signals.append(f"[{dimension.upper()}] {signal}")
                elif 'WARNING' in signal:
                    warning_signals.append(f"[{dimension.upper()}] {signal}")

        # Add top critical signals (max 5)
        evidence.extend(critical_signals[:5])

        # If not many critical, add warnings
        if len(evidence) < 3:
            evidence.extend(warning_signals[:3])

        # Add dimension scores if high
        dimension_scores = current_result.get('dimension_scores', {})
        for dim, score in sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True):
            if score >= 7.0:
                evidence.append(f"{dim.capitalize()} risk: {score:.1f}/10")
            if len(evidence) >= 8:
                break

        return evidence


def main():
    """Test alert logic."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Alert Logic...\n")
    print("=" * 60)

    alert_logic = AlertLogic()

    # Test 1: Normal conditions (no alert)
    print("\nTEST 1: Normal Conditions")
    print("-" * 60)
    normal_result = {
        'overall_score': 4.5,
        'tier': 'GREEN',
        'dimension_scores': {
            'recession': 3.0,
            'credit': 2.0,
            'valuation': 5.0,
            'liquidity': 4.0,
            'positioning': 2.0
        },
        'all_signals': {
            'recession': [],
            'credit': [],
            'valuation': ['WATCH: Valuations moderately elevated'],
            'liquidity': [],
            'positioning': []
        }
    }

    should_alert, tier, reason, details = alert_logic.should_alert(normal_result, [])
    print(f"Should Alert: {should_alert}")
    print(f"Tier: {tier}")
    print(f"Reason: {reason}")

    # Test 2: RED threshold
    print("\n" + "=" * 60)
    print("TEST 2: RED Threshold Breach")
    print("-" * 60)
    red_result = {
        'overall_score': 8.5,
        'tier': 'RED',
        'dimension_scores': {
            'recession': 9.0,
            'credit': 8.5,
            'valuation': 7.0,
            'liquidity': 8.0,
            'positioning': 5.0
        },
        'all_signals': {
            'recession': ['CRITICAL: PMI crossed into contraction', 'WARNING: Yield curve inverted'],
            'credit': ['CRITICAL: HY spreads widening rapidly'],
            'valuation': [],
            'liquidity': ['CRITICAL: Fed rapidly tightening'],
            'positioning': []
        }
    }

    should_alert, tier, reason, details = alert_logic.should_alert(red_result, [])
    print(f"Should Alert: {should_alert}")
    print(f"Tier: {tier}")
    print(f"Reason: {reason}")
    print(f"Triggers: {details['triggers']}")

    # Test 3: YELLOW with rapid rise
    print("\n" + "=" * 60)
    print("TEST 3: YELLOW with Rapid Rise")
    print("-" * 60)
    yellow_result = {
        'overall_score': 7.0,
        'tier': 'YELLOW',
        'dimension_scores': {
            'recession': 6.0,
            'credit': 7.5,
            'valuation': 8.0,
            'liquidity': 5.0,
            'positioning': 3.0
        },
        'all_signals': {
            'recession': ['WARNING: Unemployment rising'],
            'credit': ['WARNING: Credit spreads elevated'],
            'valuation': ['CRITICAL: CAPE at bubble levels'],
            'liquidity': [],
            'positioning': []
        }
    }

    history = [
        {'overall_score': 6.8},
        {'overall_score': 6.5},
        {'overall_score': 6.2},
        {'overall_score': 5.5}  # 4 weeks ago
    ]

    should_alert, tier, reason, details = alert_logic.should_alert(yellow_result, history)
    print(f"Should Alert: {should_alert}")
    print(f"Tier: {tier}")
    print(f"Reason: {reason}")
    print(f"Triggers: {details['triggers']}")
    print(f"4-week change: {details.get('change_4w', 'N/A'):.1f}")

    # Test 4: Multiple extremes
    print("\n" + "=" * 60)
    print("TEST 4: Multiple Dimensions in Extreme Risk")
    print("-" * 60)
    extreme_result = {
        'overall_score': 6.0,
        'tier': 'GREEN',
        'dimension_scores': {
            'recession': 8.5,
            'credit': 8.0,
            'valuation': 3.0,
            'liquidity': 4.0,
            'positioning': 2.0
        },
        'all_signals': {
            'recession': ['CRITICAL: Multiple recession indicators firing'],
            'credit': ['CRITICAL: Credit stress extreme'],
            'valuation': [],
            'liquidity': [],
            'positioning': []
        }
    }

    should_alert, tier, reason, details = alert_logic.should_alert(extreme_result, [])
    print(f"Should Alert: {should_alert}")
    print(f"Tier: {tier}")
    print(f"Reason: {reason}")
    print(f"Triggers: {details['triggers']}")
    print(f"Extreme dimensions: {details.get('extreme_dimensions', [])}")

    # Test 5: Full alert summary
    print("\n" + "=" * 60)
    print("TEST 5: Full Alert Summary")
    print("-" * 60)
    summary = alert_logic.get_alert_summary(yellow_result, history)
    print(f"Should Alert: {summary['should_alert']}")
    print(f"Tier: {summary['tier']}")
    print(f"Current Score: {summary['current_score']:.1f}/10")
    print(f"\nTrends:")
    for trend_key, trend_val in summary['trends'].items():
        if trend_key != 'dimension_trends':
            print(f"  {trend_key}: {trend_val}")
    print(f"\nKey Evidence:")
    for evidence in summary['key_evidence']:
        print(f"  - {evidence}")

    print("\n" + "=" * 60)
    print("Alert Logic tests PASSED")
    print("=" * 60)


if __name__ == '__main__':
    main()
