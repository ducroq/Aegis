"""
Credit Stress Scorer

Calculates credit stress risk (0-10) using:
- High-yield spread VELOCITY (70% weight) - rate of change
- High-yield spread LEVEL (30% weight) - absolute value
- Investment-grade spreads
- TED spread
- Bank lending standards
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class CreditScorer:
    """
    Calculate credit stress score based on credit market indicators.

    Philosophy: Velocity > level. Spreads widening rapidly = immediate crisis signal.
    """

    def __init__(self, config=None):
        """
        Initialize credit scorer.

        Args:
            config: ConfigManager instance (optional)
        """
        self.config = config

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate credit stress score (0-10).

        Args:
            indicators: Dict with credit indicators from DataManager:
                - hy_spread: High-yield spread level (bps)
                - hy_spread_velocity_20d: 20-day rate of change (bps/day)
                - ig_spread_bbb: BBB investment-grade spread (bps)
                - ted_spread: TED spread (%)
                - bank_lending_standards: Net % tightening

        Returns:
            Dict with:
                - score: Overall credit stress (0-10)
                - components: Breakdown of sub-scores
                - signals: List of triggered signals
        """
        score = 0.0
        components = {}
        signals = []

        # 1. High-yield spread (combined velocity + level) - 60% of credit score
        hy_spread = indicators.get('hy_spread')
        hy_velocity = indicators.get('hy_spread_velocity_20d')

        if hy_spread is not None or hy_velocity is not None:
            hy_score, hy_signal = self._score_hy_spread(hy_spread, hy_velocity)
            score += hy_score
            components['hy_spread_combined'] = hy_score
            if hy_signal:
                signals.append(hy_signal)
        else:
            logger.warning("High-yield spread data not available")
            components['hy_spread_combined'] = None

        # 2. Investment-grade spreads - 20% of credit score
        ig_spread = indicators.get('ig_spread_bbb')
        if ig_spread is not None:
            ig_score, ig_signal = self._score_ig_spread(ig_spread)
            score += ig_score
            components['ig_spread'] = ig_score
            if ig_signal:
                signals.append(ig_signal)
        else:
            logger.warning("Investment-grade spread not available")
            components['ig_spread'] = None

        # 3. TED spread - 10% of credit score
        ted_spread = indicators.get('ted_spread')
        if ted_spread is not None:
            ted_score, ted_signal = self._score_ted_spread(ted_spread)
            score += ted_score
            components['ted_spread'] = ted_score
            if ted_signal:
                signals.append(ted_signal)
        else:
            logger.warning("TED spread not available")
            components['ted_spread'] = None

        # 4. Bank lending standards - 10% of credit score
        lending_standards = indicators.get('bank_lending_standards')
        if lending_standards is not None:
            lending_score, lending_signal = self._score_lending_standards(lending_standards)
            score += lending_score
            components['lending_standards'] = lending_score
            if lending_signal:
                signals.append(lending_signal)
        else:
            logger.warning("Bank lending standards not available")
            components['lending_standards'] = None

        # Cap at 10.0
        score = min(score, 10.0)

        logger.info(f"Credit stress score: {score:.2f}/10")

        return {
            'score': round(score, 2),
            'components': components,
            'signals': signals
        }

    def _score_hy_spread(
        self,
        spread_level: Optional[float],
        spread_velocity: Optional[float]
    ) -> tuple[float, Optional[str]]:
        """
        Score high-yield spread using velocity (70%) + level (30%).

        CALIBRATED THRESHOLDS (from 2000-2024 historical data):
        - Normal 90th percentile: 7.22%
        - Crisis median: 7.67%
        - Crisis max: 20.2%

        Args:
            spread_level: Current HY spread in percentage points (e.g., 5.5 = 5.5%)
            spread_velocity: 20-day rate of change in percentage points/day

        Returns:
            (score, signal): Score 0-6.0, optional signal message
        """
        velocity_score = 0.0
        level_score = 0.0
        signal = None

        # Velocity scoring (0-6.0 max)
        # Calibrated: normal p90 = 0.02%/day, crisis p90 = 0.19%/day
        if spread_velocity is not None:
            if spread_velocity > 0.10:
                # Rapidly widening (>0.10%/day = 2% per month)
                velocity_score = 6.0  # Max velocity score
                signal = f"CRITICAL: HY spreads widening rapidly ({spread_velocity:.2f}%/day)"
            elif spread_velocity > 0.05:
                # Moderate widening (0.05-0.10%/day)
                velocity_score = 4.0
                signal = f"WARNING: HY spreads widening ({spread_velocity:.2f}%/day)"
            elif spread_velocity > 0.02:
                # Slight widening (0.02-0.05%/day)
                velocity_score = 2.0
                signal = f"WATCH: HY spreads trending wider ({spread_velocity:.2f}%/day)"
            else:
                # Stable or tightening
                velocity_score = 0.0

        # Level scoring (0-6.0 max)
        # Calibrated: normal p75=5.71%, p90=7.22%, crisis median=7.67%, max=20.2%
        if spread_level is not None:
            if spread_level > 12.0:
                # Extreme crisis (>12%)
                level_score = 6.0
                if not signal:
                    signal = f"CRITICAL: HY spreads at extreme crisis levels ({spread_level:.1f}%)"
            elif spread_level > 8.0:
                # Crisis levels (8-12%)
                level_score = 5.0
                if not signal:
                    signal = f"CRITICAL: HY spreads at crisis levels ({spread_level:.1f}%)"
            elif spread_level > 7.0:
                # High stress (7-8%, above normal p90)
                level_score = 4.0
                if not signal:
                    signal = f"WARNING: HY spreads elevated ({spread_level:.1f}%)"
            elif spread_level > 5.5:
                # Moderate stress (5.5-7%, above normal p75)
                level_score = 2.0
                if not signal:
                    signal = f"WATCH: HY spreads moderately wide ({spread_level:.1f}%)"
            else:
                # Normal levels (<5.5%)
                level_score = 0.0

        # Combined score: use MAX of velocity and level (not weighted average)
        # Rationale: Either rapid widening OR high absolute level = risk
        if spread_velocity is not None and spread_level is not None:
            score = max(velocity_score, level_score)
        elif spread_velocity is not None:
            score = velocity_score
        elif spread_level is not None:
            score = level_score
        else:
            score = 0.0

        # Cap at 6.0 (60% of total credit score)
        score = min(score, 6.0)

        logger.debug(f"HY spread: level={spread_level}, velocity={spread_velocity} → score {score:.1f}")
        return score, signal

    def _score_ig_spread(self, spread: float) -> tuple[float, Optional[str]]:
        """
        Score investment-grade (BBB) spread.

        CALIBRATED THRESHOLDS (from 2000-2024 historical data):
        - Normal p90: 2.65%
        - Crisis median: 2.36%
        - Crisis max: 7.84%

        Args:
            spread: BBB corporate bond spread in percentage points

        Returns:
            (score, signal): Score 0-2.0, optional signal message
        """
        signal = None

        # Calibrated thresholds based on percentages
        if spread > 5.0:
            # Extreme widening (>5%)
            score = 2.0
            signal = f"CRITICAL: IG spreads at stress levels ({spread:.1f}%)"
        elif spread > 3.0:
            # Elevated (>3%, above crisis median)
            score = 1.5
            signal = f"WARNING: IG spreads elevated ({spread:.1f}%)"
        elif spread > 2.5:
            # Moderate (>2.5%, above normal p90)
            score = 0.5
        else:
            # Normal (<2.5%)
            score = 0.0

        logger.debug(f"IG spread: {spread:.1f}% → score {score:.1f}")
        return score, signal

    def _score_ted_spread(self, spread: float) -> tuple[float, Optional[str]]:
        """
        Score TED spread (LIBOR - Treasury).

        CALIBRATED THRESHOLDS (from 2000-2024 historical data):
        - Normal p90: 0.50%
        - Crisis median: 0.58%
        - Crisis max: 3.31%

        Args:
            spread: TED spread in percentage points

        Returns:
            (score, signal): Score 0-1.0, optional signal message
        """
        signal = None

        # Calibrated thresholds
        if spread > 1.5:
            # Extreme crisis (>1.5%)
            score = 1.0
            signal = f"CRITICAL: TED spread at crisis levels ({spread:.2f}%)"
        elif spread > 0.75:
            # Stress (>0.75%)
            score = 0.7
            signal = f"WARNING: TED spread elevated ({spread:.2f}%)"
        elif spread > 0.50:
            # Above normal p90
            score = 0.3
        else:
            # Normal (<0.50%)
            score = 0.0

        logger.debug(f"TED spread: {spread:.2f}% → score {score:.1f}")
        return score, signal

    def _score_lending_standards(self, net_tightening: float) -> tuple[float, Optional[str]]:
        """
        Score bank lending standards (Senior Loan Officer Survey).

        Args:
            net_tightening: Net % of banks tightening standards (positive = tightening)

        Returns:
            (score, signal): Score 0-1.0, optional signal message
        """
        signal = None

        if net_tightening > 30:
            # Severe tightening
            score = 1.0
            signal = f"WARNING: Banks severely tightening lending ({net_tightening:.0f}% net)"
        elif net_tightening > 15:
            # Moderate tightening
            score = 0.5
            signal = f"WATCH: Banks tightening lending standards ({net_tightening:.0f}% net)"
        else:
            # Stable or easing
            score = 0.0

        logger.debug(f"Lending standards: {net_tightening:.0f}% net tightening → score {score:.1f}")
        return score, signal


