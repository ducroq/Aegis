"""
Positioning & Speculation Scorer

Calculates positioning risk (0-10) using:
- CFTC S&P 500 net speculative positioning (contrarian)
- CFTC Treasury positioning (squeeze risk)
- VIX futures positioning (complacency)

NOTE: Full CFTC data integration is stubbed for MVP. Uses VIX as proxy.
"""

import logging
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class PositioningScorer:
    """Calculate positioning/speculation risk score."""

    def __init__(self, config=None):
        self.config = config

    def calculate_score(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate positioning risk score (0-10).

        Args:
            indicators: Dict with positioning indicators:
                - sp500_net_speculative: CFTC S&P positioning (stubbed)
                - treasury_net_speculative: CFTC Treasury positioning (stubbed)
                - vix_proxy: VIX as proxy for speculation/complacency

        Returns:
            Dict with score, components, signals
        """
        score = 0.0
        components = {}
        signals = []

        # NOTE: Full CFTC implementation is future enhancement
        # For now, use VIX as a proxy for market positioning/complacency

        # VIX proxy (100% for now, until CFTC data integrated)
        vix = indicators.get('vix_proxy')
        if vix is not None:
            vix_score, vix_signal = self._score_vix_positioning(vix)
            score += vix_score
            components['vix_positioning'] = vix_score
            if vix_signal:
                signals.append(vix_signal)
        else:
            logger.warning("VIX positioning proxy not available")
            components['vix_positioning'] = None

        # Stubbed CFTC data (for future implementation)
        sp500_cftc = indicators.get('sp500_net_speculative')
        treasury_cftc = indicators.get('treasury_net_speculative')

        if sp500_cftc is None and treasury_cftc is None:
            signals.append("NOTE: CFTC positioning data not yet implemented")

        score = min(score, 10.0)
        logger.info(f"Positioning risk score: {score:.2f}/10")

        return {
            'score': round(score, 2),
            'components': components,
            'signals': signals
        }

    def _score_vix_positioning(self, vix: float) -> tuple[float, Optional[str]]:
        """
        Score VIX as positioning/complacency proxy.

        Very low VIX = complacency = risk of reversal.
        Very high VIX = panic = potential washout (contrarian buy).

        Args:
            vix: CBOE Volatility Index
        """
        signal = None

        if vix < 11:
            # Extreme complacency
            score = 10.0  # Full score for positioning risk
            signal = f"CRITICAL: VIX at extreme lows, market complacency ({vix:.1f})"
        elif vix < 13:
            # Very low (complacent)
            score = 5.0
            signal = f"WARNING: VIX very low, complacency risk ({vix:.1f})"
        elif vix < 15:
            # Low (somewhat complacent)
            score = 2.0
            signal = f"WATCH: VIX low, some complacency ({vix:.1f})"
        elif vix > 40:
            # Extreme fear (contrarian opportunity, but still risky)
            score = 3.0
            signal = f"NOTE: VIX extreme, panic selling possible ({vix:.1f})"
        else:
            # Normal range
            score = 0.0

        logger.debug(f"VIX positioning: {vix:.1f} → score {score:.1f}")
        return score, signal
