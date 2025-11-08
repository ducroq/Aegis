"""
Recession Risk Scorer

Calculates recession risk (0-10) using velocity-based indicators:
- Unemployment claims VELOCITY (YoY % change) - leading indicator
- ISM PMI regime cross detection (expansion → contraction)
- Dual yield curve (10Y-2Y + 3M-18M forward spread)
- Consumer sentiment
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class RecessionScorer:
    """
    Calculate recession risk score based on leading economic indicators.

    Philosophy: Rate of change > absolute values for leading signals.
    """

    def __init__(self, config=None):
        """
        Initialize recession scorer.

        Args:
            config: ConfigManager instance (optional, for future threshold overrides)
        """
        self.config = config

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate recession risk score (0-10).

        Args:
            indicators: Dict with recession indicators from DataManager:
                - unemployment_claims_velocity_yoy: YoY % change
                - ism_pmi: Current PMI value
                - ism_pmi_prev: Previous PMI value (for cross detection)
                - yield_curve_10y2y: 10Y-2Y spread
                - yield_curve_10y3m: 10Y-3M spread
                - consumer_sentiment: Consumer sentiment index

        Returns:
            Dict with:
                - score: Overall recession risk (0-10)
                - components: Breakdown of sub-scores
                - signals: List of triggered signals
        """
        score = 0.0
        components = {}
        signals = []

        # 1. Unemployment claims VELOCITY (40% of recession score)
        claims_velocity = indicators.get('unemployment_claims_velocity_yoy')
        if claims_velocity is not None:
            claims_score, claims_signal = self._score_unemployment_velocity(claims_velocity)
            score += claims_score
            components['unemployment_velocity'] = claims_score
            if claims_signal:
                signals.append(claims_signal)
        else:
            logger.warning("Unemployment claims velocity not available")
            components['unemployment_velocity'] = None

        # 2. ISM PMI regime cross (30% of recession score)
        ism_pmi = indicators.get('ism_pmi')
        ism_pmi_prev = indicators.get('ism_pmi_prev')
        if ism_pmi is not None:
            pmi_score, pmi_signal = self._score_pmi_regime(ism_pmi, ism_pmi_prev)
            score += pmi_score
            components['pmi_regime'] = pmi_score
            if pmi_signal:
                signals.append(pmi_signal)
        else:
            logger.warning("ISM PMI not available")
            components['pmi_regime'] = None

        # 3. Dual yield curve (20% of recession score)
        yield_10y2y = indicators.get('yield_curve_10y2y')
        yield_10y3m = indicators.get('yield_curve_10y3m')
        if yield_10y2y is not None or yield_10y3m is not None:
            curve_score, curve_signal = self._score_yield_curve(yield_10y2y, yield_10y3m)
            score += curve_score
            components['yield_curve'] = curve_score
            if curve_signal:
                signals.append(curve_signal)
        else:
            logger.warning("Yield curve data not available")
            components['yield_curve'] = None

        # 4. Consumer sentiment (10% of recession score)
        consumer_sentiment = indicators.get('consumer_sentiment')
        if consumer_sentiment is not None:
            sentiment_score, sentiment_signal = self._score_consumer_sentiment(consumer_sentiment)
            score += sentiment_score
            components['consumer_sentiment'] = sentiment_score
            if sentiment_signal:
                signals.append(sentiment_signal)
        else:
            logger.warning("Consumer sentiment not available")
            components['consumer_sentiment'] = None

        # Cap at 10.0
        score = min(score, 10.0)

        logger.info(f"Recession risk score: {score:.2f}/10")

        return {
            'score': round(score, 2),
            'components': components,
            'signals': signals
        }

    def _score_unemployment_velocity(self, velocity_yoy: float) -> tuple[float, Optional[str]]:
        """
        Score unemployment claims velocity (YoY % change).

        Leading indicator: Sudden spikes in claims precede recession.

        Args:
            velocity_yoy: Year-over-year percent change in 4-week avg claims

        Returns:
            (score, signal): Score 0-4.0, optional signal message
        """
        signal = None

        if velocity_yoy > 15.0:
            # Extreme spike (15%+ YoY) = severe warning
            score = 4.0
            signal = f"CRITICAL: Unemployment claims spiking {velocity_yoy:+.1f}% YoY"
        elif velocity_yoy > 8.0:
            # Moderate spike (8-15% YoY) = elevated risk
            score = 2.0
            signal = f"WARNING: Unemployment claims rising {velocity_yoy:+.1f}% YoY"
        elif velocity_yoy > 3.0:
            # Rising (3-8% YoY) = early warning
            score = 1.0
            signal = f"WATCH: Unemployment claims trending up {velocity_yoy:+.1f}% YoY"
        else:
            # Stable or declining = low risk
            score = 0.0

        logger.debug(f"Unemployment velocity: {velocity_yoy:+.1f}% YoY → score {score:.1f}")
        return score, signal

    def _score_pmi_regime(
        self,
        pmi_current: float,
        pmi_prev: Optional[float]
    ) -> tuple[float, Optional[str]]:
        """
        Score ISM PMI regime (expansion vs contraction).

        Critical signal: Cross from expansion (>50) to contraction (<50).

        Args:
            pmi_current: Current PMI value
            pmi_prev: Previous PMI value (for detecting crosses)

        Returns:
            (score, signal): Score 0-3.0, optional signal message
        """
        signal = None

        # Detect regime cross (expansion → contraction)
        if pmi_prev is not None and pmi_current < 50 and pmi_prev >= 50:
            score = 3.0
            signal = f"CRITICAL: PMI crossed into contraction (was {pmi_prev:.1f}, now {pmi_current:.1f})"

        # Already in contraction
        elif pmi_current < 50:
            if pmi_current < 45:
                score = 2.5
                signal = f"WARNING: PMI in deep contraction ({pmi_current:.1f})"
            else:
                score = 1.5
                signal = f"WATCH: PMI in contraction zone ({pmi_current:.1f})"

        # Slowing expansion
        elif pmi_current < 52:
            score = 1.0
            signal = f"WATCH: PMI slowing, approaching contraction ({pmi_current:.1f})"

        # Healthy expansion
        else:
            score = 0.0

        logger.debug(f"PMI regime: {pmi_current:.1f} → score {score:.1f}")
        return score, signal

    def _score_yield_curve(
        self,
        spread_10y2y: Optional[float],
        spread_10y3m: Optional[float]
    ) -> tuple[float, Optional[str]]:
        """
        Score yield curve inversions.

        Uses dual curves: traditional 10Y-2Y and near-term 10Y-3M.

        Args:
            spread_10y2y: 10-year minus 2-year Treasury spread (%)
            spread_10y3m: 10-year minus 3-month Treasury spread (%)

        Returns:
            (score, signal): Score 0-2.0, optional signal message
        """
        score = 0.0
        signal = None
        inversions = []

        # Traditional 10Y-2Y spread
        if spread_10y2y is not None:
            if spread_10y2y < -0.5:
                # Deep inversion
                score += 1.5
                inversions.append(f"10Y-2Y deeply inverted ({spread_10y2y:.2f}%)")
            elif spread_10y2y < 0:
                # Shallow inversion
                score += 0.75
                inversions.append(f"10Y-2Y inverted ({spread_10y2y:.2f}%)")

        # Near-term 10Y-3M spread (often inverts first)
        if spread_10y3m is not None:
            if spread_10y3m < -0.3:
                # Deep inversion
                score += 1.0
                inversions.append(f"10Y-3M deeply inverted ({spread_10y3m:.2f}%)")
            elif spread_10y3m < 0:
                # Shallow inversion
                score += 0.5
                inversions.append(f"10Y-3M inverted ({spread_10y3m:.2f}%)")

        # Bonus for dual inversion (both curves inverted)
        if spread_10y2y is not None and spread_10y3m is not None:
            if spread_10y2y < 0 and spread_10y3m < 0:
                score += 0.5
                signal = f"CRITICAL: Dual yield curve inversion - {', '.join(inversions)}"
            elif inversions:
                signal = f"WARNING: {', '.join(inversions)}"

        # Cap at 2.0
        score = min(score, 2.0)

        logger.debug(f"Yield curve: {spread_10y2y}/{spread_10y3m} → score {score:.1f}")
        return score, signal

    def _score_consumer_sentiment(self, sentiment: float) -> tuple[float, Optional[str]]:
        """
        Score consumer confidence/sentiment.

        Args:
            sentiment: Consumer sentiment index (University of Michigan)

        Returns:
            (score, signal): Score 0-1.0, optional signal message
        """
        signal = None

        if sentiment < 70:
            # Very low confidence
            score = 1.0
            signal = f"WATCH: Consumer sentiment very low ({sentiment:.1f})"
        elif sentiment < 80:
            # Low confidence
            score = 0.5
            signal = f"WATCH: Consumer sentiment weak ({sentiment:.1f})"
        else:
            # Normal to strong confidence
            score = 0.0

        logger.debug(f"Consumer sentiment: {sentiment:.1f} → score {score:.1f}")
        return score, signal


