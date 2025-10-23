"""
Unit tests for technical indicators.
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from indicators.bollinger_bands import (
    calculate_bollinger_bands,
    calculate_bbwidth,
    calculate_bbwidth_percentile,
    get_bb_position
)
from indicators.volume import (
    calculate_avg_volume,
    calculate_relative_volume_ratio,
    calculate_volume_percentile
)
from indicators.moving_averages import (
    calculate_sma,
    calculate_multiple_smas,
    check_price_above_ma,
    get_ma_regime
)
from data.data_loader import load_historical_ohlcv


class TestBollingerBands(unittest.TestCase):
    """Test Bollinger Bands calculations."""

    def setUp(self):
        """Create test data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'close': np.random.rand(100) * 10 + 100,  # Prices between 100-110
            'high': np.random.rand(100) * 10 + 105,
            'low': np.random.rand(100) * 10 + 95,
            'volume': np.random.rand(100) * 1000000
        })

    def test_calculate_bollinger_bands(self):
        """Test Bollinger Bands calculation."""
        result = calculate_bollinger_bands(self.df)

        self.assertIn('bb_middle', result.columns)
        self.assertIn('bb_upper', result.columns)
        self.assertIn('bb_lower', result.columns)

        # Upper should be > lower
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['bb_upper'] > valid_rows['bb_lower']).all())

    def test_calculate_bbwidth(self):
        """Test BBWidth calculation."""
        result = calculate_bbwidth(self.df)

        self.assertIn('bbwidth', result.columns)

        # BBWidth should be positive
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['bbwidth'] > 0).all())

    def test_calculate_bbwidth_percentile(self):
        """Test BBWidth percentile calculation."""
        result = calculate_bbwidth_percentile(self.df, lookback_period=50)

        self.assertIn('bbwidth_percentile', result.columns)

        # Percentile should be between 0 and 1
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['bbwidth_percentile'] >= 0).all())
        self.assertTrue((valid_rows['bbwidth_percentile'] <= 1).all())

    def test_get_bb_position(self):
        """Test BB position calculation."""
        result = get_bb_position(self.df)

        self.assertIn('bb_position', result.columns)
        self.assertIn('above_upper_band', result.columns)
        self.assertIn('below_lower_band', result.columns)


class TestVolumeIndicators(unittest.TestCase):
    """Test volume indicators."""

    def setUp(self):
        """Create test data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'close': np.random.rand(100) * 10 + 100,
            'volume': np.random.rand(100) * 1000000 + 500000
        })

    def test_calculate_avg_volume(self):
        """Test average volume calculation."""
        result = calculate_avg_volume(self.df, period=20)

        self.assertIn('avg_volume', result.columns)

        # Average volume should be positive
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['avg_volume'] > 0).all())

    def test_calculate_rvr(self):
        """Test RVR calculation."""
        result = calculate_relative_volume_ratio(self.df, period=20)

        self.assertIn('rvr', result.columns)
        self.assertIn('avg_volume', result.columns)

        # RVR should be positive
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['rvr'] > 0).all())

    def test_calculate_volume_percentile(self):
        """Test volume percentile calculation."""
        result = calculate_volume_percentile(self.df, lookback_period=50)

        self.assertIn('volume_percentile', result.columns)

        # Percentile should be between 0 and 1
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['volume_percentile'] >= 0).all())
        self.assertTrue((valid_rows['volume_percentile'] <= 1).all())


class TestMovingAverages(unittest.TestCase):
    """Test moving average indicators."""

    def setUp(self):
        """Create test data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'close': np.random.rand(100) * 10 + 100
        })

    def test_calculate_sma(self):
        """Test SMA calculation."""
        result = calculate_sma(self.df, period=20)

        self.assertIn('sma_20', result.columns)

        # SMA should be positive
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['sma_20'] > 0).all())

    def test_calculate_multiple_smas(self):
        """Test multiple SMA calculation."""
        result = calculate_multiple_smas(self.df, periods=[20, 50])

        self.assertIn('sma_20', result.columns)
        self.assertIn('sma_50', result.columns)

    def test_check_price_above_ma(self):
        """Test price above MA check."""
        result = check_price_above_ma(self.df, ma_period=20)

        self.assertIn('sma_20', result.columns)
        self.assertIn('above_ma_20', result.columns)

        # Result should be boolean
        self.assertTrue(result['above_ma_20'].dtype == bool)

    def test_get_ma_regime(self):
        """Test MA regime determination."""
        result = get_ma_regime(self.df, regime_period=50)

        self.assertIn('regime_uptrend', result.columns)
        self.assertIn('regime_downtrend', result.columns)

        # Regimes should be boolean and mutually exclusive
        self.assertTrue(result['regime_uptrend'].dtype == bool)
        valid_rows = result.dropna()
        self.assertTrue((valid_rows['regime_uptrend'] != valid_rows['regime_downtrend']).all())


class TestIndicatorsWithRealData(unittest.TestCase):
    """Test indicators with real market data."""

    @classmethod
    def setUpClass(cls):
        """Load real data once for all tests."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            cls.df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')
            cls.has_real_data = True
        except Exception as e:
            print(f"Warning: Could not load real data: {e}")
            cls.has_real_data = False

    def test_bollinger_bands_real_data(self):
        """Test Bollinger Bands with real data."""
        if not self.has_real_data:
            self.skipTest("Real data not available")

        result = calculate_bollinger_bands(self.df)

        # Check that bands make sense
        valid_rows = result.dropna()
        self.assertGreater(len(valid_rows), 0)
        self.assertTrue((valid_rows['bb_upper'] >= valid_rows['bb_middle']).all())
        self.assertTrue((valid_rows['bb_middle'] >= valid_rows['bb_lower']).all())

    def test_volume_indicators_real_data(self):
        """Test volume indicators with real data."""
        if not self.has_real_data:
            self.skipTest("Real data not available")

        result = calculate_relative_volume_ratio(self.df)

        valid_rows = result.dropna()
        self.assertGreater(len(valid_rows), 0)
        self.assertTrue((valid_rows['rvr'] > 0).all())


if __name__ == '__main__':
    unittest.main()
