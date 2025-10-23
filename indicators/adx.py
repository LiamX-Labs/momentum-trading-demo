"""
ADX (Average Directional Index) calculation.

ADX measures trend strength on a scale of 0-100:
- ADX > 25: Strong trend (trending market)
- ADX < 20: Weak trend (choppy/ranging market)
"""

import pandas as pd
import numpy as np


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate ADX (Average Directional Index).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default: 14)

    Returns:
        DataFrame with added columns:
        - plus_di: Plus Directional Indicator
        - minus_di: Minus Directional Indicator
        - adx: Average Directional Index
    """
    result = df.copy()

    # Calculate True Range (TR)
    high_low = result['high'] - result['low']
    high_close = abs(result['high'] - result['close'].shift(1))
    low_close = abs(result['low'] - result['close'].shift(1))

    tr = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)

    # Calculate Directional Movement
    up_move = result['high'] - result['high'].shift(1)
    down_move = result['low'].shift(1) - result['low']

    # Plus/Minus Directional Movement
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # Smooth with Wilder's moving average
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / atr

    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()

    result['plus_di'] = plus_di
    result['minus_di'] = minus_di
    result['adx'] = adx

    return result


if __name__ == "__main__":
    # Test ADX calculation
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing ADX calculation...\n")

    # Load some test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    df = load_historical_ohlcv('BTCUSDT', start_date, end_date, timeframe='1D')

    if len(df) > 0:
        df_with_adx = calculate_adx(df)

        print("Sample ADX values:")
        print(df_with_adx[['timestamp', 'close', 'plus_di', 'minus_di', 'adx']].tail(10))

        print(f"\nADX Statistics:")
        print(f"  Mean: {df_with_adx['adx'].mean():.2f}")
        print(f"  Current: {df_with_adx['adx'].iloc[-1]:.2f}")
        print(f"  Max: {df_with_adx['adx'].max():.2f}")

        trending_days = (df_with_adx['adx'] > 25).sum()
        print(f"\nTrending days (ADX > 25): {trending_days}/{len(df_with_adx)} ({trending_days/len(df_with_adx)*100:.1f}%)")
    else:
        print("No data available")
