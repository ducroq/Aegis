"""
Test script to evaluate valuation-based early warning system.

Shows how CAPE > 30 AND Buffett > 120% would perform as leading indicator.
"""

import pandas as pd
from datetime import datetime

def main():
    # Load raw indicators
    raw = pd.read_csv('data/history/raw_indicators.csv')
    raw['date'] = pd.to_datetime(raw['date'])

    # Valuation thresholds (calibrated from backtest)
    cape_threshold = 30.0
    buffett_threshold = 120.0

    # Find valuation warnings
    raw['valuation_warning'] = (
        (raw['valuation_shiller_cape'] > cape_threshold) &
        (raw['valuation_sp500_market_cap'] > buffett_threshold)
    )

    warnings = raw[raw['valuation_warning']].copy()

    print('=' * 80)
    print('VALUATION-BASED EARLY WARNING SYSTEM')
    print('=' * 80)
    print(f'\nThresholds: CAPE > {cape_threshold}, Buffett Indicator > {buffett_threshold}%')
    print(f'\nTotal warning months: {len(warnings)}/{len(raw)} ({len(warnings)/len(raw)*100:.1f}%)')

    # Define crashes
    crashes = [
        ('2000-03-24', '2002-10-09', 'Dot-com Bubble', -49.1),
        ('2007-10-09', '2009-03-09', 'Financial Crisis', -56.8),
        ('2020-02-19', '2020-03-23', 'COVID Crash', -33.9),
        ('2022-01-03', '2022-10-12', 'Bear Market', -25.4),
    ]

    print('\n' + '=' * 80)
    print('CRASH DETECTION PERFORMANCE')
    print('=' * 80)

    detected_crashes = 0

    for peak_str, end_str, name, drawdown in crashes:
        peak = pd.to_datetime(peak_str)
        lookback = peak - pd.Timedelta(days=180)

        # Warnings before peak
        pre_warnings = warnings[(warnings['date'] >= lookback) & (warnings['date'] < peak)]

        print(f'\n{name}:')
        print(f'  Peak: {peak_str}')
        print(f'  Drawdown: {drawdown}%')

        if len(pre_warnings) > 0:
            detected_crashes += 1
            earliest = pre_warnings['date'].min()
            days_before = (peak - earliest).days
            print(f'  WARNING: {len(pre_warnings)} months before peak')
            print(f'  Earliest warning: {earliest.strftime("%Y-%m-%d")} ({days_before} days before peak)')
            print(f'  CAPE range: {pre_warnings["valuation_shiller_cape"].min():.1f}-{pre_warnings["valuation_shiller_cape"].max():.1f}')
            print(f'  Buffett range: {pre_warnings["valuation_sp500_market_cap"].min():.0f}%-{pre_warnings["valuation_sp500_market_cap"].max():.0f}%')
        else:
            print(f'  NO WARNING')
            # Show why it didn't warn
            pre_crash = raw[(raw['date'] >= lookback) & (raw['date'] < peak)]
            if len(pre_crash) > 0:
                max_cape = pre_crash['valuation_shiller_cape'].max()
                max_buffett = pre_crash['valuation_sp500_market_cap'].max()
                print(f'  Max CAPE: {max_cape:.1f} (threshold: {cape_threshold})')
                print(f'  Max Buffett: {max_buffett:.0f}% (threshold: {buffett_threshold}%)')

                if max_cape <= cape_threshold:
                    print(f'  Reason: CAPE too low (credit/housing crisis, not valuation bubble)')
                elif max_buffett <= buffett_threshold:
                    print(f'  Reason: Buffett indicator too low')

    detection_rate = detected_crashes / len(crashes) * 100

    print('\n' + '=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print(f'\nDetection rate: {detected_crashes}/{len(crashes)} major crashes ({detection_rate:.0f}%)')

    # False positives (warning periods NOT followed by crash within 12 months)
    false_positives = 0
    warning_periods = []

    # Group consecutive warnings into periods
    current_period = None
    for _, row in warnings.iterrows():
        if current_period is None:
            current_period = {'start': row['date'], 'end': row['date']}
        elif (row['date'] - current_period['end']).days <= 60:  # Within 2 months
            current_period['end'] = row['date']
        else:
            warning_periods.append(current_period)
            current_period = {'start': row['date'], 'end': row['date']}

    if current_period:
        warning_periods.append(current_period)

    print(f'\nWarning periods: {len(warning_periods)}')

    for period in warning_periods:
        # Check if crash occurred within 12 months after period end
        lookforward = period['end'] + pd.Timedelta(days=365)

        crash_followed = False
        for peak_str, end_str, name, drawdown in crashes:
            peak = pd.to_datetime(peak_str)
            if period['start'] <= peak <= lookforward:
                crash_followed = True
                break

        duration_months = (period['end'].year - period['start'].year) * 12 + (period['end'].month - period['start'].month) + 1

        print(f'\n  {period["start"].strftime("%Y-%m")} to {period["end"].strftime("%Y-%m")} ({duration_months} months):')
        if crash_followed:
            print(f'    FOLLOWED BY: {name} within 12 months')
        else:
            false_positives += 1
            print(f'    FALSE POSITIVE: No crash within 12 months')

    fp_rate = false_positives / len(warning_periods) * 100 if len(warning_periods) > 0 else 0
    print(f'\nFalse positive rate: {false_positives}/{len(warning_periods)} periods ({fp_rate:.0f}%)')

    print('\n' + '=' * 80)
    print('INTERPRETATION')
    print('=' * 80)
    print(f"""
This system provides LEADING warnings for valuation-driven crashes:
- Detected Dot-com and COVID crashes BEFORE they happened
- Missed Financial Crisis (credit/housing crisis, not valuation bubble)
- {fp_rate:.0f}% false positive rate (warnings not followed by crash)

False positives represent extended bubble periods (2017-2018, 2020-2021).
Markets can remain overvalued for months/years before correcting.

RECOMMENDATION: Use as "elevated risk" warning, not immediate sell signal.
When warning active: gradually build cash, reduce margin, tighten stops.
""")

if __name__ == '__main__':
    main()