def main():
    """Test recession scorer."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Recession Scorer...\n")

    scorer = RecessionScorer()

    # Test case 1: Normal conditions
    print("="*50)
    print("TEST 1: Normal Economic Conditions")
    print("="*50)
    indicators_normal = {
        'unemployment_claims_velocity_yoy': 2.0,  # Slight increase
        'ism_pmi': 54.0,  # Expansion
        'ism_pmi_prev': 53.5,
        'yield_curve_10y2y': 0.3,  # Positive (normal)
        'yield_curve_10y3m': 0.5,
        'consumer_sentiment': 95.0
    }
    result = scorer.calculate_score(indicators_normal)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals: {result['signals']}")

    # Test case 2: Recession warning
    print("\n" + "="*50)
    print("TEST 2: Recession Warning Conditions")
    print("="*50)
    indicators_warning = {
        'unemployment_claims_velocity_yoy': 12.0,  # Spiking
        'ism_pmi': 48.5,  # Contraction
        'ism_pmi_prev': 51.0,  # Just crossed below 50
        'yield_curve_10y2y': -0.6,  # Inverted
        'yield_curve_10y3m': -0.4,
        'consumer_sentiment': 72.0
    }
    result = scorer.calculate_score(indicators_warning)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals:")
    for signal in result['signals']:
        print(f"  - {signal}")

    # Test case 3: Severe recession risk
    print("\n" + "="*50)
    print("TEST 3: Severe Recession Risk")
    print("="*50)
    indicators_severe = {
        'unemployment_claims_velocity_yoy': 20.0,  # Extreme spike
        'ism_pmi': 42.0,  # Deep contraction
        'ism_pmi_prev': 43.0,
        'yield_curve_10y2y': -1.2,  # Deep inversion
        'yield_curve_10y3m': -0.8,
        'consumer_sentiment': 65.0
    }
    result = scorer.calculate_score(indicators_severe)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals:")
    for signal in result['signals']:
        print(f"  - {signal}")

    print("\n" + "="*50)
    print("Recession Scorer test PASSED")
    print("="*50)


if __name__ == '__main__':
    main()
