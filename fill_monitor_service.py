"""
Standalone Fill Monitor Service for Momentum Bot
Runs independently to monitor SELL fills and record trade closures
"""

import asyncio
import sys
import os

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.monitors.fill_monitor import FillMonitor


class SimpleTradingEngine:
    """Minimal trading engine interface for fill monitor"""
    def __init__(self):
        self.active_trades = {}
        self.breakeven_trades = {}


async def main():
    """Main entry point for fill monitor service"""
    print("🚀 Starting Fill Monitor Service for Momentum...")

    # Create minimal trading engine
    trading_engine = SimpleTradingEngine()

    # Initialize fill monitor
    fill_monitor = FillMonitor(
        trading_engine=trading_engine,
        bot_id='momentum_001',
        redis_db=2
    )

    # Start monitoring
    await fill_monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
