"""
Calibration Script - Analyze Historical Data to Set Scoring Thresholds

This script analyzes the historical indicator data to determine appropriate
thresholds for scoring functions. It compares indicator values during:
- Normal periods (no crash within 12 months)
- Pre-crash periods (2-6 months before peak)
- Crisis periods (during the crash)

The output suggests data-driven thresholds for each scoring dimension.

Usage:
    python scripts/calibrate_thresholds.py
    python scripts/calibrate_thresholds.py --output config/thresholds_calibrated.yaml
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_logging():
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )


# Define major market crashes
CRASHES = [
    {
        'name': '2000-2002 Dot-com Bubble',
        'peak': '2000-03-24',
        'trough': '2002-10-09',
        'drawdown': -49.1,
        'pre_crash_window': 90,  # days before peak to analyze
    },
    {
        'name': '2007-2009 Financial Crisis',
        'peak': '2007-10-09',
        'trough': '2009-03-09',
        'drawdown': -56.8,
        'pre_crash_window': 90,
    },
    {
        'name': '2020 COVID Crash',
        'peak': '2020-02-19',
        'trough': '2020-03-23',
        'drawdown': -33.9,
        'pre_crash_window': 30,  # Fast crash
    },
    {
        'name': '2022 Bear Market',
        'peak': '2022-01-03',
        'trough': '2022-10-12',
        'drawdown': -25.4,
        'pre_crash_window': 60,
    },
]


def load_historical_data() -> pd.DataFrame:
    """Load historical raw indicators."""
    logger = logging.getLogger(__name__)

    data_file = project_root / 'data' / 'history' / 'raw_indicators.csv'

    if not data_file.exists():
        logger.error(f"Historical data not found: {data_file}")
        logger.error("Run backfill_history.py first")
        sys.exit(1)

    df = pd.read_csv(data_file, parse_dates=['date'])
    logger.info(f"Loaded {len(df)} historical records from {df['date'].min()} to {df['date'].max()}")

    return df


def classify_periods(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify each date as normal, pre-crash, or crisis.

    Returns:
        DataFrame with added 'period_type' column
    """
    df = df.copy()
    df['period_type'] = 'normal'

    for crash in CRASHES:
        peak_date = pd.to_datetime(crash['peak'])
        trough_date = pd.to_datetime(crash['trough'])
        pre_crash_start = peak_date - timedelta(days=crash['pre_crash_window'])

        # Mark crisis period (peak to trough)
        crisis_mask = (df['date'] >= peak_date) & (df['date'] <= trough_date)
        df.loc[crisis_mask, 'period_type'] = 'crisis'

        # Mark pre-crash period
        pre_crash_mask = (df['date'] >= pre_crash_start) & (df['date'] < peak_date)
        df.loc[pre_crash_mask, 'period_type'] = 'pre_crash'

    return df


