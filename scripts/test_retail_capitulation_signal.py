"""
Test Retail Capitulation Signal

Backtests the retail capitulation signal (Signal #10) on historical AAII sentiment data
to validate it catches extreme sentiment at major market turns.

Test periods:
- March 2009: Bulls <20% at market bottom (buying opportunity)
- January 2000: Bulls >60% at dot-com peak (sell signal)
- March 2020: Bulls <20% at COVID bottom (buying opportunity)
- Q4 2021: Bulls >60% before 2022 bear market (sell signal)
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scoring.aggregator import RiskAggregator
from src.config.config_manager import ConfigManager


def test_retail_capitulation_signal():
    """Test retail capitulation signal on historical AAII sentiment data."""

    print("="*80)
    print("TESTING RETAIL CAPITULATION SIGNAL (Signal #10)")
    print("="*80)
    print()

    # Check if AAII sentiment CSV exists
    aaii_file = 'data/external/aaii_sentiment.csv'

    if not os.path.exists(aaii_file):
        print(f"ERROR: AAII sentiment CSV not found at {aaii_file}")
        print()
        print("To create sample CSV template:")
        print(f"  python src/data/sentiment_data.py --create-sample")
        print()
        print("To download actual data:")
        print("  1. Visit https://www.aaii.com/sentimentsurvey/sent_results")
        print("  2. Download historical CSV (may require free membership)")
        print(f"  3. Save to {aaii_file}")
        print()
        return

    # Load AAII sentiment data
    try:
        aaii_data = pd.read_csv(aaii_file, parse_dates=['Date'])
        aaii_data.columns = [col.strip() for col in aaii_data.columns]
        aaii_data = aaii_data.sort_values('Date')
        print(f"Loaded {len(aaii_data)} weeks of AAII sentiment data")
        print(f"Date range: {aaii_data['Date'].min().date()} to {aaii_data['Date'].max().date()}")
        print()
    except Exception as e:
        print(f"ERROR loading AAII data: {e}")
        return

    # Initialize aggregator
    config = ConfigManager()
    aggregator = RiskAggregator(config)

    # Test periods of interest
    test_periods = [
        ('2000 Dot-Com Peak (Euphoria)', '1999-11-01', '2000-03-31'),
        ('2009 Financial Crisis Bottom (Capitulation)', '2009-02-01', '2009-04-30'),
        ('2020 COVID Bottom (Capitulation)', '2020-02-15', '2020-04-15'),
        ('2021-2022 Peak/Crash (Euphoria)', '2021-10-01', '2022-01-31'),
        ('Full Dataset', aaii_data['Date'].min().strftime('%Y-%m-%d'), aaii_data['Date'].max().strftime('%Y-%m-%d'))
    ]

    for period_name, start_date, end_date in test_periods:
        print(f"\n{'='*80}")
        print(f"PERIOD: {period_name} ({start_date} to {end_date})")
        print(f"{'='*80}\n")

        # Filter data
        period_data = aaii_data[(aaii_data['Date'] >= start_date) & (aaii_data['Date'] <= end_date)].copy()

        if len(period_data) == 0:
            print(f"No data available for {period_name}")
            continue

        # Track warnings
        capitulation_warnings = []
        euphoria_warnings = []

        # Iterate through each week
        for idx, row in period_data.iterrows():
            date = row['Date']
            bulls_pct = row['Bullish%']

            # Build sentiment data dict
            sentiment_data = {
                'bulls_percent': bulls_pct,
                'neutrals_percent': row['Neutral%'],
                'bears_percent': row['Bearish%']
            }

            # Check retail capitulation warning
            warning = aggregator._check_retail_capitulation(sentiment_data)

            if warning.get('active', False):
                warning_entry = {
                    'date': date,
                    'bulls_pct': bulls_pct,
                    'neutrals_pct': row['Neutral%'],
                    'bears_pct': row['Bearish%'],
                    'signal_type': warning['signal_type'],
                    'level': warning['level'],
                    'message': warning['message']
                }

                if warning['signal_type'] == 'CAPITULATION':
                    capitulation_warnings.append(warning_entry)
                else:
                    euphoria_warnings.append(warning_entry)

        # Report results
        print(f"Total weeks in period: {len(period_data)}")
        print(f"Capitulation warnings (bulls <20%): {len(capitulation_warnings)}")
        print(f"Euphoria warnings (bulls >60%): {len(euphoria_warnings)}")
        print()

        # Show capitulation warnings
        if len(capitulation_warnings) > 0:
            print(f"CAPITULATION signals ({len(capitulation_warnings)} weeks):")
            print(f"{'Date':<12} {'Bulls%':<10} {'Neutrals%':<12} {'Bears%':<10}")
            print("-"*50)

            for w in capitulation_warnings[:10]:  # Show first 10
                date_str = w['date'].strftime('%Y-%m-%d')
                bulls = f"{w['bulls_pct']:.1f}%"
                neutrals = f"{w['neutrals_pct']:.1f}%"
                bears = f"{w['bears_pct']:.1f}%"
                print(f"{date_str:<12} {bulls:<10} {neutrals:<12} {bears:<10}")

            if len(capitulation_warnings) > 10:
                print(f"... ({len(capitulation_warnings) - 10} more weeks)")

            # Print sample warning message
            print(f"\nSample CAPITULATION message:")
            print(f"-" * 80)
            print(capitulation_warnings[0]['message'])
            print()

        # Show euphoria warnings
        if len(euphoria_warnings) > 0:
            print(f"EUPHORIA signals ({len(euphoria_warnings)} weeks):")
            print(f"{'Date':<12} {'Bulls%':<10} {'Neutrals%':<12} {'Bears%':<10}")
            print("-"*50)

            for w in euphoria_warnings[:10]:  # Show first 10
                date_str = w['date'].strftime('%Y-%m-%d')
                bulls = f"{w['bulls_pct']:.1f}%"
                neutrals = f"{w['neutrals_pct']:.1f}%"
                bears = f"{w['bears_pct']:.1f}%"
                print(f"{date_str:<12} {bulls:<10} {neutrals:<12} {bears:<10}")

            if len(euphoria_warnings) > 10:
                print(f"... ({len(euphoria_warnings) - 10} more weeks)")

            # Print sample warning message
            print(f"\nSample EUPHORIA message:")
            print(f"-" * 80)
            print(euphoria_warnings[0]['message'])
            print()

        # Show some sample data points if no warnings
        if len(capitulation_warnings) == 0 and len(euphoria_warnings) == 0:
            print("No warnings triggered during this period.")
            print()
            print("Sample sentiment readings (first 5 weeks):")
            print(f"{'Date':<12} {'Bulls%':<10} {'Neutrals%':<12} {'Bears%':<10}")
            print("-"*50)

            for idx, row in period_data.head(5).iterrows():
                date_str = row['Date'].strftime('%Y-%m-%d')
                bulls = f"{row['Bullish%']:.1f}%"
                neutrals = f"{row['Neutral%']:.1f}%"
                bears = f"{row['Bearish%']:.1f}%"
                print(f"{date_str:<12} {bulls:<10} {neutrals:<12} {bears:<10}")
            print()

    print("="*80)
    print("RETAIL CAPITULATION SIGNAL TEST COMPLETE")
    print("="*80)
    print()
    print("Expected results:")
    print("  - March 2009: Should trigger CAPITULATION (bulls <20%)")
    print("    Market bottom at S&P 666, then rallied to 2,873 by 2019")
    print("  - January 2000: Should trigger EUPHORIA (bulls >60%)")
    print("    Dot-com peak, then -49% crash 2000-2002")
    print("  - March 2020: Should trigger CAPITULATION (bulls <20%)")
    print("    COVID bottom at S&P 2,237, then rallied to 4,818 by 2022")
    print("  - Q4 2021: May trigger EUPHORIA (bulls >60%)")
    print("    Before 2022 bear market (-25% decline)")
    print()
    print("Interpretation:")
    print("  - CAPITULATION (bulls <20%): Contrarian BUY signal")
    print("    - Extreme fear, time to deploy cash into quality assets")
    print("  - EUPHORIA (bulls >60%): Contrarian SELL signal")
    print("    - Extreme greed, time to trim positions and build cash")
    print()


if __name__ == '__main__':
    test_retail_capitulation_signal()
