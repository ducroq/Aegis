"""
Global Market Correlation Validation

Validates that Aegis risk scores correlate with worldwide market drawdowns,
not just US markets. Fetches historical data for major global ETFs and
calculates correlation with risk scores.

Usage:
    python scripts/validate_global_markets.py

Output:
    - Correlation coefficients for each market
    - Drawdown analysis during high-risk periods
    - Global validation report
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config.config_manager import ConfigManager
from src.data.market_data import MarketDataClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Global ETFs to validate against
# Using indices (^) where possible as they have longer history
GLOBAL_MARKETS = {
    # US Markets (using indices for longer history)
    '^GSPC': {'name': 'S&P 500', 'region': 'US', 'type': 'Large Cap'},
    '^IXIC': {'name': 'Nasdaq Composite', 'region': 'US', 'type': 'Tech'},
    '^DJI': {'name': 'Dow Jones', 'region': 'US', 'type': 'Large Cap'},

    # International Indices
    '^FTSE': {'name': 'FTSE 100 (UK)', 'region': 'Europe', 'type': 'Country'},
    '^GDAXI': {'name': 'DAX (Germany)', 'region': 'Europe', 'type': 'Country'},
    '^N225': {'name': 'Nikkei 225 (Japan)', 'region': 'Asia', 'type': 'Country'},
    '000001.SS': {'name': 'Shanghai Composite', 'region': 'Asia', 'type': 'Country'},
    '^BVSP': {'name': 'Bovespa (Brazil)', 'region': 'Latin America', 'type': 'Country'},

    # Also try some ETFs (may have shorter history)
    'SPY': {'name': 'S&P 500 ETF', 'region': 'US', 'type': 'ETF'},
    'EFA': {'name': 'MSCI EAFE ETF', 'region': 'Developed Ex-US', 'type': 'ETF'},
    'EEM': {'name': 'Emerging Markets ETF', 'region': 'Emerging', 'type': 'ETF'},
    'VT': {'name': 'Total World ETF', 'region': 'Global', 'type': 'ETF'},
}


def load_risk_scores() -> pd.DataFrame:
    """Load historical risk scores."""
    history_file = project_root / 'data' / 'history' / 'risk_scores.csv'

    if not history_file.exists():
        logger.error(f"Risk scores file not found: {history_file}")
        return pd.DataFrame()

    df = pd.read_csv(history_file)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    logger.info(f"Loaded {len(df)} risk score records from {df['date'].min()} to {df['date'].max()}")
    return df


def fetch_etf_data(ticker: str, start_date: str, end_date: str, retries: int = 3) -> pd.DataFrame:
    """
    Fetch historical price data for an ETF/index with retry logic.

    Args:
        ticker: ETF ticker symbol or index
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        retries: Number of retry attempts

    Returns:
        DataFrame with date and adjusted close prices
    """
    import time

    for attempt in range(retries):
        try:
            import yfinance as yf

            # Add delay between requests to avoid rate limiting
            if attempt > 0:
                time.sleep(2 * attempt)
                logger.info(f"Retry {attempt + 1}/{retries} for {ticker}")

            # Download data
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if data.empty:
                logger.warning(f"No data returned for {ticker}")
                continue

            # Handle multi-index columns if present
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            # Extract adjusted close (or Close if Adj Close not available)
            close_col = 'Adj Close' if 'Adj Close' in data.columns else 'Close'
            df = pd.DataFrame({
                'date': data.index,
                'price': data[close_col].values
            })

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            logger.info(f"Fetched {len(df)} price records for {ticker}")
            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker} (attempt {attempt + 1}): {e}")
            if attempt == retries - 1:
                return pd.DataFrame()

    return pd.DataFrame()


def calculate_forward_returns(prices: pd.DataFrame, periods: List[int] = [21, 63, 126]) -> pd.DataFrame:
    """
    Calculate forward returns for given periods.

    Args:
        prices: DataFrame with 'date' and 'price' columns
        periods: List of forward periods in days (default: 1m, 3m, 6m)

    Returns:
        DataFrame with forward return columns
    """
    df = prices.copy()

    for period in periods:
        # Forward return = (price[t+period] - price[t]) / price[t]
        df[f'fwd_{period}d_return'] = (
            df['price'].shift(-period) / df['price'] - 1
        ) * 100  # Convert to percentage

    return df


def merge_risk_and_market_data(risk_scores: pd.DataFrame, market_data: pd.DataFrame) -> pd.DataFrame:
    """
    Merge risk scores with market data on date.

    Uses as-of merge to match risk scores to nearest market date.
    """
    # Convert to monthly data (first trading day of month)
    risk_monthly = risk_scores.copy()
    risk_monthly['month'] = pd.to_datetime(risk_monthly['date']).dt.to_period('M')

    market_monthly = market_data.copy()
    market_monthly['month'] = pd.to_datetime(market_monthly['date']).dt.to_period('M')
    market_monthly = market_monthly.groupby('month').first().reset_index()

    # Merge on month
    merged = pd.merge_asof(
        risk_monthly.sort_values('date'),
        market_monthly[['month', 'price', 'fwd_21d_return', 'fwd_63d_return', 'fwd_126d_return']].sort_values('month'),
        on='month',
        direction='nearest'
    )

    # Drop rows with missing forward returns
    merged = merged.dropna(subset=['fwd_21d_return', 'fwd_63d_return', 'fwd_126d_return'])

    return merged


def calculate_correlation(merged_data: pd.DataFrame) -> Dict[str, float]:
    """Calculate correlation between risk scores and forward returns."""
    correlations = {}

    for period in ['21d', '63d', '126d']:
        col = f'fwd_{period}_return'
        if col in merged_data.columns:
            corr = merged_data['overall_risk'].corr(merged_data[col])
            correlations[period] = corr

    return correlations


def analyze_drawdowns_during_high_risk(merged_data: pd.DataFrame, threshold: float = 4.0) -> Dict:
    """
    Analyze market performance when risk score is elevated.

    Args:
        merged_data: Merged risk scores and market data
        threshold: Risk score threshold for "elevated risk"

    Returns:
        Dictionary with drawdown statistics
    """
    high_risk = merged_data[merged_data['overall_risk'] >= threshold]
    normal_risk = merged_data[merged_data['overall_risk'] < threshold]

    if len(high_risk) == 0:
        return {
            'high_risk_count': 0,
            'avg_fwd_return_1m': None,
            'avg_fwd_return_3m': None,
            'avg_fwd_return_6m': None,
        }

    stats = {
        'high_risk_count': len(high_risk),
        'high_risk_pct': len(high_risk) / len(merged_data) * 100,
        'avg_fwd_return_1m_high': high_risk['fwd_21d_return'].mean(),
        'avg_fwd_return_3m_high': high_risk['fwd_63d_return'].mean(),
        'avg_fwd_return_6m_high': high_risk['fwd_126d_return'].mean(),
        'avg_fwd_return_1m_normal': normal_risk['fwd_21d_return'].mean(),
        'avg_fwd_return_3m_normal': normal_risk['fwd_63d_return'].mean(),
        'avg_fwd_return_6m_normal': normal_risk['fwd_126d_return'].mean(),
    }

    # Calculate "lift" - how much worse returns are during high risk
    stats['return_diff_1m'] = stats['avg_fwd_return_1m_high'] - stats['avg_fwd_return_1m_normal']
    stats['return_diff_3m'] = stats['avg_fwd_return_3m_high'] - stats['avg_fwd_return_3m_normal']
    stats['return_diff_6m'] = stats['avg_fwd_return_6m_high'] - stats['avg_fwd_return_6m_normal']

    return stats


def validate_market(ticker: str, risk_scores: pd.DataFrame) -> Dict:
    """
    Validate risk scores against a single market.

    Returns:
        Dictionary with validation results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Validating {ticker} - {GLOBAL_MARKETS[ticker]['name']}")
    logger.info(f"{'='*60}")

    # Fetch market data
    start_date = risk_scores['date'].min().strftime('%Y-%m-%d')
    end_date = risk_scores['date'].max().strftime('%Y-%m-%d')

    market_data = fetch_etf_data(ticker, start_date, end_date)

    if market_data.empty:
        return {'ticker': ticker, 'status': 'FAILED', 'error': 'No data'}

    # Calculate forward returns
    market_data = calculate_forward_returns(market_data)

    # Merge with risk scores
    merged = merge_risk_and_market_data(risk_scores, market_data)

    if len(merged) < 10:
        return {'ticker': ticker, 'status': 'FAILED', 'error': 'Insufficient overlap'}

    # Calculate correlations
    correlations = calculate_correlation(merged)

    # Analyze drawdowns during high risk
    drawdown_stats = analyze_drawdowns_during_high_risk(merged, threshold=4.0)

    # Compile results
    results = {
        'ticker': ticker,
        'name': GLOBAL_MARKETS[ticker]['name'],
        'region': GLOBAL_MARKETS[ticker]['region'],
        'type': GLOBAL_MARKETS[ticker]['type'],
        'status': 'SUCCESS',
        'data_points': len(merged),
        'correlation_1m': correlations.get('21d', None),
        'correlation_3m': correlations.get('63d', None),
        'correlation_6m': correlations.get('126d', None),
        **drawdown_stats
    }

    # Log summary
    logger.info(f"Data points: {len(merged)}")
    logger.info(f"Correlations (risk vs forward returns):")
    logger.info(f"  1-month: {correlations.get('21d', 0):.3f}")
    logger.info(f"  3-month: {correlations.get('63d', 0):.3f}")
    logger.info(f"  6-month: {correlations.get('126d', 0):.3f}")
    logger.info(f"High risk periods (≥4.0): {drawdown_stats['high_risk_count']} ({drawdown_stats['high_risk_pct']:.1f}%)")
    logger.info(f"Avg forward returns when risk ≥4.0:")
    logger.info(f"  1-month: {drawdown_stats['avg_fwd_return_1m_high']:.2f}% (vs {drawdown_stats['avg_fwd_return_1m_normal']:.2f}% normal)")
    logger.info(f"  3-month: {drawdown_stats['avg_fwd_return_3m_high']:.2f}% (vs {drawdown_stats['avg_fwd_return_3m_normal']:.2f}% normal)")
    logger.info(f"  6-month: {drawdown_stats['avg_fwd_return_6m_high']:.2f}% (vs {drawdown_stats['avg_fwd_return_6m_normal']:.2f}% normal)")

    return results


