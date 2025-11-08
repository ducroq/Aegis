"""
Show current Aegis risk status - simple real-time assessment
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.data_manager import DataManager
from src.scoring.aggregator import RiskAggregator


def main():
    """Display current risk assessment."""
    print("\n" + "="*60)
    print("AEGIS - Real-Time Market Risk Assessment")
    print("="*60)

    # Fetch data
    print("\nFetching market data...")
    manager = DataManager()
    data = manager.fetch_all_indicators()

    # Calculate risk
    print("Calculating risk scores...")
    aggregator = RiskAggregator()
    result = aggregator.calculate_overall_risk(data)

    # Display results
    print("\n" + "="*60)
    print(f"OVERALL RISK: {result['overall_score']:.2f}/10")
    print(f"TIER: {result['tier']}")
    print("="*60)

    print(f"\nRisk Dimensions:")
    dims = result['dimension_scores']
    print(f"  Recession:    {dims['recession']:.2f}/10  (weight: 30%)")
    print(f"  Credit:       {dims['credit']:.2f}/10  (weight: 25%)")
    print(f"  Valuation:    {dims['valuation']:.2f}/10  (weight: 20%)")
    print(f"  Liquidity:    {dims['liquidity']:.2f}/10  (weight: 15%)")
    print(f"  Positioning:  {dims['positioning']:.2f}/10  (weight: 10%)")

    print(f"\nData Quality:")
    if 'data_completeness' in result['metadata']:
        print(f"  Completeness: {result['metadata']['data_completeness']*100:.0f}%")
    print(f"  Timestamp: {result['metadata'].get('timestamp', 'N/A')[:19]}")

    # Risk interpretation
    print(f"\nInterpretation:")
    overall = result['overall_score']
    if overall >= 8.0:
        print("  [RED] SEVERE RISK - Consider major defensive positioning")
        print("  Suggested action: 30-50% cash/bonds, trim cyclicals")
    elif overall >= 6.5:
        print("  [YELLOW] ELEVATED RISK - Review portfolio, build cash")
        print("  Suggested action: 10-20% cash, rebalance, monitor daily")
    else:
        print("  [GREEN] NORMAL CONDITIONS - Stay the course")
        print("  Suggested action: Maintain plan, rebalance opportunistically")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
