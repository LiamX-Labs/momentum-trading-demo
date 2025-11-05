"""
PRODUCTION TRADING SYSTEM

Unified system for demo and live trading.
Mode is controlled by config - no code changes needed.

To switch from demo to live:
1. Change TRADING_MODE in config/trading_config.py
2. Set LIVE API credentials in .env
3. That's it - everything else stays the same
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, time as dt_time
import time
import signal as sys_signal
import json
from typing import Dict, List
import pandas as pd

sys.path.append(str(Path(__file__).parent))

# Import all production components
from config.trading_config import config, TradingMode
from exchange.bybit_exchange import BybitExchange
from alerts.telegram_bot import TelegramBot
from database.trade_database import TradeDatabase
from integration.alpha_integration import get_integration
from signals.entry_signals import generate_entry_signals
from signals.exit_signals import check_exit_signal
from signals.btc_regime_filter import check_btc_regime
from backtest.position_sizer import PositionSizer


class TradingSystem:
    """
    Production Trading System.

    Features:
    - Automatic demo/live switching via config
    - Complete trade logging to database
    - Telegram alerts for all events
    - Multi-level risk management
    - Position tracking and management
    - Health monitoring
    - Graceful shutdown
    """

    def __init__(self):
        """Initialize trading system."""
        print("\n" + "="*80)
        print("INITIALIZING TRADING SYSTEM")
        print("="*80 + "\n")

        # Print configuration
        config.print_summary()

        # Initialize components
        self._init_exchange()
        self._init_telegram()
        self._init_database()
        self._init_position_sizer()

        # Load trading universe
        self._load_universe()

        # Initialize state
        self.capital = config.risk.initial_capital
        self.positions: Dict = {}  # symbol -> position_info
        self.daily_start_capital = self.capital
        self.weekly_start_capital = self.capital
        self.monthly_start_capital = self.capital
        self.size_multiplier = 1.0
        self.daily_trading_stopped = False
        self.system_halted = False

        # Tracking
        self.current_date = None
        self.current_week = None
        self.current_month = None
        self.running = False

        # Signal handler for graceful shutdown
        sys_signal.signal(sys_signal.SIGINT, self._signal_handler)
        sys_signal.signal(sys_signal.SIGTERM, self._signal_handler)

        print("\n✓ Trading system initialized successfully\n")

    def _init_exchange(self):
        """Initialize exchange connection."""
        print("Connecting to exchange...")
        self.exchange = BybitExchange(
            mode=config.TRADING_MODE,
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            base_url=config.exchange.base_url
        )

        # Health check
        health = self.exchange.health_check()
        if not health['healthy']:
            raise Exception(f"Exchange health check failed: {health['issues']}")

        print("✓ Exchange connected and healthy")

    def _init_telegram(self):
        """Initialize Telegram bot."""
        if config.alerts.enabled:
            print("Initializing Telegram bot...")
            self.telegram = TelegramBot(
                bot_token=config.alerts.bot_token,
                chat_id=config.alerts.chat_id
            )
            print("✓ Telegram bot ready")
        else:
            self.telegram = None
            print("⚠ Telegram alerts disabled")

    def _init_database(self):
        """Initialize database."""
        if config.database.enabled:
            print("Connecting to database...")
            self.db = TradeDatabase(config.database.db_path)

            # Alpha infrastructure integration
            self.alpha_integration = get_integration(bot_id='momentum_001')
            print(f"Alpha integration status: {'✅ Connected' if self.alpha_integration.is_connected() else '⚠️ Not connected'}")
            print("✓ Database connected")
        else:
            self.db = None
            print("⚠ Database disabled")

    def _init_position_sizer(self):
        """Initialize position sizer."""
        self.sizer = PositionSizer(
            account_size=config.risk.initial_capital,
            risk_per_trade_pct=config.risk.risk_per_trade_pct,
            stop_loss_pct=config.risk.stop_loss_pct,
            max_positions=config.risk.max_positions
        )

    def _load_universe(self):
        """Load trading universe."""
        universe_path = Path(__file__).parent / config.strategy.universe_file
        with open(universe_path, 'r') as f:
            universe_config = json.load(f)
            self.universe = universe_config['tokens']

        print(f"✓ Loaded universe: {len(self.universe)} tokens")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\n⚠️  Shutdown signal received")
        self.stop()

    # ========== Risk Management ==========

    def check_risk_limits(self) -> bool:
        """
        Check all risk limits.
        Returns True if trading should stop.
        """
        current_date = datetime.now().date()

        # Daily limit
        if self.current_date != current_date:
            self.current_date = current_date
            self.daily_start_capital = self.capital
            self.daily_trading_stopped = False

        if self.daily_trading_stopped:
            return True

        daily_loss_pct = (self.capital - self.daily_start_capital) / self.daily_start_capital

        if daily_loss_pct <= -config.risk.daily_loss_limit_pct:
            self.daily_trading_stopped = True
            self._handle_risk_event("DAILY_LOSS_LIMIT", daily_loss_pct, config.risk.daily_loss_limit_pct)
            return True

        # Weekly limit
        current_week = datetime.now().isocalendar()[1]
        if self.current_week != current_week:
            self.current_week = current_week
            self.weekly_start_capital = self.capital
            self.size_multiplier = 1.0

        weekly_loss_pct = (self.capital - self.weekly_start_capital) / self.weekly_start_capital

        if weekly_loss_pct <= -config.risk.weekly_loss_limit_pct and self.size_multiplier == 1.0:
            self.size_multiplier = 0.5
            self._handle_risk_event("WEEKLY_LOSS_LIMIT", weekly_loss_pct, config.risk.weekly_loss_limit_pct)

        # Monthly limit
        current_month = datetime.now().month
        if self.current_month != current_month:
            self.current_month = current_month
            self.monthly_start_capital = self.capital

        monthly_loss_pct = (self.capital - self.monthly_start_capital) / self.monthly_start_capital

        if monthly_loss_pct <= -config.risk.monthly_loss_limit_pct:
            self.system_halted = True
            self._handle_risk_event("MONTHLY_LOSS_LIMIT", monthly_loss_pct, config.risk.monthly_loss_limit_pct)
            return True

        # Max drawdown check
        # TODO: Implement drawdown tracking

        return False

    def _handle_risk_event(self, risk_type: str, current_value: float, limit_value: float):
        """Handle risk limit breach."""
        action = ""
        if risk_type == "DAILY_LOSS_LIMIT":
            action = "No new positions today"
            if self.telegram:
                self.telegram.alert_daily_loss_limit(current_value, limit_value)
        elif risk_type == "WEEKLY_LOSS_LIMIT":
            action = "Position size reduced 50%"
            if self.telegram:
                self.telegram.alert_weekly_loss_limit(current_value, limit_value)
        elif risk_type == "MONTHLY_LOSS_LIMIT":
            action = "Trading halted for month"
            if self.telegram:
                self.telegram.send_message(
                    f"🛑 <b>MONTHLY LOSS LIMIT</b>\n\nLoss: {current_value:.2%}\nLimit: {limit_value:.2%}\n\n⛔ Trading HALTED"
                )

        if self.db:
            self.db.log_risk_event(risk_type, current_value, limit_value, action)

        print(f"\n⚠️  {risk_type}: {current_value:.2%} (limit: {limit_value:.2%})")
        print(f"   Action: {action}")

    # ========== Trading Logic ==========

    def scan_for_signals(self) -> List[Dict]:
        """Scan universe for entry signals."""
        signals = []

        # BTC regime filter
        if config.strategy.use_btc_regime_filter:
            try:
                btc_data = self.exchange.get_kline(
                    'BTCUSDT',
                    interval='D',
                    limit=config.strategy.btc_ma_period + 50
                )
                btc_df = self._format_kline_data(btc_data)
                btc_regime = check_btc_regime(
                    btc_df,
                    ma_period=config.strategy.btc_ma_period,
                    adx_threshold=config.strategy.btc_adx_threshold
                )

                if not btc_regime.iloc[-1]['btc_regime_favorable']:
                    print("  BTC regime filter: Not active. Skipping signals.")
                    return []
            except Exception as e:
                print(f"  Error checking BTC regime: {e}")
                return []

        # Scan each symbol
        for symbol in self.universe:
            if symbol in self.positions:
                continue

            try:
                klines = self.exchange.get_kline(
                    symbol,
                    interval=config.strategy.timeframe,
                    limit=config.strategy.lookback_period + 50
                )
                df = self._format_kline_data(klines)

                if len(df) < config.strategy.lookback_period:
                    continue

                signal_df = generate_entry_signals(
                    df,
                    bbwidth_threshold=config.strategy.bbwidth_threshold,
                    rvr_threshold=config.strategy.rvr_threshold,
                    ma_period=config.strategy.ma_period,
                    lookback_period=config.strategy.lookback_period
                )

                latest = signal_df.iloc[-1]
                if latest['entry_signal']:
                    signals.append({
                        'symbol': symbol,
                        'price': latest['close'],
                        'signal_strength': latest['signal_strength'],
                        'timestamp': datetime.now()
                    })

            except Exception as e:
                print(f"  Error scanning {symbol}: {e}")
                continue

        signals.sort(key=lambda x: x['signal_strength'], reverse=True)
        return signals

    def execute_entry(self, signal: Dict) -> bool:
        """Execute entry order."""
        symbol = signal['symbol']
        price = signal['price']

        try:
            # Calculate position size
            sizing = self.sizer.calculate_position_size(
                entry_price=price,
                current_positions=len(self.positions)
            )

            if not sizing['can_open']:
                return False

            # Apply size multiplier
            position_size = sizing['position_size_usd'] * self.size_multiplier
            quantity = sizing['num_contracts'] * self.size_multiplier
            initial_stop_loss = price * (1 - config.risk.stop_loss_pct)
            trailing_stop_distance = price * config.risk.stop_loss_pct

            # Place market order with trailing stop
            # The exchange will automatically set the trailing stop after order fills
            order = self.exchange.place_order(
                symbol=symbol,
                side="Buy",
                order_type="Market",
                qty=quantity,
                trailing_stop=trailing_stop_distance,  # Trailing stop distance (not percentage)
                position_idx=0  # One-way mode
            )

            # Check if trailing stop was set successfully
            if order.get('trailing_stop_set'):
                print(f"  ✓ Trailing stop set: {config.risk.stop_loss_pct*100}% (${trailing_stop_distance:.4f})")
            elif 'trailing_stop_error' in order:
                print(f"  ⚠️  Warning: Trailing stop failed - {order['trailing_stop_error']}")
                # Try to set fixed stop loss as fallback
                try:
                    self.exchange.set_trading_stop(
                        symbol=symbol,
                        stop_loss=initial_stop_loss,
                        category="linear",
                        position_idx=0
                    )
                    print(f"  ✓ Fixed stop loss set as fallback: ${initial_stop_loss:.4f}")
                except Exception as e:
                    print(f"  ✗ Could not set any stop loss: {e}")

            # Track position
            trade_id = f"{symbol}_{int(datetime.now().timestamp())}"
            self.positions[symbol] = {
                'trade_id': trade_id,
                'entry_price': price,
                'entry_time': datetime.now(),
                'quantity': quantity,
                'position_size_usd': position_size,
                'stop_loss': initial_stop_loss,
                'trailing_stop_distance': trailing_stop_distance,
                'peak_price': price,
                'order_id': order.get('orderId')
            }

            # Log to database
            if self.db:
                self.db.log_trade_entry(
                    trade_id=trade_id,
                    mode=config.TRADING_MODE.value,
                    symbol=symbol,
                    side="Buy",
                    entry_price=price,
                    quantity=quantity,
                    position_size_usd=position_size,
                    stop_loss=initial_stop_loss,
                    signal_strength=signal['signal_strength']
                )

            # 🔥 ALPHA INTEGRATION: Also log to PostgreSQL/Redis
            if hasattr(self, 'alpha_integration') and self.alpha_integration.is_connected():
                self.alpha_integration.log_trade_entry(
                    trade_id=trade_id,
                    symbol=symbol,
                    side="Buy",
                    entry_price=price,
                    quantity=quantity,
                    position_size_usd=position_size,
                    stop_loss=initial_stop_loss,
                    signal_strength=signal['signal_strength']
                )

            # Send alert
            if self.telegram:
                self.telegram.alert_position_opened(
                    symbol=symbol,
                    side="Buy",
                    entry_price=price,
                    quantity=quantity,
                    position_size_usd=position_size,
                    order_id=order.get('orderId')
                )

            print(f"  ✓ ENTRY: {symbol} @ ${price:,.4f} (${position_size:,.2f})")
            return True

        except Exception as e:
            print(f"  ✗ Entry failed for {symbol}: {e}")
            if self.telegram:
                self.telegram.alert_error("Entry Execution", str(e), symbol)
            return False

    def check_exits(self):
        """
        Check position status and execute exit signals.

        Exit priority:
        1. MA Exit - Price crosses below MA (primary exit, ~71% of trades)
        2. Exchange Trailing Stop - 10% from peak (backup protection, ~29% of trades)
        3. Manual checks for exchange-closed positions
        """
        for symbol in list(self.positions.keys()):
            try:
                position = self.positions[symbol]

                # Get current market data for MA calculation
                if config.strategy.use_ma_exit:
                    try:
                        klines = self.exchange.get_kline(
                            symbol,
                            interval=config.strategy.timeframe,
                            limit=config.strategy.ma_period + 10
                        )
                        df = self._format_kline_data(klines)

                        if len(df) >= config.strategy.ma_period:
                            # Calculate MA
                            from indicators.moving_averages import calculate_sma
                            df = calculate_sma(df, config.strategy.ma_period)

                            current_price = float(df.iloc[-1]['close'])
                            current_ma = df.iloc[-1][f'sma_{config.strategy.ma_period}']

                            # Check MA exit condition
                            if not pd.isna(current_ma) and current_price < current_ma:
                                print(f"  {symbol}: MA exit triggered (Price: ${current_price:.4f} < MA: ${current_ma:.4f})")
                                self._close_position(symbol, current_price, "MA Exit")
                                continue  # Skip to next position

                    except Exception as e:
                        print(f"  Warning: Could not check MA exit for {symbol}: {e}")
                        # Continue to check exchange position even if MA check fails

                # Check if position still exists on exchange
                exchange_positions = self.exchange.get_positions(symbol=symbol)

                # If position was closed by exchange (e.g., trailing stop hit)
                if not exchange_positions or float(exchange_positions[0].get('size', 0)) == 0:
                    # Position closed by exchange - fetch final price and record exit
                    ticker = self.exchange.get_ticker(symbol)
                    current_price = float(ticker['lastPrice'])
                    print(f"  {symbol}: Closed by exchange (trailing stop)")
                    self._close_position(symbol, current_price, "Exchange Stop Loss")
                else:
                    # Position still open - update peak for monitoring
                    ticker = self.exchange.get_ticker(symbol)
                    current_price = float(ticker['lastPrice'])

                    if current_price > position['peak_price']:
                        position['peak_price'] = current_price
                        profit_pct = ((current_price / position['entry_price']) - 1) * 100
                        print(f"  {symbol}: New peak ${current_price:,.4f} (+{profit_pct:.2f}%)")

            except Exception as e:
                print(f"  Error checking exit for {symbol}: {e}")

    def _close_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Close a position."""
        try:
            position = self.positions[symbol]

            # Close on exchange (if not already closed)
            if exit_reason != "Exchange Stop Loss":
                # Position still open on exchange, close it
                self.exchange.close_position(symbol, qty=position['quantity'])
            # else: Position already closed by exchange (trailing stop hit)

            # Calculate P&L
            pnl_pct = (exit_price / position['entry_price']) - 1
            pnl_usd = position['position_size_usd'] * pnl_pct
            self.capital += pnl_usd

            holding_time = (datetime.now() - position['entry_time']).total_seconds()

            # Log to database
            if self.db:
                self.db.log_trade_exit(
                    trade_id=position['trade_id'],
                    exit_price=exit_price,
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason,
                    holding_time_seconds=int(holding_time)
                )

            # 🔥 ALPHA INTEGRATION: Also log exit to PostgreSQL/Redis
            if hasattr(self, 'alpha_integration') and self.alpha_integration.is_connected():
                self.alpha_integration.log_trade_exit(
                    trade_id=position['trade_id'],
                    symbol=symbol,
                    side="Buy",  # Original entry side
                    exit_price=exit_price,
                    quantity=position['quantity'],
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason,
                    holding_time_seconds=int(holding_time)
                )

            # Send alert
            if self.telegram:
                self.telegram.alert_position_closed(
                    symbol=symbol,
                    entry_price=position['entry_price'],
                    exit_price=exit_price,
                    quantity=position['quantity'],
                    pnl_usd=pnl_usd,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason,
                    holding_time=str(timedelta(seconds=int(holding_time)))
                )

            del self.positions[symbol]

            print(f"  ✓ EXIT: {symbol} @ ${exit_price:,.4f} | P&L: ${pnl_usd:+,.2f} ({pnl_pct:+.2%})")

        except Exception as e:
            print(f"  ✗ Exit failed for {symbol}: {e}")
            if self.telegram:
                self.telegram.alert_error("Exit Execution", str(e), symbol)

    def _format_kline_data(self, klines: List) -> pd.DataFrame:
        """Format kline data to DataFrame."""
        if not klines:
            return pd.DataFrame()

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = df[col].astype(float)

        return df.sort_values('timestamp').reset_index(drop=True)

    # ========== Main Trading Loop ==========

    def run_once(self):
        """Execute one trading iteration."""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running trading loop...")

        # Check risk limits
        if self.check_risk_limits() or self.system_halted:
            print("  Trading stopped due to risk limits")
            return

        # Check exits
        if self.positions:
            print(f"  Checking exits ({len(self.positions)} positions)...")
            self.check_exits()

        # Check entries
        if len(self.positions) < config.risk.max_positions:
            print(f"  Scanning for signals...")
            signals = self.scan_for_signals()

            if signals:
                print(f"  Found {len(signals)} signals")
                slots = config.risk.max_positions - len(self.positions)

                for signal in signals[:slots]:
                    self.execute_entry(signal)
            else:
                print("  No signals found")
        else:
            print(f"  Max positions reached ({config.risk.max_positions})")

        print(f"  Capital: ${self.capital:,.2f} | Positions: {len(self.positions)}")

    def start(self):
        """Start trading system."""
        print("\n" + "="*80)
        print(f"{config.get_mode_display()} - STARTING")
        print("="*80 + "\n")

        # Log system start
        if self.db:
            self.db.log_event("SYSTEM_START", "INFO", f"Trading system started in {config.TRADING_MODE.value} mode")

        # Send Telegram notification
        if self.telegram:
            exchange_name = "Bybit Demo" if config.TRADING_MODE == TradingMode.DEMO else "Bybit Live"
            self.telegram.alert_system_start(
                config={
                    "Capital": f"${self.capital:,.2f}",  # Use actual capital (from exchange or config)
                    "Max Positions": config.risk.max_positions,
                    "Position Size": f"{config.risk.risk_per_trade_pct*100}%"
                },
                mode=config.TRADING_MODE.value,
                exchange=exchange_name
            )

        self.running = True
        print("✓ System started. Press Ctrl+C to stop\n")

        # Main loop
        self._run_loop()

    def _run_loop(self):
        """Main trading loop."""
        iteration = 0
        exit_check_interval = 300  # Check exits every 5 minutes when positions are open

        while self.running:
            iteration += 1
            print(f"\n{'='*80}")
            print(f"ITERATION {iteration} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"{'='*80}")

            try:
                self.run_once()
            except Exception as e:
                print(f"\n❌ Error in trading loop: {e}")
                if self.telegram:
                    self.telegram.alert_error("Trading Loop", str(e))
                if self.db:
                    self.db.log_event("ERROR", "ERROR", f"Trading loop error: {e}")

            # Wait for next interval
            if self.running:
                next_check = self._calculate_next_check_time()
                wait_seconds = (next_check - datetime.utcnow()).total_seconds()

                if wait_seconds > 0:
                    print(f"\n💤 Next full scan: {next_check.strftime('%Y-%m-%d %H:%M:%S')} UTC")

                    # Sleep in small chunks for responsive shutdown
                    # If we have positions, wake up periodically to check exits
                    while self.running and datetime.utcnow() < next_check:
                        remaining = (next_check - datetime.utcnow()).total_seconds()
                        if remaining > 0:
                            # If we have positions, check exits more frequently
                            if self.positions:
                                sleep_duration = min(remaining, exit_check_interval)
                                if sleep_duration > 0:
                                    print(f"   (Monitoring {len(self.positions)} position(s), next exit check in {int(sleep_duration)}s)")
                                    time.sleep(sleep_duration)
                                    # Check exits after waking up (if not time for full scan yet)
                                    if self.running and datetime.utcnow() < next_check and self.positions:
                                        print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Checking exits...")
                                        try:
                                            self.check_exits()
                                        except Exception as e:
                                            print(f"  Error checking exits: {e}")
                            else:
                                # No positions, sleep longer
                                time.sleep(min(remaining, 60))

    def _calculate_next_check_time(self) -> datetime:
        """
        Calculate next check time aligned with UTC candles.

        4H candles open at: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
        """
        now = datetime.utcnow()  # Use UTC time
        interval_hours = config.strategy.check_interval_hours

        # Find next interval hour (aligned with UTC)
        next_hour = ((now.hour // interval_hours) + 1) * interval_hours

        if next_hour >= 24:
            next_check = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            next_check = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)

        return next_check

    def stop(self):
        """Stop trading system."""
        self.running = False

        print("\n" + "="*80)
        print(f"{config.get_mode_display()} - STOPPING")
        print("="*80)

        # Close all positions
        if self.positions:
            print(f"\nClosing {len(self.positions)} open positions...")
            for symbol in list(self.positions.keys()):
                try:
                    ticker = self.exchange.get_ticker(symbol)
                    price = float(ticker['lastPrice'])
                    self._close_position(symbol, price, "System Shutdown")
                except Exception as e:
                    print(f"Error closing {symbol}: {e}")

        # Log final state
        if self.db:
            stats = self.db.get_performance_stats(mode=config.TRADING_MODE.value)
            self.db.log_event("SYSTEM_STOP", "INFO", "Trading system stopped", stats)

        # Send notification
        if self.telegram:
            self.telegram.alert_system_stop()

        print(f"\nFinal Capital: ${self.capital:,.2f}")
        print(f"Total P&L: ${self.capital - config.risk.initial_capital:+,.2f}")
        print("\n✓ System stopped\n")


if __name__ == "__main__":
    """Run trading system."""
    try:
        system = TradingSystem()
        system.start()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'system' in locals():
            system.stop()