def generate_report(all_results: List[Dict]):
    """Generate markdown report of global validation results."""

    report_path = project_root / 'docs' / 'global_market_validation.md'

    with open(report_path, 'w') as f:
        f.write("# Global Market Correlation Validation\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("Validates that Aegis risk scores correlate with worldwide market drawdowns.\n\n")

        # Summary statistics
        successful = [r for r in all_results if r.get('status') == 'SUCCESS']
        f.write(f"## Summary\n\n")
        f.write(f"- **Markets Tested:** {len(GLOBAL_MARKETS)}\n")
        f.write(f"- **Successful:** {len(successful)}\n")
        f.write(f"- **Failed:** {len(all_results) - len(successful)}\n\n")

        # Average correlations
        if successful:
            avg_1m = np.mean([r['correlation_1m'] for r in successful if r.get('correlation_1m')])
            avg_3m = np.mean([r['correlation_3m'] for r in successful if r.get('correlation_3m')])
            avg_6m = np.mean([r['correlation_6m'] for r in successful if r.get('correlation_6m')])

            f.write(f"### Average Correlations (Risk Score vs Forward Returns)\n\n")
            f.write(f"- **1-month:** {avg_1m:.3f}\n")
            f.write(f"- **3-month:** {avg_3m:.3f}\n")
            f.write(f"- **6-month:** {avg_6m:.3f}\n\n")
            f.write(f"*Negative correlation = high risk predicts lower forward returns (expected)*\n\n")

        # Detailed results table
        f.write("## Detailed Results by Market\n\n")
        f.write("| Ticker | Name | Region | Corr (1m) | Corr (3m) | Corr (6m) | Return Diff (6m) | Data Points |\n")
        f.write("|--------|------|--------|-----------|-----------|-----------|------------------|-------------|\n")

        for r in sorted(successful, key=lambda x: x.get('correlation_6m', 0)):
            f.write(f"| {r['ticker']} | {r['name']} | {r['region']} | ")
            f.write(f"{r.get('correlation_1m', 0):.3f} | ")
            f.write(f"{r.get('correlation_3m', 0):.3f} | ")
            f.write(f"{r.get('correlation_6m', 0):.3f} | ")
            f.write(f"{r.get('return_diff_6m', 0):.2f}% | ")
            f.write(f"{r['data_points']} |\n")

        # Regional breakdown
        f.write("\n## Regional Analysis\n\n")
        regions = {}
        for r in successful:
            region = r['region']
            if region not in regions:
                regions[region] = []
            regions[region].append(r)

        for region, markets in sorted(regions.items()):
            avg_corr = np.mean([m.get('correlation_6m', 0) for m in markets])
            f.write(f"### {region}\n\n")
            f.write(f"Average 6-month correlation: **{avg_corr:.3f}**\n\n")
            for m in markets:
                f.write(f"- {m['ticker']} ({m['name']}): {m.get('correlation_6m', 0):.3f}\n")
            f.write("\n")

        # Interpretation
        f.write("## Interpretation\n\n")
        f.write("**Negative correlations** indicate that high risk scores predict lower forward returns (good!).\n\n")
        f.write("**Target:** Correlation < -0.3 indicates meaningful predictive power.\n\n")
        f.write("**Finding:** If correlations are weak or positive, the risk scoring system may not be predictive of global market drawdowns.\n\n")

    logger.info(f"\nReport generated: {report_path}")


def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Global Market Correlation Validation")
    logger.info("="*60)

    # Load risk scores
    risk_scores = load_risk_scores()
    if risk_scores.empty:
        logger.error("No risk scores available. Exiting.")
        return

    # Validate each market
    all_results = []
    import time
    for i, ticker in enumerate(GLOBAL_MARKETS.keys()):
        try:
            # Add delay between tickers to avoid rate limiting
            if i > 0:
                time.sleep(1)

            results = validate_market(ticker, risk_scores)
            all_results.append(results)
        except Exception as e:
            logger.error(f"Error validating {ticker}: {e}")
            all_results.append({
                'ticker': ticker,
                'status': 'FAILED',
                'error': str(e)
            })

    # Generate report
    generate_report(all_results)

    logger.info("\n" + "="*60)
    logger.info("Validation complete!")
    logger.info("="*60)


if __name__ == '__main__':
    main()
