"""
Unit tests for data_validator module.
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data.data_validator import (
    validate_data_quality,
    check_data_coverage
)
from data.data_loader import load_historical_ohlcv


class TestDataValidator(unittest.TestCase):
    """Test cases for data validator functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_symbol = 'DOGEUSDT'

    def test_validate_data_quality_valid(self):
        """Test validation with clean data."""
        # Load real data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        df = load_historical_ohlcv(self.test_symbol, start_date, end_date, timeframe='1D')

        validation = validate_data_quality(df, self.test_symbol)

        self.assertIsInstance(validation, dict)
        self.assertIn('symbol', validation)
        self.assertIn('passed', validation)
        self.assertIn('errors', validation)
        self.assertIn('warnings', validation)
        self.assertEqual(validation['symbol'], self.test_symbol)

    def test_validate_data_quality_empty(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame()
        validation = validate_data_quality(df, 'TEST')

        self.assertFalse(validation['passed'])
        self.assertGreater(len(validation['errors']), 0)

    def test_validate_data_quality_missing_values(self):
        """Test validation with missing values."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='D'),
            'open': [100, 101, np.nan, 103, 104, 105, 106, 107, 108, 109],
            'high': [102, 103, 104, 105, 106, 107, 108, 109, 110, 111],
            'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'close': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'volume': [1000] * 10,
            'turnover': [100000] * 10
        })

        validation = validate_data_quality(df, 'TEST')

        # Should have warnings or errors about missing values
        self.assertTrue(len(validation['warnings']) > 0 or len(validation['errors']) > 0)

    def test_validate_data_quality_negative_prices(self):
        """Test validation with negative prices."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'open': [100, 101, -102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000] * 5,
            'turnover': [100000] * 5
        })

        validation = validate_data_quality(df, 'TEST')

        self.assertFalse(validation['passed'])
        self.assertGreater(len(validation['errors']), 0)

    def test_validate_data_quality_ohlc_consistency(self):
        """Test validation of OHLC consistency."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [105, 100, 101, 102, 103],  # Invalid: low > high
            'close': [101, 102, 103, 104, 105],
            'volume': [1000] * 5,
            'turnover': [100000] * 5
        })

        validation = validate_data_quality(df, 'TEST')

        self.assertFalse(validation['passed'])
        self.assertGreater(len(validation['errors']), 0)

    def test_validate_data_quality_zero_volume(self):
        """Test validation with zero volume."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5, freq='D'),
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [0, 1000, 0, 1000, 1000],
            'turnover': [0, 100000, 0, 100000, 100000]
        })

        validation = validate_data_quality(df, 'TEST')

        # Should have warnings about zero volume
        self.assertTrue(len(validation['warnings']) > 0 or len(validation['errors']) > 0)

    def test_check_data_coverage_sufficient(self):
        """Test coverage check for symbol with sufficient data."""
        coverage = check_data_coverage(self.test_symbol, required_days=90)

        self.assertIsInstance(coverage, dict)
        self.assertIn('has_coverage', coverage)
        self.assertIn('days_available', coverage)
        self.assertIn('symbol', coverage)

        # DOGEUSDT should have plenty of data
        self.assertTrue(coverage['has_coverage'])
        self.assertGreater(coverage['days_available'], 90)

    def test_check_data_coverage_insufficient(self):
        """Test coverage check with very high requirements."""
        # Require an unrealistic amount of data
        coverage = check_data_coverage(self.test_symbol, required_days=10000)

        self.assertIsInstance(coverage, dict)
        self.assertFalse(coverage['has_coverage'])

    def test_check_data_coverage_invalid_symbol(self):
        """Test coverage check for non-existent symbol."""
        coverage = check_data_coverage('FAKESYMBOL', required_days=90)

        self.assertFalse(coverage['has_coverage'])
        self.assertEqual(coverage['days_available'], 0)


if __name__ == '__main__':
    unittest.main()
