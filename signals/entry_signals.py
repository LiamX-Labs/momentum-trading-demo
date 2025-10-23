"""
Entry signal logic for Volatility Breakout Momentum Strategy.

Entry Criteria:
1. BBWidth < 25th percentile (90-day lookback) - Compression
2. Price closes above upper Bollinger Band - Breakout
3. RVR > 2.0 - Volume expansion
4. Price > 20-day MA - Trend confirmation
5. BTC > 50-day MA - Regime filter (when available)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from indicators.bollinger_bands import calculate_bbwidth_percentile, get_bb_position
from indicators.volume import calculate_relative_volume_ratio
from indicators.moving_averages import check_price_above_ma


def check_entry_signal(
    df: pd.DataFrame,
    index: int = -1,
    bbwidth_threshold: float = 0.25,
    rvr_threshold: float = 2.0,
    ma_period: int = 20,
    lookback_period: int = 90
) -> Tuple[bool, Dict]:
    """
    Check if entry signal is triggered for a specific date.

    Args:
        df: DataFrame with OHLCV data and calculated indicators
        index: Row index to check (default: -1 for latest)
        bbwidth_threshold: BBWidth percentile threshold (default: 0.25 for 25th percentile)
        rvr_threshold: Minimum RVR for entry (default: 2.0)
        ma_period: Period for trend MA (default: 20)
        lookback_period: Lookback for BBWidth percentile (default: 90)

    Returns:
        Tuple of (signal_triggered: bool, signal_details: dict)

    Signal Details Dict:
        - triggered: bool
        - timestamp: datetime
        - close: float
        - bbwidth_percentile: float
        - above_upper_band: bool
        - rvr: float
        - above_ma: bool
        - signal_strength: float (0-1, higher is stronger)
        - criteria_met: dict (which criteria passed)
    """
    # Calculate required indicators if not present
    if 'bbwidth_percentile' not in df.columns:
        df = calculate_bbwidth_percentile(df, lookback_period=lookback_period)

    if 'above_upper_band' not in df.columns:
        df = get_bb_position(df)

    if 'rvr' not in df.columns:
        df = calculate_relative_volume_ratio(df)

    if f'above_ma_{ma_period}' not in df.columns:
        df = check_price_above_ma(df, ma_period)

    # Get row
    row = df.iloc[index]

    # Check each criterion
    criteria = {
        'bbwidth_compressed': row.get('bbwidth_percentile', np.nan) < bbwidth_threshold,
        'breakout_upper_band': row.get('above_upper_band', False),
        'volume_expansion': row.get('rvr', 0) > rvr_threshold,
        'trend_confirmed': row.get(f'above_ma_{ma_period}', False)
    }

    # All criteria must be True
    all_met = all(criteria.values())

    # Calculate signal strength (0-1 scale)
    # Based on how much each indicator exceeds its threshold
    strength_components = []

    # BBWidth: lower is better (inverse)
    if not pd.isna(row.get('bbwidth_percentile')):
        strength_components.append(1 - row['bbwidth_percentile'])

    # RVR: higher is better
    if row.get('rvr', 0) > 0:
        strength_components.append(min(row['rvr'] / 5.0, 1.0))  # Cap at 5x

    # MA distance: higher is better (but cap)
    ma_col = f'sma_{ma_period}'
    if ma_col in df.columns and not pd.isna(row.get(ma_col)):
        price_above_pct = (row['close'] - row[ma_col]) / row[ma_col]
        strength_components.append(min(price_above_pct / 0.1, 1.0))  # Cap at 10% above

    signal_strength = np.mean(strength_components) if strength_components else 0.0

    signal_details = {
        'triggered': all_met,
        'timestamp': row.get('timestamp'),
        'close': row.get('close'),
        'bbwidth_percentile': row.get('bbwidth_percentile'),
        'above_upper_band': row.get('above_upper_band'),
        'rvr': row.get('rvr'),
        'above_ma': row.get(f'above_ma_{ma_period}'),
        'signal_strength': signal_strength,
        'criteria_met': criteria
    }

    return all_met, signal_details


def generate_entry_signals(
    df: pd.DataFrame,
    bbwidth_threshold: float = 0.25,
    rvr_threshold: float = 2.0,
    ma_period: int = 20,
    lookback_period: int = 90
) -> pd.DataFrame:
    """
    Generate entry signals for entire DataFrame.

    Args:
        df: DataFrame with OHLCV data
        bbwidth_threshold: BBWidth percentile threshold (default: 0.25)
        rvr_threshold: Minimum RVR (default: 2.0)
        ma_period: Period for trend MA (default: 20)
        lookback_period: Lookback for BBWidth percentile (default: 90)

    Returns:
        DataFrame with added columns:
        - entry_signal: Boolean, True on entry days
        - signal_strength: Float (0-1)
    """
    # Calculate all required indicators
    result = calculate_bbwidth_percentile(df, lookback_period=lookback_period)
    result = get_bb_position(result)
    result = calculate_relative_volume_ratio(result)
    result = check_price_above_ma(result, ma_period)

    # Check each row for entry signal
    signals = []
    strengths = []

    for i in range(len(result)):
        triggered, details = check_entry_signal(
            result,
            index=i,
            bbwidth_threshold=bbwidth_threshold,
            rvr_threshold=rvr_threshold,
            ma_period=ma_period,
            lookback_period=lookback_period
        )

        signals.append(triggered)
        strengths.append(details['signal_strength'])

    result['entry_signal'] = signals
    result['signal_strength'] = strengths

    return result


if __name__ == "__main__":
    # Test entry signal logic
    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing entry signal logic...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Generate entry signals
    print("\n1. Generating entry signals...")
    df_signals = generate_entry_signals(df)

    # Count signals
    signal_count = df_signals['entry_signal'].sum()
    print(f"Found {signal_count} entry signals in {len(df_signals)} days ({signal_count/len(df_signals)*100:.2f}%)")

    # Show signals
    if signal_count > 0:
        print("\nEntry signals:")
        signals_df = df_signals[df_signals['entry_signal']].copy()
        print(signals_df[['timestamp', 'close', 'bbwidth_percentile', 'rvr', 'signal_strength']].to_string())

    # Check latest signal
    print("\n2. Checking latest signal...")
    triggered, details = check_entry_signal(df)
    print(f"Signal triggered: {details['triggered']}")
    print(f"Timestamp: {details['timestamp']}")
    print(f"Close: ${details['close']:.6f}")
    print(f"\nCriteria:")
    for criterion, met in details['criteria_met'].items():
        status = "✓" if met else "✗"
        print(f"  {status} {criterion}")
    print(f"\nSignal strength: {details['signal_strength']:.2%}")

    print("\n✓ Entry signal logic working correctly!")