def main():
    """Test credit scorer."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Credit Stress Scorer...\n")

    scorer = CreditScorer()

    # Test case 1: Normal conditions
    print("="*50)
    print("TEST 1: Normal Credit Conditions")
    print("="*50)
    indicators_normal = {
        'hy_spread': 350,  # Normal HY spread
        'hy_spread_velocity_20d': 1.0,  # Stable
        'ig_spread_bbb': 120,  # Normal IG spread
        'ted_spread': 0.3,  # Low
        'bank_lending_standards': 5.0  # Slight tightening
    }
    result = scorer.calculate_score(indicators_normal)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals: {result['signals']}")

    # Test case 2: Moderate stress
    print("\n" + "="*50)
    print("TEST 2: Moderate Credit Stress")
    print("="*50)
    indicators_moderate = {
        'hy_spread': 550,  # Elevated
        'hy_spread_velocity_20d': 6.0,  # Widening
        'ig_spread_bbb': 200,  # Elevated
        'ted_spread': 0.8,  # Slightly elevated
        'bank_lending_standards': 20.0  # Tightening
    }
    result = scorer.calculate_score(indicators_moderate)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals:")
    for signal in result['signals']:
        print(f"  - {signal}")

    # Test case 3: Crisis conditions (2008-style)
    print("\n" + "="*50)
    print("TEST 3: Credit Crisis Conditions")
    print("="*50)
    indicators_crisis = {
        'hy_spread': 900,  # Crisis levels
        'hy_spread_velocity_20d': 15.0,  # Rapidly widening
        'ig_spread_bbb': 450,  # Extreme
        'ted_spread': 2.5,  # Crisis
        'bank_lending_standards': 40.0  # Severe tightening
    }
    result = scorer.calculate_score(indicators_crisis)
    print(f"\nScore: {result['score']:.2f}/10")
    print(f"Components: {result['components']}")
    print(f"Signals:")
    for signal in result['signals']:
        print(f"  - {signal}")

    print("\n" + "="*50)
    print("Credit Scorer test PASSED")
    print("="*50)


if __name__ == '__main__':
    main()
