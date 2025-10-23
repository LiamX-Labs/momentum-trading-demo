"""
Simple Telegram Test - No Dependencies

Tests Telegram notifications without requiring pandas or other heavy dependencies.
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime


def load_env():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value


def send_telegram_message(bot_token, chat_id, message):
    """Send a message via Telegram bot"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get('ok'):
            return True, "Message sent successfully"
        else:
            return False, result.get('description', 'Unknown error')
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"


def main():
    """Run Telegram notification test"""
    print("\n" + "="*80)
    print("SIMPLE TELEGRAM NOTIFICATION TEST")
    print("="*80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Load environment
    print("Loading environment variables...")
    load_env()

    # Get credentials
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    enabled = os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'

    # Validate
    print("\n" + "="*80)
    print("CONFIGURATION CHECK")
    print("="*80)

    if not enabled:
        print("❌ Telegram is disabled")
        print("   Set TELEGRAM_ENABLED=true in .env")
        return

    if not bot_token:
        print("❌ Missing TELEGRAM_BOT_TOKEN")
        print("\nSetup instructions:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions")
        print("3. Copy the token and add to .env:")
        print("   TELEGRAM_BOT_TOKEN=your_token_here")
        return

    if not chat_id:
        print("❌ Missing TELEGRAM_CHAT_ID")
        print("\nSetup instructions:")
        print("1. Open Telegram and search for @userinfobot")
        print("2. Send /start to get your chat ID")
        print("3. Add to .env:")
        print("   TELEGRAM_CHAT_ID=your_chat_id")
        return

    print(f"✓ Telegram Enabled: {enabled}")
    print(f"✓ Bot Token: {bot_token[:20]}...{bot_token[-10:]}")
    print(f"✓ Chat ID: {chat_id}")

    # Confirm
    print("\n" + "="*80)
    print("SEND TEST MESSAGE")
    print("="*80)
    print("This will send a test message to your Telegram.")

    response = input("\nProceed? (yes/no): ")
    if response.lower() != 'yes':
        print("\nTest cancelled.")
        return

    # Send test messages
    print("\nSending test messages...\n")

    tests = [
        {
            "name": "Simple Test",
            "message": "🧪 <b>Test #1: Simple Message</b>\n\nThis is a basic test from your Apex Momentum Trading System."
        },
        {
            "name": "System Start Alert",
            "message": """🚀 <b>SYSTEM START</b>

Mode: 🟡 DEMO
Capital: $5,000.00
Max Positions: 3
Position Size: 5%

System started successfully.
Ready to trade!"""
        },
        {
            "name": "Position Opened",
            "message": """📈 <b>POSITION OPENED</b>

Symbol: <code>BTCUSDT</code>
Side: Buy
Entry Price: $65,000.00
Quantity: 0.01
Position Size: $650.00
Order ID: <code>test_123</code>

✅ Position entered successfully"""
        },
        {
            "name": "Position Closed (Profit)",
            "message": """💰 <b>POSITION CLOSED</b>

Symbol: <code>BTCUSDT</code>
Entry: $65,000.00
Exit: $67,500.00
Quantity: 0.01

<b>P&L: +$25.00 (+3.85%)</b>
Exit Reason: MA Exit
Holding Time: 2 days, 4:30:00

✅ Profitable trade!"""
        },
        {
            "name": "Position Closed (Loss)",
            "message": """📉 <b>POSITION CLOSED</b>

Symbol: <code>ETHUSDT</code>
Entry: $3,200.00
Exit: $2,900.00
Quantity: 0.5

<b>P&L: -$150.00 (-9.38%)</b>
Exit Reason: Exchange Stop Loss
Holding Time: 1 day, 2:15:00

❌ Stop loss hit"""
        },
        {
            "name": "Risk Alert - Daily Loss",
            "message": """⚠️ <b>DAILY LOSS LIMIT</b>

Current Loss: -3.50%
Limit: -3.00%

⛔ No new positions until tomorrow
All existing positions remain active."""
        },
        {
            "name": "Risk Alert - Weekly Loss",
            "message": """⚠️ <b>WEEKLY LOSS LIMIT</b>

Current Loss: -9.00%
Limit: -8.00%

📉 Position size reduced to 50%
All existing positions remain active."""
        },
        {
            "name": "Error Alert",
            "message": """❌ <b>ERROR ALERT</b>

Type: Connection Error
Context: BTCUSDT

Error: Failed to connect to exchange API

⚠️ Please check system logs"""
        },
        {
            "name": "System Stop",
            "message": """🛑 <b>SYSTEM STOPPED</b>

Trading system has been stopped.
All positions have been closed.

Time: {}

System shutdown complete.""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        }
    ]

    # Send each test
    results = []
    for i, test in enumerate(tests, 1):
        print(f"Test {i}/{len(tests)}: {test['name']}...", end=" ")
        success, message = send_telegram_message(bot_token, chat_id, test['message'])

        if success:
            print("✓")
            results.append((test['name'], True))
        else:
            print(f"✗ - {message}")
            results.append((test['name'], False))

        # Small delay between messages
        import time
        time.sleep(1)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Telegram notifications working correctly!")
        print("\n📱 Check your Telegram app to see all the test messages.")
        print("   You should have received 9 different notification types.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nTroubleshooting:")
        print("1. Verify bot token is correct")
        print("2. Verify chat ID is correct")
        print("3. Make sure you've started a conversation with the bot")
        print("4. Check bot permissions")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
