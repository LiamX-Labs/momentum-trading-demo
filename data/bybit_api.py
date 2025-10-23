"""
Bybit API integration for live market data.

This module fetches real-time data from Bybit to make backtests
more realistic by:
- Getting actual available symbols at any point in time
- Fetching live OHLCV data
- Checking real-time volume and liquidity
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pybit.unified_trading import HTTP
import time
import os
import json


class BybitDataFetcher:
    """
    Fetches live market data from Bybit API.
    """

    def __init__(self, testnet: bool = False):
        """
        Initialize Bybit API client.

        Args:
            testnet: Whether to use testnet (default: False for mainnet)
        """
        self.session = HTTP(testnet=testnet)
        self.rate_limit_delay = 0.1  # 100ms between requests

    def get_all_usdt_symbols(self, min_volume_24h: float = 0) -> List[Dict]:
        """
        Get all USDT perpetual symbols currently trading on Bybit.

        Args:
            min_volume_24h: Minimum 24h volume in USD (default: 0)

        Returns:
            List of dictionaries with symbol info
        """
        try:
            response = self.session.get_tickers(category="linear")

            if response['retCode'] != 0:
                raise Exception(f"API Error: {response['retMsg']}")

            symbols_info = []

            for ticker in response['result']['list']:
                symbol = ticker['symbol']

                # Only USDT perpetuals
                if not symbol.endswith('USDT'):
                    continue

                # Get 24h volume
                volume_24h = float(ticker.get('turnover24h', 0))

                if volume_24h >= min_volume_24h:
                    symbols_info.append({
                        'symbol': symbol,
                        'last_price': float(ticker.get('lastPrice', 0)),
                        'volume_24h': volume_24h,
                        'price_change_24h': float(ticker.get('price24hPcnt', 0)),
                        'high_24h': float(ticker.get('highPrice24h', 0)),
                        'low_24h': float(ticker.get('lowPrice24h', 0))
                    })

            # Sort by volume
            symbols_info.sort(key=lambda x: x['volume_24h'], reverse=True)

            print(f"Found {len(symbols_info)} USDT symbols with volume >= ${min_volume_24h:,.0f}")

            return symbols_info

        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []

    def get_klines(
        self,
        symbol: str,
        interval: str = '60',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 200
    ) -> pd.DataFrame:
        """
        Fetch historical klines (OHLCV) data.

        If limit > 1000, automatically fetches in multiple paginated requests.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Timeframe ('1', '5', '15', '60' for 1-hour, '240'/'4h' for 4-hour, 'D' for daily)
            start_time: Start datetime
            end_time: End datetime
            limit: Max number of candles (can exceed 1000, will paginate automatically)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # If limit <= 1000, use single request
            if limit <= 1000:
                return self._fetch_single_kline_batch(symbol, interval, start_time, end_time, limit)

            # Otherwise, paginate
            all_data = []
            current_end = end_time
            remaining = limit

            while remaining > 0:
                batch_limit = min(remaining, 1000)
                df = self._fetch_single_kline_batch(symbol, interval, start_time, current_end, batch_limit)

                if df.empty:
                    break

                all_data.append(df)
                remaining -= len(df)

                # Update end time to oldest timestamp in this batch for next request
                current_end = df['timestamp'].min() - timedelta(seconds=1)

                # If we got less than requested, we've reached the start
                if len(df) < batch_limit:
                    break

            if not all_data:
                return pd.DataFrame()

            # Combine all batches
            combined = pd.concat(all_data, ignore_index=True)
            combined = combined.sort_values('timestamp').drop_duplicates(subset=['timestamp']).reset_index(drop=True)

            return combined

        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_single_kline_batch(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        limit: int
    ) -> pd.DataFrame:
        """Fetch a single batch of klines (max 1000)."""
        try:
            # Convert interval to Bybit format
            interval_map = {
                '1': '1',
                '5': '5',
                '15': '15',
                '60': '60',
                '240': '240',  # 4 hour
                '4h': '240',
                '4H': '240',
                'D': 'D',
                '1D': 'D'
            }
            bybit_interval = interval_map.get(interval, '240')

            # Convert timestamps to milliseconds
            params = {
                'category': 'linear',
                'symbol': symbol,
                'interval': bybit_interval,
                'limit': min(limit, 1000)
            }

            if start_time:
                params['start'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['end'] = int(end_time.timestamp() * 1000)

            response = self.session.get_kline(**params)

            if response['retCode'] != 0:
                raise Exception(f"API Error: {response['retMsg']}")

            klines = response['result']['list']

            if not klines:
                return pd.DataFrame()

            # Parse klines
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                df[col] = df[col].astype(float)

            # Sort by timestamp (oldest first)
            df = df.sort_values('timestamp').reset_index(drop=True)

            time.sleep(self.rate_limit_delay)

            return df

        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")
            return pd.DataFrame()

    def get_multiple_symbols_klines(
        self,
        symbols: List[str],
        interval: str = 'D',
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 200
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch klines for multiple symbols.

        Args:
            symbols: List of symbols
            interval: Timeframe
            start_time: Start datetime
            end_time: End datetime
            limit: Max candles per symbol

        Returns:
            Dictionary mapping symbol -> DataFrame
        """
        data = {}

        for i, symbol in enumerate(symbols):
            print(f"Fetching {symbol} ({i+1}/{len(symbols)})...", end='\r')

            df = self.get_klines(symbol, interval, start_time, end_time, limit)

            if len(df) > 0:
                data[symbol] = df

        print(f"\nSuccessfully fetched {len(data)}/{len(symbols)} symbols")

        return data

    def get_symbol_info_at_date(self, date: datetime, min_volume_24h: float = 10_000_000) -> List[str]:
        """
        Get symbols that would have been tradeable at a specific date.

        Note: This is an approximation since we can't query historical symbol listings.
        We use current symbols but filter by those that existed at that date.

        Args:
            date: Date to check
            min_volume_24h: Minimum 24h volume

        Returns:
            List of symbol names
        """
        # Get current symbols
        symbols_info = self.get_all_usdt_symbols(min_volume_24h=0)

        # Fetch klines to see which existed at that date
        valid_symbols = []

        # Check top 200 symbols (increased from 50 to catch more liquid tokens)
        for info in symbols_info[:200]:
            symbol = info['symbol']

            # Try to get data from that date using 4h interval
            df = self.get_klines(
                symbol,
                interval='4h',
                start_time=date - timedelta(days=100),
                end_time=date,
                limit=600  # 100 days * 6 candles/day
            )

            if len(df) > 0:
                # Check if symbol has data at target date
                symbol_start = df['timestamp'].min()
                if symbol_start <= date:
                    # Check volume requirement (aggregate 4h to daily)
                    # Last 30 days = last 180 4h candles (30 days * 6 candles/day)
                    recent_df = df.tail(180).copy()

                    # Group by day and sum turnover to get daily (24h) volume
                    recent_df['date'] = recent_df['timestamp'].dt.date
                    daily_volume = recent_df.groupby('date')['turnover'].sum()
                    avg_daily_volume = daily_volume.mean()

                    if avg_daily_volume >= min_volume_24h:
                        valid_symbols.append(symbol)

        print(f"Found {len(valid_symbols)} symbols valid at {date.date()} with ${min_volume_24h:,.0f}+ volume")

        return valid_symbols


class DynamicUniverseScanner:
    """
    Scans and updates the trading universe dynamically.

    This makes backtesting realistic by:
    - Only trading symbols that actually existed at that time
    - Updating universe based on live volume/liquidity
    - Simulating real market conditions
    """

    def __init__(
        self,
        min_volume_usd: float = 10_000_000,
        max_symbols: int = 20,
        update_frequency_days: int = 7,
        cache_dir: str = "cache/universe_scans"
    ):
        """
        Initialize scanner.

        Args:
            min_volume_usd: Minimum daily volume (default: $10M)
            max_symbols: Maximum symbols in universe (default: 20)
            update_frequency_days: Days between universe updates (default: 7)
            cache_dir: Directory to cache scan results (default: cache/universe_scans)
        """
        self.api = BybitDataFetcher()
        self.min_volume_usd = min_volume_usd
        self.max_symbols = max_symbols
        self.update_frequency_days = update_frequency_days

        self.universe_history = {}  # date -> list of symbols

        # Setup cache directory
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()

    def _get_cache_filename(self) -> str:
        """Get cache filename based on scan parameters."""
        return f"{self.cache_dir}/scan_vol{self.min_volume_usd:.0f}_max{self.max_symbols}.json"

    def _load_cache(self):
        """Load cached universe scans from disk."""
        cache_file = self._get_cache_filename()
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    # Convert string dates back to date objects
                    from datetime import date as date_obj
                    for date_str, symbols in cached_data.items():
                        date_key = date_obj.fromisoformat(date_str)
                        self.universe_history[date_key] = symbols
                print(f"Loaded {len(self.universe_history)} cached universe scans from {cache_file}")
        except Exception as e:
            print(f"Could not load cache: {e}")

    def _save_cache(self):
        """Save universe scans to disk."""
        cache_file = self._get_cache_filename()
        try:
            # Convert date objects to strings for JSON
            cache_data = {date_key.isoformat(): symbols
                         for date_key, symbols in self.universe_history.items()}
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"Saved {len(self.universe_history)} universe scans to cache")
        except Exception as e:
            print(f"Could not save cache: {e}")

    def scan_universe_at_date(self, date: datetime) -> List[str]:
        """
        Scan and return tradeable universe at a specific date.

        Args:
            date: Target date

        Returns:
            List of symbols meeting criteria
        """
        # Check if we already scanned this exact date
        date_key = date.date()
        if date_key in self.universe_history:
            print(f"  Using cached universe for {date.date()}: {len(self.universe_history[date_key])} symbols")
            return self.universe_history[date_key]

        # Check for nearby cached scans (within update_frequency_days)
        # This allows reusing scans even if dates don't match exactly
        for cached_date in self.universe_history.keys():
            days_diff = abs((date_key - cached_date).days)
            if days_diff < self.update_frequency_days:
                print(f"  Using cached universe from {cached_date} for {date_key} ({days_diff} days diff): {len(self.universe_history[cached_date])} symbols")
                # Store under the requested date too for faster lookup next time
                self.universe_history[date_key] = self.universe_history[cached_date]
                return self.universe_history[cached_date]

        print(f"\n  Fetching NEW universe scan for {date.date()} via API...")

        # Get symbols that existed at this date
        symbols = self.api.get_symbol_info_at_date(date, self.min_volume_usd)

        # Limit to max_symbols
        universe = symbols[:self.max_symbols]

        # Cache result in memory
        self.universe_history[date_key] = universe

        # Save to disk cache
        self._save_cache()

        print(f"  Universe at {date.date()}: {len(universe)} symbols")

        return universe

    def get_universe_for_period(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[datetime, List[str]]:
        """
        Get universe updates for an entire period.

        Args:
            start_date: Start of period
            end_date: End of period

        Returns:
            Dictionary mapping date -> list of symbols
        """
        # Check if we have recent enough cached data
        if self.universe_history:
            latest_cached = max(self.universe_history.keys())
            days_since_latest = (datetime.now().date() - latest_cached).days

            if days_since_latest < self.update_frequency_days:
                print(f"Latest cached scan is from {latest_cached} ({days_since_latest} days old)")
                print(f"No new scan needed (threshold: {self.update_frequency_days} days)")

        universe_updates = {}
        cached_count = 0
        api_count = 0

        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.date()
            was_cached = date_key in self.universe_history

            universe = self.scan_universe_at_date(current_date)
            universe_updates[current_date] = universe

            if was_cached:
                cached_count += 1
            else:
                api_count += 1

            # Move to next update
            current_date += timedelta(days=self.update_frequency_days)

        print(f"\nUniverse scan summary: {cached_count} from cache, {api_count} fetched via API")
        return universe_updates


if __name__ == "__main__":
    # Test Bybit API fetcher
    print("Testing Bybit API integration...\n")

    fetcher = BybitDataFetcher()

    # 1. Get top symbols by volume
    print("1. Fetching top USDT symbols...")
    symbols = fetcher.get_all_usdt_symbols(min_volume_24h=50_000_000)

    print(f"\nTop 10 by volume:")
    for i, info in enumerate(symbols[:10], 1):
        print(f"  {i}. {info['symbol']:<15} ${info['volume_24h']:>15,.0f}  "
              f"(24h: {info['price_change_24h']*100:+.2f}%)")

    # 2. Fetch klines
    if symbols:
        test_symbol = symbols[0]['symbol']
        print(f"\n2. Fetching klines for {test_symbol}...")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        df = fetcher.get_klines(test_symbol, interval='D', start_time=start_date, end_time=end_date)

        print(f"Fetched {len(df)} days of data:")
        print(df[['timestamp', 'close', 'volume', 'turnover']].head())

    # 3. Test dynamic scanner
    print("\n3. Testing dynamic universe scanner...")
    scanner = DynamicUniverseScanner(min_volume_usd=10_000_000, max_symbols=10)

    test_date = datetime.now() - timedelta(days=180)
    universe = scanner.scan_universe_at_date(test_date)

    print(f"\nUniverse 6 months ago: {universe}")

    print("\n✓ Bybit API integration working!")
