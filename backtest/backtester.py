"""
Event-driven backtester for Volatility Breakout Momentum Strategy.

Simulates trading day-by-day across multiple assets with:
- Entry/exit signal evaluation
- Position management
- Risk controls
- Performance tracking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backtest.position_sizer import PositionSizer
from signals.entry_signals import generate_entry_signals
from signals.exit_signals import simulate_position_exit
from data.data_loader import load_historical_ohlcv, load_multiple_symbols


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    entry_date: datetime
    entry_index: int
    entry_price: float
    position_size_usd: float
    num_contracts: float
    peak_price: float
    peak_date: datetime

    def update_peak(self, price: float, date: datetime):
        """Update peak price if new high."""
        if price > self.peak_price:
            self.peak_price = price
            self.peak_date = date


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    entry_date: datetime
    entry_price: float
    exit_date: datetime
    exit_price: float
    position_size_usd: float
    num_contracts: float
    return_pct: float
    return_usd: float
    holding_days: int
    exit_reason: str
    peak_price: float
    max_adverse_excursion: float


@dataclass
class BacktestResult:
    """Container for backtest results."""
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    daily_returns: pd.Series = field(default_factory=pd.Series)
    metrics: Dict = field(default_factory=dict)
    config: Dict = field(default_factory=dict)


class Backtester:
    """
    Event-driven backtester for the strategy.
    """

    def __init__(
        self,
        initial_capital: float = 10000,
        risk_per_trade_pct: float = 0.02,
        stop_loss_pct: float = 0.20,
        max_positions: int = 5,
        commission_pct: float = 0.001,  # 0.1% per trade
        slippage_pct: float = 0.001,  # 0.1% slippage
        daily_loss_limit_pct: float = 0.03,  # 3% daily loss limit
        weekly_loss_limit_pct: float = 0.08  # 8% weekly loss limit triggers 50% size reduction
    ):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting account size
            risk_per_trade_pct: Risk per trade (default: 2%)
            stop_loss_pct: Stop loss percentage (default: 20%)
            max_positions: Max concurrent positions (default: 5)
            commission_pct: Commission per trade (default: 0.1%)
            slippage_pct: Slippage per trade (default: 0.1%)
            daily_loss_limit_pct: Daily loss limit (default: 3%)
            weekly_loss_limit_pct: Weekly loss limit for size reduction (default: 8%)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.risk_per_trade_pct = risk_per_trade_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_positions = max_positions
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.weekly_loss_limit_pct = weekly_loss_limit_pct

        # Position sizer
        self.sizer = PositionSizer(
            account_size=initial_capital,
            risk_per_trade_pct=risk_per_trade_pct,
            stop_loss_pct=stop_loss_pct,
            max_positions=max_positions
        )

        # Trading state
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_history: List[Dict] = []

        # Risk management tracking
        self.daily_start_capital = initial_capital
        self.weekly_start_capital = initial_capital
        self.current_date = None
        self.current_week = None
        self.size_multiplier = 1.0  # For weekly loss limit adjustment
        self.daily_trading_stopped = False

    def _check_daily_loss_limit(self, current_date: datetime) -> bool:
        """
        Check if daily loss limit has been hit.
        Returns True if trading should stop for the day.
        """
        if self.current_date != current_date:
            # New day - reset tracking
            self.current_date = current_date
            self.daily_start_capital = self.capital
            self.daily_trading_stopped = False

        if self.daily_trading_stopped:
            return True

        # Calculate current day's loss
        daily_loss_pct = (self.capital - self.daily_start_capital) / self.daily_start_capital

        if daily_loss_pct <= -self.daily_loss_limit_pct:
            self.daily_trading_stopped = True
            print(f"\n  [RISK] Daily loss limit hit ({daily_loss_pct*100:.2f}%). No new positions for today.")
            return True

        return False

    def _check_weekly_loss_limit(self, current_date: datetime):
        """
        Check if weekly loss limit has been hit.
        Reduces position size by 50% if weekly loss >= 8%.
        """
        current_week = current_date.isocalendar()[1]  # Week number

        if self.current_week != current_week:
            # New week - reset tracking
            self.current_week = current_week
            self.weekly_start_capital = self.capital
            self.size_multiplier = 1.0  # Reset multiplier

        # Calculate current week's loss
        weekly_loss_pct = (self.capital - self.weekly_start_capital) / self.weekly_start_capital

        if weekly_loss_pct <= -self.weekly_loss_limit_pct and self.size_multiplier == 1.0:
            self.size_multiplier = 0.5  # Reduce size by 50%
            print(f"\n  [RISK] Weekly loss limit hit ({weekly_loss_pct*100:.2f}%). Position size reduced by 50%.")

    def run(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        bbwidth_threshold: float = 0.25,
        rvr_threshold: float = 2.0,
        ma_period: int = 20,
        use_ma_exit: bool = True
    ) -> BacktestResult:
        """
        Run backtest across multiple symbols.

        Args:
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            bbwidth_threshold: BBWidth percentile threshold
            rvr_threshold: Minimum RVR for entry
            ma_period: MA period for trend/exit
            use_ma_exit: Use MA as exit signal

        Returns:
            BacktestResult with trades, equity curve, and metrics
        """
        print(f"\n{'='*80}")
        print(f"BACKTESTING: {len(symbols)} symbols from {start_date.date()} to {end_date.date()}")
        print(f"{'='*80}\n")

        # Load data for all symbols
        print("Loading historical data...")
        data = load_multiple_symbols(symbols, start_date, end_date, timeframe='1D')

        # Generate entry signals for all symbols
        print("\nGenerating entry signals...")
        signals = {}
        for symbol in symbols:
            if symbol not in data:
                continue
            signals[symbol] = generate_entry_signals(
                data[symbol],
                bbwidth_threshold=bbwidth_threshold,
                rvr_threshold=rvr_threshold,
                ma_period=ma_period
            )

        # Get all unique dates
        all_dates = set()
        for df in signals.values():
            all_dates.update(df['timestamp'].tolist())
        trading_days = sorted(all_dates)

        print(f"\nSimulating {len(trading_days)} trading days...")

        # Event-driven loop: day by day
        for day_idx, current_date in enumerate(trading_days):
            if day_idx % 50 == 0:
                print(f"  Day {day_idx}/{len(trading_days)}: {current_date.date()} | "
                      f"Equity: ${self.capital:,.2f} | Positions: {len(self.positions)}")

            # 1. Check exits for existing positions
            self._check_exits(current_date, data, ma_period, use_ma_exit)

            # 2. Check entries for new positions
            self._check_entries(current_date, signals, data)

            # 3. Update equity
            self._update_equity(current_date, data)

        # Close any remaining positions
        self._close_all_positions(end_date, data)

        # Generate results
        result = self._generate_results()

        print(f"\n{'='*80}")
        print("BACKTEST COMPLETE")
        print(f"{'='*80}\n")
        print(f"Total Trades: {len(self.trades)}")
        print(f"Final Equity: ${self.capital:,.2f}")
        print(f"Total Return: {((self.capital/self.initial_capital)-1)*100:.2f}%")

        return result

    def _check_exits(
        self,
        current_date: datetime,
        data: Dict[str, pd.DataFrame],
        ma_period: int,
        use_ma_exit: bool
    ):
        """Check exit conditions for all open positions."""
        from signals.exit_signals import check_exit_signal

        positions_to_close = []

        for symbol, position in self.positions.items():
            if symbol not in data:
                continue

            df = data[symbol]

            # Find current index
            try:
                current_idx = df[df['timestamp'] == current_date].index[0]
            except IndexError:
                continue

            # Update peak price
            current_price = df.iloc[current_idx]['high']
            position.update_peak(current_price, current_date)

            # Check exit
            exit_triggered, exit_details = check_exit_signal(
                df,
                entry_index=position.entry_index,
                current_index=current_idx,
                entry_price=position.entry_price,
                trailing_stop_pct=self.stop_loss_pct,
                ma_period=ma_period,
                use_ma_exit=use_ma_exit
            )

            if exit_triggered:
                positions_to_close.append((symbol, current_idx, exit_details))

        # Close positions
        for symbol, exit_idx, exit_details in positions_to_close:
            self._close_position(symbol, exit_idx, exit_details, data[symbol])

    def _check_entries(
        self,
        current_date: datetime,
        signals: Dict[str, pd.DataFrame],
        data: Dict[str, pd.DataFrame]
    ):
        """Check entry signals and open new positions."""
        # Check daily loss limit
        if self._check_daily_loss_limit(current_date):
            return  # Stop trading for the day

        # Check and update weekly loss limit
        self._check_weekly_loss_limit(current_date)

        # Can we open more positions?
        if len(self.positions) >= self.max_positions:
            return

        # Find signals for current date
        entry_opportunities = []

        for symbol, signal_df in signals.items():
            if symbol in self.positions:  # Already have position
                continue

            # Check if signal exists for this date
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

        # Sort by signal strength and take best opportunities
        entry_opportunities.sort(key=lambda x: x['strength'], reverse=True)

        # Open positions up to max
        slots_available = self.max_positions - len(self.positions)
        for opp in entry_opportunities[:slots_available]:
            self._open_position(opp['symbol'], opp['date'], opp['price'], data[opp['symbol']])

    def _open_position(
        self,
        symbol: str,
        entry_date: datetime,
        entry_price: float,
        df: pd.DataFrame
    ):
        """Open a new position."""
        # Apply slippage
        entry_price_with_slippage = entry_price * (1 + self.slippage_pct)

        # Calculate position size
        sizing = self.sizer.calculate_position_size(
            entry_price_with_slippage,
            current_positions=len(self.positions)
        )

        if not sizing['can_open']:
            return

        # Apply size multiplier (from weekly loss limit)
        sizing['position_size_usd'] *= self.size_multiplier
        sizing['num_contracts'] *= self.size_multiplier

        # Apply commission
        commission = sizing['position_size_usd'] * self.commission_pct
        net_position_size = sizing['position_size_usd'] - commission

        # Get entry index
        entry_idx = df[df['timestamp'] == entry_date].index[0]

        # Create position
        position = Position(
            symbol=symbol,
            entry_date=entry_date,
            entry_index=entry_idx,
            entry_price=entry_price_with_slippage,
            position_size_usd=net_position_size,
            num_contracts=sizing['num_contracts'],
            peak_price=entry_price_with_slippage,
            peak_date=entry_date
        )

        self.positions[symbol] = position

        # Update capital (deduct position size + commission)
        self.capital -= (sizing['position_size_usd'])

    def _close_position(
        self,
        symbol: str,
        exit_idx: int,
        exit_details: Dict,
        df: pd.DataFrame
    ):
        """Close an existing position."""
        position = self.positions[symbol]

        # Apply slippage to exit
        exit_price = exit_details['close'] * (1 - self.slippage_pct)

        # Calculate P&L
        price_return = (exit_price - position.entry_price) / position.entry_price
        gross_pnl = position.num_contracts * (exit_price - position.entry_price)

        # Apply commission on exit
        exit_commission = (position.num_contracts * exit_price) * self.commission_pct
        net_pnl = gross_pnl - exit_commission

        # Update capital
        position_value = position.num_contracts * exit_price
        self.capital += position_value - exit_commission

        # Create trade record
        trade = Trade(
            symbol=symbol,
            entry_date=position.entry_date,
            entry_price=position.entry_price,
            exit_date=exit_details['timestamp'],
            exit_price=exit_price,
            position_size_usd=position.position_size_usd,
            num_contracts=position.num_contracts,
            return_pct=price_return,
            return_usd=net_pnl,
            holding_days=exit_details['holding_days'],
            exit_reason=exit_details['exit_reason'],
            peak_price=position.peak_price,
            max_adverse_excursion=(df.iloc[position.entry_index:exit_idx+1]['low'].min() - position.entry_price) / position.entry_price
        )

        self.trades.append(trade)

        # Remove position
        del self.positions[symbol]

        # Update position sizer account size
        self.sizer.update_account_size(self.capital)

    def _update_equity(self, current_date: datetime, data: Dict[str, pd.DataFrame]):
        """Update equity based on current positions."""
        # Calculate total portfolio value
        positions_value = 0

        for symbol, position in self.positions.items():
            if symbol not in data:
                continue

            df = data[symbol]
            try:
                current_row = df[df['timestamp'] == current_date].iloc[0]
                current_price = current_row['close']
                position_value = position.num_contracts * current_price
                positions_value += position_value
            except:
                continue

        total_equity = self.capital + positions_value

        self.equity_history.append({
            'date': current_date,
            'equity': total_equity,
            'cash': self.capital,
            'positions_value': positions_value,
            'num_positions': len(self.positions)
        })

    def _close_all_positions(self, end_date: datetime, data: Dict[str, pd.DataFrame]):
        """Close all remaining positions at end of backtest."""
        for symbol in list(self.positions.keys()):
            position = self.positions[symbol]
            df = data[symbol]

            # Get last available price
            last_idx = len(df) - 1
            last_row = df.iloc[last_idx]

            exit_details = {
                'close': last_row['close'],
                'timestamp': last_row['timestamp'],
                'holding_days': last_idx - position.entry_index,
                'exit_reason': 'end_of_backtest'
            }

            self._close_position(symbol, last_idx, exit_details, df)

    def _generate_results(self) -> BacktestResult:
        """Generate backtest results."""
        # Convert equity history to DataFrame
        equity_df = pd.DataFrame(self.equity_history)

        if len(equity_df) > 0:
            equity_df['returns'] = equity_df['equity'].pct_change()
            daily_returns = equity_df['returns'].dropna()
        else:
            daily_returns = pd.Series()

        # Store config
        config = {
            'initial_capital': self.initial_capital,
            'risk_per_trade_pct': self.risk_per_trade_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'max_positions': self.max_positions,
            'commission_pct': self.commission_pct,
            'slippage_pct': self.slippage_pct
        }

        return BacktestResult(
            trades=self.trades,
            equity_curve=equity_df,
            daily_returns=daily_returns,
            config=config
        )


if __name__ == "__main__":
    # Test backtester
    from datetime import timedelta

    print("Testing Backtester...")

    symbols = ['DOGEUSDT', 'ENAUSDT']
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)

    backtester = Backtester(initial_capital=10000)

    result = backtester.run(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nTrades: {len(result.trades)}")
    if len(result.trades) > 0:
        print("\nFirst 5 trades:")
        for i, trade in enumerate(result.trades[:5]):
            print(f"  {i+1}. {trade.symbol}: {trade.return_pct*100:.2f}% in {trade.holding_days} days")

    print("\n✓ Backtester working!")
