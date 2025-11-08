"""
Market Data Client using Yahoo Finance

Fetches market prices, indices, and metrics using yfinance library.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

from src.config.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class MarketDataClient:
    """
    Client for fetching market data from Yahoo Finance.

    Features:
    - Stock/index prices
    - VIX volatility index
    - Forward P/E ratios
    - Sector ETFs for rotation analysis
    - Caching to reduce API calls
    """

    def __init__(self, config: Optional[ConfigManager] = None, cache_dir: Optional[str] = None):
        """
        Initialize market data client.

        Args:
            config: ConfigManager instance
            cache_dir: Directory for caching data
        """
        if config is None:
            config = ConfigManager()
        self.config = config

        if yf is None:
            raise ImportError("yfinance library not installed. Run: pip install yfinance")

        # Setup cache directory
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "data" / "cache" / "yahoo"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Market data client initialized")

    def get_ticker_data(
        self,
        ticker: str,
        period: str = "1y",
        use_cache: bool = True,
        cache_ttl_hours: int = 6
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a ticker.

        Args:
            ticker: Ticker symbol (e.g., "^GSPC", "^VIX")
            period: Data period ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            use_cache: Whether to use cached data
            cache_ttl_hours: Cache time-to-live in hours

        Returns:
            DataFrame with OHLCV data, or None if error
        """
        # Check cache
        if use_cache:
            cached_data = self._load_from_cache(ticker, period, cache_ttl_hours)
            if cached_data is not None:
                logger.debug(f"Loaded {ticker} from cache")
                return cached_data

        try:
            logger.info(f"Fetching Yahoo Finance data: {ticker} ({period})")
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period=period)

            if hist is None or len(hist) == 0:
                logger.warning(f"No data returned for {ticker}")
                return None

            # Cache the data
            if use_cache:
                self._save_to_cache(ticker, period, hist)

            logger.debug(f"Fetched {ticker}: {len(hist)} observations")
            return hist

        except Exception as e:
            logger.error(f"Failed to fetch {ticker}: {e}")
            return None

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the most recent closing price.

        Args:
            ticker: Ticker symbol

        Returns:
            Latest close price or None
        """
        data = self.get_ticker_data(ticker, period="5d")
        if data is None or len(data) == 0:
            return None

        return float(data['Close'].iloc[-1])

    def get_vix(self) -> Optional[float]:
        """
        Get current VIX (CBOE Volatility Index).

        Returns:
            Current VIX level or None
        """
        return self.get_latest_price('^VIX')

    def get_sp500_price(self) -> Optional[float]:
        """
        Get current S&P 500 price.

        Returns:
            Current S&P 500 level or None
        """
        return self.get_latest_price('^GSPC')

    def get_forward_pe(self, ticker: str = '^GSPC') -> Optional[float]:
        """
        Get forward P/E ratio for a ticker.

        Args:
            ticker: Ticker symbol (default: S&P 500)

        Returns:
            Forward P/E ratio or None
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            # Try different keys (Yahoo Finance API can be inconsistent)
            for key in ['forwardPE', 'forwardEps', 'trailingPE']:
                if key in info and info[key] is not None:
                    logger.debug(f"{ticker} {key}: {info[key]}")
                    if key == 'forwardEps' and 'price' in info:
                        # Calculate from forward EPS and price
                        return float(info['price'] / info[key])
                    return float(info[key])

            logger.warning(f"Forward P/E not available for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Failed to get forward P/E for {ticker}: {e}")
            return None

    def get_sector_rotation_signal(self) -> Optional[Dict[str, float]]:
        """
        Get sector rotation signals (defensive vs cyclical performance).

        Returns:
            Dict with sector ETF performance, or None
        """
        # Sector ETFs
        sectors = {
            'XLV': 'Healthcare (defensive)',
            'XLP': 'Consumer Staples (defensive)',
            'XLU': 'Utilities (defensive)',
            'XLY': 'Consumer Discretionary (cyclical)',
            'XLI': 'Industrials (cyclical)',
            'XLF': 'Financials (cyclical)'
        }

        try:
            results = {}
            for ticker, name in sectors.items():
                data = self.get_ticker_data(ticker, period="3mo")
                if data is not None and len(data) > 1:
                    # 3-month return
                    returns = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
                    results[ticker] = {
                        'name': name,
                        'return_3mo': float(returns),
                        'current_price': float(data['Close'].iloc[-1])
                    }

            # Calculate defensive vs cyclical
            defensive_avg = sum(
                v['return_3mo'] for k, v in results.items()
                if k in ['XLV', 'XLP', 'XLU']
            ) / 3

            cyclical_avg = sum(
                v['return_3mo'] for k, v in results.items()
                if k in ['XLY', 'XLI', 'XLF']
            ) / 3

            results['rotation_signal'] = {
                'defensive_avg': defensive_avg,
                'cyclical_avg': cyclical_avg,
                'spread': defensive_avg - cyclical_avg  # Positive = defensive outperforming
            }

            return results

        except Exception as e:
            logger.error(f"Failed to calculate sector rotation: {e}")
            return None

    def get_market_cap_to_gdp(self, market_cap_series_id: str = 'WILSHIRE5000IND') -> Optional[float]:
        """
        Calculate Buffett Indicator (Market Cap / GDP).

        Note: Requires FRED data for accurate calculation.
        This is a simplified version using S&P 500 market cap proxy.

        Args:
            market_cap_series_id: FRED series for market cap

        Returns:
            Market Cap to GDP ratio or None
        """
        # This would ideally use FRED data
        # For now, return None and implement in scoring module with FRED client
        logger.warning("Market Cap to GDP calculation requires FRED integration")
        return None

    def _get_cache_path(self, ticker: str, period: str) -> Path:
        """Get cache file path for a ticker/period."""
        safe_ticker = ticker.replace('^', '_')
        return self.cache_dir / f"{safe_ticker}_{period}.csv"

    def _load_from_cache(self, ticker: str, period: str, ttl_hours: int) -> Optional[pd.DataFrame]:
        """Load ticker data from cache if fresh enough."""
        cache_path = self._get_cache_path(ticker, period)

        if not cache_path.exists():
            return None

        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if cache_age > timedelta(hours=ttl_hours):
            logger.debug(f"Cache expired for {ticker} (age: {cache_age})")
            return None

        try:
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            return df
        except Exception as e:
            logger.warning(f"Failed to load cache for {ticker}: {e}")
            return None

    def _save_to_cache(self, ticker: str, period: str, data: pd.DataFrame) -> None:
        """Save ticker data to cache."""
        try:
            cache_path = self._get_cache_path(ticker, period)
            data.to_csv(cache_path)
            logger.debug(f"Cached {ticker} to {cache_path}")
        except Exception as e:
            logger.warning(f"Failed to cache {ticker}: {e}")


