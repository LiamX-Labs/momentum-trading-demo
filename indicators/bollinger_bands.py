"""
Bollinger Bands indicator calculations.

Bollinger Bands are volatility bands placed above and below a moving average.
The bands widen during volatile periods and contract during calm periods.

For the strategy:
- 20-period simple moving average (middle band)
- Upper/lower bands: 2 standard deviations from middle
- BBWidth measures band compression (identifies low volatility)
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.

    Args:
        df: DataFrame with OHLCV data
        period: Period for moving average (default: 20)
        num_std: Number of standard deviations for bands (default: 2.0)
        price_col: Column to use for calculation (default: 'close')

    Returns:
        DataFrame with added columns: bb_middle, bb_upper, bb_lower

    Formula:
        Middle Band = 20-period SMA
        Upper Band = Middle Band + (2 * 20-period std dev)
        Lower Band = Middle Band - (2 * 20-period std dev)
    """
    result = df.copy()

    # Calculate middle band (SMA)
    result['bb_middle'] = result[price_col].rolling(window=period).mean()

    # Calculate standard deviation
    std = result[price_col].rolling(window=period).std()

    # Calculate upper and lower bands
    result['bb_upper'] = result['bb_middle'] + (num_std * std)
    result['bb_lower'] = result['bb_middle'] - (num_std * std)

    return result


def calculate_bbwidth(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate Bollinger Band Width (BBWidth).

    BBWidth measures the percentage difference between upper and lower bands.
    Low BBWidth indicates low volatility (band compression) - potential breakout setup.

    Args:
        df: DataFrame with OHLCV data
        period: Period for Bollinger Bands (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        price_col: Column to use for calculation (default: 'close')

    Returns:
        DataFrame with added column: bbwidth

    Formula:
        BBWidth = (Upper Band - Lower Band) / Middle Band
    """
    result = calculate_bollinger_bands(df, period, num_std, price_col)

    # Calculate BBWidth
    result['bbwidth'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']

    return result


def calculate_bbwidth_percentile(
    df: pd.DataFrame,
    lookback_period: int = 90,
    bb_period: int = 20,
    num_std: float = 2.0,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate BBWidth percentile ranking.

    For each day, calculate what percentile the current BBWidth is relative
    to the past N days. Low percentile (e.g., <25th) indicates unusually
    compressed volatility.

    Args:
        df: DataFrame with OHLCV data
        lookback_period: Days to look back for percentile calculation (default: 90)
        bb_period: Period for Bollinger Bands (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        price_col: Column to use for calculation (default: 'close')

    Returns:
        DataFrame with added column: bbwidth_percentile (0-1 scale)

    Example:
        bbwidth_percentile = 0.15 means current BBWidth is lower than 85% of
        the past 90 days (very compressed, potential breakout)
    """
    result = calculate_bbwidth(df, bb_period, num_std, price_col)

    # Calculate rolling percentile rank
    def percentile_rank(series):
        """Calculate percentile rank of last value in series."""
        if len(series) < 2:
            return np.nan
        # Rank from 0 to 1
        return (series < series.iloc[-1]).sum() / (len(series) - 1)

    result['bbwidth_percentile'] = result['bbwidth'].rolling(
        window=lookback_period
    ).apply(percentile_rank, raw=False)

    return result


def get_bb_position(
    df: pd.DataFrame,
    period: int = 20,
    num_std: float = 2.0,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate price position relative to Bollinger Bands.

    Useful for identifying when price breaks above/below bands.

    Args:
        df: DataFrame with OHLCV data
        period: Period for Bollinger Bands (default: 20)
        num_std: Number of standard deviations (default: 2.0)
        price_col: Column to use for calculation (default: 'close')

    Returns:
        DataFrame with added columns:
        - bb_position: 0-1 scale (0 = at lower band, 1 = at upper band)
        - above_upper_band: Boolean, True if close > upper band
        - below_lower_band: Boolean, True if close < lower band
    """
    result = calculate_bollinger_bands(df, period, num_std, price_col)

    # Calculate position (0-1 scale)
    band_range = result['bb_upper'] - result['bb_lower']
    result['bb_position'] = (result[price_col] - result['bb_lower']) / band_range

    # Boolean flags
    result['above_upper_band'] = result[price_col] > result['bb_upper']
    result['below_lower_band'] = result[price_col] < result['bb_lower']

    return result


if __name__ == "__main__":
    # Test the Bollinger Bands calculator
    import sys
    from pathlib import Path

    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent))

    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing Bollinger Bands calculator...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Calculate Bollinger Bands
    print("\n1. Calculating Bollinger Bands...")
    df_bb = calculate_bollinger_bands(df)
    print("Latest values:")
    print(df_bb[['timestamp', 'close', 'bb_lower', 'bb_middle', 'bb_upper']].tail())

    # Calculate BBWidth
    print("\n2. Calculating BBWidth...")
    df_bbw = calculate_bbwidth(df)
    print("Latest BBWidth values:")
    print(df_bbw[['timestamp', 'close', 'bbwidth']].tail())

    # Calculate BBWidth percentile
    print("\n3. Calculating BBWidth percentile (90-day lookback)...")
    df_pct = calculate_bbwidth_percentile(df)
    print("Latest percentile values:")
    print(df_pct[['timestamp', 'close', 'bbwidth', 'bbwidth_percentile']].tail())

    # Find compressed periods (< 25th percentile)
    compressed = df_pct[df_pct['bbwidth_percentile'] < 0.25].copy()
    print(f"\n4. Found {len(compressed)} days with BBWidth < 25th percentile:")
    if len(compressed) > 0:
        print(compressed[['timestamp', 'close', 'bbwidth_percentile']].tail(10))

    # Check breakouts above upper band
    print("\n5. Checking for breakouts above upper band...")
    df_pos = get_bb_position(df)
    breakouts = df_pos[df_pos['above_upper_band']].copy()
    print(f"Found {len(breakouts)} days where close > upper band:")
    if len(breakouts) > 0:
        print(breakouts[['timestamp', 'close', 'bb_upper']].tail(10))

    print("\n✓ Bollinger Bands calculator working correctly!")
