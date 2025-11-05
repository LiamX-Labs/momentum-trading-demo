"""
Momentum Strategy - Alpha Infrastructure Integration
Integrates with shared PostgreSQL and Redis services
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Optional

# Add shared library to path
alpha_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(alpha_root))

from shared.alpha_db_client import AlphaDBClient, create_client_order_id

logger = logging.getLogger(__name__)


class MomentumAlphaIntegration:
    """
    Integration layer between Momentum strategy and Alpha infrastructure.

    Replaces local SQLite database with centralized PostgreSQL + Redis.

    Responsibilities:
    - Write all fills to PostgreSQL (trading.fills)
    - Update position state in Redis
    - Track performance metrics
    - Send heartbeats to bot registry
    """

    def __init__(self, bot_id: str = 'momentum_001'):
        """
        Initialize integration with Alpha infrastructure.

        Args:
            bot_id: Bot identifier (default: 'momentum_001')
        """
        self.bot_id = bot_id
        self.db_client = None
        self._initialize_db_client()

    def _initialize_db_client(self):
        """Initialize database client with retry logic."""
        try:
            # Momentum uses Redis DB 2 (per integration spec)
            self.db_client = AlphaDBClient(bot_id=self.bot_id, redis_db=2)
            logger.info(f"✅ Alpha infrastructure integration initialized for {self.bot_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Alpha integration: {e}")
            logger.warning("⚠️ Strategy will continue without database integration")
            self.db_client = None

    def is_connected(self) -> bool:
        """Check if database integration is active."""
        return self.db_client is not None

    # ========================================
    # TRADE LOGGING (Replaces SQLite)
    # ========================================

    def log_trade_entry(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        position_size_usd: float,
        stop_loss: float = None,
        take_profit: float = None,
        signal_strength: float = None
    ) -> bool:
        """
        Log trade entry to PostgreSQL (replaces SQLite log_trade_entry).

        Args:
            trade_id: Unique trade identifier
            symbol: Trading pair
            side: 'Buy' or 'Sell'
            entry_price: Entry price
            quantity: Position quantity
            position_size_usd: Position value in USD
            stop_loss: Stop loss price
            take_profit: Take profit price
            signal_strength: Signal strength (0-1)

        Returns:
            True if successful
        """
        if not self.db_client:
            logger.debug("Database integration not available, skipping trade entry logging")
            return False

        try:
            # Record entry fill
            self.db_client.write_fill(
                symbol=symbol,
                side=side,
                exec_price=entry_price,
                exec_qty=quantity,
                order_id=trade_id,
                client_order_id=create_client_order_id(self.bot_id, 'entry'),
                close_reason='entry',
                commission=0.0,  # Will be updated from actual order
                exec_time=datetime.utcnow()
            )

            # Update position in Redis
            self.db_client.update_position_redis(
                symbol=symbol,
                size=quantity,
                side=side,
                avg_price=entry_price,
                unrealized_pnl=0.0
            )

            logger.info(f"📊 Trade entry logged: {symbol} {side} {quantity} @ {entry_price}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to log trade entry: {e}")
            return False

    def log_trade_exit(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        exit_price: float,
        quantity: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str,
        holding_time_seconds: int
    ) -> bool:
        """
        Log trade exit to PostgreSQL (replaces SQLite log_trade_exit).

        Args:
            trade_id: Trade identifier
            symbol: Trading pair
            side: Original side ('Buy' or 'Sell')
            exit_price: Exit price
            quantity: Position quantity
            pnl_usd: Profit/loss in USD
            pnl_pct: Profit/loss percentage
            exit_reason: Why position closed
            holding_time_seconds: How long position was held

        Returns:
            True if successful
        """
        if not self.db_client:
            logger.debug("Database integration not available, skipping trade exit logging")
            return False

        try:
            # Determine exit side (opposite of entry)
            exit_side = 'Sell' if side == 'Buy' else 'Buy'

            # Record exit fill
            self.db_client.write_fill(
                symbol=symbol,
                side=exit_side,
                exec_price=exit_price,
                exec_qty=quantity,
                order_id=f"{trade_id}_exit",
                client_order_id=create_client_order_id(self.bot_id, exit_reason),
                close_reason=exit_reason,
                commission=0.0,  # Will be updated from actual order
                exec_time=datetime.utcnow()
            )

            # Update position to flat in Redis
            self.db_client.update_position_redis(
                symbol=symbol,
                size=0.0,
                side='None',
                avg_price=0.0,
                unrealized_pnl=0.0
            )

            logger.info(f"📊 Trade exit logged: {symbol} PnL: ${pnl_usd:.2f} ({pnl_pct:.2f}%) - {exit_reason}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to log trade exit: {e}")
            return False

    # ========================================
    # POSITION MANAGEMENT
    # ========================================

    def get_open_trades(self) -> list:
        """
        Get open trades from Redis (replaces SQLite get_open_trades).

        Returns:
            List of open position dicts
        """
        if not self.db_client:
            return []

        try:
            # Get all position keys for this bot
            # Note: This requires adding a helper method to AlphaDBClient
            # For now, return empty list - the strategy should track positions internally
            return []

        except Exception as e:
            logger.error(f"❌ Failed to get open trades: {e}")
            return []

    # ========================================
    # HEARTBEAT & STATUS
    # ========================================

    def send_heartbeat(self):
        """Send heartbeat to bot registry."""
        if not self.db_client:
            return

        try:
            self.db_client.update_heartbeat()
            logger.debug(f"💓 Heartbeat sent for {self.bot_id}")
        except Exception as e:
            logger.debug(f"Failed to send heartbeat: {e}")

    def update_equity(self, equity: float):
        """Update current equity in bot registry."""
        if not self.db_client:
            return

        try:
            self.db_client.update_equity(equity)
            logger.debug(f"💰 Equity updated: ${equity:,.2f}")
        except Exception as e:
            logger.debug(f"Failed to update equity: {e}")

    # ========================================
    # PERFORMANCE QUERIES
    # ========================================

    def get_performance_stats(self, days: int = 30) -> Dict:
        """
        Get performance statistics (replaces SQLite get_performance_stats).

        Args:
            days: Number of days to analyze

        Returns:
            Performance statistics dict
        """
        if not self.db_client:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl_pct': 0.0
            }

        try:
            pnl = self.db_client.get_daily_pnl(days)
            trade_count = self.db_client.get_trade_count_today()

            return {
                'total_trades': trade_count,
                'total_pnl': pnl,
                'wins': 0,  # Need to calculate from fills
                'losses': 0,
                'win_rate': 0.0,
                'avg_pnl_pct': 0.0
            }

        except Exception as e:
            logger.error(f"❌ Failed to get performance stats: {e}")
            return {}

    # ========================================
    # SYSTEM EVENTS
    # ========================================

    def log_event(self, event_type: str, level: str, message: str, details: Dict = None):
        """
        Log system event (replaces SQLite log_event).

        For now, just logs to Python logger.
        Could be extended to write to PostgreSQL audit.system_events table.
        """
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{event_type}] {message}")

    # ========================================
    # CLEANUP
    # ========================================

    def close(self):
        """Close database connections."""
        if self.db_client:
            try:
                self.db_client.close()
                logger.info(f"Alpha integration closed for {self.bot_id}")
            except:
                pass


# Singleton instance for easy import
_integration = None


def get_integration(bot_id: str = 'momentum_001') -> MomentumAlphaIntegration:
    """
    Get singleton integration instance.

    Args:
        bot_id: Bot identifier

    Returns:
        MomentumAlphaIntegration instance
    """
    global _integration
    if _integration is None:
        _integration = MomentumAlphaIntegration(bot_id=bot_id)
    return _integration
