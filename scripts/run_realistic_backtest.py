"""
Run realistic backtest using live Bybit API data.

This script runs a backtest that closely simulates real trading:
- Dynamic universe (symbols added/removed based on volume)
- Live API data from Bybit
- Symbol availability checks
- Real market conditions

Compare this to the static backtest to see the difference.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.realistic_backtester import RealisticBacktester
from backtest.performance import calculate_performance_metrics, generate_performance_report


def run_realistic_backtest(
    initial_capital: float = 10000,
    backtest_months: int = 10,
    min_volume_usd: float = 10_000_000,
    max_universe_size: int = 40,
    universe_update_days: int = 3,
    bbwidth_threshold: float = 0.25,
    rvr_threshold: float = 2.0,
    ma_period: int = 20,  # Same as daily - 20 periods on 4h
    bb_period: int = 20,  # Same as daily - 20 periods on 4h
    lookback_period: int = 90,  # Same as daily - 90 periods on 4h
    save_results: bool = True,
    use_static_universe: bool = False,
    static_universe_file: str = "config/static_universe.json"
):
    """
    Run realistic backtest with live API data.

    Args:
        initial_capital: Starting capital
        backtest_months: Months to backtest
        min_volume_usd: Minimum daily volume for symbols
        max_universe_size: Max symbols in universe
        universe_update_days: Days between universe updates
        bbwidth_threshold: BBWidth percentile threshold
        rvr_threshold: Minimum RVR
        save_results: Save results to CSV
    """
    print("="*80)
    print("REALISTIC BACKTEST - Using Live Bybit API")
    print("="*80)

    # Load static universe if enabled
    static_universe = None
    if use_static_universe:
        static_universe_path = Path(__file__).parent / static_universe_file
        with open(static_universe_path, 'r') as f:
            universe_config = json.load(f)
            static_universe = universe_config['tokens']
        print(f"\nLoaded static universe: {len(static_universe)} tokens from {static_universe_file}")

    # Set dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*backtest_months)

    print(f"\nBacktest Configuration:")
    print(f"  Period: {start_date.date()} to {end_date.date()} ({backtest_months} months)")
    print(f"  Timeframe: 4-hour (4h)")
    print(f"  Initial Capital: ${initial_capital:,.2f}")
    if use_static_universe:
        print(f"  Universe Mode: STATIC")
        print(f"  Universe Size: {len(static_universe)} tokens (70% consistency)")
    else:
        print(f"  Universe Mode: DYNAMIC (scanned)")
        print(f"  Min Volume: ${min_volume_usd:,.0f}/day")
        print(f"  Max Universe: {max_universe_size} symbols")
        print(f"  Universe Updates: Every {universe_update_days} days")
    print(f"  MA Period: {ma_period} candles")
    print(f"  BB Lookback: {lookback_period} candles")
    print(f"  BBWidth Threshold: {bbwidth_threshold*100:.0f}th percentile")
    print(f"  RVR Threshold: {rvr_threshold}x")
    print(f"  Position Size: 5% per trade")
    print(f"  Max Concurrent Positions: 3")
    print(f"  Daily Loss Limit: -3% (stops new entries)")
    print(f"  Weekly Loss Limit: -8% (reduces size 50%)")
    print(f"  BTC Regime Filter: DISABLED")

    # Initialize realistic backtester
    print(f"\nInitializing realistic backtester...")

    backtester = RealisticBacktester(
        initial_capital=initial_capital,
        risk_per_trade_pct=0.02,  # 5% position size
        stop_loss_pct=0.10,  # 10% trailing stop
        max_positions=3,  # Max 3 concurrent positions
        min_volume_usd=min_volume_usd,
        max_universe_size=max_universe_size,
        universe_update_days=universe_update_days,
        static_universe=static_universe,
        daily_loss_limit_pct=0.03,  # 3% daily loss limit
        weekly_loss_limit_pct=0.08  # 8% weekly loss limit
    )

    # Run backtest
    print(f"\nStarting realistic backtest...")
    print("This may take a few minutes due to API calls...\n")

    result = backtester.run_realistic(
        start_date=start_date,
        end_date=end_date,
        bbwidth_threshold=bbwidth_threshold,
        rvr_threshold=rvr_threshold,
        ma_period=ma_period,
        lookback_period=lookback_period,
        use_btc_regime_filter=False,
        btc_ma_period=200,
        btc_adx_threshold=25.0
    )

    # Calculate metrics
    print("\nCalculating performance metrics...")
    metrics = calculate_performance_metrics(
        result.trades,
        result.equity_curve,
        result.daily_returns,
        initial_capital
    )

    # Generate report
    report = generate_performance_report(metrics)
    print(f"\n{report}")

    # Additional realistic backtest info
    print(f"\n{'='*80}")
    print("REALISTIC BACKTEST SPECIFICS")
    print(f"{'='*80}\n")
    print(f"Universe Changes: {result.universe_changes}")
    print(f"Data Source: Live Bybit API")
    print(f"Dynamic Universe: Yes (updated every {universe_update_days} days)")
    print(f"Symbol Availability: Checked at each time point")

    # Analyze universe-related exits
    if len(result.trades) > 0:
        universe_exits = sum(1 for t in result.trades if t.exit_reason == 'removed_from_universe')
        if universe_exits > 0:
            print(f"\nTrades exited due to universe removal: {universe_exits} "
                  f"({universe_exits/len(result.trades)*100:.1f}%)")

    # Save results
    if save_results and len(result.trades) > 0:
        print("\nSaving results...")

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
        trades_file = Path(__file__).parent / 'results' / 'realistic_backtest_trades.csv'
        trades_file.parent.mkdir(exist_ok=True)
        trades_df.to_csv(trades_file, index=False)
        print(f"  Saved trades to: {trades_file}")

        # Save equity curve
        equity_file = Path(__file__).parent / 'results' / 'realistic_equity_curve.csv'
        result.equity_curve.to_csv(equity_file, index=False)
        print(f"  Saved equity curve to: {equity_file}")

        # Save metrics with comparison flag
        metrics['backtest_type'] = 'realistic_api'
        metrics['universe_dynamic'] = True
        metrics['data_source'] = 'bybit_api'

        metrics_df = pd.DataFrame([metrics])
        metrics_file = Path(__file__).parent / 'results' / 'realistic_performance_metrics.csv'
        metrics_df.to_csv(metrics_file, index=False)
        print(f"  Saved metrics to: {metrics_file}")

    print(f"\n{'='*80}")
    print("REALISTIC BACKTEST COMPLETE")
    print(f"{'='*80}\n")

    return result, metrics


def compare_with_static_backtest():
    """
    Compare realistic backtest with static backtest results.
    """
    realistic_file = Path(__file__).parent / 'results' / 'realistic_performance_metrics.csv'
    static_file = Path(__file__).parent / 'results' / 'performance_metrics.csv'

    if not realistic_file.exists() or not static_file.exists():
        print("Run both backtests first to compare")
        return

    realistic = pd.read_csv(realistic_file)
    static = pd.read_csv(static_file)

    print("\n" + "="*80)
    print("BACKTEST COMPARISON: Realistic API vs Static Warehouse")
    print("="*80 + "\n")

    comparison = pd.DataFrame({
        'Metric': [
            'Total Trades',
            'Win Rate',
            'Total Return',
            'Avg Win',
            'Avg Loss',
            'Profit Factor',
            'Max Drawdown',
            'Sharpe Ratio'
        ],
        'Static': [
            static['total_trades'].iloc[0],
            f"{static['win_rate'].iloc[0]*100:.1f}%",
            f"{static.get('total_return_pct', [0]).iloc[0]:.2f}%",
            f"{static['avg_win_pct'].iloc[0]*100:.1f}%",
            f"{static['avg_loss_pct'].iloc[0]*100:.1f}%",
            f"{static['profit_factor'].iloc[0]:.2f}",
            f"{static.get('max_drawdown_pct', [0]).iloc[0]:.2f}%",
            f"{static.get('sharpe_ratio', [0]).iloc[0]:.2f}"
        ],
        'Realistic API': [
            realistic['total_trades'].iloc[0],
            f"{realistic['win_rate'].iloc[0]*100:.1f}%",
            f"{realistic.get('total_return_pct', [0]).iloc[0]:.2f}%",
            f"{realistic['avg_win_pct'].iloc[0]*100:.1f}%",
            f"{realistic['avg_loss_pct'].iloc[0]*100:.1f}%",
            f"{realistic['profit_factor'].iloc[0]:.2f}",
            f"{realistic.get('max_drawdown_pct', [0]).iloc[0]:.2f}%",
            f"{realistic.get('sharpe_ratio', [0]).iloc[0]:.2f}"
        ]
    })

    print(comparison.to_string(index=False))
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    # Run realistic backtest
    print("Running REALISTIC backtest with live Bybit API data...\n")

    # Run backtest on 4h timeframe with STATIC universe (70% qualified tokens)
    result, metrics = run_realistic_backtest(
        initial_capital=10000,
        backtest_months=27,
        min_volume_usd=15_000_000,
        max_universe_size=40,
        universe_update_days=7,
        bbwidth_threshold=0.35,  # 35th percentile
        ma_period=20,  # Same as daily
        bb_period=20,  # Same as daily
        lookback_period=90,  # Same as daily
        save_results=True,
        use_static_universe=True,  # Enable static universe
        static_universe_file="config/static_universe.json"
    )

    # Uncomment to run full year comparison:
    # print("\n\nNow running FULL YEAR realistic backtest...\n")
    # result_full, metrics_full = run_realistic_backtest(
    #     initial_capital=10000,
    #     backtest_months=12,
    #     min_volume_usd=10_000_000,
    #     max_universe_size=20,
    #     universe_update_days=7,
    #     save_results=True
    # )

    # Compare if static backtest exists
    # compare_with_static_backtest()
