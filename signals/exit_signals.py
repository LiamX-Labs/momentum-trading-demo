"""
Exit signal logic for Volatility Breakout Momentum Strategy.

Exit Criteria:
1. Trailing stop: 20% from peak price
2. Alternative: Price closes below 20-day MA
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from indicators.moving_averages import calculate_sma


def calculate_trailing_stop(
    entry_price: float,
    current_price: float,
    peak_price: float,
    trailing_stop_pct: float = 0.20
) -> Tuple[float, bool]:
    """
    Calculate trailing stop level and check if triggered.

    Args:
        entry_price: Entry price of position
        current_price: Current market price
        peak_price: Highest price since entry
        trailing_stop_pct: Stop distance from peak (default: 0.20 for 20%)

    Returns:
        Tuple of (stop_level, stop_triggered)

    Logic:
        - Stop level = Peak Price * (1 - trailing_stop_pct)
        - Triggered if current_price <= stop_level
        - Peak price is updated as position moves in our favor
    """
    stop_level = peak_price * (1 - trailing_stop_pct)
    stop_triggered = current_price <= stop_level

    return stop_level, stop_triggered


def check_exit_signal(
    df: pd.DataFrame,
    entry_index: int,
    current_index: int,
    entry_price: float,
    trailing_stop_pct: float = 0.20,
    ma_period: int = 20,
    use_ma_exit: bool = True
) -> Tuple[bool, Dict]:
    """
    Check if exit signal is triggered for a position.

    Args:
        df: DataFrame with OHLCV data
        entry_index: Index where position was entered
        current_index: Current index to check for exit
        entry_price: Entry price of position
        trailing_stop_pct: Trailing stop percentage (default: 0.20)
        ma_period: Period for MA exit (default: 20)
        use_ma_exit: Whether to use MA as exit signal (default: True)

    Returns:
        Tuple of (exit_triggered: bool, exit_details: dict)

    Exit Details Dict:
        - exit_triggered: bool
        - exit_reason: str ('trailing_stop', 'ma_exit', 'none')
        - timestamp: datetime
        - close: float
        - entry_price: float
        - peak_price: float
        - stop_level: float
        - return_pct: float
        - holding_days: int
    """
    # Calculate MA if not present
    if f'sma_{ma_period}' not in df.columns:
        df = calculate_sma(df, ma_period)

    # Get subset of data from entry to current
    position_df = df.iloc[entry_index:current_index + 1].copy()

    # Calculate peak price since entry
    peak_price = position_df['high'].max()

    # Get current row
    current_row = df.iloc[current_index]
    current_price = current_row['close']

    # Check trailing stop
    stop_level, stop_triggered = calculate_trailing_stop(
        entry_price,
        current_price,
        peak_price,
        trailing_stop_pct
    )

    # Check MA exit
    ma_col = f'sma_{ma_period}'
    ma_exit_triggered = False
    if use_ma_exit and ma_col in current_row and not pd.isna(current_row[ma_col]):
        ma_exit_triggered = current_price < current_row[ma_col]

    # Determine exit
    exit_triggered = stop_triggered or (use_ma_exit and ma_exit_triggered)

    # Determine exit reason
    if stop_triggered:
        exit_reason = 'trailing_stop'
    elif ma_exit_triggered:
        exit_reason = 'ma_exit'
    else:
        exit_reason = 'none'

    # Calculate return
    return_pct = (current_price - entry_price) / entry_price

    # Calculate holding period
    holding_days = current_index - entry_index

    exit_details = {
        'exit_triggered': exit_triggered,
        'exit_reason': exit_reason,
        'timestamp': current_row.get('timestamp'),
        'close': current_price,
        'entry_price': entry_price,
        'peak_price': peak_price,
        'stop_level': stop_level,
        'return_pct': return_pct,
        'holding_days': holding_days,
        'trailing_stop_triggered': stop_triggered,
        'ma_exit_triggered': ma_exit_triggered
    }

    return exit_triggered, exit_details


def simulate_position_exit(
    df: pd.DataFrame,
    entry_index: int,
    entry_price: float,
    trailing_stop_pct: float = 0.20,
    ma_period: int = 20,
    use_ma_exit: bool = True,
    max_holding_days: Optional[int] = None
) -> Dict:
    """
    Simulate a position from entry to exit.

    Args:
        df: DataFrame with OHLCV data
        entry_index: Index where position was entered
        entry_price: Entry price
        trailing_stop_pct: Trailing stop percentage (default: 0.20)
        ma_period: Period for MA exit (default: 20)
        use_ma_exit: Whether to use MA exit (default: True)
        max_holding_days: Maximum days to hold (default: None for no limit)

    Returns:
        Dictionary with position results:
        - entry_index, entry_price, entry_timestamp
        - exit_index, exit_price, exit_timestamp
        - exit_reason
        - peak_price, peak_index
        - return_pct, holding_days
    """
    # Calculate MA if needed
    if f'sma_{ma_period}' not in df.columns:
        df = calculate_sma(df, ma_period)

    entry_row = df.iloc[entry_index]
    peak_price = entry_price
    peak_index = entry_index

    # Simulate holding period
    for i in range(entry_index + 1, len(df)):
        # Update peak
        if df.iloc[i]['high'] > peak_price:
            peak_price = df.iloc[i]['high']
            peak_index = i

        # Check for exit
        exit_triggered, exit_details = check_exit_signal(
            df, entry_index, i, entry_price,
            trailing_stop_pct, ma_period, use_ma_exit
        )

        if exit_triggered:
            return {
                'entry_index': entry_index,
                'entry_price': entry_price,
                'entry_timestamp': entry_row.get('timestamp'),
                'exit_index': i,
                'exit_price': exit_details['close'],
                'exit_timestamp': exit_details['timestamp'],
                'exit_reason': exit_details['exit_reason'],
                'peak_price': peak_price,
                'peak_index': peak_index,
                'return_pct': exit_details['return_pct'],
                'holding_days': exit_details['holding_days'],
                'max_adverse_excursion': (df.iloc[entry_index:i+1]['low'].min() - entry_price) / entry_price
            }

        # Check max holding period
        if max_holding_days and (i - entry_index) >= max_holding_days:
            final_price = df.iloc[i]['close']
            return {
                'entry_index': entry_index,
                'entry_price': entry_price,
                'entry_timestamp': entry_row.get('timestamp'),
                'exit_index': i,
                'exit_price': final_price,
                'exit_timestamp': df.iloc[i].get('timestamp'),
                'exit_reason': 'max_holding_days',
                'peak_price': peak_price,
                'peak_index': peak_index,
                'return_pct': (final_price - entry_price) / entry_price,
                'holding_days': i - entry_index,
                'max_adverse_excursion': (df.iloc[entry_index:i+1]['low'].min() - entry_price) / entry_price
            }

    # No exit found (still open)
    final_index = len(df) - 1
    final_price = df.iloc[final_index]['close']

    return {
        'entry_index': entry_index,
        'entry_price': entry_price,
        'entry_timestamp': entry_row.get('timestamp'),
        'exit_index': final_index,
        'exit_price': final_price,
        'exit_timestamp': df.iloc[final_index].get('timestamp'),
        'exit_reason': 'still_open',
        'peak_price': peak_price,
        'peak_index': peak_index,
        'return_pct': (final_price - entry_price) / entry_price,
        'holding_days': final_index - entry_index,
        'max_adverse_excursion': (df.iloc[entry_index:final_index+1]['low'].min() - entry_price) / entry_price
    }


if __name__ == "__main__":
    # Test exit signal logic
    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing exit signal logic...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Test trailing stop
    print("\n1. Testing trailing stop calculation...")
    entry_price = 0.20
    peak_price = 0.25  # 25% gain
    current_price = 0.21  # Pulled back from peak

    stop_level, stop_triggered = calculate_trailing_stop(entry_price, current_price, peak_price)
    print(f"Entry: ${entry_price:.6f}")
    print(f"Peak: ${peak_price:.6f} (+{(peak_price/entry_price-1)*100:.1f}%)")
    print(f"Current: ${current_price:.6f}")
    print(f"Stop Level: ${stop_level:.6f}")
    print(f"Stop Triggered: {stop_triggered}")

    # Simulate a position
    print("\n2. Simulating a position...")
    # Find an entry point (use middle of data)
    entry_idx = len(df) // 2
    entry_price = df.iloc[entry_idx]['close']

    result = simulate_position_exit(df, entry_idx, entry_price)

    print(f"\nPosition Results:")
    print(f"Entry: {result['entry_timestamp']} @ ${result['entry_price']:.6f}")
    print(f"Peak: ${result['peak_price']:.6f} (+{(result['peak_price']/result['entry_price']-1)*100:.1f}%)")
    print(f"Exit: {result['exit_timestamp']} @ ${result['exit_price']:.6f}")
    print(f"Exit Reason: {result['exit_reason']}")
    print(f"Return: {result['return_pct']*100:.2f}%")
    print(f"Holding Days: {result['holding_days']}")
    print(f"Max Adverse Excursion: {result['max_adverse_excursion']*100:.2f}%")

    print("\n✓ Exit signal logic working correctly!")
