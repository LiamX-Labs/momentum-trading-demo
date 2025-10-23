"""
Asset universe configuration and selection.

This module handles selection of the trading universe based on:
- Data availability (90+ days)
- Liquidity ($50M+ daily volume)
- Data quality
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.data_validator import scan_all_symbols


class AssetUniverse:
    """
    Manages the trading asset universe.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize asset universe.

        Args:
            config_path: Path to universe.json config file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "universe.json"

        self.config_path = config_path
        self.assets = []
        self.metadata = {}

        if self.config_path.exists():
            self.load_from_file()

    def load_from_file(self):
        """Load universe from JSON config file."""
        with open(self.config_path, 'r') as f:
            data = json.load(f)

        self.assets = data.get('assets', [])
        self.metadata = data.get('metadata', {})

        print(f"Loaded {len(self.assets)} assets from {self.config_path}")

    def save_to_file(self):
        """Save universe to JSON config file."""
        data = {
            'metadata': self.metadata,
            'assets': self.assets
        }

        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        print(f"Saved {len(self.assets)} assets to {self.config_path}")

    def scan_and_select(
        self,
        num_assets: int = 20,
        required_days: int = 90,
        min_volume_usd: float = 50_000_000,
        include_btc: bool = True
    ):
        """
        Scan datawarehouse and select top assets by volume.

        Args:
            num_assets: Number of assets to select (excluding BTC if included)
            required_days: Minimum days of historical data
            min_volume_usd: Minimum average daily volume
            include_btc: Whether to include BTC for regime filter
        """
        print(f"\n{'='*60}")
        print("ASSET UNIVERSE SELECTION")
        print(f"{'='*60}")
        print(f"Requirements:")
        print(f"  - Historical data: {required_days}+ days")
        print(f"  - Daily volume: ${min_volume_usd:,.0f}+")
        print(f"  - Target count: {num_assets} assets")
        if include_btc:
            print(f"  - BTC included for regime filter")
        print()

        # Scan all symbols
        results_df = scan_all_symbols(required_days, min_volume_usd)

        if len(results_df) == 0:
            print("Error: No symbols meet the requirements")
            return

        # Filter for quality
        quality_df = results_df[results_df['data_quality_passed'] == True].copy()

        print(f"\nFiltering:")
        print(f"  Total symbols scanned: {len(results_df)}")
        print(f"  Symbols passing quality checks: {len(quality_df)}")

        # Ensure BTC is included if requested
        selected_assets = []

        if include_btc:
            btc_symbols = ['BTCUSDT', 'BTCUSD', 'BTC-USD', 'BTCPERP']
            btc_found = False

            for btc_sym in btc_symbols:
                if btc_sym in quality_df['symbol'].values:
                    selected_assets.append({
                        'symbol': btc_sym,
                        'role': 'regime_filter',
                        'avg_daily_volume_usd': float(quality_df[quality_df['symbol'] == btc_sym]['avg_daily_volume_usd'].iloc[0]),
                        'days_available': int(quality_df[quality_df['symbol'] == btc_sym]['days_available'].iloc[0])
                    })
                    btc_found = True
                    print(f"\n✓ Added {btc_sym} for regime filter")
                    # Remove from quality_df so it's not selected again
                    quality_df = quality_df[quality_df['symbol'] != btc_sym]
                    break

            if not btc_found:
                print("\nWarning: BTC not found in datawarehouse!")

        # Select top N assets by volume (excluding BTC)
        top_assets = quality_df.head(num_assets)

        print(f"\nTop {num_assets} assets by volume:")
        print(f"{'='*80}")
        print(f"{'Rank':<6} {'Symbol':<20} {'Avg Daily Volume':<20} {'Days':<10}")
        print(f"{'-'*80}")

        for i, row in enumerate(top_assets.itertuples(), 1):
            selected_assets.append({
                'symbol': row.symbol,
                'role': 'trading',
                'avg_daily_volume_usd': float(row.avg_daily_volume_usd),
                'days_available': int(row.days_available)
            })

            print(f"{i:<6} {row.symbol:<20} ${row.avg_daily_volume_usd:>17,.0f} {row.days_available:<10}")

        # Update the universe
        self.assets = selected_assets
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'selection_criteria': {
                'required_days': required_days,
                'min_volume_usd': min_volume_usd,
                'num_assets': num_assets,
                'include_btc': include_btc
            },
            'total_assets': len(selected_assets),
            'trading_assets': sum(1 for a in selected_assets if a['role'] == 'trading'),
            'regime_assets': sum(1 for a in selected_assets if a['role'] == 'regime_filter')
        }

        print(f"\n{'='*80}")
        print(f"✓ Selected {len(selected_assets)} total assets")
        print(f"  - Trading: {self.metadata['trading_assets']}")
        print(f"  - Regime filter: {self.metadata['regime_assets']}")

    def get_trading_symbols(self) -> List[str]:
        """Get list of symbols for trading (excluding regime filter)."""
        return [a['symbol'] for a in self.assets if a['role'] == 'trading']

    def get_regime_symbols(self) -> List[str]:
        """Get list of symbols for regime filtering."""
        return [a['symbol'] for a in self.assets if a['role'] == 'regime_filter']

    def get_all_symbols(self) -> List[str]:
        """Get all symbols."""
        return [a['symbol'] for a in self.assets]


def load_universe(config_path: Optional[Path] = None) -> AssetUniverse:
    """
    Load asset universe from config file.

    Args:
        config_path: Path to universe.json (default: ./universe.json)

    Returns:
        AssetUniverse instance
    """
    return AssetUniverse(config_path)


if __name__ == "__main__":
    # Run asset selection
    print("Starting asset universe selection...")

    universe = AssetUniverse()
    universe.scan_and_select(
        num_assets=20,
        required_days=90,
        min_volume_usd=50_000_000,
        include_btc=True
    )

    # Save to file
    universe.save_to_file()

    print("\n" + "="*60)
    print("FINAL UNIVERSE")
    print("="*60)
    print(f"\nTrading symbols ({len(universe.get_trading_symbols())}):")
    for symbol in universe.get_trading_symbols():
        print(f"  - {symbol}")

    print(f"\nRegime filter symbols ({len(universe.get_regime_symbols())}):")
    for symbol in universe.get_regime_symbols():
        print(f"  - {symbol}")

    print(f"\nConfig saved to: {universe.config_path}")
