"""
Run full backtest on the asset universe.

This script:
1. Loads the asset universe
2. Runs backtest on all trading symbols
3. Calculates performance metrics
4. Generates detailed report
5. Saves results to CSV
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.assets import load_universe
from backtest.backtester import Backtester
from backtest.performance import calculate_performance_metrics, generate_performance_report


def run_full_backtest(
    initial_capital: float = 10000,
    backtest_days: int = 365,
    bbwidth_threshold: float = 0.25,
    rvr_threshold: float = 2.0,
    save_results: bool = True
):
    """
    Run full backtest on asset universe.

    Args:
        initial_capital: Starting capital (default: $10,000)
        backtest_days: Days to backtest (default: 365)
        bbwidth_threshold: BBWidth percentile threshold (default: 0.25)
        rvr_threshold: Minimum RVR (default: 2.0)
        save_results: Whether to save results to CSV (default: True)
    """
    print("="*80)
    print("VOLATILITY BREAKOUT MOMENTUM STRATEGY - BACKTEST")
    print("="*80)

    # Load universe
    print("\n1. Loading asset universe...")
    universe = load_universe()
    symbols = universe.get_trading_symbols()
    print(f"   Loaded {len(symbols)} trading symbols")

    # Set dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=backtest_days)

    print(f"\n2. Backtest period:")
    print(f"   Start: {start_date.date()}")
    print(f"   End: {end_date.date()}")
    print(f"   Days: {backtest_days}")

    # Initialize backtester
    print(f"\n3. Initializing backtester...")
    print(f"   Initial Capital: ${initial_capital:,.2f}")
    print(f"   Risk per Trade: 2%")
    print(f"   Stop Loss: 20%")
    print(f"   Max Positions: 5")

    backtester = Backtester(
        initial_capital=initial_capital,
        risk_per_trade_pct=0.02,
        stop_loss_pct=0.20,
        max_positions=5
    )

    # Run backtest
    print(f"\n4. Running backtest...")
    result = backtester.run(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        bbwidth_threshold=bbwidth_threshold,
        rvr_threshold=rvr_threshold
    )

    # Calculate metrics
    print("\n5. Calculating performance metrics...")
    metrics = calculate_performance_metrics(
        result.trades,
        result.equity_curve,
        result.daily_returns,
        initial_capital
    )

    # Generate report
    report = generate_performance_report(metrics)
    print(f"\n{report}")

    # Save results
    if save_results and len(result.trades) > 0:
        print("\n6. Saving results...")

        # Save trades
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                'symbol': trade.symbol,
                'entry_date': trade.entry_date,
                'entry_price': trade.entry_price,
                'exit_date': trade.exit_date,
                'exit_price': trade.exit_price,
                'position_size_usd': trade.position_size_usd,
                'return_pct': trade.return_pct,
                'return_usd': trade.return_usd,
                'holding_days': trade.holding_days,
                'exit_reason': trade.exit_reason,
                'peak_price': trade.peak_price,
                'max_adverse_excursion': trade.max_adverse_excursion
            })

        trades_df = pd.DataFrame(trades_data)
        trades_file = Path(__file__).parent / 'results' / 'backtest_trades.csv'
        trades_file.parent.mkdir(exist_ok=True)
        trades_df.to_csv(trades_file, index=False)
        print(f"   Saved trades to: {trades_file}")

        # Save equity curve
        equity_file = Path(__file__).parent / 'results' / 'equity_curve.csv'
        result.equity_curve.to_csv(equity_file, index=False)
        print(f"   Saved equity curve to: {equity_file}")

        # Save metrics
        metrics_df = pd.DataFrame([metrics])
        metrics_file = Path(__file__).parent / 'results' / 'performance_metrics.csv'
        metrics_df.to_csv(metrics_file, index=False)
        print(f"   Saved metrics to: {metrics_file}")

    print(f"\n{'='*80}")
    print("BACKTEST COMPLETE")
    print(f"{'='*80}\n")

    return result, metrics


if __name__ == "__main__":
    # Run backtest with different parameters

    print("Running baseline backtest (1 year)...")
    result, metrics = run_full_backtest(
        initial_capital=10000,
        backtest_days=365,
        bbwidth_threshold=0.25,
        rvr_threshold=2.0
    )

    # You can run sensitivity analysis here
    # print("\n\n" + "="*80)
    # print("SENSITIVITY ANALYSIS - BBWidth Threshold")
    # print("="*80)
    #
    # for threshold in [0.20, 0.25, 0.30]:
    #     print(f"\nTesting BBWidth threshold: {threshold*100:.0f}th percentile")
    #     result, metrics = run_full_backtest(
    #         initial_capital=10000,
    #         backtest_days=365,
    #         bbwidth_threshold=threshold,
    #         rvr_threshold=2.0,
    #         save_results=False
    #     )
    #     print(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
    #     print(f"Win Rate: {metrics.get('win_rate', 0)*100:.2f}%")
    #     print(f"Sharpe: {metrics.get('sharpe_ratio', 0):.2f}")
