"""
Quick BTC Regime Status Check

Shows current BTC regime status to understand why signals may not be appearing.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from signals.btc_regime_filter import check_btc_regime
from data.bybit_api import BybitDataFetcher

print("="*80)
print("BTC REGIME STATUS CHECK")
print("="*80)

try:
    fetcher = BybitDataFetcher()

    # Fetch BTC 4h data (last 90 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    print(f"\nFetching BTC 4h data (last 90 days)...")
    btc_data = fetcher.get_klines(
        symbol='BTCUSDT',
        interval='240',  # 4h
        start_time=start_date,
        end_time=end_date,
        limit=600
    )

    print(f"Retrieved {len(btc_data)} candles")

    # Calculate regime
    print("\nCalculating BTC regime...")
    regime = check_btc_regime(
        btc_data,
        ma_period=200,
        adx_threshold=25.0
    )

    # Get latest status
    latest = regime.iloc[-1]

    print("\n" + "="*80)
    print("CURRENT BTC STATUS")
    print("="*80)

    print(f"\nPrice: ${latest['close']:,.2f}")
    print(f"200-day MA: ${latest['ma_200']:,.2f}")
    print(f"ADX: {latest['adx']:.2f}")

    print(f"\n{'='*80}")
    print("REGIME CONDITIONS")
    print("="*80)

    conditions = [
        ("✓" if latest['btc_above_ma'] else "✗", "BTC above 200-day MA", latest['btc_above_ma']),
        ("✓" if latest['new_high_recently'] else "✗", "Made new 20-day high recently", latest['new_high_recently']),
        ("✓" if latest['adx_trending'] else "✗", f"ADX > 25 (trending)", latest['adx_trending']),
    ]

    for symbol, description, value in conditions:
        status = "PASS" if value else "FAIL"
        print(f"{symbol} {description}: {status}")

    print(f"\n{'='*80}")
    regime_favorable = latest['btc_regime_favorable']
    print(f"OVERALL REGIME: {'✅ FAVORABLE' if regime_favorable else '❌ UNFAVORABLE'}")
    print("="*80)

    if not regime_favorable:
        print("\n⚠️  BTC regime is NOT favorable")
        print("   The system will NOT generate signals until BTC shows trending behavior.")
        print("\n   This is by design - the strategy only trades when BTC is strong.")
        print("   Wait for BTC to trend upward with conviction.")
    else:
        print("\n✅ BTC regime IS favorable")
        print("   The system can now scan for altcoin signals.")
        print("   Signals will appear when individual tokens meet entry criteria.")

    # Show historical regime stats
    print(f"\n{'='*80}")
    print("HISTORICAL REGIME STATS (Last 90 days)")
    print("="*80)

    favorable_count = regime['btc_regime_favorable'].sum()
    total_count = len(regime[regime['btc_regime_favorable'].notna()])
    favorable_pct = (favorable_count / total_count * 100) if total_count > 0 else 0

    print(f"Favorable periods: {favorable_count}/{total_count} ({favorable_pct:.1f}%)")
    print(f"Unfavorable periods: {total_count - favorable_count}/{total_count} ({100-favorable_pct:.1f}%)")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
