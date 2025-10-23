"""
Market regime filter for Volatility Breakout Momentum Strategy.

Only take long positions when the market (BTC) is in an uptrend.
This reduces losing trades during bear markets.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from indicators.moving_averages import get_ma_regime


def check_regime_filter(
    df: pd.DataFrame,
    index: int = -1,
    regime_period: int = 50,
    price_col: str = 'close'
) -> Tuple[bool, Dict]:
    """
    Check if market regime allows trading.

    Args:
        df: DataFrame with OHLCV data (typically BTC)
        index: Row index to check (default: -1 for latest)
        regime_period: Period for regime MA (default: 50)
        price_col: Column to use (default: 'close')

    Returns:
        Tuple of (trading_allowed: bool, regime_details: dict)

    Regime Details Dict:
        - trading_allowed: bool
        - regime: str ('uptrend' or 'downtrend')
        - timestamp: datetime
        - close: float
        - ma: float
        - distance_from_ma_pct: float
    """
    # Calculate regime indicators if not present
    if 'regime_uptrend' not in df.columns:
        df = get_ma_regime(df, regime_period, price_col)

    row = df.iloc[index]
    ma_col = f'sma_{regime_period}'

    trading_allowed = row.get('regime_uptrend', False)
    regime = 'uptrend' if trading_allowed else 'downtrend'

    # Calculate distance from MA
    distance_pct = np.nan
    if ma_col in row and not pd.isna(row[ma_col]):
        distance_pct = (row[price_col] - row[ma_col]) / row[ma_col]

    regime_details = {
        'trading_allowed': trading_allowed,
        'regime': regime,
        'timestamp': row.get('timestamp'),
        'close': row.get(price_col),
        'ma': row.get(ma_col),
        'distance_from_ma_pct': distance_pct
    }

    return trading_allowed, regime_details


def apply_regime_filter(
    trading_signals_df: pd.DataFrame,
    regime_df: pd.DataFrame,
    regime_period: int = 50
) -> pd.DataFrame:
    """
    Apply regime filter to trading signals.

    Args:
        trading_signals_df: DataFrame with entry signals for trading asset
        regime_df: DataFrame with OHLCV for regime asset (e.g., BTC)
        regime_period: Period for regime MA (default: 50)

    Returns:
        DataFrame with filtered signals (entry_signal set to False when regime is downtrend)

    Usage:
        # Generate signals for DOGEUSDT
        signals_df = generate_entry_signals(doge_df)

        # Load BTC data
        btc_df = load_historical_ohlcv('BTCUSDT')

        # Apply regime filter
        filtered_signals_df = apply_regime_filter(signals_df, btc_df)
    """
    result = trading_signals_df.copy()

    # Calculate regime for BTC
    if 'regime_uptrend' not in regime_df.columns:
        regime_df = get_ma_regime(regime_df, regime_period)

    # Merge regime data with trading signals on timestamp
    merged = result.merge(
        regime_df[['timestamp', 'regime_uptrend']],
        on='timestamp',
        how='left',
        suffixes=('', '_regime')
    )

    # Filter signals: only allow when regime is uptrend
    if 'entry_signal' in merged.columns:
        # Set entry_signal to False when regime is downtrend
        merged.loc[merged['regime_uptrend'] == False, 'entry_signal'] = False

        # Add filtered signal count
        original_count = result.get('entry_signal', pd.Series()).sum()
        filtered_count = merged['entry_signal'].sum()
        removed_count = original_count - filtered_count

        print(f"Regime filter applied:")
        print(f"  Original signals: {original_count}")
        print(f"  Filtered signals: {filtered_count}")
        print(f"  Removed: {removed_count} ({removed_count/max(original_count,1)*100:.1f}%)")

    return merged


if __name__ == "__main__":
    # Test regime filter
    from data.data_loader import load_historical_ohlcv
    from datetime import datetime, timedelta

    print("Testing regime filter...")

    # Load test data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    df = load_historical_ohlcv('DOGEUSDT', start_date, end_date, timeframe='1D')

    print(f"\nLoaded {len(df)} days of DOGEUSDT data")

    # Check current regime
    print("\n1. Checking current regime...")
    trading_allowed, details = check_regime_filter(df, regime_period=50)

    print(f"Trading Allowed: {details['trading_allowed']}")
    print(f"Regime: {details['regime'].upper()}")
    print(f"Timestamp: {details['timestamp']}")
    print(f"Close: ${details['close']:.6f}")
    print(f"50-day MA: ${details['ma']:.6f}")
    print(f"Distance from MA: {details['distance_from_ma_pct']*100:.2f}%")

    # Analyze regime over time
    print("\n2. Analyzing regime over time...")
    df_regime = get_ma_regime(df, regime_period=50)

    uptrend_days = df_regime['regime_uptrend'].sum()
    total_days = len(df_regime)

    print(f"Uptrend days: {uptrend_days}/{total_days} ({uptrend_days/total_days*100:.1f}%)")
    print(f"Downtrend days: {total_days - uptrend_days}/{total_days} ({(total_days-uptrend_days)/total_days*100:.1f}%)")

    # Find regime changes
    regime_changes = df_regime['regime_uptrend'].diff()
    uptrend_starts = df_regime[regime_changes == True]
    downtrend_starts = df_regime[regime_changes == False]

    print(f"\nRegime changes:")
    print(f"  Uptrend starts: {len(uptrend_starts)}")
    print(f"  Downtrend starts: {len(downtrend_starts)}")

    if len(uptrend_starts) > 0:
        print("\nLatest uptrend start:")
        print(uptrend_starts[['timestamp', 'close', 'sma_50']].tail(1).to_string(index=False))

    print("\n✓ Regime filter working correctly!")
