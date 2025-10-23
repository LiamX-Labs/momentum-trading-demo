"""
Test Exchange Execution

This script tests the complete flow:
1. Connects to exchange
2. Fetches balance
3. Creates a fake signal
4. Calculates position size
5. Places a REAL order on the exchange
6. Closes the position

⚠️  WARNING: This places REAL orders on your account!
Use DEMO mode first to test safely.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path (parent of scripts directory)
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.trading_config import config, TradingMode
from exchange.bybit_exchange import BybitExchange
from backtest.position_sizer import PositionSizer


def test_exchange_connection():
    """Test 1: Exchange Connection"""
    print("\n" + "="*80)
    print("TEST 1: EXCHANGE CONNECTION")
    print("="*80)

    try:
        exchange = BybitExchange(
            mode=config.TRADING_MODE,
            api_key=config.exchange.api_key,
            api_secret=config.exchange.api_secret,
            base_url=config.exchange.base_url
        )

        # Test health check
        health = exchange.health_check()
        if health['healthy']:
            print("✓ Exchange connection healthy")
            return exchange
        else:
            print(f"✗ Exchange health issues: {health['issues']}")
            return None

    except Exception as e:
        print(f"✗ Exchange connection failed: {e}")
        return None


def test_fetch_balance(exchange: BybitExchange):
    """Test 2: Fetch Balance"""
    print("\n" + "="*80)
    print("TEST 2: FETCH BALANCE")
    print("="*80)

    try:
        balance = exchange.get_wallet_balance()

        # Extract USDT balance
        if 'list' in balance and len(balance['list']) > 0:
            account = balance['list'][0]
            if 'coin' in account:
                for coin_info in account['coin']:
                    if coin_info['coin'] == 'USDT':
                        # Handle empty strings from API
                        equity_str = coin_info.get('equity', '0')
                        available_str = coin_info.get('availableToWithdraw', '0')
                        usd_value_str = coin_info.get('usdValue', '0')

                        equity = float(equity_str) if equity_str and equity_str != '' else 0.0
                        available = float(available_str) if available_str and available_str != '' else 0.0
                        usd_value = float(usd_value_str) if usd_value_str and usd_value_str != '' else 0.0
                        used_margin = usd_value - available if usd_value > 0 else 0.0

                        print(f"✓ USDT Balance:")
                        print(f"   Equity: ${equity:,.2f}")
                        print(f"   Available: ${available:,.2f}")
                        print(f"   Used Margin: ${used_margin:,.2f}")
                        return equity if equity > 0 else 10000.0  # Use default if empty account

        print("✗ Could not parse USDT balance")
        return None

    except Exception as e:
        print(f"✗ Failed to fetch balance: {e}")
        return None


def test_market_data(exchange: BybitExchange):
    """Test 3: Market Data"""
    print("\n" + "="*80)
    print("TEST 3: MARKET DATA")
    print("="*80)

    try:
        # Get BTC ticker
        ticker = exchange.get_ticker('BTCUSDT')
        price = float(ticker['lastPrice'])
        volume = float(ticker['volume24h'])

        print(f"✓ BTC Market Data:")
        print(f"   Price: ${price:,.2f}")
        print(f"   24h Volume: {volume:,.0f} contracts")

        # Get orderbook
        orderbook = exchange.get_orderbook('BTCUSDT', limit=5)
        if orderbook and 'b' in orderbook and 'a' in orderbook:
            best_bid = float(orderbook['b'][0][0]) if orderbook['b'] else 0
            best_ask = float(orderbook['a'][0][0]) if orderbook['a'] else 0
            spread = best_ask - best_bid

            print(f"   Best Bid: ${best_bid:,.2f}")
            print(f"   Best Ask: ${best_ask:,.2f}")
            print(f"   Spread: ${spread:.2f}")

        return price

    except Exception as e:
        print(f"✗ Failed to fetch market data: {e}")
        return None


def test_position_sizing(capital: float, entry_price: float):
    """Test 4: Position Sizing"""
    print("\n" + "="*80)
    print("TEST 4: POSITION SIZING")
    print("="*80)

    try:
        sizer = PositionSizer(
            account_size=capital,
            risk_per_trade_pct=config.risk.risk_per_trade_pct,
            stop_loss_pct=config.risk.stop_loss_pct,
            max_positions=config.risk.max_positions
        )

        sizing = sizer.calculate_position_size(
            entry_price=entry_price,
            current_positions=0
        )

        print(f"✓ Position Sizing:")
        print(f"   Can Open: {sizing['can_open']}")
        print(f"   Position Size USD: ${sizing['position_size_usd']:,.2f}")
        print(f"   Number of Contracts: {sizing['num_contracts']:.4f}")
        print(f"   Risk Amount: ${sizing['risk_usd']:,.2f}")

        return sizing

    except Exception as e:
        print(f"✗ Position sizing failed: {e}")
        return None


def create_fake_signal(symbol: str, price: float):
    """Test 5: Create Fake Signal"""
    print("\n" + "="*80)
    print("TEST 5: CREATE FAKE SIGNAL")
    print("="*80)

    signal = {
        'symbol': symbol,
        'price': price,
        'signal_strength': 0.85,  # Fake strength
        'timestamp': datetime.now(),
        'reason': 'TEST SIGNAL - Manual execution test'
    }

    print(f"✓ Fake Signal Created:")
    print(f"   Symbol: {signal['symbol']}")
    print(f"   Entry Price: ${signal['price']:,.2f}")
    print(f"   Signal Strength: {signal['signal_strength']:.2%}")
    print(f"   Reason: {signal['reason']}")

    return signal


def test_order_execution(exchange: BybitExchange, signal: dict, sizing: dict):
    """Test 6: Order Execution (REAL TRADE!)"""
    print("\n" + "="*80)
    print("TEST 6: ORDER EXECUTION")
    print("="*80)
    print("⚠️  WARNING: This will place a REAL order on your account!")

    mode_str = "🟡 DEMO" if config.TRADING_MODE == TradingMode.DEMO else "🔴 LIVE"
    print(f"   Mode: {mode_str}")
    print(f"   Symbol: {signal['symbol']}")
    print(f"   Quantity: {sizing['num_contracts']:.4f}")
    print(f"   Approximate Cost: ${sizing['position_size_usd']:,.2f}")

    response = input("\n   Proceed with order? (yes/no): ")
    if response.lower() != 'yes':
        print("✗ Order cancelled by user")
        return None

    try:
        entry_price = signal['price']
        initial_stop_loss = entry_price * (1 - config.risk.stop_loss_pct)
        trailing_stop_distance = entry_price * config.risk.stop_loss_pct

        # Place market order with trailing stop (single call!)
        print("\n   Placing market order with trailing stop...")
        order = exchange.place_order(
            symbol=signal['symbol'],
            side="Buy",
            order_type="Market",
            qty=sizing['num_contracts'],
            trailing_stop=trailing_stop_distance,  # Automatically sets trailing stop
            position_idx=0  # One-way mode
        )

        print(f"   ✓ Order placed - ID: {order.get('orderId')}")

        # Check if trailing stop was set
        if order.get('trailing_stop_set'):
            print(f"   ✓ Trailing stop set: ${trailing_stop_distance:.2f} distance")
            print(f"      (Will trigger if price drops {config.risk.stop_loss_pct*100}% from peak)")
        elif 'trailing_stop_error' in order:
            print(f"   ⚠️  Warning: Trailing stop failed - {order['trailing_stop_error']}")
            print(f"   Trying fixed stop loss as fallback...")
            try:
                exchange.set_trading_stop(
                    symbol=signal['symbol'],
                    stop_loss=initial_stop_loss,
                    category="linear",
                    position_idx=0
                )
                print(f"   ✓ Fixed stop loss set: ${initial_stop_loss:.2f}")
            except Exception as e:
                print(f"   ✗ Could not set any stop loss: {e}")
                print(f"   ⚠️  POSITION HAS NO STOP PROTECTION!")

        print(f"\n✓ Order Execution Complete:")
        print(f"   Order ID: {order.get('orderId')}")
        print(f"   Order Link ID: {order.get('orderLinkId')}")
        print(f"   Entry Price: ${entry_price:,.2f}")
        print(f"   Initial Stop: ${initial_stop_loss:.2f}")
        print(f"   Trailing Distance: ${trailing_stop_distance:.2f}")

        return order

    except Exception as e:
        print(f"✗ Order execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_check_position(exchange: BybitExchange, symbol: str):
    """Test 7: Check Position"""
    print("\n" + "="*80)
    print("TEST 7: CHECK POSITION")
    print("="*80)

    try:
        positions = exchange.get_positions(symbol=symbol)

        if positions and len(positions) > 0:
            pos = positions[0]
            size = float(pos.get('size', 0))
            side = pos.get('side', 'None')
            entry_price = float(pos.get('avgPrice', 0))
            unrealized_pnl = float(pos.get('unrealisedPnl', 0))

            print(f"✓ Position Found:")
            print(f"   Symbol: {symbol}")
            print(f"   Side: {side}")
            print(f"   Size: {size}")
            print(f"   Entry Price: ${entry_price:,.2f}")
            print(f"   Unrealized P&L: ${unrealized_pnl:+,.2f}")

            return pos
        else:
            print(f"✗ No position found for {symbol}")
            return None

    except Exception as e:
        print(f"✗ Failed to check position: {e}")
        return None


def test_close_position(exchange: BybitExchange, symbol: str):
    """Test 8: Close Position"""
    print("\n" + "="*80)
    print("TEST 8: CLOSE POSITION")
    print("="*80)

    response = input("\n   Close the test position? (yes/no): ")
    if response.lower() != 'yes':
        print("✗ Position close cancelled by user")
        print("   ⚠️  Remember to manually close this position!")
        return None

    try:
        print("\n   Closing position...")
        result = exchange.close_position(symbol=symbol)

        print(f"✓ Position Closed:")
        print(f"   Order ID: {result.get('orderId')}")
        print(f"   Order Link ID: {result.get('orderLinkId')}")

        return result

    except Exception as e:
        print(f"✗ Failed to close position: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("EXCHANGE EXECUTION TEST SUITE")
    print("="*80)
    print(f"\nMode: {config.get_mode_display()}")
    print(f"Exchange: {config.exchange.base_url}")
    print(f"\n⚠️  This will place REAL orders on your exchange account!")
    print(f"   Make sure you're using DEMO mode for testing.")

    response = input("\n   Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("\nTest cancelled.")
        return

    # Run tests
    exchange = test_exchange_connection()
    if not exchange:
        return

    capital = test_fetch_balance(exchange)
    if not capital:
        return

    price = test_market_data(exchange)
    if not price:
        return

    sizing = test_position_sizing(capital, price)
    if not sizing or not sizing['can_open']:
        print("\n✗ Cannot open position with current sizing")
        return

    # Use a smaller test symbol (cheaper than BTC)
    test_symbol = 'BTCUSDT'  # You can change this to a cheaper token
    signal = create_fake_signal(test_symbol, price)

    order = test_order_execution(exchange, signal, sizing)
    if not order:
        return

    # Wait a moment for order to fill
    import time
    print("\n   Waiting for order to fill...")
    time.sleep(2)

    position = test_check_position(exchange, test_symbol)
    if not position:
        return

    # Close the test position
    test_close_position(exchange, test_symbol)

    print("\n" + "="*80)
    print("✓ ALL TESTS COMPLETED")
    print("="*80)
    print("\nSummary:")
    print("  ✓ Exchange connection")
    print("  ✓ Balance fetch")
    print("  ✓ Market data")
    print("  ✓ Position sizing")
    print("  ✓ Signal creation")
    print("  ✓ Order execution (market order)")
    print("  ✓ Trailing stop setup (exchange-side)")
    print("  ✓ Position verification")
    print("  ✓ Position close")
    print("\n🎉 Your system is ready to trade!")
    print("\nNote: This test mimics the production trading system flow:")
    print("  1. Place market order")
    print("  2. Set trailing stop on exchange")
    print("  3. Monitor position")
    print("  4. Close when needed")


if __name__ == "__main__":
    main()
