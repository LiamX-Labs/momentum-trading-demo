"""
Production Trading Configuration System.

Centralized configuration for demo/live trading with environment-based switching.
All parameters controlled from this file - no code changes needed to switch modes.
"""

import os
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


def load_env_file(env_path: Path):
    """Load environment variables from .env file manually."""
    if not env_path.exists():
        return

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value


# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_env_file(env_path)


class TradingMode(Enum):
    """Trading mode: DEMO or LIVE."""
    DEMO = "demo"
    LIVE = "live"


@dataclass
class ExchangeConfig:
    """Exchange API configuration."""
    mode: TradingMode
    api_key: str
    api_secret: str
    base_url: str

    @classmethod
    def from_env(cls, mode: TradingMode):
        """Load from environment variables."""
        if mode == TradingMode.DEMO:
            return cls(
                mode=mode,
                api_key=os.getenv('BYBIT_DEMO_API_KEY', ''),
                api_secret=os.getenv('BYBIT_DEMO_API_SECRET', ''),
                base_url='https://api-demo.bybit.com'
            )
        else:  # LIVE
            return cls(
                mode=mode,
                api_key=os.getenv('BYBIT_LIVE_API_KEY', ''),
                api_secret=os.getenv('BYBIT_LIVE_API_SECRET', ''),
                base_url='https://api.bybit.com'
            )


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position sizing
    initial_capital: float = 10000
    risk_per_trade_pct: float = 0.05  # 5% per trade
    max_positions: int = 3
    stop_loss_pct: float = 0.10  # 10% trailing stop

    # Loss limits
    daily_loss_limit_pct: float = 0.03  # -3% daily limit
    weekly_loss_limit_pct: float = 0.08  # -8% weekly limit
    monthly_loss_limit_pct: float = 0.15  # -15% monthly limit

    # Drawdown protection
    max_drawdown_pct: float = 0.20  # Stop trading at -20% drawdown

    # Fees
    commission_pct: float = 0.001  # 0.1% per trade
    slippage_pct: float = 0.001  # 0.1% estimated slippage

    def scale_for_live(self, live_capital: float):
        """Scale parameters for live trading."""
        self.initial_capital = live_capital
        # Keep percentages the same, but can add live-specific adjustments here


@dataclass
class StrategyConfig:
    """Trading strategy parameters."""
    # Signal generation
    bbwidth_threshold: float = 0.35  # 35th percentile
    rvr_threshold: float = 2.0
    ma_period: int = 20
    lookback_period: int = 90

    # BTC regime filter
    use_btc_regime_filter: bool = False
    btc_ma_period: int = 200
    btc_adx_threshold: float = 25.0

    # Timeframe
    timeframe: str = '240'  # 4-hour candles
    check_interval_hours: int = 4

    # Universe
    universe_file: str = 'config/static_universe.json'

    # Exit rules
    use_ma_exit: bool = True
    use_trailing_stop: bool = True


@dataclass
class AlertConfig:
    """Telegram alert configuration."""
    enabled: bool = True
    bot_token: str = ''
    chat_id: str = ''

    # Alert settings
    send_entry_signals: bool = True
    send_exit_signals: bool = True
    send_daily_summary: bool = True
    send_weekly_summary: bool = True
    send_errors: bool = True

    # Summary times (UTC)
    daily_summary_hour: int = 20  # 8 PM UTC
    weekly_summary_day: int = 6  # Sunday

    @classmethod
    def from_env(cls):
        """Load from environment variables."""
        return cls(
            enabled=os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true',
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            chat_id=os.getenv('TELEGRAM_CHAT_ID', '')
        )


@dataclass
class DatabaseConfig:
    """Database configuration for trade logging."""
    enabled: bool = True
    db_path: str = 'data/trading.db'
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class MonitoringConfig:
    """System monitoring configuration."""
    health_check_interval_minutes: int = 5
    log_level: str = 'INFO'  # DEBUG, INFO, WARNING, ERROR
    log_file: str = 'logs/trading.log'
    max_log_size_mb: int = 100
    log_retention_days: int = 30


