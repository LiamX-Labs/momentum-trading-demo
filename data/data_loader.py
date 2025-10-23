"""
Data loader for the Volatility Breakout Momentum Strategy.

Loads OHLCV data from the existing Bybit datawarehouse and resamples
to daily timeframe for strategy calculations.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import glob

# Path to Bybit datawarehouse
BYBIT_DATA_DIR = Path("/home/william/STRATEGIES/datawarehouse/bybit_data")


def get_available_symbols() -> List[str]:
    """
    Scan the datawarehouse and return all available symbols.

    Returns:
        List of symbol names (e.g., ['1000PEPEUSDT', 'BTCUSDT', ...])
    """
    if not BYBIT_DATA_DIR.exists():
        raise FileNotFoundError(f"Bybit data directory not found: {BYBIT_DATA_DIR}")

    symbols = []
    for path in BYBIT_DATA_DIR.iterdir():
        if path.is_dir() and not path.name.startswith('.'):
            symbols.append(path.name)

    return sorted(symbols)


def get_symbol_date_range(symbol: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Get the available date range for a symbol.

    Args:
        symbol: Symbol name (e.g., '1000PEPEUSDT')

    Returns:
        Tuple of (start_date, end_date) or (None, None) if no data
    """
    symbol_dir = BYBIT_DATA_DIR / symbol

    if not symbol_dir.exists():
        return None, None

    # Find all 1m CSV files (we'll use 1m as the source)
    csv_files = sorted(glob.glob(str(symbol_dir / "*_1m.csv")))

    if not csv_files:
        return None, None

    # Extract dates from filenames
    dates = []
    for file in csv_files:
        filename = Path(file).stem  # e.g., "2024-08-16_1m"
        date_str = filename.split('_')[0]  # e.g., "2024-08-16"
        try:
            dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
        except ValueError:
            continue

    if not dates:
        return None, None

    return min(dates), max(dates)


def load_historical_ohlcv(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    timeframe: str = '1D'
) -> pd.DataFrame:
    """
    Load historical OHLCV data for a symbol and resample to desired timeframe.

    Args:
        symbol: Symbol name (e.g., '1000PEPEUSDT')
        start_date: Start date for data (default: 90 days ago)
        end_date: End date for data (default: today)
        timeframe: Target timeframe ('1D' for daily, '1H' for hourly, etc.)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, turnover
        Resampled to the specified timeframe with proper OHLCV aggregation

    Raises:
        FileNotFoundError: If symbol directory doesn't exist
        ValueError: If no data found in the specified date range
    """
    symbol_dir = BYBIT_DATA_DIR / symbol

    if not symbol_dir.exists():
        raise FileNotFoundError(f"Symbol directory not found: {symbol_dir}")

    # Set default date range if not provided
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=90)

    # Find all 1m CSV files in the date range
    all_data = []
    current_date = start_date

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        csv_path = symbol_dir / f"{date_str}_1m.csv"

        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                all_data.append(df)
            except Exception as e:
                print(f"Warning: Error reading {csv_path}: {e}")

        current_date += timedelta(days=1)

    if not all_data:
        raise ValueError(f"No data found for {symbol} between {start_date} and {end_date}")

    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='first')

    # Set timestamp as index for resampling
    combined_df = combined_df.set_index('timestamp')

    # Resample to target timeframe
    if timeframe != '1T':  # If not 1-minute (raw data)
        resampled = combined_df.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'turnover': 'sum'
        })

        # Drop rows with no data (all NaN)
        resampled = resampled.dropna(subset=['open', 'close'])

        # Reset index to have timestamp as column
        resampled = resampled.reset_index()
    else:
        resampled = combined_df.reset_index()

    return resampled


def load_multiple_symbols(
    symbols: List[str],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    timeframe: str = '1D'
) -> dict:
    """
    Load OHLCV data for multiple symbols.

    Args:
        symbols: List of symbol names
        start_date: Start date for data (default: 90 days ago)
        end_date: End date for data (default: today)
        timeframe: Target timeframe ('1D' for daily)

    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    data = {}

    for symbol in symbols:
        try:
            df = load_historical_ohlcv(symbol, start_date, end_date, timeframe)
            data[symbol] = df
            print(f"Loaded {symbol}: {len(df)} rows from {df['timestamp'].min()} to {df['timestamp'].max()}")
        except Exception as e:
            print(f"Error loading {symbol}: {e}")

    return data


def calculate_avg_daily_volume(symbol: str, days: int = 30) -> float:
    """
    Calculate average daily volume (in USD) for a symbol.

    Args:
        symbol: Symbol name
        days: Number of days to look back

    Returns:
        Average daily turnover in USD
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = load_historical_ohlcv(symbol, start_date, end_date, timeframe='1D')

        if len(df) == 0:
            return 0.0

        # Turnover is in USD (volume * price)
        avg_turnover = df['turnover'].mean()

        return avg_turnover

    except Exception as e:
        print(f"Error calculating volume for {symbol}: {e}")
        return 0.0


if __name__ == "__main__":
    # Test the data loader
    print("Testing data loader...")
    print("\n1. Getting available symbols...")
    symbols = get_available_symbols()
    print(f"Found {len(symbols)} symbols")
    print(f"First 10: {symbols[:10]}")

    print("\n2. Checking date range for BTCUSDT...")
    if 'BTCUSDT' in symbols:
        start, end = get_symbol_date_range('BTCUSDT')
        print(f"BTCUSDT data range: {start} to {end}")

        print("\n3. Loading BTCUSDT daily data (last 90 days)...")
        df = load_historical_ohlcv('BTCUSDT', timeframe='1D')
        print(f"Loaded {len(df)} days of data")
        print(df.head())
        print("\nData info:")
        print(df.info())

        print("\n4. Calculating average daily volume...")
        avg_vol = calculate_avg_daily_volume('BTCUSDT', days=30)
        print(f"Average daily volume (30d): ${avg_vol:,.2f}")
