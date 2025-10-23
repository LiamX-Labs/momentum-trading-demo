"""
BTC Regime Filter - Only trade when Bitcoin shows clear trending behavior.

This filter prevents trading during choppy/uncertain market conditions
by requiring Bitcoin to demonstrate strong directional movement.
"""

import pandas as pd
import numpy as np
from typing import Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from indicators.adx import calculate_adx
from indicators.moving_averages import calculate_sma


def check_btc_regime(
    btc_data: pd.DataFrame,
    ma_period: int = 50,
    lookback_high_period: int = 20,
    recent_high_days: int = 5,
    adx_period: int = 14,
    adx_threshold: float = 25.0
) -> pd.DataFrame:
    """
    Check if Bitcoin is in a favorable regime for altcoin momentum trading.

    Only trade when Bitcoin shows clear trending behavior:
    1. BTC price > 50-period MA (uptrend)
    2. BTC made new 20-period high recently (last 5 periods)
    3. ADX > 25 (trending, not choppy)

    Args:
        btc_data: DataFrame with BTC OHLCV data
        ma_period: Moving average period for trend (default: 50)
        lookback_high_period: Period for high calculation (default: 20)
        recent_high_days: Days to check for recent high (default: 5)
        adx_period: ADX calculation period (default: 14)
        adx_threshold: Minimum ADX for trending (default: 25)

    Returns:
        DataFrame with added columns:
        - ma_50: 50-period moving average
        - adx: Average Directional Index
        - rolling_high_20: 20-period high
        - new_high_recently: Boolean, new high in last 5 periods
        - btc_regime_favorable: Boolean, all conditions met
    """
    result = btc_data.copy()

    # 1. Calculate 50-period MA
    result = calculate_sma(result, period=ma_period)
    result[f'ma_{ma_period}'] = result[f'sma_{ma_period}']

    # 2. Calculate ADX
    result = calculate_adx(result, period=adx_period)

    # 3. Calculate rolling highs
    result['rolling_high_20'] = result['high'].rolling(lookback_high_period).max()

    # 4. Check if made new high recently (last 5 periods)
    recent_high = result['high'].rolling(recent_high_days).max()
    past_high = result['rolling_high_20'].shift(recent_high_days)
    result['new_high_recently'] = recent_high >= past_high

    # 5. Combine all conditions
    btc_above_ma = result['close'] > result[f'ma_{ma_period}']
    adx_trending = result['adx'] > adx_threshold

    result['btc_regime_favorable'] = (
        btc_above_ma &
        result['new_high_recently'] &
        adx_trending
    )

    # Add individual condition columns for debugging
    result['btc_above_ma'] = btc_above_ma
    result['adx_trending'] = adx_trending

    return result


def apply_regime_filter(
    signals_df: pd.DataFrame,
    btc_data: pd.DataFrame,
    ma_period: int = 50,
    adx_threshold: float = 25.0
) -> pd.DataFrame:
    """
    Apply BTC regime filter to existing entry signals.

    Args:
        signals_df: DataFrame with entry signals and timestamps
        btc_data: DataFrame with BTC OHLCV data
        ma_period: MA period for BTC trend (default: 50)
        adx_threshold: Minimum ADX threshold (default: 25)

    Returns:
        DataFrame with regime-filtered signals (entry_signal set to False
        when BTC regime is unfavorable)
    """
    # Calculate BTC regime
    btc_regime = check_btc_regime(btc_data, ma_period=ma_period, adx_threshold=adx_threshold)

    # Merge regime data with signals on timestamp
    result = signals_df.copy()

    # Create a mapping of date -> regime status
    regime_map = dict(zip(
        btc_regime['timestamp'].dt.date,
        btc_regime['btc_regime_favorable']
    ))

    # Apply regime filter
    result['btc_regime_favorable'] = result['timestamp'].dt.date.map(regime_map).fillna(False)

    # Filter out signals when regime is unfavorable
    original_signals = result['entry_signal'].sum()
    result.loc[~result['btc_regime_favorable'], 'entry_signal'] = False
    filtered_signals = result['entry_signal'].sum()

    if original_signals > 0:
        filtered_pct = (original_signals - filtered_signals) / original_signals * 100
        print(f"  BTC Regime Filter: {original_signals} signals -> {filtered_signals} signals "
              f"({filtered_pct:.1f}% filtered out)")

    return result


if __name__ == "__main__":
    # Test BTC regime filter
    from data.bybit_api import BybitDataFetcher
    from datetime import datetime, timedelta

    print("Testing BTC Regime Filter...\n")

    fetcher = BybitDataFetcher()

    # Fetch BTC data (4h timeframe)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    print(f"Fetching BTC data from {start_date.date()} to {end_date.date()}...")
    btc_data = fetcher.get_klines('BTCUSDT', interval='4h', start_time=start_date, end_time=end_date, limit=600)

    if len(btc_data) > 0:
        print(f"Retrieved {len(btc_data)} candles\n")

        # Calculate regime
        btc_regime = check_btc_regime(btc_data)

        # Show recent regime status
        print("Recent BTC Regime Status:")
        print(btc_regime[['timestamp', 'close', 'ma_50', 'adx', 'btc_above_ma',
                          'new_high_recently', 'adx_trending', 'btc_regime_favorable']].tail(10))

        # Statistics
        favorable_count = btc_regime['btc_regime_favorable'].sum()
        total_count = len(btc_regime[btc_regime['btc_regime_favorable'].notna()])

        print(f"\nRegime Statistics:")
        print(f"  Favorable periods: {favorable_count}/{total_count} ({favorable_count/total_count*100:.1f}%)")
        print(f"  Current ADX: {btc_regime['adx'].iloc[-1]:.2f}")
        print(f"  Current regime: {'FAVORABLE' if btc_regime['btc_regime_favorable'].iloc[-1] else 'UNFAVORABLE'}")

    else:
        print("No data available")
