"""
Test Real Interest Rate Warning Signal

Backtests the real rate signal on historical data to validate it catches
Fed tightening cycles like 2022 bear market, 1994, 2018 Q4.
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scoring.aggregator import RiskAggregator
from src.config.config_manager import ConfigManager


def test_real_rate_signal():
    """Test real rate warning signal on historical data."""

    print("="*70)
    print("TESTING REAL INTEREST RATE WARNING SIGNAL")
    print("="*70)
    print()

    # Load historical data
    raw_file = 'data/history/raw_indicators.csv'

    if not os.path.exists(raw_file):
        print(f"ERROR: {raw_file} not found. Run backfill_history.py first.")
        return

    raw = pd.read_csv(raw_file, parse_dates=['date'])
    print(f"Loaded {len(raw)} months of historical data ({raw['date'].min().date()} to {raw['date'].max().date()})")
    print()

    # Initialize aggregator
    config = ConfigManager()
    aggregator = RiskAggregator(config)

    # Test periods of interest
    test_periods = [
        ('2022 Bear Market', '2022-01-01', '2023-12-31'),
        ('2018 Q4 Selloff', '2018-01-01', '2018-12-31'),
        ('2015-2016 Tightening', '2015-01-01', '2016-12-31'),
        ('Full Dataset', raw['date'].min().strftime('%Y-%m-%d'), raw['date'].max().strftime('%Y-%m-%d'))
    ]

    for period_name, start_date, end_date in test_periods:
        print(f"\n{'='*70}")
        print(f"PERIOD: {period_name} ({start_date} to {end_date})")
        print(f"{'='*70}\n")

        # Filter data
        period_data = raw[(raw['date'] >= start_date) & (raw['date'] <= end_date)].copy()

        if len(period_data) == 0:
            print(f"No data available for {period_name}")
            continue

        # Track warnings
        warnings_found = []

        # Iterate through each month
        for idx, row in period_data.iterrows():
            date = row['date']

            # Build liquidity data dict
            liquidity_data = {
                'fed_funds_rate': row.get('liquidity_fed_funds_rate'),
                'cpi_inflation_yoy': row.get('liquidity_cpi_inflation_yoy'),
                'fed_funds_velocity_6m': row.get('liquidity_fed_funds_velocity_6m')
            }

            # Check real rate warning
            warning = aggregator._check_real_rate_warning(liquidity_data)

            if warning.get('active', False):
                warnings_found.append({
                    'date': date,
                    'level': warning['level'],
                    'real_rate': warning['real_rate'],
                    'fed_funds': warning['fed_funds'],
                    'inflation': warning['inflation'],
                    'velocity_6m': warning['velocity_6m'],
                    'message': warning['message']
                })

        # Report results
        print(f"Total months in period: {len(period_data)}")
        print(f"Warnings triggered: {len(warnings_found)}")

        if len(warnings_found) > 0:
            print(f"\nWarning months ({len(warnings_found)} total):")
            print(f"{'Date':<12} {'Real Rate':>10} {'Fed Funds':>10} {'Inflation':>10} {'6M Velocity':>12} {'Level':<10}")
            print("-"*70)

            for w in warnings_found:
                print(f"{w['date'].strftime('%Y-%m'):<12} {w['real_rate']:>9.1f}% {w['fed_funds']:>9.2f}% {w['inflation']:>9.1f}% {w['velocity_6m']:>11.1f}% {w['level']:<10}")

            print(f"\nFirst warning: {warnings_found[0]['date'].strftime('%Y-%m-%d')}")
            print(f"Last warning: {warnings_found[-1]['date'].strftime('%Y-%m-%d')}")

            # Show first warning message
            print(f"\nExample warning message:")
            print(f"  {warnings_found[0]['message'][:200]}...")
        else:
            print("\nNO WARNINGS triggered in this period")

            # Show why (look at a sample)
            if len(period_data) > 0:
                sample = period_data.iloc[len(period_data)//2]  # Mid-period
                fed_funds = sample.get('liquidity_fed_funds_rate')
                cpi_yoy = sample.get('liquidity_cpi_inflation_yoy')
                velocity = sample.get('liquidity_fed_funds_velocity_6m')

                if fed_funds and cpi_yoy:
                    real_rate = fed_funds - cpi_yoy
                    print(f"\nSample (mid-period {sample['date'].strftime('%Y-%m')}):")
                    print(f"  Fed funds: {fed_funds:.2f}%")
                    print(f"  CPI inflation: {cpi_yoy:.1f}%")
                    print(f"  Real rate: {real_rate:.1f}%")
                    print(f"  6M velocity: {velocity:.1f}% change" if velocity else "  6M velocity: N/A")
                    print(f"\n  Threshold: Real rate > 2.0% AND 6M velocity > 3.0%")

    print("\n" + "="*70)
    print("BACKTEST COMPLETE")
    print("="*70)
    print("\nSignal #3 (Real Interest Rate Warning) status: TESTED")
    print("\nExpected performance:")
    print("  - 2022 bear market: Should warn ~Q1-Q2 2022 (early in tightening cycle)")
    print("  - 2018 Q4: Possible warning (Fed was tightening before Dec pivot)")
    print("  - Other periods: May not trigger (need both high real rates + rapid tightening)")


if __name__ == '__main__':
    test_real_rate_signal()
