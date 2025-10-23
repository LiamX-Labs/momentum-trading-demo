"""
Moving average indicators.

Moving averages smooth price data and help identify trends.
Used for both trend confirmation and regime filtering.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict


def calculate_sma(
    df: pd.DataFrame,
    period: int,
    price_col: str = 'close',
    output_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate Simple Moving Average (SMA).

    Args:
        df: DataFrame with OHLCV data
        period: Period for moving average
        price_col: Column to use for calculation (default: 'close')
        output_col: Name for output column (default: 'sma_{period}')

    Returns:
        DataFrame with added SMA column

    Formula:
        SMA = Sum of prices over N periods / N
    """
    result = df.copy()

    if output_col is None:
        output_col = f'sma_{period}'

    result[output_col] = result[price_col].rolling(window=period).mean()

    return result


def calculate_multiple_smas(
    df: pd.DataFrame,
    periods: List[int],
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate multiple SMAs at once.

    Args:
        df: DataFrame with OHLCV data
        periods: List of periods to calculate (e.g., [20, 50, 200])
        price_col: Column to use for calculation (default: 'close')

    Returns:
        DataFrame with added columns: sma_20, sma_50, etc.

    Example:
        df = calculate_multiple_smas(df, [20, 50, 200])
        # Adds columns: sma_20, sma_50, sma_200
    """
    result = df.copy()

    for period in periods:
        result = calculate_sma(result, period, price_col)

    return result


def calculate_ema(
    df: pd.DataFrame,
    period: int,
    price_col: str = 'close',
    output_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Calculate Exponential Moving Average (EMA).

    EMA gives more weight to recent prices compared to SMA.

    Args:
        df: DataFrame with OHLCV data
        period: Period for moving average
        price_col: Column to use for calculation (default: 'close')
        output_col: Name for output column (default: 'ema_{period}')

    Returns:
        DataFrame with added EMA column

    Formula:
        EMA = Price * (2 / (period + 1)) + EMA_prev * (1 - (2 / (period + 1)))
    """
    result = df.copy()

    if output_col is None:
        output_col = f'ema_{period}'

    result[output_col] = result[price_col].ewm(span=period, adjust=False).mean()

    return result


def check_price_above_ma(
    df: pd.DataFrame,
    ma_period: int,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Check if price is above its moving average.

    Used for trend confirmation - we generally want to trade in the
    direction of the trend.

    Args:
        df: DataFrame with OHLCV data
        ma_period: Period for moving average
        price_col: Column to use (default: 'close')

    Returns:
        DataFrame with added columns:
        - sma_{period}: The moving average
        - above_ma_{period}: Boolean, True if price > MA
    """
    result = calculate_sma(df, ma_period, price_col)

    ma_col = f'sma_{ma_period}'
    result[f'above_ma_{ma_period}'] = result[price_col] > result[ma_col]

    return result


def calculate_ma_distance(
    df: pd.DataFrame,
    ma_period: int,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Calculate distance of price from its moving average.

    Useful for identifying overbought/oversold conditions.

    Args:
        df: DataFrame with OHLCV data
        ma_period: Period for moving average
        price_col: Column to use (default: 'close')

    Returns:
        DataFrame with added columns:
        - sma_{period}: The moving average
        - ma_distance_{period}: Percentage distance from MA
        - ma_distance_pct_{period}: Distance as percentage

    Formula:
        MA Distance % = (Price - MA) / MA
    """
    result = calculate_sma(df, ma_period, price_col)

    ma_col = f'sma_{ma_period}'
    result[f'ma_distance_{ma_period}'] = result[price_col] - result[ma_col]
    result[f'ma_distance_pct_{ma_period}'] = (
        (result[price_col] - result[ma_col]) / result[ma_col]
    )

    return result


def calculate_ma_crossover(
    df: pd.DataFrame,
    fast_period: int,
    slow_period: int,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Detect moving average crossovers.

    Golden Cross: Fast MA crosses above slow MA (bullish)
    Death Cross: Fast MA crosses below slow MA (bearish)

    Args:
        df: DataFrame with OHLCV data
        fast_period: Period for fast MA (e.g., 20)
        slow_period: Period for slow MA (e.g., 50)
        price_col: Column to use (default: 'close')

    Returns:
        DataFrame with added columns:
        - sma_{fast_period}, sma_{slow_period}: The MAs
        - ma_cross_bullish: True on day of bullish crossover
        - ma_cross_bearish: True on day of bearish crossover
        - fast_above_slow: True when fast MA > slow MA
    """
    result = df.copy()

    # Calculate both MAs
    result = calculate_sma(result, fast_period, price_col)
    result = calculate_sma(result, slow_period, price_col)

    fast_col = f'sma_{fast_period}'
    slow_col = f'sma_{slow_period}'

    # Check if fast is above slow
    result['fast_above_slow'] = result[fast_col] > result[slow_col]

    # Detect crossovers (when fast_above_slow changes)
    result['ma_cross_bullish'] = (
        (result['fast_above_slow'] == True) &
        (result['fast_above_slow'].shift(1) == False)
    )

    result['ma_cross_bearish'] = (
        (result['fast_above_slow'] == False) &
        (result['fast_above_slow'].shift(1) == True)
    )

    return result


def get_ma_regime(
    df: pd.DataFrame,
    regime_period: int = 50,
    price_col: str = 'close'
) -> pd.DataFrame:
    """
    Determine market regime based on MA.

    Used for filtering trades - only trade when in uptrend regime.

    Args:
        df: DataFrame with OHLCV data
        regime_period: Period for regime MA (default: 50)
        price_col: Column to use (default: 'close')

    Returns:
        DataFrame with added columns:
        - sma_{regime_period}: The regime MA
        - regime_uptrend: Boolean, True if price > MA (uptrend)
        - regime_downtrend: Boolean, True if price < MA (downtrend)

    Interpretation:
        Only take long positions when regime_uptrend = True
    """
    result = check_price_above_ma(df, regime_period, price_col)

    ma_col = f'above_ma_{regime_period}'
    result['regime_uptrend'] = result[ma_col]
    result['regime_downtrend'] = ~result[ma_col]

    return result


if __name__ == "__main__":
    # Test the moving average indicators
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))

    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing moving average indicators...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Calculate single SMA
    print("\n1. Calculating 20-day SMA...")
    df_sma = calculate_sma(df, 20)
    print("Latest values:")
    print(df_sma[['timestamp', 'close', 'sma_20']].tail())

    # Calculate multiple SMAs
    print("\n2. Calculating multiple SMAs (20, 50, 200)...")
    df_multi = calculate_multiple_smas(df, [20, 50, 200])
    print("Latest values:")
    print(df_multi[['timestamp', 'close', 'sma_20', 'sma_50', 'sma_200']].tail())

    # Check price above MA
    print("\n3. Checking price above 20-day MA...")
    df_above = check_price_above_ma(df, 20)
    above_count = df_above['above_ma_20'].sum()
    print(f"Price above 20-day MA: {above_count}/{len(df_above)} days ({above_count/len(df_above)*100:.1f}%)")

    # Calculate MA distance
    print("\n4. Calculating distance from 20-day MA...")
    df_dist = calculate_ma_distance(df, 20)
    print("Latest distance values:")
    print(df_dist[['timestamp', 'close', 'sma_20', 'ma_distance_pct_20']].tail())

    # Detect crossovers
    print("\n5. Detecting MA crossovers (20/50)...")
    df_cross = calculate_ma_crossover(df, fast_period=20, slow_period=50)
    bullish_crosses = df_cross[df_cross['ma_cross_bullish']].copy()
    bearish_crosses = df_cross[df_cross['ma_cross_bearish']].copy()
    print(f"Bullish crossovers (golden cross): {len(bullish_crosses)}")
    print(f"Bearish crossovers (death cross): {len(bearish_crosses)}")

    if len(bullish_crosses) > 0:
        print("\nLatest bullish crossovers:")
        print(bullish_crosses[['timestamp', 'sma_20', 'sma_50']].tail(5))

    # Get market regime
    print("\n6. Determining market regime (50-day MA)...")
    df_regime = get_ma_regime(df, regime_period=50)
    uptrend_count = df_regime['regime_uptrend'].sum()
    print(f"Uptrend days: {uptrend_count}/{len(df_regime)} ({uptrend_count/len(df_regime)*100:.1f}%)")
    print("Current regime:", "UPTREND" if df_regime['regime_uptrend'].iloc[-1] else "DOWNTREND")

    print("\n✓ Moving average indicators working correctly!")
