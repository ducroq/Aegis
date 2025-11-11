"""
Test Dollar Liquidity Stress Signal

Backtests the dollar liquidity stress signal on historical data to validate
it catches global dollar funding shortages like 2008 Lehman crisis and March 2020 COVID panic.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scoring.aggregator import RiskAggregator
from src.config.config_manager import ConfigManager


def test_dollar_liquidity_signal():
    """Test dollar liquidity stress signal on historical data."""

    print("="*80)
    print("TESTING DOLLAR LIQUIDITY STRESS SIGNAL")
    print("="*80)
    print()

    # Load historical data
    raw_file = 'data/history/raw_indicators.csv'

    if not os.path.exists(raw_file):
        print(f"ERROR: {raw_file} not found. Run incremental_backfill.py first.")
        return

    raw = pd.read_csv(raw_file, parse_dates=['date'])
    print(f"Loaded {len(raw)} months of historical data ({raw['date'].min().date()} to {raw['date'].max().date()})")
    print()

    # Initialize aggregator
    config = ConfigManager()
    aggregator = RiskAggregator(config)

    # Test periods of interest (dollar index only available from 2006+)
    test_periods = [
        ('2008 Financial Crisis', '2008-01-01', '2009-12-31'),
        ('March 2020 COVID Panic', '2020-01-01', '2020-06-30'),
        ('2022 Dollar Surge', '2022-01-01', '2022-12-31'),
        ('Full Dataset (2006+)', '2006-01-01', raw['date'].max().strftime('%Y-%m-%d'))
    ]

    for period_name, start_date, end_date in test_periods:
        print(f"\n{'='*80}")
        print(f"PERIOD: {period_name} ({start_date} to {end_date})")
        print(f"{'='*80}\n")

        # Filter data
        period_data = raw[(raw['date'] >= start_date) & (raw['date'] <= end_date)].copy()

        if len(period_data) == 0:
            print(f"No data available for {period_name}")
            continue

        # Track warnings
        warnings_found = []

        # Iterate through each month (need at least 4 months history for 3-month change)
        for i in range(len(period_data)):
            if i < 3:
                continue  # Skip first 3 months (need 3-month lookback)

            current_row = period_data.iloc[i]
            date = current_row['date']

            # Build liquidity data dict
            liquidity_data = {
                'dollar_index': current_row.get('liquidity_dollar_index'),
                'fed_swap_lines': current_row.get('liquidity_fed_swap_lines')
            }

            # Get historical data window for lookback calculations
            historical_window = period_data.iloc[:i+1]

            # Check dollar liquidity stress warning
            warning = aggregator._check_dollar_liquidity_stress(
                liquidity_data,
                historical_window
            )

            if warning.get('active', False):
                warnings_found.append({
                    'date': date,
                    'level': warning['level'],
                    'dollar_index': warning.get('current_dollar_index'),
                    'dollar_3m_ago': warning.get('dollar_3m_ago'),
                    'dollar_change_3m_pct': warning.get('dollar_change_3m_pct'),
                    'swap_lines': warning.get('swap_lines_outstanding'),
                    'swap_elevated': warning.get('swap_lines_elevated'),
                    'message': warning['message']
                })

        # Report results
        print(f"Total months in period: {len(period_data)}")
        print(f"Warnings triggered: {len(warnings_found)}")

        if len(warnings_found) > 0:
            print(f"\nWarning months ({len(warnings_found)} total):")
            print(f"{'Date':<12} {'DXY':<8} {'3M Ago':<8} {'3M Chg%':<10} {'Swap $B':<10} {'Elevated':>10} {'Level':<10}")
            print("-"*80)

            for w in warnings_found:
                date_str = w['date'].strftime('%Y-%m-%d')
                dxy = f"{w['dollar_index']:.2f}" if w['dollar_index'] is not None else 'N/A'
                dxy_3m = f"{w['dollar_3m_ago']:.2f}" if w['dollar_3m_ago'] is not None else 'N/A'
                chg_3m = f"{w['dollar_change_3m_pct']:+.1f}%" if w['dollar_change_3m_pct'] is not None else 'N/A'
                swap = f"${w['swap_lines']:.1f}B" if w['swap_lines'] is not None else 'N/A'
                elevated = "YES" if w.get('swap_elevated') else "NO"
                level = w['level']

                print(f"{date_str:<12} {dxy:<8} {dxy_3m:<8} {chg_3m:<10} {swap:<10} {elevated:>10} {level:<10}")

            # Print sample warning message
            print(f"\nSample warning message:")
            print(f"-" * 80)
            print(warnings_found[0]['message'])
            print()

        else:
            print("No warnings triggered during this period.")
            print()

            # Show some sample data points to verify data availability
            print("Sample data points (first 5 months with dollar index):")
            print(f"{'Date':<12} {'Dollar Index':<15} {'Fed Swap Lines ($B)':<20}")
            print("-"*50)

            count = 0
            for idx, row in period_data.iterrows():
                dxy = row.get('liquidity_dollar_index')
                swap = row.get('liquidity_fed_swap_lines')

                if dxy is not None:
                    date_str = row['date'].strftime('%Y-%m-%d')
                    dxy_str = f"{dxy:.2f}"
                    swap_str = f"${swap:.1f}B" if swap is not None else 'N/A'
                    print(f"{date_str:<12} {dxy_str:<15} {swap_str:<20}")
                    count += 1

                    if count >= 5:
                        break

            if count == 0:
                print("(No dollar index data available for this period)")
            print()

    print("="*80)
    print("DOLLAR LIQUIDITY STRESS SIGNAL TEST COMPLETE")
    print("="*80)
    print()
    print("Expected results:")
    print("  - 2008 Financial Crisis: Should trigger during Lehman collapse (Sep-Dec 2008)")
    print("    with rapid dollar surge + elevated swap lines")
    print("  - March 2020 COVID: Should trigger during panic (Mar-Apr 2020)")
    print("    with extreme dollar spike (8%+ in weeks)")
    print("  - 2022 Dollar Surge: May trigger if dollar rose >5% in 3 months,")
    print("    but likely gradual (not panic-level)")
    print()


if __name__ == '__main__':
    test_dollar_liquidity_signal()
