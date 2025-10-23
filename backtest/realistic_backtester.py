"""
Realistic backtester using live Bybit API data.

Key differences from static backtest:
1. Universe updates dynamically (symbols come/go based on volume)
2. Uses live API data (not cached warehouse)
3. Checks symbol availability at each time point
4. Simulates real market conditions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.bybit_api import BybitDataFetcher, DynamicUniverseScanner
from backtest.backtester import Backtester, BacktestResult, Position, Trade
from backtest.position_sizer import PositionSizer
from signals.entry_signals import generate_entry_signals
from signals.exit_signals import check_exit_signal
from signals.btc_regime_filter import check_btc_regime, apply_regime_filter


class RealisticBacktester(Backtester):
    """
    Realistic backtester with dynamic universe and live API data.

    Extends the base backtester with:
    - Dynamic universe updates (weekly rebalancing)
    - Live API data fetching
    - Symbol availability checks
    - Real market condition simulation
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        risk_per_trade_pct: float = 0.02,
        stop_loss_pct: float = 0.20,
        max_positions: int = 5,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.001,
        min_volume_usd: float = 10_000_000,
        max_universe_size: int = 20,
        universe_update_days: int = 7,
        static_universe: Optional[List[str]] = None,
        daily_loss_limit_pct: float = 0.03,
        weekly_loss_limit_pct: float = 0.08
    ):
        """
        Initialize realistic backtester.

        Args:
            (inherited from Backtester)
            min_volume_usd: Minimum 24h volume for symbol selection
            max_universe_size: Maximum symbols in universe
            universe_update_days: Days between universe updates
            static_universe: Optional list of symbols for static universe (disables dynamic scanning)
            daily_loss_limit_pct: Daily loss limit (default: 3%)
            weekly_loss_limit_pct: Weekly loss limit for size reduction (default: 8%)
        """
        super().__init__(
            initial_capital, risk_per_trade_pct, stop_loss_pct,
            max_positions, commission_pct, slippage_pct,
            daily_loss_limit_pct, weekly_loss_limit_pct
        )

        self.min_volume_usd = min_volume_usd
        self.max_universe_size = max_universe_size
        self.universe_update_days = universe_update_days
        self.static_universe = static_universe

        # API and scanner
        self.api = BybitDataFetcher()

        # Only initialize scanner if not using static universe
        if static_universe is None:
            self.scanner = DynamicUniverseScanner(
                min_volume_usd=min_volume_usd,
                max_symbols=max_universe_size,
                update_frequency_days=universe_update_days
            )
        else:
            self.scanner = None

        # Track universe changes
        self.universe_history = []

    def run_realistic(
        self,
        start_date: datetime,
        end_date: datetime,
        bbwidth_threshold: float = 0.25,
        rvr_threshold: float = 2.0,
        ma_period: int = 20,
        lookback_period: int = 90,
        use_btc_regime_filter: bool = False,
        btc_ma_period: int = 50,
        btc_adx_threshold: float = 25.0,
        use_ma_exit: bool = True
    ) -> BacktestResult:
        """
        Run realistic backtest with dynamic universe.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            (other parameters same as base backtester)

        Returns:
            BacktestResult with trades and metrics
        """
        print(f"\n{'='*80}")
        print(f"REALISTIC BACKTEST: {start_date.date()} to {end_date.date()}")
        print(f"{'='*80}\n")

        print("Configuration:")
        if self.static_universe:
            print(f"  Universe Mode: STATIC (fixed token list)")
            print(f"  Universe Size: {len(self.static_universe)} symbols")
        else:
            print(f"  Universe Mode: DYNAMIC (scanned)")
            print(f"  Min Volume: ${self.min_volume_usd:,.0f}/day")
            print(f"  Max Universe Size: {self.max_universe_size}")
            print(f"  Universe Update: Every {self.universe_update_days} days")
        print(f"  Initial Capital: ${self.initial_capital:,.2f}\n")

        # Get universe updates for the period
        if self.static_universe:
            print(f"Using static universe: {len(self.static_universe)} symbols")
            # Create a single universe update that applies for the entire period
            universe_updates = {start_date: self.static_universe}
        else:
            print("Scanning universe history...")
            universe_updates = self.scanner.get_universe_for_period(start_date, end_date)

        # Create date-to-universe mapping
        update_dates = sorted(universe_updates.keys())

        # Fetch data for all symbols that appear in any universe
        all_symbols = set()
        for symbols in universe_updates.values():
            all_symbols.update(symbols)

        print(f"\nTotal unique symbols across period: {len(all_symbols)}")
        print("Fetching historical data from API...")

        # Fetch data with buffer for indicators (4h timeframe)
        # Need lookback_period (90) + some extra for calculations
        # Add 100 periods buffer to ensure we have enough data at backtest start
        buffer_periods = 100
        buffer_days = buffer_periods // 6  # Convert 4h periods to days (6 candles per day)
        data_start = start_date - timedelta(days=buffer_days)

        # Calculate required candles for full backtest period
        total_days = (end_date - data_start).days
        required_candles = total_days * 6 + 100  # 6 candles per day (4h) + small buffer

        print(f"Fetching {total_days} days of data (~{required_candles} 4h candles)...")
        if required_candles > 1000:
            print(f"Note: Will use pagination to fetch {required_candles} candles (> 1000 limit)")

        data = self.api.get_multiple_symbols_klines(
            list(all_symbols),
            interval='240',  # 4-hour timeframe
            start_time=data_start,
            end_time=end_date,
            limit=required_candles  # Pagination handled automatically
        )

        # Generate signals for all data
        print("\nGenerating entry signals...")
        signals = {}
        min_required_candles = lookback_period + ma_period + 10  # lookback + MA + small buffer
        for symbol in data.keys():
            if symbol not in data or len(data[symbol]) < min_required_candles:
                print(f"  Skipping {symbol}: insufficient data ({len(data.get(symbol, []))} < {min_required_candles} candles)")
                continue

            signals[symbol] = generate_entry_signals(
                data[symbol],
                bbwidth_threshold=bbwidth_threshold,
                rvr_threshold=rvr_threshold,
                ma_period=ma_period,
                lookback_period=lookback_period
            )

        # Apply BTC regime filter if enabled
        if use_btc_regime_filter:
            print("\nApplying BTC regime filter...")

            # Fetch BTC data on DAILY timeframe for regime filter
            print("  Fetching BTCUSDT data (daily timeframe for regime)...")
            btc_data = self.api.get_klines(
                'BTCUSDT',
                interval='D',  # Daily timeframe for BTC regime
                start_time=data_start,
                end_time=end_date,
                limit=total_days + 100  # Daily candles needed
            )

            if len(btc_data) > 0:
                print(f"  Retrieved {len(btc_data)} BTC candles")

                # Calculate BTC regime
                btc_regime = check_btc_regime(
                    btc_data,
                    ma_period=btc_ma_period,
                    adx_threshold=btc_adx_threshold
                )

                # Apply filter to each symbol's signals
                for symbol in signals.keys():
                    signals[symbol] = apply_regime_filter(
                        signals[symbol],
                        btc_regime,
                        ma_period=btc_ma_period,
                        adx_threshold=btc_adx_threshold
                    )
            else:
                print("  WARNING: Could not fetch BTC data, skipping regime filter")

        # Get all trading days
        all_dates = set()
        for df in signals.values():
            dates = df[df['timestamp'] >= start_date]['timestamp'].tolist()
            all_dates.update(dates)
        trading_days = sorted(all_dates)

        print(f"\nSimulating {len(trading_days)} trading days...")
        print(f"Universe will update {len(update_dates)} times\n")

        # Current universe
        current_universe = []
        next_update_idx = 0

        # Event-driven loop
        for day_idx, current_date in enumerate(trading_days):
            # Update universe if needed
            if next_update_idx < len(update_dates) and current_date >= update_dates[next_update_idx]:
                new_universe = universe_updates[update_dates[next_update_idx]]

                # Log universe change
                added = set(new_universe) - set(current_universe)
                removed = set(current_universe) - set(new_universe)

                if added or removed:
                    self.universe_history.append({
                        'date': current_date,
                        'universe': new_universe.copy(),
                        'added': list(added),
                        'removed': list(removed)
                    })

                    print(f"\n[{current_date.date()}] Universe Update:")
                    if added:
                        print(f"  + Added: {added}")
                    if removed:
                        print(f"  - Removed: {removed}")
                    print(f"  = Total: {len(new_universe)} symbols")

                current_universe = new_universe
                next_update_idx += 1

            if day_idx % 50 == 0:
                print(f"  Day {day_idx}/{len(trading_days)}: {current_date.date()} | "
                      f"Equity: ${self.capital:,.2f} | Positions: {len(self.positions)} | "
                      f"Universe: {len(current_universe)}")

            # Close positions for symbols no longer in universe
            self._check_universe_exits(current_date, current_universe, data, ma_period)

            # Check regular exits
            self._check_exits(current_date, data, ma_period, use_ma_exit)

            # Check entries (only from current universe)
            self._check_entries_filtered(current_date, signals, data, current_universe)

            # Update equity
            self._update_equity(current_date, data)

        # Close remaining positions
        self._close_all_positions(end_date, data)

        # Generate results
        result = self._generate_results()

        # Add universe history to result
        result.universe_changes = len(self.universe_history)

        print(f"\n{'='*80}")
        print("REALISTIC BACKTEST COMPLETE")
        print(f"{'='*80}\n")
        print(f"Universe Updates: {len(self.universe_history)}")
        print(f"Total Trades: {len(self.trades)}")
        print(f"Final Equity: ${self.capital:,.2f}")
        print(f"Total Return: {((self.capital/self.initial_capital)-1)*100:.2f}%")

        return result

    def _check_universe_exits(
        self,
        current_date: datetime,
        current_universe: List[str],
        data: Dict[str, pd.DataFrame],
        ma_period: int
    ):
        """Exit positions for symbols removed from universe."""
        positions_to_close = []

        for symbol in list(self.positions.keys()):
            if symbol not in current_universe:
                # Symbol removed from universe, must exit
                if symbol not in data:
                    continue

                df = data[symbol]
                try:
                    current_idx = df[df['timestamp'] == current_date].index[0]
                except IndexError:
                    continue

                # Create exit details
                exit_details = {
                    'close': df.iloc[current_idx]['close'],
                    'timestamp': current_date,
                    'holding_days': current_idx - self.positions[symbol].entry_index,
                    'exit_reason': 'removed_from_universe'
                }

                positions_to_close.append((symbol, current_idx, exit_details))

        # Close positions
        for symbol, exit_idx, exit_details in positions_to_close:
            print(f"  [EXIT] {symbol} removed from universe")
            self._close_position(symbol, exit_idx, exit_details, data[symbol])

    def _check_entries_filtered(
        self,
        current_date: datetime,
        signals: Dict[str, pd.DataFrame],
        data: Dict[str, pd.DataFrame],
        current_universe: List[str]
    ):
        """Check entry signals only for symbols in current universe."""
        if len(self.positions) >= self.max_positions:
            return

        entry_opportunities = []

        for symbol, signal_df in signals.items():
            # Only consider symbols in current universe
            if symbol not in current_universe:
                continue

            if symbol in self.positions:
                continue

            # Check for signal
            signal_rows = signal_df[
                (signal_df['timestamp'] == current_date) &
                (signal_df['entry_signal'] == True)
            ]

            if len(signal_rows) > 0:
                signal_row = signal_rows.iloc[0]
                entry_opportunities.append({
                    'symbol': symbol,
                    'date': current_date,
                    'price': signal_row['close'],
                    'strength': signal_row['signal_strength']
                })

        # Sort by strength and open positions
        entry_opportunities.sort(key=lambda x: x['strength'], reverse=True)

        slots_available = self.max_positions - len(self.positions)
        for opp in entry_opportunities[:slots_available]:
            print(f"  [ENTRY] {opp['symbol']} @ ${opp['price']:.6f} (strength: {opp['strength']:.2%})")
            self._open_position(opp['symbol'], opp['date'], opp['price'], data[opp['symbol']])


if __name__ == "__main__":
    # Test realistic backtester
    print("Testing Realistic Backtester...\n")

    # Run shorter test (3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    backtester = RealisticBacktester(
        initial_capital=10000,
        min_volume_usd=20_000_000,  # Higher threshold for test
        max_universe_size=10,  # Smaller universe for faster test
        universe_update_days=14  # Update every 2 weeks
    )

    result = backtester.run_realistic(
        start_date=start_date,
        end_date=end_date
    )

    print(f"\n✓ Realistic backtester operational!")
    print(f"\nTrades executed: {len(result.trades)}")

    if len(result.trades) > 0:
        print("\nTrade summary:")
        for i, trade in enumerate(result.trades[:5], 1):
            print(f"  {i}. {trade.symbol}: {trade.return_pct*100:+.2f}% "
                  f"({trade.holding_days} days, {trade.exit_reason})")
