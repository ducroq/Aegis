"""
Comprehensive backtest of new liquidity override rules (2000-2024).

Tests:
1. Recalculate all risk scores with new weights (recession 25%, liquidity 20%)
2. Apply liquidity override rule (Fed velocity > 300% -> force YELLOW)
3. Identify all YELLOW/RED alerts
4. Calculate false positive rate vs known crisis periods

Known crisis periods (20%+ drawdowns):
- 2000-09 to 2002-10: Tech bubble (-49%)
- 2007-10 to 2009-03: Financial crisis (-57%)
- 2020-02 to 2020-03: COVID crash (-34%)
- 2022-01 to 2022-10: Fed bear market (-25%)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

# Crisis periods (YYYY-MM format)
CRISIS_PERIODS = [
    ('2000-09', '2002-10', 'Tech Bubble', -49),
    ('2007-10', '2009-03', 'Financial Crisis', -57),
    ('2020-02', '2020-03', 'COVID Crash', -34),
    ('2022-01', '2022-10', 'Fed Bear Market', -25),
]

def parse_date(date_str):
    """Parse YYYY-MM or YYYY-MM-DD to datetime"""
    if pd.isna(date_str):
        return None
    try:
        return pd.to_datetime(date_str)
    except:
        return None

def is_in_crisis(date_str: str, crisis_periods: List[Tuple]) -> Tuple[bool, str]:
    """Check if date falls within any crisis period"""
    try:
        date = pd.to_datetime(date_str)
        for start, end, name, drawdown in crisis_periods:
            start_date = pd.to_datetime(start)
            end_date = pd.to_datetime(end)
            if start_date <= date <= end_date:
                return True, name
        return False, None
    except:
        return False, None

def recalculate_risk_with_new_weights(row: pd.Series) -> float:
    """Recalculate overall risk score with new weights"""
    # New weights (from config/app.yaml update)
    weights = {
        'recession': 0.25,   # Was 0.30
        'credit': 0.25,
        'valuation': 0.20,
        'liquidity': 0.20,   # Was 0.15
        'positioning': 0.10
    }

    # Get dimension scores
    recession = row.get('recession', 0)
    credit = row.get('credit', 0)
    valuation = row.get('valuation', 0)
    liquidity = row.get('liquidity', 0)
    positioning = row.get('positioning', 0)

    # Weighted average
    overall = (
        recession * weights['recession'] +
        credit * weights['credit'] +
        valuation * weights['valuation'] +
        liquidity * weights['liquidity'] +
        positioning * weights['positioning']
    )

    return round(overall, 2)

def check_liquidity_override(liquidity_score: float, fed_velocity: float) -> Dict:
    """Check if liquidity override should trigger"""
    # Trigger 1: Liquidity dimension score >= 8.5
    if liquidity_score >= 8.5:
        return {
            'active': True,
            'trigger': 'liquidity_score',
            'liquidity_score': liquidity_score,
            'fed_velocity': fed_velocity
        }

    # Trigger 2: Fed velocity > 300% in 6 months
    if not pd.isna(fed_velocity) and abs(fed_velocity) > 300:
        return {
            'active': True,
            'trigger': 'fed_velocity',
            'liquidity_score': liquidity_score,
            'fed_velocity': fed_velocity
        }

    # No override
    return {
        'active': False,
        'trigger': None,
        'liquidity_score': liquidity_score,
        'fed_velocity': fed_velocity
    }

def get_tier(overall_score: float, override_active: bool, original_tier: str) -> str:
    """Determine risk tier with override logic"""
    # Calculate tier from score
    if overall_score >= 5.0:
        tier = 'RED'
    elif overall_score >= 4.0:
        tier = 'YELLOW'
    else:
        tier = 'GREEN'

    # Apply override if score would be GREEN
    if override_active and tier == 'GREEN':
        tier = 'YELLOW'

    return tier

def main():
    print("="*80)
    print("COMPREHENSIVE BACKTEST: New Liquidity Override Rules (2000-2024)")
    print("="*80)
    print()

    # Load historical data
    print("Loading historical data...")
    risk_df = pd.read_csv('data/history/risk_scores.csv')
    raw_df = pd.read_csv('data/history/raw_indicators.csv')

    # Merge on date
    df = pd.merge(risk_df, raw_df[['date', 'liquidity_fed_funds_velocity_6m']], on='date', how='left')

    print(f"Loaded {len(df)} months of data ({df['date'].min()} to {df['date'].max()})")
    print()

    # Recalculate scores with new weights
    print("Recalculating risk scores with new weights...")
    df['new_overall_risk'] = df.apply(recalculate_risk_with_new_weights, axis=1)

    # Check liquidity override for each row
    print("Applying liquidity override rules...")
    override_results = df.apply(
        lambda row: check_liquidity_override(
            row['liquidity'],
            row['liquidity_fed_funds_velocity_6m']
        ),
        axis=1
    )

    df['override_active'] = override_results.apply(lambda x: x['active'])
    df['override_trigger'] = override_results.apply(lambda x: x['trigger'])

    # Determine new tier
    df['new_tier'] = df.apply(
        lambda row: get_tier(
            row['new_overall_risk'],
            row['override_active'],
            row['tier']
        ),
        axis=1
    )

    # Check if in crisis period
    df['in_crisis'] = df['date'].apply(lambda d: is_in_crisis(d, CRISIS_PERIODS)[0])
    df['crisis_name'] = df['date'].apply(lambda d: is_in_crisis(d, CRISIS_PERIODS)[1])

    print()
    print("="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    print()

    # Count alerts by tier
    yellow_alerts = df[df['new_tier'] == 'YELLOW']
    red_alerts = df[df['new_tier'] == 'RED']
    total_alerts = len(yellow_alerts) + len(red_alerts)

    print(f"Total months analyzed: {len(df)}")
    print(f"YELLOW alerts: {len(yellow_alerts)} ({len(yellow_alerts)/len(df)*100:.1f}%)")
    print(f"RED alerts: {len(red_alerts)} ({len(red_alerts)/len(df)*100:.1f}%)")
    print(f"Total alerts: {total_alerts} ({total_alerts/len(df)*100:.1f}%)")
    print()

    # Override statistics
    override_months = df[df['override_active']]
    fed_vel_overrides = df[df['override_trigger'] == 'fed_velocity']
    liq_score_overrides = df[df['override_trigger'] == 'liquidity_score']

    print(f"Liquidity override triggered: {len(override_months)} months ({len(override_months)/len(df)*100:.1f}%)")
    print(f"  - Fed velocity > 300%: {len(fed_vel_overrides)} months")
    print(f"  - Liquidity score >= 8.5: {len(liq_score_overrides)} months")
    print()

    # Crisis period coverage
    print("="*80)
    print("CRISIS PERIOD COVERAGE")
    print("="*80)
    print()

    for start, end, name, drawdown in CRISIS_PERIODS:
        crisis_df = df[(df['date'] >= start) & (df['date'] <= end)]
        alerts_in_crisis = crisis_df[crisis_df['new_tier'].isin(['YELLOW', 'RED'])]

        coverage = len(alerts_in_crisis) / len(crisis_df) * 100 if len(crisis_df) > 0 else 0

        print(f"{name} ({start} to {end}, {drawdown}% drawdown):")
        print(f"  Months in period: {len(crisis_df)}")
        print(f"  Months alerted: {len(alerts_in_crisis)} ({coverage:.1f}% coverage)")

        if len(alerts_in_crisis) > 0:
            first_alert = alerts_in_crisis.iloc[0]
            print(f"  First alert: {first_alert['date']} ({first_alert['new_tier']})")

            # Check if override was used
            if first_alert['override_active']:
                print(f"  Override trigger: {first_alert['override_trigger']}")
        else:
            print(f"  WARNING: NO ALERTS during this crisis!")

        print()

    # False positive analysis
    print("="*80)
    print("FALSE POSITIVE ANALYSIS")
    print("="*80)
    print()

    crisis_months = df[df['in_crisis']]
    non_crisis_months = df[~df['in_crisis']]

    alerts_in_crisis = crisis_months[crisis_months['new_tier'].isin(['YELLOW', 'RED'])]
    alerts_in_non_crisis = non_crisis_months[non_crisis_months['new_tier'].isin(['YELLOW', 'RED'])]

    print(f"Crisis months (20%+ drawdowns): {len(crisis_months)}")
    print(f"  Alerts during crises: {len(alerts_in_crisis)} ({len(alerts_in_crisis)/len(crisis_months)*100:.1f}%)")
    print()
    print(f"Non-crisis months: {len(non_crisis_months)}")
    print(f"  Alerts outside crises: {len(alerts_in_non_crisis)} ({len(alerts_in_non_crisis)/len(non_crisis_months)*100:.1f}%)")
    print()

    # False positive rate
    false_positive_rate = len(alerts_in_non_crisis) / len(non_crisis_months) * 100
    print(f"FALSE POSITIVE RATE: {false_positive_rate:.1f}%")
    print(f"  (Alerts outside 20%+ drawdown periods)")
    print()

    # Expected alerts per year
    alerts_per_month = total_alerts / len(df)
    alerts_per_year = alerts_per_month * 12
    print(f"Expected alert frequency: {alerts_per_year:.1f} alerts/year")
    print()

    # Show all alerts outside crisis periods
    if len(alerts_in_non_crisis) > 0:
        print("="*80)
        print(f"ALL ALERTS OUTSIDE CRISIS PERIODS ({len(alerts_in_non_crisis)} months)")
        print("="*80)
        print()

        for idx, row in alerts_in_non_crisis.iterrows():
            override_str = ""
            if row['override_active']:
                override_str = f" [OVERRIDE: {row['override_trigger']}]"

            fed_vel_str = ""
            if not pd.isna(row['liquidity_fed_funds_velocity_6m']):
                fed_vel_str = f" (FedVel: {row['liquidity_fed_funds_velocity_6m']:+.1f}%)"

            print(f"{row['date']}: {row['new_tier']} (Score: {row['new_overall_risk']:.2f}){override_str}{fed_vel_str}")
            print(f"  Dimensions: R={row['recession']:.1f} C={row['credit']:.1f} V={row['valuation']:.1f} L={row['liquidity']:.1f} P={row['positioning']:.1f}")
        print()

    # Show 2022 specifically
    print("="*80)
    print("2022 BEAR MARKET DETAIL")
    print("="*80)
    print()

    df_2022 = df[df['date'].str.startswith('2022')]
    print(f"{'Date':<12} {'Tier':<8} {'Score':<6} {'Liq':<5} {'FedVel':<10} {'Override':<20}")
    print("-"*80)
    for idx, row in df_2022.iterrows():
        override_str = row['override_trigger'] if row['override_active'] else '-'
        fed_vel_str = f"{row['liquidity_fed_funds_velocity_6m']:+.1f}" if not pd.isna(row['liquidity_fed_funds_velocity_6m']) else 'N/A'
        print(f"{row['date']:<12} {row['new_tier']:<8} {row['new_overall_risk']:<6.2f} {row['liquidity']:<5.1f} {fed_vel_str:<10} {override_str:<20}")

    print()
    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print()

    # Final assessment
    print("ASSESSMENT:")
    print()

    # Check 2022
    df_2022_alerts = df_2022[df_2022['new_tier'].isin(['YELLOW', 'RED'])]
    if len(df_2022_alerts) > 0:
        print("[PASS] 2022 bear market NOW DETECTED")
    else:
        print("[FAIL] 2022 bear market STILL MISSED (unexpected!)")

    # Check false positive rate
    if false_positive_rate < 10:
        print(f"[PASS] False positive rate acceptable ({false_positive_rate:.1f}% < 10%)")
    else:
        print(f"[WARN] False positive rate high ({false_positive_rate:.1f}% >= 10%)")

    # Check expected frequency
    if 2 <= alerts_per_year <= 6:
        print(f"[PASS] Alert frequency reasonable ({alerts_per_year:.1f} alerts/year)")
    elif alerts_per_year < 2:
        print(f"[WARN] Alert frequency too low ({alerts_per_year:.1f} alerts/year)")
    else:
        print(f"[WARN] Alert frequency too high ({alerts_per_year:.1f} alerts/year)")

    print()

if __name__ == '__main__':
    main()
