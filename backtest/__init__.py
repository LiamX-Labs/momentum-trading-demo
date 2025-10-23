"""
Backtesting framework for Volatility Breakout Momentum Strategy.

This module provides event-driven backtesting with:
- Position sizing and risk management
- Multi-asset portfolio tracking
- Performance metrics calculation
"""

from .position_sizer import PositionSizer, calculate_position_size
from .backtester import Backtester, BacktestResult
from .performance import calculate_performance_metrics, generate_performance_report

__all__ = [
    'PositionSizer',
    'calculate_position_size',
    'Backtester',
    'BacktestResult',
    'calculate_performance_metrics',
    'generate_performance_report'
]
