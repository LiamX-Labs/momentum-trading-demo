"""
Test Telegram Notifications

Simple script to test if Telegram bot is working correctly.
Sends various test messages to verify all notification types.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.trading_config import config
from alerts.telegram_bot import TelegramBot


def test_telegram_connection():
    """Test 1: Basic Connection"""
    print("\n" + "="*80)
    print("TEST 1: TELEGRAM BOT CONNECTION")
    print("="*80)

    if not config.alerts.enabled:
        print("❌ Telegram is disabled in config")
        print("   Set TELEGRAM_ENABLED=true in .env")
        return None

    if not config.alerts.bot_token or not config.alerts.chat_id:
        print("❌ Missing Telegram credentials")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return None

    print(f"✓ Bot Token: {config.alerts.bot_token[:20]}...")
    print(f"✓ Chat ID: {config.alerts.chat_id}")

    try:
        telegram = TelegramBot(
            bot_token=config.alerts.bot_token,
            chat_id=config.alerts.chat_id
        )
        print("✓ Telegram bot initialized")
        return telegram
    except Exception as e:
        print(f"❌ Failed to initialize Telegram bot: {e}")
        return None


def test_simple_message(telegram: TelegramBot):
    """Test 2: Simple Message"""
    print("\n" + "="*80)
    print("TEST 2: SEND SIMPLE MESSAGE")
    print("="*80)

    try:
        telegram.send_message("🧪 <b>Test Message</b>\n\nThis is a test from your Apex Momentum Trading System!")
        print("✓ Simple message sent")
        print("   Check your Telegram to confirm!")
        return True
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False


def test_system_start(telegram: TelegramBot):
    """Test 3: System Start Alert"""
    print("\n" + "="*80)
    print("TEST 3: SYSTEM START ALERT")
    print("="*80)

    try:
        telegram.alert_system_start({
            "Mode": "DEMO",
            "Capital": "$5,000.00",
            "Max Positions": 3,
            "Position Size": "5%"
        })
        print("✓ System start alert sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send system start alert: {e}")
        return False


def test_position_opened(telegram: TelegramBot):
    """Test 4: Position Opened Alert"""
    print("\n" + "="*80)
    print("TEST 4: POSITION OPENED ALERT")
    print("="*80)

    try:
        telegram.alert_position_opened(
            symbol="BTCUSDT",
            side="Buy",
            entry_price=65000.00,
            quantity=0.01,
            position_size_usd=650.00,
            order_id="test_order_123"
        )
        print("✓ Position opened alert sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send position opened alert: {e}")
        return False


def test_position_closed(telegram: TelegramBot):
    """Test 5: Position Closed Alert"""
    print("\n" + "="*80)
    print("TEST 5: POSITION CLOSED ALERT")
    print("="*80)

    try:
        telegram.alert_position_closed(
            symbol="BTCUSDT",
            entry_price=65000.00,
            exit_price=67500.00,
            quantity=0.01,
            pnl_usd=25.00,
            pnl_pct=0.0385,
            exit_reason="MA Exit",
            holding_time="2 days, 4:30:00"
        )
        print("✓ Position closed alert sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send position closed alert: {e}")
        return False


def test_risk_alerts(telegram: TelegramBot):
    """Test 6: Risk Limit Alerts"""
    print("\n" + "="*80)
    print("TEST 6: RISK LIMIT ALERTS")
    print("="*80)

    try:
        # Daily loss limit
        telegram.alert_daily_loss_limit(-0.035, -0.03)
        print("✓ Daily loss limit alert sent")

        # Weekly loss limit
        telegram.alert_weekly_loss_limit(-0.09, -0.08)
        print("✓ Weekly loss limit alert sent")

        return True
    except Exception as e:
        print(f"❌ Failed to send risk alerts: {e}")
        return False


def test_error_alert(telegram: TelegramBot):
    """Test 7: Error Alert"""
    print("\n" + "="*80)
    print("TEST 7: ERROR ALERT")
    print("="*80)

    try:
        telegram.alert_error(
            error_type="Connection Error",
            error_message="Failed to connect to exchange API",
            context="BTCUSDT"
        )
        print("✓ Error alert sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send error alert: {e}")
        return False


def test_system_stop(telegram: TelegramBot):
    """Test 8: System Stop Alert"""
    print("\n" + "="*80)
    print("TEST 8: SYSTEM STOP ALERT")
    print("="*80)

    try:
        telegram.alert_system_stop()
        print("✓ System stop alert sent")
        return True
    except Exception as e:
        print(f"❌ Failed to send system stop alert: {e}")
        return False


def main():
    """Run all Telegram tests"""
    print("\n" + "="*80)
    print("TELEGRAM NOTIFICATION TEST SUITE")
    print("="*80)
    print(f"\nTesting Telegram integration for Apex Momentum Trading System")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Test 1: Connection
    telegram = test_telegram_connection()
    if not telegram:
        print("\n❌ Cannot proceed without Telegram connection")
        print("\nSetup instructions:")
        print("1. Create bot with @BotFather on Telegram")
        print("2. Get your chat ID from @userinfobot")
        print("3. Add to .env file:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   TELEGRAM_CHAT_ID=your_chat_id")
        print("   TELEGRAM_ENABLED=true")
        return

    # Wait for user confirmation
    print("\n⚠️  This will send multiple test messages to your Telegram")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("\nTest cancelled.")
        return

    # Run all tests
    results = {
        "Connection": True,
        "Simple Message": test_simple_message(telegram),
        "System Start": test_system_start(telegram),
        "Position Opened": test_position_opened(telegram),
        "Position Closed": test_position_closed(telegram),
        "Risk Alerts": test_risk_alerts(telegram),
        "Error Alert": test_error_alert(telegram),
        "System Stop": test_system_stop(telegram)
    }

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Telegram notifications working correctly!")
        print("   Check your Telegram app to see all the test messages.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("   Check the error messages above for details.")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