class TradingConfig:
    """
    Master configuration class.

    Change TRADING_MODE to switch between demo and live.
    All other settings apply to both modes.
    """

    # ========================================
    # MAIN SWITCH: Change this to go live
    # ========================================
    TRADING_MODE = TradingMode.DEMO  # or TradingMode.LIVE

    def __init__(self, fetch_capital_from_exchange: bool = True):
        """
        Initialize all configurations.

        Args:
            fetch_capital_from_exchange: If True, fetches actual balance from exchange.
                                        If False, uses configured initial_capital.
        """
        # Exchange
        self.exchange = ExchangeConfig.from_env(self.TRADING_MODE)

        # Risk management
        self.risk = RiskConfig()

        # Fetch capital from exchange if requested
        if fetch_capital_from_exchange:
            try:
                capital = self._fetch_capital_from_exchange()
                if capital is not None:
                    self.risk.initial_capital = capital
                    print(f"✓ Fetched capital from exchange: ${capital:,.2f}")
            except Exception as e:
                print(f"⚠️  Could not fetch capital from exchange: {e}")
                print(f"   Using configured capital: ${self.risk.initial_capital:,.2f}")

        # Strategy
        self.strategy = StrategyConfig()

        # Alerts
        self.alerts = AlertConfig.from_env()

        # Database
        self.database = DatabaseConfig()

        # Monitoring
        self.monitoring = MonitoringConfig()

        # Validate configuration
        self._validate()

    def _fetch_capital_from_exchange(self) -> Optional[float]:
        """
        Fetch available capital from exchange.

        Returns:
            Available USDT balance, or None if failed
        """
        try:
            # Lazy import to avoid circular dependency
            from exchange.bybit_exchange import BybitExchange

            # Create temporary exchange connection
            exchange = BybitExchange(
                mode=self.TRADING_MODE,
                api_key=self.exchange.api_key,
                api_secret=self.exchange.api_secret,
                base_url=self.exchange.base_url
            )

            # Get wallet balance
            balance = exchange.get_wallet_balance()

            # Extract USDT balance from unified account
            if 'list' in balance and len(balance['list']) > 0:
                account = balance['list'][0]
                if 'coin' in account:
                    for coin_info in account['coin']:
                        if coin_info['coin'] == 'USDT':
                            # Use available balance (equity - used margin)
                            # Handle empty strings from API
                            available_str = coin_info.get('availableToWithdraw', '0')
                            equity_str = coin_info.get('equity', '0')

                            # Convert, handling empty strings
                            available = float(available_str) if available_str and available_str != '' else 0.0
                            equity = float(equity_str) if equity_str and equity_str != '' else 0.0

                            # Return equity (total balance including positions)
                            return equity if equity > 0 else available

            return None

        except Exception as e:
            raise Exception(f"Failed to fetch balance: {str(e)}")

    def _validate(self):
        """Validate configuration before running."""
        errors = []

        # Check exchange credentials
        if not self.exchange.api_key:
            errors.append(f"{self.TRADING_MODE.value.upper()}: Missing API key")
        if not self.exchange.api_secret:
            errors.append(f"{self.TRADING_MODE.value.upper()}: Missing API secret")

        # Check Telegram if enabled
        if self.alerts.enabled:
            if not self.alerts.bot_token:
                errors.append("Telegram enabled but missing bot token")
            if not self.alerts.chat_id:
                errors.append("Telegram enabled but missing chat ID")

        # Validate risk parameters
        if self.risk.risk_per_trade_pct <= 0 or self.risk.risk_per_trade_pct > 0.2:
            errors.append(f"Risk per trade {self.risk.risk_per_trade_pct*100}% is outside safe range (0-20%)")

        if self.risk.max_positions < 1 or self.risk.max_positions > 10:
            errors.append(f"Max positions {self.risk.max_positions} is outside reasonable range (1-10)")

        # Live mode specific checks
        if self.TRADING_MODE == TradingMode.LIVE:
            if self.risk.initial_capital < 100:
                errors.append(f"Live capital ${self.risk.initial_capital} seems too low")

        if errors:
            raise ValueError(
                "Configuration validation failed:\n" +
                "\n".join(f"  - {err}" for err in errors)
            )

    def is_demo(self) -> bool:
        """Check if running in demo mode."""
        return self.TRADING_MODE == TradingMode.DEMO

    def is_live(self) -> bool:
        """Check if running in live mode."""
        return self.TRADING_MODE == TradingMode.LIVE

    def get_mode_display(self) -> str:
        """Get displayable mode string."""
        if self.is_demo():
            return "🟡 DEMO TRADING"
        else:
            return "🔴 LIVE TRADING"

    def print_summary(self):
        """Print configuration summary."""
        print("="*80)
        print(f"TRADING SYSTEM CONFIGURATION")
        print("="*80)
        print(f"\nMode: {self.get_mode_display()}")
        print(f"Exchange: Bybit ({self.exchange.base_url})")
        print(f"\nCapital: ${self.risk.initial_capital:,.2f}")
        print(f"Position Size: {self.risk.risk_per_trade_pct*100}% per trade")
        print(f"Max Positions: {self.risk.max_positions}")
        print(f"Stop Loss: {self.risk.stop_loss_pct*100}%")
        print(f"\nRisk Limits:")
        print(f"  Daily: {self.risk.daily_loss_limit_pct*100}%")
        print(f"  Weekly: {self.risk.weekly_loss_limit_pct*100}%")
        print(f"  Monthly: {self.risk.monthly_loss_limit_pct*100}%")
        print(f"  Max Drawdown: {self.risk.max_drawdown_pct*100}%")
        print(f"\nStrategy:")
        print(f"  BBWidth Threshold: {self.strategy.bbwidth_threshold*100:.0f}th percentile")
        print(f"  RVR Threshold: {self.strategy.rvr_threshold}x")
        print(f"  Timeframe: {self.strategy.timeframe} ({self.strategy.check_interval_hours}h check)")
        print(f"  BTC Regime Filter: {'ON' if self.strategy.use_btc_regime_filter else 'OFF'}")
        if self.strategy.use_btc_regime_filter:
            print(f"    - MA: {self.strategy.btc_ma_period} days")
            print(f"    - ADX: {self.strategy.btc_adx_threshold}")
        print(f"\nAlerts: {'✓ Enabled' if self.alerts.enabled else '✗ Disabled'}")
        if self.alerts.enabled:
            print(f"  Chat ID: {self.alerts.chat_id}")
        print(f"\nDatabase: {'✓ Enabled' if self.database.enabled else '✗ Disabled'}")
        if self.database.enabled:
            print(f"  Path: {self.database.db_path}")
        print("\n" + "="*80)

        # Warning for live mode
        if self.is_live():
            print("\n⚠️  WARNING: LIVE TRADING MODE ⚠️")
            print("Real money will be used. Ensure all settings are correct.")
            print("="*80 + "\n")


# Global config instance
config = TradingConfig()


if __name__ == "__main__":
    """Test configuration."""
    try:
        config.print_summary()
        print("\n✓ Configuration valid and ready")
    except ValueError as e:
        print(f"\n❌ Configuration Error:\n{e}")
        print("\nPlease fix configuration before running.")