def main():
    """Test market data client."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )

    print("Testing Market Data Client...\n")

    try:
        client = MarketDataClient()

        # Test S&P 500
        print("[TEST] Fetching S&P 500 price...")
        sp500 = client.get_sp500_price()
        if sp500 is not None:
            print(f"[OK] S&P 500: ${sp500:.2f}")
        else:
            print("[ERROR] Failed to fetch S&P 500")

        # Test VIX
        print("\n[TEST] Fetching VIX...")
        vix = client.get_vix()
        if vix is not None:
            print(f"[OK] VIX: {vix:.2f}")
        else:
            print("[ERROR] Failed to fetch VIX")

        # Test forward P/E
        print("\n[TEST] Fetching S&P 500 forward P/E...")
        pe = client.get_forward_pe()
        if pe is not None:
            print(f"[OK] Forward P/E: {pe:.2f}")
        else:
            print("[WARNING] Forward P/E not available")

        # Test sector rotation
        print("\n[TEST] Calculating sector rotation...")
        sectors = client.get_sector_rotation_signal()
        if sectors and 'rotation_signal' in sectors:
            rotation = sectors['rotation_signal']
            print(f"[OK] Defensive avg: {rotation['defensive_avg']:+.1f}%")
            print(f"[OK] Cyclical avg: {rotation['cyclical_avg']:+.1f}%")
            print(f"[OK] Rotation spread: {rotation['spread']:+.1f}%")
        else:
            print("[WARNING] Sector rotation not available")

        print("\n" + "="*50)
        print("Market Data Client test PASSED")
        print("="*50)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
