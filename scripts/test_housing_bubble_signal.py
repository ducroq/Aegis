"""
Test Script for Signal #5 (Housing Bubble Warning)

This script backtests the housing bubble signal on historical data
to validate it catches housing market stress periods.

Expected to catch:
- 2007-2008 housing crash
- 2022-2023 housing freeze
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

def test_housing_bubble_signal():
    """Test housing bubble signal on historical data."""
    print("=" * 70)
    print("TESTING HOUSING BUBBLE WARNING SIGNAL")
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
            'name': '2007-2008 Housing Crisis',
            'start': '2007-01-01',
            'end': '2008-12-31',
            'description': 'Subprime collapse + housing crash led to financial crisis'
        },
        {
            'name': '2022-2023 Housing Freeze',
            'start': '2022-01-01',
            'end': '2023-12-31',
            'description': 'Fed rate hikes caused mortgage rates to spike, freezing housing market'
        },
        {
            'name': '2005-2006 Housing Peak',
            'start': '2005-01-01',
            'end': '2006-12-31',
            'description': 'Peak of housing bubble before collapse'
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
                'new_home_sales': row.get('valuation_new_home_sales'),
                'mortgage_rate_30y': row.get('valuation_mortgage_rate_30y'),
                'median_home_price': row.get('valuation_median_home_price')
            }

            # Check housing bubble
            housing_warning = aggregator._check_housing_bubble(
                valuation_data,
                hist_window
            )

            if housing_warning.get('active', False):
                warnings.append({
                    'date': date,
                    'new_home_sales': housing_warning.get('new_home_sales'),
                    'sales_6m_ago': housing_warning.get('new_home_sales_6m_ago'),
                    'sales_change_pct': housing_warning.get('sales_change_6m_pct'),
                    'mortgage_rate': housing_warning.get('mortgage_rate_30y'),
                    'message': housing_warning.get('message')
                })

        print(f"Warnings triggered: {len(warnings)}")
        print()

        if len(warnings) > 0:
            print(f"Warning months ({len(warnings)} total):")
            print(f"{'Date':<15} {'Sales (k)':<12} {'6M Ago (k)':<12} {'% Change':<10} {'Mtg Rate':<10} {'Level':<10}")
            print("-" * 80)

            for w in warnings:
                sales_change = w['sales_change_pct'] if w['sales_change_pct'] is not None else 0
                sales = w['new_home_sales'] if w['new_home_sales'] is not None else 0
                sales_6m = w['sales_6m_ago'] if w['sales_6m_ago'] is not None else 0
                mtg_rate = w['mortgage_rate'] if w['mortgage_rate'] is not None else 0
                print(f"{w['date']:<15} {sales:<11.0f} {sales_6m:<11.0f} {sales_change:<9.1f}% {mtg_rate:<9.2f}% {'HIGH':<10}")

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

                sales = mid_row.get('valuation_new_home_sales')
                mtg_rate = mid_row.get('valuation_mortgage_rate_30y')

                if sales and mid_idx >= 6:
                    six_mo_row = period_data.iloc[mid_idx - 6]
                    sales_6m = six_mo_row.get('valuation_new_home_sales')

                    if sales_6m and sales_6m > 0:
                        sales_change = (sales - sales_6m) / sales_6m * 100

                        print(f"Sample (mid-period {mid_date}):")
                        print(f"  Current sales: {sales:.0f}k units")
                        print(f"  6M Ago sales: {sales_6m:.0f}k units")
                        print(f"  6M Change: {sales_change:.1f}%")
                        print(f"  Mortgage rate: {mtg_rate:.2f}%" if mtg_rate else "  Mortgage rate: N/A")
                        print()
                        print(f"  Thresholds: Sales change < -20% AND Mortgage rate > 6.5%")
                else:
                    print(f"Sample (mid-period {mid_date}):")
                    print(f"  Home sales: {sales:.0f}k units" if sales else "  Home sales: N/A")
                    print(f"  Mortgage rate: {mtg_rate:.2f}%" if mtg_rate else "  Mortgage rate: N/A")

        print()

    print("=" * 70)
    print("BACKTEST COMPLETE")
    print("=" * 70)
    print()
    print("Signal #5 (Housing Bubble Warning) status: TESTED")
    print()
    print("Expected performance:")
    print("  - 2007-2008: Should warn as housing crash accelerates")
    print("  - 2022-2023: Should warn as Fed hikes freeze housing market")
    print("  - Other periods: May warn during housing downturns with high rates")


if __name__ == '__main__':
    test_housing_bubble_signal()
