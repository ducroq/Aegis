"""
Test Script for Signal #4 (Earnings Recession Warning)

This script backtests the earnings recession signal on historical data
to validate it catches profit declines without GDP recessions.

NOTE: Uses Shiller TRAILING 12-month earnings (lagging indicator).
Forward earnings estimates are not available historically. This detects
earnings recessions DURING the decline, not predictively.

Expected to catch:
- 2001-2002 post-tech bubble earnings collapse
- 2008-2009 financial crisis earnings decline
- 2015-2016 energy/industrial earnings recession
- Other periods of corporate profit pressure
"""

import sys
import os
import pandas as pd
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config.config_manager import ConfigManager
from src.scoring.aggregator import RiskAggregator

logging.basicConfig(
    level=logging.WARNING,  # Suppress info logs, only show warnings
    format='%(levelname)s - %(message)s'
)

def test_earnings_recession_signal():
    """Test earnings recession signal on historical data."""
    print("=" * 70)
    print("TESTING EARNINGS RECESSION WARNING SIGNAL")
    print("=" * 70)
    print()

    # Load historical data
    raw_indicators_path = 'data/history/raw_indicators.csv'
    if not os.path.exists(raw_indicators_path):
        print(f"ERROR: {raw_indicators_path} not found!")
        print("Run backfill_history.py first.")
        return

    raw = pd.read_csv(raw_indicators_path)
    print(f"Loaded {len(raw)} months of historical data ({raw['date'].iloc[0]} to {raw['date'].iloc[-1]})")
    print()

    # Initialize aggregator
    config = ConfigManager()
    aggregator = RiskAggregator(config)

    # Test periods
    test_periods = [
        {
            'name': '2015-2016 Earnings Recession',
            'start': '2015-01-01',
            'end': '2016-12-31',
            'description': 'Energy sector collapse + industrial recession caused earnings decline without GDP recession'
        },
        {
            'name': '2022 Q1-Q2 Margin Compression',
            'start': '2022-01-01',
            'end': '2022-06-30',
            'description': 'Inflation + supply chains squeezed profit margins early in 2022 bear market'
        },
        {
            'name': '2001-2002 Tech Earnings Collapse',
            'start': '2001-01-01',
            'end': '2002-12-31',
            'description': 'Post-bubble earnings plunge during recession'
        },
        {
            'name': '2008-2009 Financial Crisis',
            'start': '2008-01-01',
            'end': '2009-12-31',
            'description': 'Massive earnings decline during recession'
        },
        {
            'name': 'Full Dataset',
            'start': raw['date'].iloc[0],
            'end': raw['date'].iloc[-1],
            'description': 'All historical data'
        }
    ]

    for period in test_periods:
        print("=" * 70)
        print(f"PERIOD: {period['name']} ({period['start']} to {period['end']})")
        print("=" * 70)
        print()

        # Filter data for period
        period_data = raw[
            (raw['date'] >= period['start']) &
            (raw['date'] <= period['end'])
        ]

        if len(period_data) == 0:
            print(f"NO DATA for period {period['name']}")
            print()
            continue

        print(f"Total months in period: {len(period_data)}")

        # Collect warnings
        warnings = []

        for idx in range(len(period_data)):
            row = period_data.iloc[idx]
            date = row['date']

            # Get historical window (need 7 rows for 6-month lookback)
            hist_start_idx = max(0, idx - 6)
            hist_window = period_data.iloc[hist_start_idx:idx+1]

            # Prepare data for aggregator
            valuation_data = {
                'shiller_trailing_earnings': row.get('valuation_shiller_trailing_earnings')
            }

            # Check earnings recession
            earnings_warning = aggregator._check_earnings_recession(
                valuation_data,
                hist_window
            )

            if earnings_warning.get('active', False):
                warnings.append({
                    'date': date,
                    'current_earnings': earnings_warning.get('current_trailing_earnings'),
                    'earnings_12m_ago': earnings_warning.get('trailing_earnings_12m_ago'),
                    'earnings_change_pct': earnings_warning.get('earnings_change_12m_pct'),
                    'message': earnings_warning.get('message')
                })

        print(f"Warnings triggered: {len(warnings)}")
        print()

        if len(warnings) > 0:
            print(f"Warning months ({len(warnings)} total):")
            print(f"{'Date':<15} {'Current E12M':<14} {'12M Ago E12M':<14} {'% Change':<10} {'Level':<10}")
            print("-" * 75)

            for w in warnings:
                earnings_change = w['earnings_change_pct'] if w['earnings_change_pct'] is not None else 0
                current_earnings = w['current_earnings'] if w['current_earnings'] is not None else 0
                earnings_12m = w['earnings_12m_ago'] if w['earnings_12m_ago'] is not None else 0
                print(f"{w['date']:<15} ${current_earnings:<13.2f} ${earnings_12m:<13.2f} {earnings_change:<9.1f}% {'HIGH':<10}")

            print()
            print(f"First warning: {warnings[0]['date']}")
            print(f"Last warning: {warnings[-1]['date']}")
            print()
            print("Example warning message:")
            print(f"  {warnings[0]['message'][:150]}...")
        else:
            print("NO WARNINGS triggered in this period")
            print()

            # Show sample mid-period data for debugging
            if len(period_data) > 0:
                mid_idx = len(period_data) // 2
                mid_row = period_data.iloc[mid_idx]
                mid_date = mid_row['date']

                trailing_earnings = mid_row.get('valuation_shiller_trailing_earnings')

                if trailing_earnings:
                    # Get 12 months ago if available
                    if mid_idx >= 12:
                        twelve_mo_row = period_data.iloc[mid_idx - 12]
                        trailing_earnings_12m = twelve_mo_row.get('valuation_shiller_trailing_earnings')

                        if trailing_earnings_12m and trailing_earnings_12m > 0:
                            earnings_change = (trailing_earnings - trailing_earnings_12m) / trailing_earnings_12m * 100

                            print(f"Sample (mid-period {mid_date}):")
                            print(f"  Current trailing 12M earnings: ${trailing_earnings:.2f}")
                            print(f"  12M Ago trailing 12M earnings: ${trailing_earnings_12m:.2f}")
                            print(f"  12M Change: {earnings_change:.1f}%")
                            print()
                            print(f"  Threshold: Earnings change < -10.0%")
                        else:
                            print(f"Sample (mid-period {mid_date}):")
                            print(f"  Current trailing 12M earnings: ${trailing_earnings:.2f}")
                            print(f"  12M historical data not available yet")
                else:
                    print(f"Sample (mid-period {mid_date}):")
                    print(f"  Trailing earnings not available (missing data)")

        print()

    print("=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)
    print()
    print("Signal #4 (Earnings Recession Warning) status: TESTED")
    print()
    print("Expected performance:")
    print("  - 2001-2002: Should warn during post-tech bubble earnings collapse")
    print("  - 2008-2009: Should warn during financial crisis earnings decline")
    print("  - 2015-2016: Should warn during energy/industrial earnings recession")
    print("  - Other periods: Catches profit declines distinct from GDP recessions")
    print()
    print("NOTE: Uses Shiller TRAILING 12M earnings (lagging indicator)")
    print("      This detects earnings recessions DURING the decline, not predictively.")


if __name__ == '__main__':
    test_earnings_recession_signal()
