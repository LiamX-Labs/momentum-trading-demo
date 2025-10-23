"""
Unit tests for data_loader module.
"""

import unittest
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.data_loader import (
    get_available_symbols,
    get_symbol_date_range,
    load_historical_ohlcv,
    calculate_avg_daily_volume
)


class TestDataLoader(unittest.TestCase):
    """Test cases for data loader functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_symbol = 'DOGEUSDT'  # Known to exist with good data
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=90)

    def test_get_available_symbols(self):
        """Test getting list of available symbols."""
        symbols = get_available_symbols()

        self.assertIsInstance(symbols, list)
        self.assertGreater(len(symbols), 0)
        self.assertIn(self.test_symbol, symbols)

    def test_get_symbol_date_range(self):
        """Test getting date range for a symbol."""
        start, end = get_symbol_date_range(self.test_symbol)

        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertIsInstance(start, datetime)
        self.assertIsInstance(end, datetime)
        self.assertLess(start, end)

    def test_get_symbol_date_range_invalid(self):
        """Test date range for non-existent symbol."""
        start, end = get_symbol_date_range('FAKESYMBOL')

        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_load_historical_ohlcv_daily(self):
        """Test loading daily OHLCV data."""
        df = load_historical_ohlcv(
            self.test_symbol,
            self.start_date,
            self.end_date,
            timeframe='1D'
        )

        # Check DataFrame structure
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)

        # Check required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
        for col in required_cols:
            self.assertIn(col, df.columns)

        # Check data types
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['timestamp']))

        # Check OHLC logic
        self.assertTrue((df['high'] >= df['low']).all())
        self.assertTrue((df['high'] >= df['open']).all())
        self.assertTrue((df['high'] >= df['close']).all())
        self.assertTrue((df['low'] <= df['open']).all())
        self.assertTrue((df['low'] <= df['close']).all())

        # Check no negative prices
        self.assertTrue((df['open'] > 0).all())
        self.assertTrue((df['high'] > 0).all())
        self.assertTrue((df['low'] > 0).all())
        self.assertTrue((df['close'] > 0).all())

    def test_load_historical_ohlcv_invalid_symbol(self):
        """Test loading data for non-existent symbol."""
        with self.assertRaises(FileNotFoundError):
            load_historical_ohlcv('FAKESYMBOL', self.start_date, self.end_date)

    def test_calculate_avg_daily_volume(self):
        """Test calculating average daily volume."""
        avg_vol = calculate_avg_daily_volume(self.test_symbol, days=30)

        self.assertIsInstance(avg_vol, float)
        self.assertGreater(avg_vol, 0)

    def test_load_ohlcv_date_order(self):
        """Test that data is returned in chronological order."""
        df = load_historical_ohlcv(
            self.test_symbol,
            self.start_date,
            self.end_date,
            timeframe='1D'
        )

        # Check timestamps are sorted
        timestamps = df['timestamp'].values
        self.assertTrue(all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1)))

    def test_load_ohlcv_no_duplicates(self):
        """Test that there are no duplicate timestamps."""
        df = load_historical_ohlcv(
            self.test_symbol,
            self.start_date,
            self.end_date,
            timeframe='1D'
        )

        # Check for duplicate timestamps
        duplicates = df['timestamp'].duplicated().sum()
        self.assertEqual(duplicates, 0)


if __name__ == '__main__':
    unittest.main()
