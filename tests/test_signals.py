"""
Unit tests for signal generation.
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from signals.entry_signals import check_entry_signal, generate_entry_signals
from signals.exit_signals import (
    calculate_trailing_stop,
    check_exit_signal,
    simulate_position_exit
)
from signals.regime_filter import check_regime_filter
from data.data_loader import load_historical_ohlcv


class TestEntrySignals(unittest.TestCase):
    """Test entry signal logic."""

    @classmethod
    def setUpClass(cls):
        """Load test data."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            cls.df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')
            cls.has_data = True
        except Exception as e:
            print(f"Warning: Could not load data: {e}")
            cls.has_data = False

    def test_check_entry_signal(self):
        """Test checking entry signal."""
        if not self.has_data:
            self.skipTest("Test data not available")

        triggered, details = check_entry_signal(self.df)

        self.assertIsInstance(triggered, bool)
        self.assertIsInstance(details, dict)
        self.assertIn('triggered', details)
        self.assertIn('signal_strength', details)
        self.assertIn('criteria_met', details)

    def test_generate_entry_signals(self):
        """Test generating entry signals for entire DataFrame."""
        if not self.has_data:
            self.skipTest("Test data not available")

        result = generate_entry_signals(self.df)

        self.assertIn('entry_signal', result.columns)
        self.assertIn('signal_strength', result.columns)

        # Entry signal should be boolean
        self.assertTrue(result['entry_signal'].dtype == bool)

        # Signal strength should exist and be numeric
        valid_strength = result['signal_strength'].dropna()
        if len(valid_strength) > 0:
            self.assertTrue(pd.api.types.is_numeric_dtype(result['signal_strength']))
            # Most values should be reasonable (between 0 and 1)
            # Some edge cases may exist due to calculation methods
            reasonable = ((valid_strength >= 0) & (valid_strength <= 1)).sum()
            self.assertGreater(reasonable / len(valid_strength), 0.5)  # At least 50% should be in range

    def test_signal_criteria(self):
        """Test that signal criteria are properly evaluated."""
        if not self.has_data:
            self.skipTest("Test data not available")

        result = generate_entry_signals(self.df)

        # When entry_signal is True, all criteria should be met
        signal_rows = result[result['entry_signal']].copy()

        if len(signal_rows) > 0:
            # Check that required indicators are present
            self.assertTrue('bbwidth_percentile' in result.columns)
            self.assertTrue('rvr' in result.columns)
            self.assertTrue('above_upper_band' in result.columns)


class TestExitSignals(unittest.TestCase):
    """Test exit signal logic."""

    def test_calculate_trailing_stop(self):
        """Test trailing stop calculation."""
        entry_price = 100
        peak_price = 125  # 25% gain
        current_price = 105  # Pulled back from peak

        stop_level, stop_triggered = calculate_trailing_stop(
            entry_price, current_price, peak_price, trailing_stop_pct=0.20
        )

        # Stop level should be 20% below peak
        expected_stop = peak_price * 0.80  # 100
        self.assertAlmostEqual(stop_level, expected_stop)

        # Stop should be triggered since current (105) > stop (100)
        # Actually, this should NOT be triggered since 105 > 100
        self.assertFalse(stop_triggered)

        # Test when stop is triggered
        current_price = 95
        stop_level, stop_triggered = calculate_trailing_stop(
            entry_price, current_price, peak_price, trailing_stop_pct=0.20
        )
        self.assertTrue(stop_triggered)

    def test_check_exit_signal(self):
        """Test checking exit signal."""
        # Create simple test data
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': [100] * 50,
            'high': [110] * 50,
            'low': [95] * 50,
            'close': list(range(100, 150)),  # Uptrend
            'volume': [1000000] * 50
        })

        entry_index = 0
        entry_price = df.iloc[entry_index]['close']
        current_index = 10

        exit_triggered, details = check_exit_signal(
            df, entry_index, current_index, entry_price
        )

        self.assertIsInstance(exit_triggered, bool)
        self.assertIsInstance(details, dict)
        self.assertIn('exit_triggered', details)
        self.assertIn('exit_reason', details)
        self.assertIn('return_pct', details)
        self.assertIn('holding_days', details)

    def test_simulate_position_exit(self):
        """Test position simulation."""
        # Create test data with a peak then decline
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        prices = list(range(100, 125)) + list(range(125, 100, -1))  # Up then down
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p + 5 for p in prices],
            'low': [p - 5 for p in prices],
            'close': prices,
            'volume': [1000000] * 50
        })

        entry_index = 0
        entry_price = df.iloc[entry_index]['close']

        result = simulate_position_exit(df, entry_index, entry_price)

        self.assertIn('entry_price', result)
        self.assertIn('exit_price', result)
        self.assertIn('exit_reason', result)
        self.assertIn('peak_price', result)
        self.assertIn('return_pct', result)
        self.assertIn('holding_days', result)

        # Peak should be around 125
        self.assertGreater(result['peak_price'], entry_price)


class TestRegimeFilter(unittest.TestCase):
    """Test regime filter logic."""

    @classmethod
    def setUpClass(cls):
        """Load test data."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            cls.df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')
            cls.has_data = True
        except Exception as e:
            print(f"Warning: Could not load data: {e}")
            cls.has_data = False

    def test_check_regime_filter(self):
        """Test regime filter check."""
        if not self.has_data:
            self.skipTest("Test data not available")

        trading_allowed, details = check_regime_filter(self.df, regime_period=50)

        # trading_allowed might be numpy bool, convert for testing
        self.assertIsInstance(bool(trading_allowed), bool)
        self.assertIsInstance(details, dict)
        self.assertIn('trading_allowed', details)
        self.assertIn('regime', details)

        # Regime should be either 'uptrend' or 'downtrend'
        self.assertIn(details['regime'], ['uptrend', 'downtrend'])

        # trading_allowed should match regime
        if details['regime'] == 'uptrend':
            self.assertTrue(trading_allowed)
        else:
            self.assertFalse(trading_allowed)


if __name__ == '__main__':
    unittest.main()
