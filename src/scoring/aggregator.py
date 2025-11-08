"""
Risk Score Aggregator

Combines all dimension scores into overall risk score using weighted average.
"""

import logging
from typing import Dict, Any, Optional

from src.config.config_manager import ConfigManager
from src.scoring.recession import RecessionScorer
from src.scoring.credit import CreditScorer
from src.scoring.valuation import ValuationScorer
from src.scoring.liquidity import LiquidityScorer
from src.scoring.positioning import PositioningScorer


logger = logging.getLogger(__name__)


class RiskAggregator:
    """
    Aggregate individual dimension scores into overall risk score.

    Weights (configurable, must sum to 1.0):
    - Recession: 0.30
    - Credit: 0.25
    - Valuation: 0.20
    - Liquidity: 0.15
    - Positioning: 0.10
    """

    def __init__(self, config: Optional[ConfigManager] = None):
        """
        Initialize risk aggregator.

        Args:
            config: ConfigManager instance. If None, creates new one.
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        # Get weights from config
        self.weights = config.get_all_weights()
        self._validate_weights()

        # Initialize scorers
        self.recession_scorer = RecessionScorer(config)
        self.credit_scorer = CreditScorer(config)
        self.valuation_scorer = ValuationScorer(config)
        self.liquidity_scorer = LiquidityScorer(config)
        self.positioning_scorer = PositioningScorer(config)

        logger.info("Risk aggregator initialized with weights: %s", self.weights)

    def _validate_weights(self) -> None:
        """Validate that weights sum to 1.0."""
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Weights must sum to 1.0, got {total}. Weights: {self.weights}"
            )

    def calculate_overall_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall risk score from all dimensions.

        Args:
            data: Dict with data for all dimensions (from DataManager.fetch_all_indicators())

        Returns:
            Dict with:
                - overall_score: Weighted average risk (0-10)
                - dimension_scores: Individual dimension scores
                - all_signals: All triggered signals from all dimensions
                - metadata: Calculation details
        """
        logger.info("Calculating overall risk score...")

        # Calculate individual dimension scores
        recession_result = self.recession_scorer.calculate_score(data.get('recession', {}))
        credit_result = self.credit_scorer.calculate_score(data.get('credit', {}))
        valuation_result = self.valuation_scorer.calculate_score(data.get('valuation', {}))
        liquidity_result = self.liquidity_scorer.calculate_score(data.get('liquidity', {}))
        positioning_result = self.positioning_scorer.calculate_score(data.get('positioning', {}))

        # Extract scores
        dimension_scores = {
            'recession': recession_result['score'],
            'credit': credit_result['score'],
            'valuation': valuation_result['score'],
            'liquidity': liquidity_result['score'],
            'positioning': positioning_result['score']
        }

        # Calculate weighted average
        overall_score = sum(
            dimension_scores[dim] * self.weights[dim]
            for dim in dimension_scores
        )

        # Round to 2 decimal places
        overall_score = round(overall_score, 2)

        # Determine risk tier
        tier = self._get_risk_tier(overall_score)

        # Collect all signals
        all_signals = {
            'recession': recession_result['signals'],
            'credit': credit_result['signals'],
            'valuation': valuation_result['signals'],
            'liquidity': liquidity_result['signals'],
            'positioning': positioning_result['signals']
        }

        logger.info(f"Overall risk score: {overall_score:.2f}/10 ({tier})")

        return {
            'overall_score': overall_score,
            'tier': tier,
            'dimension_scores': dimension_scores,
            'dimension_details': {
                'recession': recession_result,
                'credit': credit_result,
                'valuation': valuation_result,
                'liquidity': liquidity_result,
                'positioning': positioning_result
            },
            'all_signals': all_signals,
            'weights': self.weights,
            'metadata': {
                'weighted_calculation': {
                    dim: f"{dimension_scores[dim]:.2f} × {self.weights[dim]:.2f} = {dimension_scores[dim] * self.weights[dim]:.2f}"
                    for dim in dimension_scores
                }
            }
        }

    def _get_risk_tier(self, score: float) -> str:
        """
        Get risk tier based on score.

        Args:
            score: Overall risk score (0-10)

        Returns:
            'GREEN', 'YELLOW', or 'RED'
        """
        # Get thresholds from config
        thresholds = self.config.get_alert_thresholds()
        red_threshold = thresholds.get('red_threshold', 8.0)
        yellow_threshold = thresholds.get('yellow_threshold', 6.5)

        if score >= red_threshold:
            return 'RED'
        elif score >= yellow_threshold:
            return 'YELLOW'
        else:
            return 'GREEN'


def main():
    """Test risk aggregator."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Risk Aggregator...\n")

    aggregator = RiskAggregator()

    # Test case: Mixed conditions
    print("="*60)
    print("TEST: Mixed Market Conditions")
    print("="*60)

    test_data = {
        'recession': {
            'unemployment_claims_velocity_yoy': 5.0,
            'ism_pmi': 51.0,
            'ism_pmi_prev': 52.0,
            'yield_curve_10y2y': -0.2,
            'yield_curve_10y3m': 0.1,
            'consumer_sentiment': 85.0
        },
        'credit': {
            'hy_spread': 450,
            'hy_spread_velocity_20d': 3.0,
            'ig_spread_bbb': 180,
            'ted_spread': 0.5,
            'bank_lending_standards': 12.0
        },
        'valuation': {
            'shiller_cape': 28.0,
            'wilshire_5000': 45000,
            'gdp': 28000,  # Results in ~160% ratio
            'sp500_forward_pe': 21.0
        },
        'liquidity': {
            'fed_funds_rate': 5.5,
            'fed_funds_velocity_6m': 1.5,
            'm2_velocity_yoy': 3.0,
            'vix': 18.0
        },
        'positioning': {
            'sp500_net_speculative': None,
            'treasury_net_speculative': None,
            'vix_proxy': 18.0
        }
    }

    result = aggregator.calculate_overall_risk(test_data)

    print(f"\nOverall Risk Score: {result['overall_score']:.2f}/10 ({result['tier']})")
    print(f"\nDimension Scores:")
    for dim, score in result['dimension_scores'].items():
        weight = result['weights'][dim]
        weighted = score * weight
        print(f"  {dim.capitalize():15s}: {score:.2f}/10 (weight: {weight:.2f}) = {weighted:.2f}")

    print(f"\nWeighted Calculation:")
    for dim, calc in result['metadata']['weighted_calculation'].items():
        print(f"  {dim.capitalize():15s}: {calc}")

    print(f"\nTotal: {result['overall_score']:.2f}/10")

    print(f"\nAll Signals:")
    for dim, signals in result['all_signals'].items():
        if signals:
            print(f"\n  {dim.upper()}:")
            for signal in signals:
                print(f"    - {signal}")

    print("\n" + "="*60)
    print("Risk Aggregator test PASSED")
    print("="*60)


if __name__ == '__main__':
    main()