def analyze_indicator(
    df: pd.DataFrame,
    indicator_name: str,
    direction: str = 'higher_is_worse'
) -> Dict:
    """
    Analyze an indicator's distribution across period types.

    Args:
        df: DataFrame with historical data
        indicator_name: Column name of indicator
        direction: 'higher_is_worse' or 'lower_is_worse'

    Returns:
        Dict with statistics and suggested thresholds
    """
    if indicator_name not in df.columns:
        return {'error': f'Indicator {indicator_name} not found in data'}

    # Get values for each period type
    normal = df[df['period_type'] == 'normal'][indicator_name].dropna()
    pre_crash = df[df['period_type'] == 'pre_crash'][indicator_name].dropna()
    crisis = df[df['period_type'] == 'crisis'][indicator_name].dropna()

    if len(normal) == 0 and len(pre_crash) == 0 and len(crisis) == 0:
        return {'error': f'No data available for {indicator_name}'}

    # Calculate statistics
    stats = {
        'indicator': indicator_name,
        'direction': direction,
        'normal': {
            'count': len(normal),
            'median': normal.median() if len(normal) > 0 else None,
            'mean': normal.mean() if len(normal) > 0 else None,
            'p75': normal.quantile(0.75) if len(normal) > 0 else None,
            'p90': normal.quantile(0.90) if len(normal) > 0 else None,
            'p95': normal.quantile(0.95) if len(normal) > 0 else None,
            'max': normal.max() if len(normal) > 0 else None,
        },
        'pre_crash': {
            'count': len(pre_crash),
            'median': pre_crash.median() if len(pre_crash) > 0 else None,
            'mean': pre_crash.mean() if len(pre_crash) > 0 else None,
            'min': pre_crash.min() if len(pre_crash) > 0 else None,
            'max': pre_crash.max() if len(pre_crash) > 0 else None,
        },
        'crisis': {
            'count': len(crisis),
            'median': crisis.median() if len(crisis) > 0 else None,
            'mean': crisis.mean() if len(crisis) > 0 else None,
            'min': crisis.min() if len(crisis) > 0 else None,
            'max': crisis.max() if len(crisis) > 0 else None,
        },
    }

    # Suggest thresholds based on data
    # Threshold logic: normal p90 = warning, pre-crash median = high risk, crisis median = crisis
    if direction == 'higher_is_worse':
        thresholds = {
            'watch': stats['normal']['p75'],      # 75th percentile of normal
            'warning': stats['normal']['p90'],    # 90th percentile of normal
            'high_risk': stats['pre_crash']['median'],  # Median of pre-crash
            'crisis': stats['crisis']['median'],   # Median during crisis
        }
    else:  # lower_is_worse (e.g., yield curve, consumer sentiment)
        thresholds = {
            'watch': stats['normal']['p75'],      # Use quantile(0.25) for lower tail
            'warning': stats['pre_crash']['median'],
            'high_risk': stats['crisis']['median'],
            'crisis': stats['crisis']['min'],
        }

    stats['suggested_thresholds'] = thresholds

    return stats


def print_analysis(analysis: Dict):
    """Pretty print the analysis results."""
    print("\n" + "="*80)
    print(f"INDICATOR: {analysis['indicator']}")
    print("="*80)

    if 'error' in analysis:
        print(f"  ERROR: {analysis['error']}")
        return

    print(f"Direction: {analysis['direction']}")
    print()

    # Normal periods
    normal = analysis['normal']
    print(f"NORMAL PERIODS (n={normal['count']}):")
    if normal['count'] > 0:
        print(f"  Median: {normal['median']:.2f}")
        print(f"  Mean:   {normal['mean']:.2f}")
        print(f"  75th %: {normal['p75']:.2f}")
        print(f"  90th %: {normal['p90']:.2f}")
        print(f"  95th %: {normal['p95']:.2f}")
        print(f"  Max:    {normal['max']:.2f}")

    # Pre-crash periods
    pre = analysis['pre_crash']
    print(f"\nPRE-CRASH PERIODS (n={pre['count']}):")
    if pre['count'] > 0:
        print(f"  Median: {pre['median']:.2f}")
        print(f"  Mean:   {pre['mean']:.2f}")
        print(f"  Range:  {pre['min']:.2f} - {pre['max']:.2f}")

    # Crisis periods
    crisis = analysis['crisis']
    print(f"\nCRISIS PERIODS (n={crisis['count']}):")
    if crisis['count'] > 0:
        print(f"  Median: {crisis['median']:.2f}")
        print(f"  Mean:   {crisis['mean']:.2f}")
        print(f"  Range:  {crisis['min']:.2f} - {crisis['max']:.2f}")

    # Suggested thresholds
    thresholds = analysis['suggested_thresholds']
    print(f"\nSUGGESTED THRESHOLDS:")
    print(f"  WATCH:     {thresholds['watch']:.2f}  (score ~3/10)")
    print(f"  WARNING:   {thresholds['warning']:.2f}  (score ~6/10)")
    print(f"  HIGH RISK: {thresholds['high_risk']:.2f}  (score ~8/10)")
    print(f"  CRISIS:    {thresholds['crisis']:.2f}  (score 10/10)")


