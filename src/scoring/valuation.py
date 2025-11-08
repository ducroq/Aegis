"""
Valuation Extremes Scorer

Calculates valuation risk (0-10) using:
- Shiller CAPE ratio
- Buffett Indicator (Market Cap / GDP)
- Forward P/E ratio
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class ValuationScorer:
    """Calculate valuation extremes score."""

    def __init__(self, config=None):
        self.config = config

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate valuation extremes score (0-10).

        Args:
            indicators: Dict with valuation indicators:
                - shiller_cape: Shiller CAPE ratio
                - wilshire_5000: Wilshire 5000 index
                - gdp: US GDP (for Buffett indicator)
                - sp500_forward_pe: S&P 500 forward P/E

        Returns:
            Dict with score, components, signals
        """
        score = 0.0
        components = {}
        signals = []

        # 1. Shiller CAPE (40% of valuation score)
        cape = indicators.get('shiller_cape')
        if cape is not None:
            cape_score, cape_signal = self._score_cape(cape)
            score += cape_score
            components['cape'] = cape_score
            if cape_signal:
                signals.append(cape_signal)
        else:
            logger.warning("Shiller CAPE not available")
            components['cape'] = None

        # 2. Buffett Indicator (40% of valuation score)
        wilshire = indicators.get('wilshire_5000')
        gdp = indicators.get('gdp')
        if wilshire is not None and gdp is not None:
            buffett_score, buffett_signal = self._score_buffett_indicator(wilshire, gdp)
            score += buffett_score
            components['buffett_indicator'] = buffett_score
            if buffett_signal:
                signals.append(buffett_signal)
        else:
            logger.warning("Buffett Indicator data not available")
            components['buffett_indicator'] = None

        # 3. Forward P/E (20% of valuation score)
        forward_pe = indicators.get('sp500_forward_pe')
        if forward_pe is not None:
            pe_score, pe_signal = self._score_forward_pe(forward_pe)
            score += pe_score
            components['forward_pe'] = pe_score
            if pe_signal:
                signals.append(pe_signal)
        else:
            logger.warning("Forward P/E not available")
            components['forward_pe'] = None

        score = min(score, 10.0)
        logger.info(f"Valuation extremes score: {score:.2f}/10")

        return {
            'score': round(score, 2),
            'components': components,
            'signals': signals
        }

    def _score_cape(self, cape: float) -> tuple[float, Optional[str]]:
        """Score Shiller CAPE ratio (historical avg ~16-17)."""
        signal = None

        if cape > 35:
            # Extreme bubble (dot-com levels)
            score = 4.0
            signal = f"CRITICAL: CAPE at bubble levels ({cape:.1f}, historical avg ~17)"
        elif cape > 30:
            # Very elevated
            score = 3.0
            signal = f"WARNING: CAPE very elevated ({cape:.1f})"
        elif cape > 25:
            # Elevated
            score = 2.0
            signal = f"WATCH: CAPE elevated ({cape:.1f})"
        elif cape > 20:
            # Moderately high
            score = 1.0
        else:
            # Normal to attractive
            score = 0.0

        logger.debug(f"CAPE: {cape:.1f} → score {score:.1f}")
        return score, signal

    def _score_buffett_indicator(self, market_cap: float, gdp: float) -> tuple[float, Optional[str]]:
        """Score Market Cap / GDP ratio (Buffett's favorite indicator)."""
        ratio = (market_cap / gdp) * 100  # Express as percentage
        signal = None

        if ratio > 200:
            # Extreme overvaluation
            score = 4.0
            signal = f"CRITICAL: Market Cap/GDP at extreme levels ({ratio:.0f}%, Buffett 'fair' = 100%)"
        elif ratio > 150:
            # Very overvalued
            score = 3.0
            signal = f"WARNING: Market Cap/GDP very elevated ({ratio:.0f}%)"
        elif ratio > 120:
            # Overvalued
            score = 2.0
            signal = f"WATCH: Market Cap/GDP elevated ({ratio:.0f}%)"
        elif ratio > 100:
            # Moderately overvalued
            score = 1.0
        else:
            # Fair to undervalued
            score = 0.0

        logger.debug(f"Buffett Indicator: {ratio:.0f}% → score {score:.1f}")
        return score, signal

    def _score_forward_pe(self, pe: float) -> tuple[float, Optional[str]]:
        """Score forward P/E ratio (historical avg ~18)."""
        signal = None

        if pe > 25:
            # Very expensive
            score = 2.0
            signal = f"WARNING: Forward P/E very high ({pe:.1f}, historical avg ~18)"
        elif pe > 22:
            # Expensive
            score = 1.5
            signal = f"WATCH: Forward P/E elevated ({pe:.1f})"
        elif pe > 18:
            # Moderately expensive
            score = 0.5
        else:
            # Normal to cheap
            score = 0.0

        logger.debug(f"Forward P/E: {pe:.1f} → score {score:.1f}")
        return score, signal
