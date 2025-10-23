"""
Data validator for the Volatility Breakout Momentum Strategy.

Validates data quality, checks for gaps, and ensures data meets
requirements for backtesting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from .data_loader import get_available_symbols, get_symbol_date_range, load_historical_ohlcv


def validate_data_quality(df: pd.DataFrame, symbol: str = "Unknown") -> Dict:
    """
    Validate the quality of OHLCV data.

    Checks for:
    - Missing values
    - Price anomalies (negative prices, extreme jumps)
    - Volume anomalies
    - Timestamp gaps
    - OHLC consistency (high >= low, etc.)

    Args:
        df: DataFrame with OHLCV data
        symbol: Symbol name for reporting

    Returns:
        Dictionary with validation results
    """
    results = {
        'symbol': symbol,
        'total_rows': len(df),
        'passed': True,
        'warnings': [],
        'errors': []
    }

    # Check for empty dataframe
    if len(df) == 0:
        results['passed'] = False
        results['errors'].append("DataFrame is empty")
        return results

    # 1. Check for missing values
    missing = df.isnull().sum()
    if missing.any():
        for col, count in missing[missing > 0].items():
            pct = (count / len(df)) * 100
            msg = f"Column '{col}' has {count} missing values ({pct:.2f}%)"
            if pct > 5:
                results['errors'].append(msg)
                results['passed'] = False
            else:
                results['warnings'].append(msg)

    # 2. Check for negative prices
    price_cols = ['open', 'high', 'low', 'close']
    for col in price_cols:
        if col in df.columns:
            negative_count = (df[col] <= 0).sum()
            if negative_count > 0:
                results['errors'].append(f"Column '{col}' has {negative_count} negative/zero values")
                results['passed'] = False

    # 3. Check OHLC consistency
    if all(col in df.columns for col in price_cols):
        # High should be >= Low
        invalid_hl = (df['high'] < df['low']).sum()
        if invalid_hl > 0:
            results['errors'].append(f"Found {invalid_hl} rows where high < low")
            results['passed'] = False

        # High should be >= Open and Close
        invalid_ho = (df['high'] < df['open']).sum()
        invalid_hc = (df['high'] < df['close']).sum()
        if invalid_ho > 0 or invalid_hc > 0:
            results['warnings'].append(f"Found {invalid_ho + invalid_hc} rows where high < open/close")

        # Low should be <= Open and Close
        invalid_lo = (df['low'] > df['open']).sum()
        invalid_lc = (df['low'] > df['close']).sum()
        if invalid_lo > 0 or invalid_lc > 0:
            results['warnings'].append(f"Found {invalid_lo + invalid_lc} rows where low > open/close")

    # 4. Check for extreme price jumps (>50% in one period)
    if 'close' in df.columns and len(df) > 1:
        price_changes = df['close'].pct_change().abs()
        extreme_moves = (price_changes > 0.5).sum()
        if extreme_moves > 0:
            max_change = price_changes.max()
            results['warnings'].append(f"Found {extreme_moves} extreme price moves (>50%), max: {max_change:.2%}")

    # 5. Check for zero volume
    if 'volume' in df.columns:
        zero_vol = (df['volume'] == 0).sum()
        if zero_vol > 0:
            pct = (zero_vol / len(df)) * 100
            msg = f"Found {zero_vol} rows with zero volume ({pct:.2f}%)"
            if pct > 10:
                results['errors'].append(msg)
                results['passed'] = False
            else:
                results['warnings'].append(msg)

    # 6. Check timestamp gaps (for daily data)
    if 'timestamp' in df.columns and len(df) > 1:
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff()

        # For daily data, expect roughly 1 day between timestamps
        # Allow some flexibility for weekends/holidays
        expected_freq = pd.Timedelta(days=1)
        large_gaps = time_diffs[time_diffs > expected_freq * 3]  # Gaps > 3 days

        if len(large_gaps) > 0:
            results['warnings'].append(f"Found {len(large_gaps)} large time gaps (>3 days)")

    return results


def check_data_coverage(
    symbol: str,
    required_days: int = 90,
    end_date: Optional[datetime] = None
) -> Dict:
    """
    Check if a symbol has sufficient data coverage.

    Args:
        symbol: Symbol name
        required_days: Minimum number of days required
        end_date: Reference end date (default: today)

    Returns:
        Dictionary with coverage information
    """
    if end_date is None:
        end_date = datetime.now()

    start_date, available_end_date = get_symbol_date_range(symbol)

    if start_date is None:
        return {
            'symbol': symbol,
            'has_coverage': False,
            'days_available': 0,
            'required_days': required_days,
            'start_date': None,
            'end_date': None
        }

    # Calculate available days
    days_available = (available_end_date - start_date).days

    return {
        'symbol': symbol,
        'has_coverage': days_available >= required_days,
        'days_available': days_available,
        'required_days': required_days,
        'start_date': start_date,
        'end_date': available_end_date
    }


def scan_all_symbols(required_days: int = 90, min_volume_usd: float = 50_000_000) -> pd.DataFrame:
    """
    Scan all available symbols and return those meeting requirements.

    Args:
        required_days: Minimum days of historical data required
        min_volume_usd: Minimum average daily volume in USD

    Returns:
        DataFrame with symbol analysis including:
        - symbol, days_available, avg_daily_volume, data_quality, etc.
    """
    print("Scanning all symbols in datawarehouse...")
    symbols = get_available_symbols()
    print(f"Found {len(symbols)} total symbols\n")

    results = []

    for i, symbol in enumerate(symbols):
        if i % 20 == 0:
            print(f"Processing {i}/{len(symbols)} symbols...")

        # Check data coverage
        coverage = check_data_coverage(symbol, required_days)

        if not coverage['has_coverage']:
            continue

        # Load recent data to calculate volume
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            df = load_historical_ohlcv(symbol, start_date, end_date, timeframe='1D')

            if len(df) == 0:
                continue

            # Calculate average daily volume
            avg_volume = df['turnover'].mean()

            # Validate data quality
            validation = validate_data_quality(df, symbol)

            results.append({
                'symbol': symbol,
                'days_available': coverage['days_available'],
                'start_date': coverage['start_date'],
                'end_date': coverage['end_date'],
                'avg_daily_volume_usd': avg_volume,
                'data_quality_passed': validation['passed'],
                'warnings_count': len(validation['warnings']),
                'errors_count': len(validation['errors']),
                'recent_close': df['close'].iloc[-1] if len(df) > 0 else None
            })

        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            continue

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    if len(results_df) > 0:
        # Sort by average volume descending
        results_df = results_df.sort_values('avg_daily_volume_usd', ascending=False)

        # Filter by minimum volume
        results_df = results_df[results_df['avg_daily_volume_usd'] >= min_volume_usd]

    print(f"\n✓ Scan complete!")
    print(f"  Symbols with {required_days}+ days data: {len(results_df)}")
    print(f"  Symbols with ${min_volume_usd:,.0f}+ daily volume: {len(results_df)}")

    return results_df


def print_validation_report(validation: Dict):
    """
    Print a formatted validation report.

    Args:
        validation: Validation results dictionary
    """
    print(f"\n{'='*60}")
    print(f"Data Quality Report: {validation['symbol']}")
    print(f"{'='*60}")
    print(f"Total rows: {validation['total_rows']}")
    print(f"Status: {'✓ PASSED' if validation['passed'] else '✗ FAILED'}")

    if validation['errors']:
        print(f"\nErrors ({len(validation['errors'])}):")
        for error in validation['errors']:
            print(f"  ✗ {error}")

    if validation['warnings']:
        print(f"\nWarnings ({len(validation['warnings'])}):")
        for warning in validation['warnings']:
            print(f"  ! {warning}")

    if not validation['errors'] and not validation['warnings']:
        print("\n✓ No issues found")


if __name__ == "__main__":
    # Test the validator
    print("Testing data validator...")

    # Test individual symbol
    print("\n1. Testing individual symbol validation...")
    try:
        df = load_historical_ohlcv('BTCUSDT', timeframe='1D')
        validation = validate_data_quality(df, 'BTCUSDT')
        print_validation_report(validation)
    except Exception as e:
        print(f"Error: {e}")

    # Test coverage check
    print("\n2. Testing coverage check...")
    coverage = check_data_coverage('BTCUSDT', required_days=90)
    print(f"Symbol: {coverage['symbol']}")
    print(f"Has coverage: {coverage['has_coverage']}")
    print(f"Days available: {coverage['days_available']}")
    print(f"Date range: {coverage['start_date']} to {coverage['end_date']}")

    # Scan all symbols (commented out by default as it's slow)
    # print("\n3. Scanning all symbols...")
    # results_df = scan_all_symbols(required_days=90, min_volume_usd=50_000_000)
    # print("\nTop 20 by volume:")
    # print(results_df.head(20)[['symbol', 'avg_daily_volume_usd', 'days_available']])
