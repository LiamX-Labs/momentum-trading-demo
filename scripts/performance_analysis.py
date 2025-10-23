"""
Daily and Weekly Performance Analysis Script.

Runs daily at 12:00 AM UTC to analyze trading performance.
On Mondays, also generates weekly performance summary.

Usage:
    python performance_analysis.py

Schedule with cron:
    0 0 * * * cd /path/to/momentum2 && python performance_analysis.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.trading_config import TradingConfig
from database.trade_logger import TradeLogger
from utils.telegram_alerts import TelegramAlerts


class PerformanceAnalyzer:
    """Analyzes trading performance and generates daily/weekly reports."""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.db = TradeLogger(config.database.db_path)
        self.telegram = TelegramAlerts(
            config.alerts.bot_token,
            config.alerts.chat_id
        ) if config.alerts.enabled else None

    def analyze_daily_performance(self) -> Dict:
        """Analyze performance for the last 24 hours."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        # Get trades from last 24 hours
        all_trades = self.db.get_all_trades()
        if not all_trades:
            return self._empty_daily_report()

        df = pd.DataFrame(all_trades)
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])

        # Filter for trades that closed in last 24 hours
        daily_trades = df[
            (df['exit_time'] >= yesterday) &
            (df['exit_time'] < now)
        ]

        if len(daily_trades) == 0:
            return self._empty_daily_report()

        # Calculate metrics
        total_trades = len(daily_trades)
        winners = daily_trades[daily_trades['return_pct'] > 0]
        losers = daily_trades[daily_trades['return_pct'] <= 0]

        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        total_pnl = daily_trades['return_usd'].sum()
        avg_win = winners['return_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['return_pct'].mean() if len(losers) > 0 else 0

        # Best and worst trades
        best_trade = daily_trades.loc[daily_trades['return_pct'].idxmax()] if len(daily_trades) > 0 else None
        worst_trade = daily_trades.loc[daily_trades['return_pct'].idxmin()] if len(daily_trades) > 0 else None

        return {
            'period': 'daily',
            'start_time': yesterday.isoformat(),
            'end_time': now.isoformat(),
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'best_trade': {
                'symbol': best_trade['symbol'],
                'return_pct': best_trade['return_pct'],
                'return_usd': best_trade['return_usd']
            } if best_trade is not None else None,
            'worst_trade': {
                'symbol': worst_trade['symbol'],
                'return_pct': worst_trade['return_pct'],
                'return_usd': worst_trade['return_usd']
            } if worst_trade is not None else None
        }

    def analyze_weekly_performance(self) -> Dict:
        """Analyze performance for the last 7 days."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        # Get trades from last 7 days
        all_trades = self.db.get_all_trades()
        if not all_trades:
            return self._empty_weekly_report()

        df = pd.DataFrame(all_trades)
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])

        # Filter for trades that closed in last 7 days
        weekly_trades = df[
            (df['exit_time'] >= week_ago) &
            (df['exit_time'] < now)
        ]

        if len(weekly_trades) == 0:
            return self._empty_weekly_report()

        # Calculate metrics
        total_trades = len(weekly_trades)
        winners = weekly_trades[weekly_trades['return_pct'] > 0]
        losers = weekly_trades[weekly_trades['return_pct'] <= 0]

        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        total_pnl = weekly_trades['return_usd'].sum()
        avg_win = winners['return_pct'].mean() if len(winners) > 0 else 0
        avg_loss = losers['return_pct'].mean() if len(losers) > 0 else 0

        # Profit factor
        gross_profit = winners['return_usd'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['return_usd'].sum()) if len(losers) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Best and worst trades
        best_trade = weekly_trades.loc[weekly_trades['return_pct'].idxmax()] if len(weekly_trades) > 0 else None
        worst_trade = weekly_trades.loc[weekly_trades['return_pct'].idxmin()] if len(weekly_trades) > 0 else None

        # Top symbols
        symbol_performance = weekly_trades.groupby('symbol').agg({
            'return_usd': 'sum',
            'symbol': 'count'
        }).rename(columns={'symbol': 'trades'})
        symbol_performance = symbol_performance.sort_values('return_usd', ascending=False)
        top_symbols = symbol_performance.head(5).to_dict('index')

        # Daily breakdown
        daily_pnl = weekly_trades.groupby(weekly_trades['exit_time'].dt.date)['return_usd'].sum()

        return {
            'period': 'weekly',
            'start_time': week_ago.isoformat(),
            'end_time': now.isoformat(),
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'best_trade': {
                'symbol': best_trade['symbol'],
                'return_pct': best_trade['return_pct'],
                'return_usd': best_trade['return_usd']
            } if best_trade is not None else None,
            'worst_trade': {
                'symbol': worst_trade['symbol'],
                'return_pct': worst_trade['return_pct'],
                'return_usd': worst_trade['return_usd']
            } if worst_trade is not None else None,
            'top_symbols': top_symbols,
            'daily_pnl': daily_pnl.to_dict()
        }

    def analyze_all_time_performance(self) -> Dict:
        """Analyze all-time performance statistics."""
        all_trades = self.db.get_all_trades()
        if not all_trades:
            return {}

        df = pd.DataFrame(all_trades)

        total_trades = len(df)
        winners = df[df['return_pct'] > 0]
        losers = df[df['return_pct'] <= 0]

        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        total_pnl = df['return_usd'].sum()

        return {
            'period': 'all_time',
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl_usd': total_pnl,
            'current_equity': self.db.get_current_equity()
        }

    def _empty_daily_report(self) -> Dict:
        """Return empty daily report."""
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        return {
            'period': 'daily',
            'start_time': yesterday.isoformat(),
            'end_time': now.isoformat(),
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'win_rate': 0,
            'total_pnl_usd': 0,
            'message': 'No trades closed in the last 24 hours'
        }

    def _empty_weekly_report(self) -> Dict:
        """Return empty weekly report."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        return {
            'period': 'weekly',
            'start_time': week_ago.isoformat(),
            'end_time': now.isoformat(),
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'win_rate': 0,
            'total_pnl_usd': 0,
            'message': 'No trades closed in the last 7 days'
        }

    def format_daily_report(self, metrics: Dict) -> str:
        """Format daily metrics as readable text."""
        if metrics.get('total_trades', 0) == 0:
            return f"📊 **Daily Performance Report**\n{metrics.get('message', 'No trades')}"

        report = f"""
📊 **Daily Performance Report** - {datetime.utcnow().strftime('%Y-%m-%d')}

**Trading Activity:**
  Trades: {metrics['total_trades']}
  Winners: {metrics['winners']} | Losers: {metrics['losers']}
  Win Rate: {metrics['win_rate']*100:.1f}%

**Returns:**
  Total P&L: ${metrics['total_pnl_usd']:,.2f}
  Avg Win: {metrics['avg_win_pct']:.2f}%
  Avg Loss: {metrics['avg_loss_pct']:.2f}%

**Highlights:**
"""

        if metrics.get('best_trade'):
            bt = metrics['best_trade']
            report += f"  Best: {bt['symbol']} +{bt['return_pct']:.2f}% (${bt['return_usd']:,.2f})\n"

        if metrics.get('worst_trade'):
            wt = metrics['worst_trade']
            report += f"  Worst: {wt['symbol']} {wt['return_pct']:.2f}% (${wt['return_usd']:,.2f})\n"

        return report.strip()

    def format_weekly_report(self, metrics: Dict) -> str:
        """Format weekly metrics as readable text."""
        if metrics.get('total_trades', 0) == 0:
            return f"📈 **Weekly Performance Report**\n{metrics.get('message', 'No trades')}"

        report = f"""
📈 **Weekly Performance Report** - Week ending {datetime.utcnow().strftime('%Y-%m-%d')}

**Trading Activity:**
  Trades: {metrics['total_trades']}
  Winners: {metrics['winners']} | Losers: {metrics['losers']}
  Win Rate: {metrics['win_rate']*100:.1f}%

**Returns:**
  Total P&L: ${metrics['total_pnl_usd']:,.2f}
  Gross Profit: ${metrics['gross_profit']:,.2f}
  Gross Loss: ${metrics['gross_loss']:,.2f}
  Profit Factor: {metrics['profit_factor']:.2f}

**Performance:**
  Avg Win: {metrics['avg_win_pct']:.2f}%
  Avg Loss: {metrics['avg_loss_pct']:.2f}%

**Top Performers:**
"""

        if metrics.get('top_symbols'):
            for symbol, data in list(metrics['top_symbols'].items())[:3]:
                report += f"  {symbol}: ${data['return_usd']:,.2f} ({int(data['trades'])} trades)\n"

        if metrics.get('best_trade'):
            bt = metrics['best_trade']
            report += f"\n**Best Trade:** {bt['symbol']} +{bt['return_pct']:.2f}% (${bt['return_usd']:,.2f})\n"

        return report.strip()

    def save_report(self, daily_metrics: Dict, weekly_metrics: Optional[Dict] = None):
        """Save performance reports to file."""
        reports_dir = Path(__file__).parent / 'reports'
        reports_dir.mkdir(exist_ok=True)

        # Save daily report
        daily_file = reports_dir / f"daily_{datetime.utcnow().strftime('%Y%m%d')}.json"
        with open(daily_file, 'w') as f:
            json.dump(daily_metrics, f, indent=2, default=str)

        # Save weekly report if Monday
        if weekly_metrics:
            weekly_file = reports_dir / f"weekly_{datetime.utcnow().strftime('%Y%m%d')}.json"
            with open(weekly_file, 'w') as f:
                json.dump(weekly_metrics, f, indent=2, default=str)

    def run(self):
        """Run performance analysis - called daily at 12 AM UTC."""
        print("="*80)
        print(f"PERFORMANCE ANALYSIS - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("="*80)

        # Daily analysis (always run)
        print("\nAnalyzing daily performance...")
        daily_metrics = self.analyze_daily_performance()
        daily_report = self.format_daily_report(daily_metrics)

        print(daily_report)

        # Send daily report via Telegram
        if self.telegram and self.config.alerts.send_daily_summary:
            self.telegram.send_message(daily_report)

        # Weekly analysis (only on Mondays)
        weekly_metrics = None
        if datetime.utcnow().weekday() == 0:  # Monday
            print("\n" + "="*80)
            print("WEEKLY ANALYSIS")
            print("="*80)

            weekly_metrics = self.analyze_weekly_performance()
            weekly_report = self.format_weekly_report(weekly_metrics)

            print(weekly_report)

            # Send weekly report via Telegram
            if self.telegram and self.config.alerts.send_weekly_summary:
                self.telegram.send_message(weekly_report)

        # All-time summary
        print("\n" + "="*80)
        print("ALL-TIME STATISTICS")
        print("="*80)
        all_time = self.analyze_all_time_performance()
        if all_time:
            print(f"Total Trades: {all_time['total_trades']}")
            print(f"Win Rate: {all_time['win_rate']*100:.1f}%")
            print(f"Total P&L: ${all_time['total_pnl_usd']:,.2f}")
            print(f"Current Equity: ${all_time['current_equity']:,.2f}")

        # Save reports
        self.save_report(daily_metrics, weekly_metrics)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)


if __name__ == "__main__":
    """Run performance analysis."""

    # Load configuration
    config = TradingConfig(fetch_capital_from_exchange=False)

    # Run analysis
    analyzer = PerformanceAnalyzer(config)
    analyzer.run()