def main():
    """Main execution."""
    setup_logging()
    logger = logging.getLogger(__name__)

    print("="*80)
    print("AEGIS THRESHOLD CALIBRATION")
    print("="*80)
    print()

    # Load data
    df = load_historical_data()

    # Classify periods
    df = classify_periods(df)

    period_counts = df['period_type'].value_counts()
    print(f"Period classification:")
    print(f"  Normal:    {period_counts.get('normal', 0)} months")
    print(f"  Pre-crash: {period_counts.get('pre_crash', 0)} months")
    print(f"  Crisis:    {period_counts.get('crisis', 0)} months")

    # Analyze key indicators
    indicators_to_analyze = [
        # Recession indicators
        ('recession_unemployment_claims', 'higher_is_worse'),
        ('recession_unemployment_claims_velocity_yoy', 'higher_is_worse'),
        ('recession_yield_curve_10y2y', 'lower_is_worse'),
        ('recession_yield_curve_10y3m', 'lower_is_worse'),
        ('recession_consumer_sentiment', 'lower_is_worse'),

        # Credit indicators
        ('credit_hy_spread', 'higher_is_worse'),
        ('credit_hy_spread_velocity_20d', 'higher_is_worse'),
        ('credit_ig_spread_bbb', 'higher_is_worse'),
        ('credit_ted_spread', 'higher_is_worse'),

        # Valuation indicators
        ('valuation_shiller_cape', 'higher_is_worse'),

        # Liquidity indicators
        ('liquidity_fed_funds_rate', 'higher_is_worse'),
        ('liquidity_vix', 'higher_is_worse'),
    ]

    all_analyses = []

    for indicator, direction in indicators_to_analyze:
        analysis = analyze_indicator(df, indicator, direction)
        all_analyses.append(analysis)
        print_analysis(analysis)

    # Summary recommendations
    print("\n" + "="*80)
    print("CALIBRATION SUMMARY")
    print("="*80)
    print()
    print("Key findings:")
    print()

    # High-yield spreads
    hy_analysis = next((a for a in all_analyses if a.get('indicator') == 'credit_hy_spread'), None)
    if hy_analysis and 'error' not in hy_analysis:
        print("HIGH-YIELD SPREADS:")
        print(f"  Current thresholds in code: 400/600/800 bps (4%/6%/8%)")
        print(f"  Data shows (in %):")
        print(f"    Normal max: {hy_analysis['normal']['max']:.1f}%")
        print(f"    Pre-crash median: {hy_analysis['pre_crash']['median']:.1f}%")
        print(f"    Crisis median: {hy_analysis['crisis']['median']:.1f}%")
        print(f"  RECOMMENDATION: Use percentages, not basis points!")
        print(f"    Watch:     {hy_analysis['suggested_thresholds']['watch']:.1f}%")
        print(f"    Warning:   {hy_analysis['suggested_thresholds']['warning']:.1f}%")
        print(f"    High Risk: {hy_analysis['suggested_thresholds']['high_risk']:.1f}%")
        print(f"    Crisis:    {hy_analysis['suggested_thresholds']['crisis']:.1f}%")
        print()

    # Unemployment claims velocity
    uc_vel = next((a for a in all_analyses if a.get('indicator') == 'recession_unemployment_claims_velocity_yoy'), None)
    if uc_vel and 'error' not in uc_vel:
        print("UNEMPLOYMENT CLAIMS VELOCITY (YoY %):")
        print(f"  Normal 90th %: {uc_vel['normal']['p90']:.1f}%")
        print(f"  Crisis median: {uc_vel['crisis']['median']:.1f}%")
        print(f"  RECOMMENDATION:")
        print(f"    Watch:     {uc_vel['suggested_thresholds']['watch']:.1f}%")
        print(f"    Warning:   {uc_vel['suggested_thresholds']['warning']:.1f}%")
        print(f"    High Risk: {uc_vel['suggested_thresholds']['high_risk']:.1f}%")
        print()

    print("="*80)
    print("Next steps:")
    print("  1. Review suggested thresholds above")
    print("  2. Update scoring functions in src/scoring/*.py")
    print("  3. Re-run backfill: rm data/history/*.csv && python scripts/backfill_history.py ...")
    print("  4. Re-run backtest: python scripts/backtest.py")
    print("="*80)


if __name__ == '__main__':
    main()
