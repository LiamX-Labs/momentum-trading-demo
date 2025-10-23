"""
Performance metrics calculation for backtest results.

Calculates standard trading metrics:
- Win rate, profit factor
- Sharpe ratio, max drawdown
- Average win/loss
- And more...
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass


def calculate_performance_metrics(
    trades: List,
    equity_curve: pd.DataFrame,
    daily_returns: pd.Series,
    initial_capital: float
) -> Dict:
    """
    Calculate comprehensive performance metrics.

    Args:
        trades: List of Trade objects
        equity_curve: DataFrame with equity history
        daily_returns: Series of daily returns
        initial_capital: Starting capital

    Returns:
        Dictionary with performance metrics
    """
    metrics = {}

    # Basic metrics
    metrics['total_trades'] = len(trades)

    if len(trades) == 0:
        return _empty_metrics()

    # Trade-based metrics
    winning_trades = [t for t in trades if t.return_pct > 0]
    losing_trades = [t for t in trades if t.return_pct <= 0]

    metrics['winning_trades'] = len(winning_trades)
    metrics['losing_trades'] = len(losing_trades)
    metrics['win_rate'] = len(winning_trades) / len(trades) if len(trades) > 0 else 0

    # Return metrics
    returns = [t.return_pct for t in trades]
    metrics['avg_return_pct'] = np.mean(returns) if returns else 0
    metrics['median_return_pct'] = np.median(returns) if returns else 0
    metrics['std_return_pct'] = np.std(returns) if returns else 0

    # Win/Loss metrics
    if winning_trades:
        metrics['avg_win_pct'] = np.mean([t.return_pct for t in winning_trades])
        metrics['max_win_pct'] = max([t.return_pct for t in winning_trades])
    else:
        metrics['avg_win_pct'] = 0
        metrics['max_win_pct'] = 0

    if losing_trades:
        metrics['avg_loss_pct'] = np.mean([t.return_pct for t in losing_trades])
        metrics['max_loss_pct'] = min([t.return_pct for t in losing_trades])
    else:
        metrics['avg_loss_pct'] = 0
        metrics['max_loss_pct'] = 0

    # Profit factor
    total_wins = sum([t.return_usd for t in winning_trades])
    total_losses = abs(sum([t.return_usd for t in losing_trades]))
    metrics['total_profit_usd'] = total_wins
    metrics['total_loss_usd'] = total_losses
    metrics['profit_factor'] = total_wins / total_losses if total_losses > 0 else np.inf

    # Holding period
    holding_days = [t.holding_days for t in trades]
    metrics['avg_holding_days'] = np.mean(holding_days) if holding_days else 0
    metrics['median_holding_days'] = np.median(holding_days) if holding_days else 0

    # Equity curve metrics
    if len(equity_curve) > 0:
        final_equity = equity_curve['equity'].iloc[-1]
        metrics['final_equity'] = final_equity
        metrics['total_return'] = (final_equity / initial_capital) - 1
        metrics['total_return_pct'] = metrics['total_return'] * 100

        # Drawdown
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['cummax']) / equity_curve['cummax']
        metrics['max_drawdown'] = equity_curve['drawdown'].min()
        metrics['max_drawdown_pct'] = metrics['max_drawdown'] * 100

    # Daily returns metrics
    if len(daily_returns) > 0:
        # Sharpe ratio (annualized, assuming 365 trading days in crypto)
        metrics['sharpe_ratio'] = (
            daily_returns.mean() / daily_returns.std() * np.sqrt(365)
            if daily_returns.std() > 0 else 0
        )

        # Sortino ratio (downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            metrics['sortino_ratio'] = (
                daily_returns.mean() / downside_returns.std() * np.sqrt(365)
            )
        else:
            metrics['sortino_ratio'] = 0

    # Exit reason breakdown
    exit_reasons = {}
    for trade in trades:
        reason = trade.exit_reason
        if reason not in exit_reasons:
            exit_reasons[reason] = 0
        exit_reasons[reason] += 1
    metrics['exit_reasons'] = exit_reasons

    # Symbol breakdown
    symbol_stats = {}
    for trade in trades:
        if trade.symbol not in symbol_stats:
            symbol_stats[trade.symbol] = {
                'trades': 0,
                'wins': 0,
                'total_return': 0
            }
        symbol_stats[trade.symbol]['trades'] += 1
        if trade.return_pct > 0:
            symbol_stats[trade.symbol]['wins'] += 1
        symbol_stats[trade.symbol]['total_return'] += trade.return_pct

    metrics['symbol_stats'] = symbol_stats

    return metrics


def _empty_metrics() -> Dict:
    """Return empty metrics dict when no trades."""
    return {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0,
        'avg_return_pct': 0,
        'avg_win_pct': 0,
        'avg_loss_pct': 0,
        'profit_factor': 0,
        'total_return': 0,
        'max_drawdown': 0,
        'sharpe_ratio': 0
    }


def generate_performance_report(metrics: Dict) -> str:
    """
    Generate formatted performance report.

    Args:
        metrics: Performance metrics dictionary

    Returns:
        Formatted report string
    """
    report = []
    report.append("="*80)
    report.append("PERFORMANCE REPORT")
    report.append("="*80)

    # Trading Activity
    report.append("\nTRADING ACTIVITY:")
    report.append(f"  Total Trades: {metrics.get('total_trades', 0)}")
    report.append(f"  Winning Trades: {metrics.get('winning_trades', 0)}")
    report.append(f"  Losing Trades: {metrics.get('losing_trades', 0)}")
    report.append(f"  Win Rate: {metrics.get('win_rate', 0)*100:.2f}%")

    # Returns
    report.append("\nRETURNS:")
    report.append(f"  Total Return: {metrics.get('total_return_pct', 0):.2f}%")
    report.append(f"  Average Return per Trade: {metrics.get('avg_return_pct', 0)*100:.2f}%")
    report.append(f"  Median Return per Trade: {metrics.get('median_return_pct', 0)*100:.2f}%")
    report.append(f"  Average Win: {metrics.get('avg_win_pct', 0)*100:.2f}%")
    report.append(f"  Average Loss: {metrics.get('avg_loss_pct', 0)*100:.2f}%")
    report.append(f"  Max Win: {metrics.get('max_win_pct', 0)*100:.2f}%")
    report.append(f"  Max Loss: {metrics.get('max_loss_pct', 0)*100:.2f}%")

    # Risk Metrics
    report.append("\nRISK METRICS:")
    report.append(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    report.append(f"  Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
    report.append(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    report.append(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")

    # Holding Period
    report.append("\nHOLDING PERIOD:")
    report.append(f"  Average: {metrics.get('avg_holding_days', 0):.1f} days")
    report.append(f"  Median: {metrics.get('median_holding_days', 0):.1f} days")

    # Exit Reasons
    if 'exit_reasons' in metrics:
        report.append("\nEXIT REASONS:")
        for reason, count in metrics['exit_reasons'].items():
            pct = count / metrics['total_trades'] * 100 if metrics['total_trades'] > 0 else 0
            report.append(f"  {reason}: {count} ({pct:.1f}%)")

    # Top Performers
    if 'symbol_stats' in metrics:
        report.append("\nTOP PERFORMING SYMBOLS:")
        symbol_stats = metrics['symbol_stats']
        sorted_symbols = sorted(
            symbol_stats.items(),
            key=lambda x: x[1]['total_return'],
            reverse=True
        )[:5]

        for symbol, stats in sorted_symbols:
            win_rate = stats['wins'] / stats['trades'] * 100 if stats['trades'] > 0 else 0
            report.append(f"  {symbol}: {stats['trades']} trades, {win_rate:.1f}% win rate, {stats['total_return']*100:.1f}% total return")

    report.append("\n" + "="*80)

    return "\n".join(report)


if __name__ == "__main__":
    # Test with dummy data
    from dataclasses import dataclass

    @dataclass
    class DummyTrade:
        symbol: str
        return_pct: float
        return_usd: float
        holding_days: int
        exit_reason: str

    trades = [
        DummyTrade('BTC', 0.15, 150, 5, 'trailing_stop'),
        DummyTrade('ETH', -0.08, -80, 3, 'trailing_stop'),
        DummyTrade('BTC', 0.25, 250, 8, 'ma_exit'),
        DummyTrade('SOL', -0.05, -50, 2, 'trailing_stop'),
        DummyTrade('BTC', 0.30, 300, 10, 'ma_exit'),
    ]

    equity_curve = pd.DataFrame({
        'equity': [10000, 10150, 10070, 10320, 10270, 10570]
    })

    daily_returns = pd.Series([0, 0.015, -0.008, 0.025, -0.005, 0.03])

    metrics = calculate_performance_metrics(trades, equity_curve, daily_returns, 10000)
    report = generate_performance_report(metrics)

    print(report)
    print("\n✓ Performance calculator working!")
