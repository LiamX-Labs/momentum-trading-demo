"""
Production Trade Database.

SQLite database for persistent storage of all trading activity.
Works identically for demo and live - mode is just a column.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import shutil


class TradeDatabase:
    """
    Production-ready trade logging database.

    Stores:
    - All trades with full details
    - Daily performance snapshots
    - System events and errors
    - Configuration changes
    """

    def __init__(self, db_path: str = 'data/trading.db'):
        """
        Initialize database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries

        self._create_tables()
        print(f"✓ Database initialized: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                mode TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_time TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                exit_time TIMESTAMP,
                exit_price REAL,
                quantity REAL NOT NULL,
                position_size_usd REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                pnl_usd REAL,
                pnl_pct REAL,
                exit_reason TEXT,
                holding_time_seconds INTEGER,
                signal_strength REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Daily snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE NOT NULL,
                mode TEXT NOT NULL,
                starting_equity REAL NOT NULL,
                ending_equity REAL NOT NULL,
                daily_pnl REAL NOT NULL,
                daily_pnl_pct REAL NOT NULL,
                trades_count INTEGER DEFAULT 0,
                wins_count INTEGER DEFAULT 0,
                losses_count INTEGER DEFAULT 0,
                open_positions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # System events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TIMESTAMP NOT NULL,
                event_type TEXT NOT NULL,
                event_level TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Risk events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_time TIMESTAMP NOT NULL,
                risk_type TEXT NOT NULL,
                current_value REAL NOT NULL,
                limit_value REAL NOT NULL,
                action_taken TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indices for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_mode ON trades(mode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_snapshots(date)')

        self.conn.commit()

    # ========== Trade Operations ==========

    def log_trade_entry(
        self,
        trade_id: str,
        mode: str,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        position_size_usd: float,
        stop_loss: float = None,
        take_profit: float = None,
        signal_strength: float = None
    ) -> int:
        """Log a new trade entry."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO trades (
                trade_id, mode, symbol, side, entry_time, entry_price,
                quantity, position_size_usd, stop_loss, take_profit, signal_strength
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_id, mode, symbol, side, datetime.now(),
            entry_price, quantity, position_size_usd,
            stop_loss, take_profit, signal_strength
        ))

        self.conn.commit()
        return cursor.lastrowid

    def log_trade_exit(
        self,
        trade_id: str,
        exit_price: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str,
        holding_time_seconds: int
    ):
        """Log trade exit."""
        cursor = self.conn.cursor()

        cursor.execute('''
            UPDATE trades
            SET exit_time = ?, exit_price = ?, pnl_usd = ?,
                pnl_pct = ?, exit_reason = ?, holding_time_seconds = ?
            WHERE trade_id = ?
        ''', (
            datetime.now(), exit_price, pnl_usd,
            pnl_pct, exit_reason, holding_time_seconds, trade_id
        ))

        self.conn.commit()

    def get_open_trades(self, mode: str = None) -> List[Dict]:
        """Get all open trades."""
        cursor = self.conn.cursor()

        if mode:
            cursor.execute('''
                SELECT * FROM trades
                WHERE exit_time IS NULL AND mode = ?
                ORDER BY entry_time DESC
            ''', (mode,))
        else:
            cursor.execute('''
                SELECT * FROM trades
                WHERE exit_time IS NULL
                ORDER BY entry_time DESC
            ''')

        return [dict(row) for row in cursor.fetchall()]

    def get_recent_trades(self, limit: int = 50, mode: str = None) -> List[Dict]:
        """Get recent closed trades."""
        cursor = self.conn.cursor()

        if mode:
            cursor.execute('''
                SELECT * FROM trades
                WHERE exit_time IS NOT NULL AND mode = ?
                ORDER BY exit_time DESC
                LIMIT ?
            ''', (mode, limit))
        else:
            cursor.execute('''
                SELECT * FROM trades
                WHERE exit_time IS NOT NULL
                ORDER BY exit_time DESC
                LIMIT ?
            ''', (limit,))

        return [dict(row) for row in cursor.fetchall()]

    # ========== Daily Snapshots ==========

    def save_daily_snapshot(
        self,
        date: str,
        mode: str,
        starting_equity: float,
        ending_equity: float,
        daily_pnl: float,
        daily_pnl_pct: float,
        trades_count: int,
        wins_count: int,
        losses_count: int,
        open_positions: int
    ):
        """Save daily performance snapshot."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO daily_snapshots (
                date, mode, starting_equity, ending_equity,
                daily_pnl, daily_pnl_pct, trades_count, wins_count,
                losses_count, open_positions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            date, mode, starting_equity, ending_equity,
            daily_pnl, daily_pnl_pct, trades_count, wins_count,
            losses_count, open_positions
        ))

        self.conn.commit()

    def get_daily_snapshots(self, days: int = 30, mode: str = None) -> List[Dict]:
        """Get recent daily snapshots."""
        cursor = self.conn.cursor()

        if mode:
            cursor.execute('''
                SELECT * FROM daily_snapshots
                WHERE mode = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (mode, days))
        else:
            cursor.execute('''
                SELECT * FROM daily_snapshots
                ORDER BY date DESC
                LIMIT ?
            ''', (days,))

        return [dict(row) for row in cursor.fetchall()]

    # ========== System Events ==========

    def log_event(
        self,
        event_type: str,
        level: str,
        message: str,
        details: Dict = None
    ):
        """
        Log a system event.

        Args:
            event_type: Type (SYSTEM_START, SYSTEM_STOP, TRADE, ERROR, etc.)
            level: Level (INFO, WARNING, ERROR, CRITICAL)
            message: Event message
            details: Additional details as dict
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO system_events (event_time, event_type, event_level, message, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now(), event_type, level, message,
            json.dumps(details) if details else None
        ))

        self.conn.commit()

    def get_recent_events(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Get recent system events."""
        cursor = self.conn.cursor()

        if level:
            cursor.execute('''
                SELECT * FROM system_events
                WHERE event_level = ?
                ORDER BY event_time DESC
                LIMIT ?
            ''', (level, limit))
        else:
            cursor.execute('''
                SELECT * FROM system_events
                ORDER BY event_time DESC
                LIMIT ?
            ''', (limit,))

        return [dict(row) for row in cursor.fetchall()]

    # ========== Risk Events ==========

    def log_risk_event(
        self,
        risk_type: str,
        current_value: float,
        limit_value: float,
        action_taken: str
    ):
        """Log a risk limit event."""
        cursor = self.conn.cursor()

        cursor.execute('''
            INSERT INTO risk_events (event_time, risk_type, current_value, limit_value, action_taken)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now(), risk_type, current_value, limit_value, action_taken))

        self.conn.commit()

    # ========== Statistics ==========

    def get_performance_stats(self, mode: str = None, days: int = None) -> Dict:
        """Get performance statistics."""
        cursor = self.conn.cursor()

        # Build query conditions
        conditions = ["exit_time IS NOT NULL"]
        params = []

        if mode:
            conditions.append("mode = ?")
            params.append(mode)

        if days:
            conditions.append("exit_time >= datetime('now', '-{} days')".format(days))

        where_clause = " AND ".join(conditions)

        # Get trades
        cursor.execute(f'''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_usd > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_usd < 0 THEN 1 ELSE 0 END) as losses,
                SUM(pnl_usd) as total_pnl,
                AVG(pnl_pct) as avg_pnl_pct,
                AVG(CASE WHEN pnl_usd > 0 THEN pnl_pct END) as avg_win_pct,
                AVG(CASE WHEN pnl_usd < 0 THEN pnl_pct END) as avg_loss_pct,
                MAX(pnl_usd) as best_trade,
                MIN(pnl_usd) as worst_trade,
                AVG(holding_time_seconds) as avg_holding_seconds
            FROM trades
            WHERE {where_clause}
        ''', params)

        row = cursor.fetchone()

        total_trades = row['total_trades'] or 0
        wins = row['wins'] or 0
        losses = row['losses'] or 0

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': wins / total_trades if total_trades > 0 else 0,
            'total_pnl': row['total_pnl'] or 0,
            'avg_pnl_pct': row['avg_pnl_pct'] or 0,
            'avg_win_pct': row['avg_win_pct'] or 0,
            'avg_loss_pct': row['avg_loss_pct'] or 0,
            'best_trade': row['best_trade'] or 0,
            'worst_trade': row['worst_trade'] or 0,
            'avg_holding_hours': (row['avg_holding_seconds'] or 0) / 3600
        }

    # ========== Backup & Maintenance ==========

    def backup(self, backup_path: str = None):
        """Create database backup."""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup_{timestamp}"

        shutil.copy2(self.db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        return backup_path

    def close(self):
        """Close database connection."""
        self.conn.close()


if __name__ == "__main__":
    """Test database."""
    import tempfile
    import os

    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
        test_db_path = tmp.name

    try:
        print("Testing Trade Database...\n")

        db = TradeDatabase(test_db_path)

        # Test trade entry
        print("1. Logging trade entry...")
        trade_id = f"TRADE_{datetime.now().timestamp()}"
        db.log_trade_entry(
            trade_id=trade_id,
            mode="demo",
            symbol="BTCUSDT",
            side="Buy",
            entry_price=45000,
            quantity=0.01,
            position_size_usd=450,
            stop_loss=40500,
            signal_strength=0.85
        )
        print("   ✓ Trade entry logged")

        # Test trade exit
        print("\n2. Logging trade exit...")
        db.log_trade_exit(
            trade_id=trade_id,
            exit_price=47000,
            pnl_usd=20,
            pnl_pct=0.044,
            exit_reason="Trailing Stop",
            holding_time_seconds=86400
        )
        print("   ✓ Trade exit logged")

        # Test statistics
        print("\n3. Getting performance stats...")
        stats = db.get_performance_stats(mode="demo")
        print(f"   Total Trades: {stats['total_trades']}")
        print(f"   Win Rate: {stats['win_rate']*100:.1f}%")
        print(f"   Total P&L: ${stats['total_pnl']:.2f}")

        # Test system event
        print("\n4. Logging system event...")
        db.log_event("TEST", "INFO", "Database test successful")
        print("   ✓ Event logged")

        # Test backup
        print("\n5. Testing backup...")
        backup_path = db.backup()
        print(f"   ✓ Backup created")

        db.close()
        print("\n✓ All database tests passed")

    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
        if 'backup_path' in locals() and os.path.exists(backup_path):
            os.unlink(backup_path)
