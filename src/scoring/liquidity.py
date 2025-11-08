"""
Liquidity Conditions Scorer

Calculates liquidity risk (0-10) using:
- Fed funds rate trajectory (rate of change)
- M2 money supply velocity
- VIX (volatility as liquidity proxy)
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class LiquidityScorer:
    """Calculate liquidity conditions score."""

    def __init__(self, config=None):
        self.config = config

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate liquidity conditions score (0-10).

        Args:
            indicators: Dict with liquidity indicators:
                - fed_funds_rate: Current Fed funds rate
                - fed_funds_velocity_6m: 6-month rate of change
                - m2_velocity_yoy: M2 YoY growth rate
                - vix: VIX volatility index

        Returns:
            Dict with score, components, signals
        """
        score = 0.0
        components = {}
        signals = []

        # 1. Fed funds rate trajectory (40% of liquidity score)
        fed_funds_velocity = indicators.get('fed_funds_velocity_6m')
        if fed_funds_velocity is not None:
            fed_score, fed_signal = self._score_fed_trajectory(fed_funds_velocity)
            score += fed_score
            components['fed_trajectory'] = fed_score
            if fed_signal:
                signals.append(fed_signal)
        else:
            logger.warning("Fed funds velocity not available")
            components['fed_trajectory'] = None

        # 2. M2 money supply growth (30% of liquidity score)
        m2_velocity = indicators.get('m2_velocity_yoy')
        if m2_velocity is not None:
            m2_score, m2_signal = self._score_m2_growth(m2_velocity)
            score += m2_score
            components['m2_growth'] = m2_score
            if m2_signal:
                signals.append(m2_signal)
        else:
            logger.warning("M2 velocity not available")
            components['m2_growth'] = None

        # 3. VIX (volatility/liquidity stress) (30% of liquidity score)
        vix = indicators.get('vix')
        if vix is not None:
            vix_score, vix_signal = self._score_vix(vix)
            score += vix_score
            components['vix'] = vix_score
            if vix_signal:
                signals.append(vix_signal)
        else:
            logger.warning("VIX not available")
            components['vix'] = None

        score = min(score, 10.0)
        logger.info(f"Liquidity conditions score: {score:.2f}/10")

        return {
            'score': round(score, 2),
            'components': components,
            'signals': signals
        }

    def _score_fed_trajectory(self, velocity: float) -> tuple[float, Optional[str]]:
        """
        Score Fed funds rate trajectory (rate of change).

        Rapid tightening = liquidity stress.

        Args:
            velocity: 6-month rate of change in percentage points
        """
        signal = None

        if velocity > 2.0:
            # Rapid tightening (>2pp in 6 months)
            score = 4.0
            signal = f"CRITICAL: Fed rapidly tightening ({velocity:+.1f}pp in 6 months)"
        elif velocity > 1.0:
            # Moderate tightening
            score = 2.0
            signal = f"WARNING: Fed tightening policy ({velocity:+.1f}pp in 6 months)"
        elif velocity > 0.5:
            # Gradual tightening
            score = 1.0
            signal = f"WATCH: Fed gradually tightening ({velocity:+.1f}pp)"
        elif velocity < -1.0:
            # Emergency easing (negative score = good for markets, but may signal crisis)
            score = 0.0  # Don't penalize emergency easing
        else:
            # Stable or gradual easing
            score = 0.0

        logger.debug(f"Fed trajectory: {velocity:+.1f}pp → score {score:.1f}")
        return score, signal

    def _score_m2_growth(self, yoy_growth: float) -> tuple[float, Optional[str]]:
        """
        Score M2 money supply growth.

        Contraction or very low growth = liquidity stress.

        Args:
            yoy_growth: Year-over-year M2 growth percentage
        """
        signal = None

        if yoy_growth < 0:
            # Contraction (very rare and concerning)
            score = 3.0
            signal = f"CRITICAL: M2 contracting ({yoy_growth:.1f}% YoY)"
        elif yoy_growth < 2:
            # Very low growth
            score = 2.0
            signal = f"WARNING: M2 growth very low ({yoy_growth:.1f}% YoY)"
        elif yoy_growth < 4:
            # Below normal growth (normal ~6%)
            score = 1.0
            signal = f"WATCH: M2 growth below normal ({yoy_growth:.1f}% YoY)"
        else:
            # Normal or high growth
            score = 0.0

        logger.debug(f"M2 growth: {yoy_growth:.1f}% YoY → score {score:.1f}")
        return score, signal

    def _score_vix(self, vix: float) -> tuple[float, Optional[str]]:
        """
        Score VIX (volatility as liquidity stress proxy).

        High VIX = stress, low VIX = complacency.

        Args:
            vix: CBOE Volatility Index level
        """
        signal = None

        if vix > 40:
            # Panic levels
            score = 3.0
            signal = f"CRITICAL: VIX at panic levels ({vix:.1f})"
        elif vix > 30:
            # Fear/stress
            score = 2.0
            signal = f"WARNING: VIX elevated, market stress ({vix:.1f})"
        elif vix > 20:
            # Elevated
            score = 1.0
            signal = f"WATCH: VIX moderately elevated ({vix:.1f})"
        elif vix < 12:
            # Complacency (not scored as risk here, but noted)
            score = 0.0
            signal = f"NOTE: VIX very low, potential complacency ({vix:.1f})"
        else:
            # Normal range
            score = 0.0

        logger.debug(f"VIX: {vix:.1f} → score {score:.1f}")
        return score, signal
