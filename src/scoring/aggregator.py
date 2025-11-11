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

        # Extract scores and results
        dimension_results = {
            'recession': recession_result,
            'credit': credit_result,
            'valuation': valuation_result,
            'liquidity': liquidity_result,
            'positioning': positioning_result
        }

        dimension_scores = {
            'recession': recession_result['score'],
            'credit': credit_result['score'],
            'valuation': valuation_result['score'],
            'liquidity': liquidity_result['score'],
            'positioning': positioning_result['score']
        }

        # Filter out dimensions with no data (all components are None)
        valid_dimensions = {}
        excluded_dimensions = []

        for dim, result in dimension_results.items():
            components = result.get('components', {})
            # Check if dimension has any non-None component
            has_data = any(val is not None for val in components.values())

            if has_data:
                valid_dimensions[dim] = dimension_scores[dim]
            else:
                excluded_dimensions.append(dim)
                logger.warning(f"Excluding {dim} from aggregation (no data available)")

        # Re-normalize weights for valid dimensions only
        if not valid_dimensions:
            raise ValueError("No valid dimensions with data available for scoring")

        total_valid_weight = sum(self.weights[dim] for dim in valid_dimensions)
        normalized_weights = {
            dim: self.weights[dim] / total_valid_weight
            for dim in valid_dimensions
        }

        if excluded_dimensions:
            logger.info(f"Re-normalized weights (excluded: {', '.join(excluded_dimensions)})")
            logger.info(f"Normalized weights: {normalized_weights}")

        # Calculate weighted average using only valid dimensions
        overall_score = sum(
            valid_dimensions[dim] * normalized_weights[dim]
            for dim in valid_dimensions
        )

        # Round to 2 decimal places
        overall_score = round(overall_score, 2)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            dimension_results=dimension_results,
            valid_dimensions=valid_dimensions,
            excluded_dimensions=excluded_dimensions
        )

        # Determine risk tier
        tier = self._get_risk_tier(overall_score)

        # Check for valuation-based early warning (leading indicator)
        valuation_warning = self._check_valuation_warning(data.get('valuation', {}))

        # Check for double inversion warning (yield curve + credit stress)
        double_inversion_warning = self._check_double_inversion(
            data.get('recession', {}),
            data.get('credit', {})
        )

        # Check for real interest rate warning (Fed tightening)
        real_rate_warning = self._check_real_rate_warning(data.get('liquidity', {}))

        # Check for earnings recession warning (profit decline)
        # NOTE: Requires historical data window (not available during live fetch)
        earnings_recession_warning = self._check_earnings_recession(
            data.get('valuation', {}),
            None  # No historical data in live mode - will be populated during backtest
        )

        # Check for housing bubble warning (housing market stress)
        # NOTE: Requires historical data window (not available during live fetch)
        housing_bubble_warning = self._check_housing_bubble(
            data.get('valuation', {}),
            None  # No historical data in live mode - will be populated during backtest
        )

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
            'confidence': confidence,
            'tier': tier,
            'valuation_warning': valuation_warning,  # Early warning from valuation extremes
            'double_inversion_warning': double_inversion_warning,  # Recession + credit stress combo
            'real_rate_warning': real_rate_warning,  # Fed tightening warning
            'earnings_recession_warning': earnings_recession_warning,  # Profit decline warning
            'housing_bubble_warning': housing_bubble_warning,  # Housing market stress
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
            'normalized_weights': normalized_weights if excluded_dimensions else self.weights,
            'excluded_dimensions': excluded_dimensions,
            'metadata': {
                'weighted_calculation': {
                    dim: f"{valid_dimensions[dim]:.2f} × {normalized_weights[dim]:.2f} = {valid_dimensions[dim] * normalized_weights[dim]:.2f}"
                    for dim in valid_dimensions
                },
                'confidence_details': confidence
            }
        }

    def _calculate_confidence(
        self,
        dimension_results: Dict[str, Any],
        valid_dimensions: Dict[str, float],
        excluded_dimensions: list
    ) -> Dict[str, Any]:
        """
        Calculate confidence score based on data availability.

        Confidence factors:
        1. Dimension coverage (40%) - How many dimensions have data
        2. Component completeness (40%) - % of components available per dimension
        3. Key indicator bonus (20%) - Extra credit for having critical indicators

        Args:
            dimension_results: Full results from all dimension scorers
            valid_dimensions: Dimensions with at least some data
            excluded_dimensions: Dimensions with no data

        Returns:
            Dict with:
                - score: Overall confidence (0-100%)
                - level: 'HIGH', 'MEDIUM', 'LOW'
                - breakdown: Details by factor
        """
        total_dimensions = 5
        valid_dimension_count = len(valid_dimensions)

        # 1. Dimension coverage (40%)
        dimension_coverage = (valid_dimension_count / total_dimensions) * 40

        # 2. Component completeness (40%)
        # Count total components and available components across all dimensions
        total_components = 0
        available_components = 0

        for dim, result in dimension_results.items():
            components = result.get('components', {})
            for comp_name, comp_value in components.items():
                total_components += 1
                if comp_value is not None:
                    available_components += 1

        component_completeness = (available_components / total_components * 40) if total_components > 0 else 0

        # 3. Key indicator bonus (20%)
        # Check for critical indicators that matter most for crisis detection
        key_indicators_present = []
        key_indicators_missing = []

        # Critical recession indicators
        recession_comps = dimension_results['recession'].get('components', {})
        if recession_comps.get('yield_curve_10y2y') is not None:
            key_indicators_present.append('yield_curve')
        else:
            key_indicators_missing.append('yield_curve')

        if recession_comps.get('unemployment_claims_velocity') is not None:
            key_indicators_present.append('unemployment_velocity')
        else:
            key_indicators_missing.append('unemployment_velocity')

        # Critical credit indicators
        credit_comps = dimension_results['credit'].get('components', {})
        if credit_comps.get('hy_spread') is not None or credit_comps.get('hy_spread_velocity') is not None:
            key_indicators_present.append('credit_spreads')
        else:
            key_indicators_missing.append('credit_spreads')

        # Critical valuation indicators
        valuation_comps = dimension_results['valuation'].get('components', {})
        if valuation_comps.get('cape') is not None:
            key_indicators_present.append('cape')
        else:
            key_indicators_missing.append('cape')

        # Liquidity indicators
        liquidity_comps = dimension_results['liquidity'].get('components', {})
        if liquidity_comps.get('fed_trajectory') is not None:
            key_indicators_present.append('fed_policy')
        else:
            key_indicators_missing.append('fed_policy')

        total_key_indicators = len(key_indicators_present) + len(key_indicators_missing)
        key_indicator_bonus = (len(key_indicators_present) / total_key_indicators * 20) if total_key_indicators > 0 else 0

        # Total confidence score
        confidence_score = dimension_coverage + component_completeness + key_indicator_bonus
        confidence_score = round(confidence_score, 1)

        # Determine confidence level
        if confidence_score >= 80:
            level = 'HIGH'
        elif confidence_score >= 60:
            level = 'MEDIUM'
        else:
            level = 'LOW'

        logger.info(f"Confidence: {confidence_score:.1f}% ({level})")

        return {
            'score': confidence_score,
            'level': level,
            'breakdown': {
                'dimension_coverage': {
                    'score': round(dimension_coverage, 1),
                    'details': f"{valid_dimension_count}/{total_dimensions} dimensions with data"
                },
                'component_completeness': {
                    'score': round(component_completeness, 1),
                    'details': f"{available_components}/{total_components} indicators available"
                },
                'key_indicators': {
                    'score': round(key_indicator_bonus, 1),
                    'present': key_indicators_present,
                    'missing': key_indicators_missing
                }
            }
        }

    def _check_valuation_warning(self, valuation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for valuation-based early warning (leading indicator).

        Uses empirical thresholds calibrated from 2000-2024 backtest:
        - CAPE > 30 AND Buffett > 120%: Detects 67% of crashes with 12.4% false positives

        This provides LEADING signal (months before crash) vs coincident macro indicators.

        Args:
            valuation_data: Raw valuation indicators from DataManager

        Returns:
            Dict with:
                - active: bool (is warning active?)
                - level: 'EXTREME' or None
                - message: Warning message
                - cape: Current CAPE value
                - buffett: Current Buffett indicator value
        """
        cape = valuation_data.get('shiller_cape')
        buffett = valuation_data.get('sp500_market_cap')  # This is Buffett indicator (Market Cap/GDP %)

        # Calibrated thresholds from backtest
        cape_threshold = 30.0
        buffett_threshold = 120.0

        if cape is not None and buffett is not None:
            if cape > cape_threshold and buffett > buffett_threshold:
                message = (
                    f"VALUATION WARNING: Market at extreme levels (CAPE={cape:.1f}, "
                    f"Buffett Indicator={buffett:.0f}%). "
                    f"Historical precedent: Dot-com (2000), COVID peak (2020). "
                    f"Consider building cash position incrementally."
                )
                logger.warning(message)
                return {
                    'active': True,
                    'level': 'EXTREME',
                    'message': message,
                    'cape': cape,
                    'buffett': buffett
                }

        return {
            'active': False,
            'level': None,
            'message': None,
            'cape': cape,
            'buffett': buffett
        }

    def _check_double_inversion(
        self,
        recession_data: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for double inversion warning (yield curve + credit stress).

        When BOTH recession signal AND credit stress occur = severe risk.

        Calibrated thresholds from backtest:
        - Yield curve 10Y-2Y < 0 (inverted)
        - HY spreads > 500bps (stress)

        This combination historically precedes severe crises (2007-2008).

        Args:
            recession_data: Raw recession indicators
            credit_data: Raw credit indicators

        Returns:
            Dict with:
                - active: bool (is warning active?)
                - level: 'SEVERE' or None
                - message: Warning message
                - yield_curve: Current yield curve value
                - hy_spread: Current HY spread value
        """
        yield_curve = recession_data.get('yield_curve_10y2y')
        hy_spread = credit_data.get('hy_spread')

        # Calibrated thresholds
        yield_curve_threshold = 0.0  # Inverted (negative)
        hy_spread_threshold = 5.0  # Stress level (stored as %, not bps)

        if yield_curve is not None and hy_spread is not None:
            if yield_curve < yield_curve_threshold and hy_spread > hy_spread_threshold:
                message = (
                    f"DOUBLE INVERSION WARNING: Yield curve inverted ({yield_curve:.2f}%) "
                    f"AND credit stress elevated (HY spreads {hy_spread:.1f}%). "
                    f"Historical precedent: 2007-2008 Financial Crisis. "
                    f"Recession signal + funding stress = severe risk."
                )
                logger.warning(message)
                return {
                    'active': True,
                    'level': 'SEVERE',
                    'message': message,
                    'yield_curve': yield_curve,
                    'hy_spread': hy_spread
                }

        return {
            'active': False,
            'level': None,
            'message': None,
            'yield_curve': yield_curve,
            'hy_spread': hy_spread
        }

    def _check_real_rate_warning(
        self,
        liquidity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check for real interest rate warning (Fed tightening cycles).

        When real rates (Fed funds - inflation) are positive AND rising rapidly,
        this indicates Fed tightening that can cause market selloffs even without
        recession or credit stress.

        Calibrated thresholds from expected 2022 backtest performance:
        - Real rate > 2.0% (positive real rates = restrictive)
        - 6-month change > 3.0% (rapid tightening)

        This combination catches Fed-driven selloffs like 2022 bear market (-25%),
        1994 bond massacre, 2018 Q4 selloff (-20%).

        Args:
            liquidity_data: Raw liquidity indicators including fed_funds_rate and cpi_inflation_yoy

        Returns:
            Dict with:
                - active: bool (is warning active?)
                - level: 'HIGH' or None
                - message: Warning message
                - real_rate: Current real interest rate
                - fed_funds: Current fed funds rate
                - inflation: Current inflation rate
        """
        fed_funds = liquidity_data.get('fed_funds_rate')
        cpi_inflation_yoy = liquidity_data.get('cpi_inflation_yoy')
        fed_funds_velocity_6m = liquidity_data.get('fed_funds_velocity_6m')

        # Calibrated thresholds
        real_rate_threshold = 2.0  # Positive real rates (restrictive)
        velocity_threshold = 3.0  # Rapid tightening (3% in 6 months)

        if fed_funds is not None and cpi_inflation_yoy is not None:
            # Calculate real interest rate
            real_rate = fed_funds - cpi_inflation_yoy

            # Check if we have velocity data
            has_velocity = fed_funds_velocity_6m is not None

            # WARNING: High positive real rates + rapid tightening
            if real_rate > real_rate_threshold and has_velocity and fed_funds_velocity_6m > velocity_threshold:
                message = (
                    f"REAL RATE WARNING: Fed tightening aggressively. "
                    f"Real rate {real_rate:.1f}% (Fed {fed_funds:.2f}% - Inflation {cpi_inflation_yoy:.1f}%) "
                    f"and rising rapidly (+{fed_funds_velocity_6m:.1f}% in 6 months). "
                    f"Historical precedent: 2022 bear market (-25%), 1994 bond sell-off, 2018 Q4 (-20%). "
                    f"Fed headwind can cause selloff even without recession."
                )
                logger.warning(message)
                return {
                    'active': True,
                    'level': 'HIGH',
                    'message': message,
                    'real_rate': real_rate,
                    'fed_funds': fed_funds,
                    'inflation': cpi_inflation_yoy,
                    'velocity_6m': fed_funds_velocity_6m
                }

            # MODERATE: High real rates but not rising rapidly (may be stabilizing)
            elif real_rate > real_rate_threshold:
                message = (
                    f"Real rates elevated at {real_rate:.1f}% "
                    f"(Fed {fed_funds:.2f}% - Inflation {cpi_inflation_yoy:.1f}%). "
                    f"Restrictive policy but not rapidly tightening."
                )
                return {
                    'active': False,  # Don't alert for moderate level
                    'level': 'MODERATE',
                    'message': message,
                    'real_rate': real_rate,
                    'fed_funds': fed_funds,
                    'inflation': cpi_inflation_yoy,
                    'velocity_6m': fed_funds_velocity_6m
                }

        return {
            'active': False,
            'level': None,
            'message': None,
            'real_rate': real_rate if fed_funds and cpi_inflation_yoy else None,
            'fed_funds': fed_funds,
            'inflation': cpi_inflation_yoy,
            'velocity_6m': fed_funds_velocity_6m
        }

    def _check_earnings_recession(
        self,
        valuation_data: Dict[str, Any],
        raw_indicators: 'pd.DataFrame' = None
    ) -> Dict[str, Any]:
        """
        Check for earnings recession warning (profit decline without economic recession).

        NOTE: Uses Shiller TRAILING 12-month earnings (historical actual earnings).
        This is a LAGGING indicator - detects earnings recessions DURING the decline,
        not predictively. Forward earnings estimates not available historically.

        When trailing earnings decline significantly (10%+ over 12 months), this indicates
        corporate profit pressure that can cause market selloffs even without full recession.

        Examples: 2001-2002 post-tech bubble, 2008-2009 financial crisis, 2015-2016 energy collapse.
        """
        # NOTE: Using Shiller trailing earnings (12M historical actuals, NOT forward estimates)
        trailing_earnings = valuation_data.get('shiller_trailing_earnings')

        # Thresholds
        earnings_decline_threshold = -0.10  # 10% decline in trailing 12M earnings

        # Check if we have current earnings
        if trailing_earnings is not None:
            # Need historical data to calculate 12-month change
            if raw_indicators is not None and len(raw_indicators) >= 13:
                # Get earnings from 12 months ago (need 13 rows for 12-month lookback)
                try:
                    twelve_months_ago = raw_indicators.iloc[-13]
                    trailing_earnings_12m = twelve_months_ago.get('valuation_shiller_trailing_earnings')

                    if trailing_earnings_12m and trailing_earnings_12m > 0:
                        earnings_change_12m = (trailing_earnings - trailing_earnings_12m) / trailing_earnings_12m

                        # WARNING: Significant earnings decline
                        if earnings_change_12m < earnings_decline_threshold:
                            message = (
                                f"EARNINGS RECESSION WARNING: Trailing 12M earnings declining sharply. "
                                f"12-month earnings change: {earnings_change_12m*100:.1f}% "
                                f"(from ${trailing_earnings_12m:.2f} to ${trailing_earnings:.2f}). "
                                f"Historical precedent: 2001-2002 tech crash, 2008-2009 financial crisis, 2015-2016 energy collapse. "
                                f"Profit pressure can cause market selloff even without GDP recession. "
                                f"NOTE: This uses TRAILING earnings (lagging indicator, not predictive)."
                            )
                            return {
                                'active': True,
                                'level': 'HIGH',
                                'message': message,
                                'current_trailing_earnings': trailing_earnings,
                                'trailing_earnings_12m_ago': trailing_earnings_12m,
                                'earnings_change_12m_pct': earnings_change_12m * 100
                            }

                        # Return inactive but with data
                        return {
                            'active': False,
                            'level': None,
                            'message': None,
                            'current_trailing_earnings': trailing_earnings,
                            'trailing_earnings_12m_ago': trailing_earnings_12m,
                            'earnings_change_12m_pct': earnings_change_12m * 100
                        }

                except (KeyError, IndexError, TypeError) as e:
                    logger.debug(f"Could not calculate historical trailing earnings: {e}")

            # Return with current data only
            return {
                'active': False,
                'level': None,
                'message': None,
                'current_trailing_earnings': trailing_earnings,
                'trailing_earnings_12m_ago': None,
                'earnings_change_12m_pct': None
            }

        # Missing data
        return {
            'active': False,
            'level': None,
            'message': None,
            'current_trailing_earnings': None,
            'trailing_earnings_12m_ago': None,
            'earnings_change_12m_pct': None
        }

    def _check_housing_bubble(
        self,
        valuation_data: Dict[str, Any],
        raw_indicators: 'pd.DataFrame' = None
    ) -> Dict[str, Any]:
        """
        Check for housing bubble warning (collapsing housing market).

        When home sales decline sharply while mortgage rates spike, this indicates
        housing market stress that can cascade into broader economic weakness.

        Examples: 2007 housing crisis, 2022-2023 housing freeze.
        """
        new_home_sales = valuation_data.get('new_home_sales')
        mortgage_rate_30y = valuation_data.get('mortgage_rate_30y')
        median_home_price = valuation_data.get('median_home_price')

        # Thresholds
        sales_decline_threshold = -0.20  # 20% decline in home sales over 6 months
        mortgage_rate_threshold = 6.5    # High mortgage rates (stress level)

        # Need historical data to calculate 6-month change in sales
        if new_home_sales is not None and raw_indicators is not None and len(raw_indicators) >= 7:
            try:
                six_months_ago = raw_indicators.iloc[-7]
                new_home_sales_6m = six_months_ago.get('valuation_new_home_sales')

                if new_home_sales_6m and new_home_sales_6m > 0:
                    sales_change_6m = (new_home_sales - new_home_sales_6m) / new_home_sales_6m

                    # WARNING: Declining sales + high mortgage rates = housing stress
                    if sales_change_6m < sales_decline_threshold and mortgage_rate_30y is not None and mortgage_rate_30y > mortgage_rate_threshold:
                        message = (
                            f"HOUSING BUBBLE WARNING: Housing market freezing up. "
                            f"New home sales down {sales_change_6m*100:.1f}% over 6 months "
                            f"(from {new_home_sales_6m:.0f}k to {new_home_sales:.0f}k units) "
                            f"while mortgage rates at {mortgage_rate_30y:.2f}%. "
                            f"Historical precedent: 2007-2008 housing crash, 2022-2023 housing freeze. "
                            f"Housing stress can cascade into broader economic weakness."
                        )
                        return {
                            'active': True,
                            'level': 'HIGH',
                            'message': message,
                            'new_home_sales': new_home_sales,
                            'new_home_sales_6m_ago': new_home_sales_6m,
                            'sales_change_6m_pct': sales_change_6m * 100,
                            'mortgage_rate_30y': mortgage_rate_30y,
                            'median_home_price': median_home_price
                        }

                    # Return inactive but with data
                    return {
                        'active': False,
                        'level': None,
                        'message': None,
                        'new_home_sales': new_home_sales,
                        'new_home_sales_6m_ago': new_home_sales_6m,
                        'sales_change_6m_pct': sales_change_6m * 100,
                        'mortgage_rate_30y': mortgage_rate_30y,
                        'median_home_price': median_home_price
                    }

            except (KeyError, IndexError, TypeError) as e:
                logger.debug(f"Could not calculate historical home sales: {e}")

        # Return with current data only
        return {
            'active': False,
            'level': None,
            'message': None,
            'new_home_sales': new_home_sales,
            'new_home_sales_6m_ago': None,
            'sales_change_6m_pct': None,
            'mortgage_rate_30y': mortgage_rate_30y,
            'median_home_price': median_home_price
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
