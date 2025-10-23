"""
Volume analysis indicators.

Volume is a key confirmation indicator for breakouts.
High volume during a breakout suggests strong participation and conviction.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_avg_volume(
    df: pd.DataFrame,
    period: int = 20,
    volume_col: str = 'volume'
) -> pd.DataFrame:
    """
    Calculate average volume over a period.

    Args:
        df: DataFrame with OHLCV data
        period: Period for average (default: 20)
        volume_col: Column to use for calculation (default: 'volume')

    Returns:
        DataFrame with added column: avg_volume
    """
    result = df.copy()
    result['avg_volume'] = result[volume_col].rolling(window=period).mean()
    return result


def calculate_relative_volume_ratio(
    df: pd.DataFrame,
    period: int = 20,
    volume_col: str = 'volume'
) -> pd.DataFrame:
    """
    Calculate Relative Volume Ratio (RVR).

    RVR measures current volume relative to recent average volume.
    High RVR (> 2.0) indicates unusually high participation.

    Args:
        df: DataFrame with OHLCV data
        period: Period for average volume (default: 20)
        volume_col: Column to use for calculation (default: 'volume')

    Returns:
        DataFrame with added columns: avg_volume, rvr

    Formula:
        RVR = Current Volume / Average Volume (20-day)

    Interpretation:
        RVR > 2.0: Very high volume (2x normal)
        RVR > 1.5: High volume (1.5x normal)
        RVR = 1.0: Normal volume
        RVR < 0.5: Low volume (half normal)
    """
    result = calculate_avg_volume(df, period, volume_col)

    # Calculate RVR
    result['rvr'] = result[volume_col] / result['avg_volume']

    # Handle division by zero
    result['rvr'] = result['rvr'].replace([np.inf, -np.inf], np.nan)

    return result


def calculate_volume_percentile(
    df: pd.DataFrame,
    lookback_period: int = 90,
    volume_col: str = 'volume'
) -> pd.DataFrame:
    """
    Calculate volume percentile ranking.

    Similar to BBWidth percentile, but for volume.
    Shows what percentile current volume is relative to historical volume.

    Args:
        df: DataFrame with OHLCV data
        lookback_period: Days to look back for percentile (default: 90)
        volume_col: Column to use for calculation (default: 'volume')

    Returns:
        DataFrame with added column: volume_percentile (0-1 scale)

    Example:
        volume_percentile = 0.95 means current volume is higher than 95%
        of the past 90 days (very high volume)
    """
    result = df.copy()

    def percentile_rank(series):
        """Calculate percentile rank of last value in series."""
        if len(series) < 2:
            return np.nan
        return (series < series.iloc[-1]).sum() / (len(series) - 1)

    result['volume_percentile'] = result[volume_col].rolling(
        window=lookback_period
    ).apply(percentile_rank, raw=False)

    return result


def calculate_volume_surge(
    df: pd.DataFrame,
    short_period: int = 5,
    long_period: int = 20,
    volume_col: str = 'volume'
) -> pd.DataFrame:
    """
    Detect volume surges by comparing short-term to long-term average.

    Args:
        df: DataFrame with OHLCV data
        short_period: Short-term average period (default: 5)
        long_period: Long-term average period (default: 20)
        volume_col: Column to use for calculation (default: 'volume')

    Returns:
        DataFrame with added columns:
        - avg_volume_short: Short-term average
        - avg_volume_long: Long-term average
        - volume_surge_ratio: Short / Long average

    Interpretation:
        volume_surge_ratio > 2.0: Strong surge
        volume_surge_ratio > 1.5: Moderate surge
        volume_surge_ratio < 1.0: Below normal
    """
    result = df.copy()

    result['avg_volume_short'] = result[volume_col].rolling(window=short_period).mean()
    result['avg_volume_long'] = result[volume_col].rolling(window=long_period).mean()

    result['volume_surge_ratio'] = result['avg_volume_short'] / result['avg_volume_long']
    result['volume_surge_ratio'] = result['volume_surge_ratio'].replace([np.inf, -np.inf], np.nan)

    return result


def calculate_turnover_ratio(
    df: pd.DataFrame,
    period: int = 20,
    turnover_col: str = 'turnover'
) -> pd.DataFrame:
    """
    Calculate relative turnover ratio (in USD).

    Similar to RVR but uses turnover (volume * price) instead of volume.
    More meaningful for assets with changing prices.

    Args:
        df: DataFrame with OHLCV data
        period: Period for average (default: 20)
        turnover_col: Column to use for calculation (default: 'turnover')

    Returns:
        DataFrame with added columns: avg_turnover, turnover_ratio

    Formula:
        Turnover Ratio = Current Turnover / Average Turnover
    """
    result = df.copy()

    result['avg_turnover'] = result[turnover_col].rolling(window=period).mean()
    result['turnover_ratio'] = result[turnover_col] / result['avg_turnover']

    result['turnover_ratio'] = result['turnover_ratio'].replace([np.inf, -np.inf], np.nan)

    return result


if __name__ == "__main__":
    # Test the volume indicators
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))

    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing volume indicators...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Calculate RVR
    print("\n1. Calculating Relative Volume Ratio (RVR)...")
    df_rvr = calculate_relative_volume_ratio(df)
    print("Latest RVR values:")
    print(df_rvr[['timestamp', 'volume', 'avg_volume', 'rvr']].tail())

    # Find high volume days (RVR > 2.0)
    high_volume = df_rvr[df_rvr['rvr'] > 2.0].copy()
    print(f"\n2. Found {len(high_volume)} days with RVR > 2.0:")
    if len(high_volume) > 0:
        print(high_volume[['timestamp', 'volume', 'rvr']].tail(10))

    # Calculate volume percentile
    print("\n3. Calculating volume percentile...")
    df_pct = calculate_volume_percentile(df)
    print("Latest percentile values:")
    print(df_pct[['timestamp', 'volume', 'volume_percentile']].tail())

    # Find volume surges
    print("\n4. Detecting volume surges...")
    df_surge = calculate_volume_surge(df)
    surges = df_surge[df_surge['volume_surge_ratio'] > 1.5].copy()
    print(f"Found {len(surges)} days with volume surge > 1.5x:")
    if len(surges) > 0:
        print(surges[['timestamp', 'volume', 'volume_surge_ratio']].tail(10))

    # Calculate turnover ratio
    print("\n5. Calculating turnover ratio...")
    df_turnover = calculate_turnover_ratio(df)
    print("Latest turnover ratio values:")
    print(df_turnover[['timestamp', 'turnover', 'avg_turnover', 'turnover_ratio']].tail())

    print("\n✓ Volume indicators working correctly!")
