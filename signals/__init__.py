"""
Signal generation for Volatility Breakout Momentum Strategy.

This module generates entry and exit signals based on:
- Bollinger Band compression and breakout
- Volume expansion
- Trend confirmation
"""

from .entry_signals import check_entry_signal, generate_entry_signals
from .exit_signals import check_exit_signal, calculate_trailing_stop
from .regime_filter import check_regime_filter

__all__ = [
    'check_entry_signal',
    'generate_entry_signals',
    'check_exit_signal',
    'calculate_trailing_stop',
    'check_regime_filter'
]
