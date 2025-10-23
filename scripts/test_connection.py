"""
Simple Exchange Connection Test

Quick test to verify:
1. API credentials work
2. Exchange responds
3. Balance can be fetched
4. Market data accessible

No trades are placed - read-only test.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.trading_config import config
from exchange.bybit_exchange import BybitExchange


def main():
    print("\n" + "="*80)
    print("EXCHANGE CONNECTION TEST")
    print("="*80)
    print(f"\nMode: {config.get_mode_display()}")
    print(f"API Endpoint: {config.exchange.base_url}")
    print(f"Capital (configured): ${config.risk.initial_capital:,.2f}")

    # Initialize exchange
    print("\n1. Connecting to exchange...")
    try:
        exchange = BybitExchange(
            mode=config.TRADING_MODE,
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            base_url=config.exchange.base_url
        )
        print("   ✓ Exchange initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        return

    # Health check
    print("\n2. Running health check...")
    try:
        health = exchange.health_check()
        if health['healthy']:
            print("   ✓ Health check passed")
        else:
            print(f"   ✗ Health issues: {health['issues']}")
            return
    except Exception as e:
        print(f"   ✗ Health check failed: {e}")
        return

    # Test public endpoint (market data)
    print("\n3. Testing public endpoint (market data)...")
    try:
        ticker = exchange.get_ticker('BTCUSDT')
        price = float(ticker.get('lastPrice', 0))
        volume = float(ticker.get('volume24h', 0))
        print(f"   ✓ BTC Price: ${price:,.2f}")
        print(f"   ✓ 24h Volume: {volume:,.0f} contracts")
    except Exception as e:
        print(f"   ✗ Market data failed: {e}")
        return

    # Test private endpoint (account balance)
    print("\n4. Testing private endpoint (account balance)...")
    try:
        balance = exchange.get_wallet_balance()

        # Extract USDT balance
        usdt_found = False
        if 'list' in balance and len(balance['list']) > 0:
            account = balance['list'][0]
            print(f"   ✓ Account Type: {account.get('accountType', 'Unknown')}")

            if 'coin' in account:
                for coin_info in account['coin']:
                    if coin_info['coin'] == 'USDT':
                        # Handle empty strings from API
                        equity_str = coin_info.get('equity', '0')
                        available_str = coin_info.get('availableToWithdraw', '0')

                        equity = float(equity_str) if equity_str and equity_str != '' else 0.0
                        available = float(available_str) if available_str and available_str != '' else 0.0

                        print(f"   ✓ USDT Equity: ${equity:,.2f}")
                        print(f"   ✓ USDT Available: ${available:,.2f}")
                        usdt_found = True
                        break

        if not usdt_found:
            print("   ⚠️  No USDT balance found (this is OK for a new account)")

    except Exception as e:
        print(f"   ✗ Balance fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test position query
    print("\n5. Testing position query...")
    try:
        positions = exchange.get_positions()
        open_positions = [p for p in positions if float(p.get('size', 0)) > 0]
        print(f"   ✓ Open Positions: {len(open_positions)}")
        if open_positions:
            for pos in open_positions:
                symbol = pos.get('symbol')
                size = float(pos.get('size', 0))
                side = pos.get('side')
                print(f"      - {symbol}: {side} {size}")
    except Exception as e:
        print(f"   ✗ Position query failed: {e}")
        return

    # Summary
    print("\n" + "="*80)
    print("✓ CONNECTION TEST PASSED")
    print("="*80)
    print("\nYour exchange connection is working correctly!")
    print("You can now run the full trading system.")
    print("\nNext steps:")
    print("  1. Run full execution test: python3 test_exchange_execution.py")
    print("  2. Start trading system: python3 trading_system.py")


if __name__ == "__main__":
    main()
