"""
Telegram Alert System for Paper Trading.

Sends notifications for:
- Entry signals
- Position exits
- Stop loss hits
- Daily performance summaries
- System errors
"""

import os
import requests
from typing import Optional
from datetime import datetime
import json


class TelegramBot:
    """
    Telegram bot for trading alerts.

    Setup:
    1. Create bot with @BotFather on Telegram
    2. Get bot token
    3. Get your chat_id (send /start to bot, then check getUpdates)
    4. Set environment variables:
       - TELEGRAM_BOT_TOKEN
       - TELEGRAM_CHAT_ID
    """

    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram bot.

        Args:
            bot_token: Bot token from @BotFather
            chat_id: Your chat ID
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.enabled = bool(self.bot_token and self.chat_id)

        if self.enabled:
            print("✓ Telegram bot initialized")
        else:
            print("⚠ Telegram bot disabled (no credentials)")

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram.

        Args:
            message: Message text (supports HTML formatting)
            parse_mode: Formatting mode (HTML or Markdown)

        Returns:
            True if successful
        """
        if not self.enabled:
            print(f"[TELEGRAM DISABLED] {message}")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            return response.json().get('ok', False)

        except Exception as e:
            print(f"Telegram send error: {e}")
            return False

    # ========== Trading Alerts ==========

    def alert_entry_signal(
        self,
        symbol: str,
        price: float,
        signal_strength: float,
        position_size_usd: float,
        stop_loss: float
    ):
        """Alert when entry signal is detected."""
        message = f"""
🚀 <b>ENTRY SIGNAL</b>

<b>Symbol:</b> {symbol}
<b>Price:</b> ${price:,.4f}
<b>Signal Strength:</b> {signal_strength:.1%}
<b>Position Size:</b> ${position_size_usd:,.2f}
<b>Stop Loss:</b> ${stop_loss:,.4f} ({((stop_loss/price)-1)*100:.1f}%)

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_position_opened(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        position_size_usd: float,
        order_id: str = None
    ):
        """Alert when position is opened."""
        message = f"""
✅ <b>POSITION OPENED</b>

<b>Symbol:</b> {symbol}
<b>Side:</b> {side.upper()}
<b>Entry Price:</b> ${entry_price:,.4f}
<b>Quantity:</b> {quantity:,.4f}
<b>Position Size:</b> ${position_size_usd:,.2f}
{f'<b>Order ID:</b> {order_id}' if order_id else ''}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_position_closed(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl_usd: float,
        pnl_pct: float,
        exit_reason: str,
        holding_time: str = None
    ):
        """Alert when position is closed."""
        emoji = "🟢" if pnl_usd >= 0 else "🔴"
        message = f"""
{emoji} <b>POSITION CLOSED</b>

<b>Symbol:</b> {symbol}
<b>Entry:</b> ${entry_price:,.4f}
<b>Exit:</b> ${exit_price:,.4f}
<b>Quantity:</b> {quantity:,.4f}

<b>P&L:</b> ${pnl_usd:+,.2f} ({pnl_pct:+.2%})
<b>Reason:</b> {exit_reason}
{f'<b>Holding Time:</b> {holding_time}' if holding_time else ''}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_stop_loss_hit(
        self,
        symbol: str,
        entry_price: float,
        stop_price: float,
        loss_usd: float,
        loss_pct: float
    ):
        """Alert when stop loss is hit."""
        message = f"""
🛑 <b>STOP LOSS HIT</b>

<b>Symbol:</b> {symbol}
<b>Entry Price:</b> ${entry_price:,.4f}
<b>Stop Price:</b> ${stop_price:,.4f}

<b>Loss:</b> -${abs(loss_usd):,.2f} ({loss_pct:.2%})

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    # ========== Risk Alerts ==========

    def alert_daily_loss_limit(self, daily_loss_pct: float, limit_pct: float):
        """Alert when daily loss limit is hit."""
        message = f"""
⚠️ <b>DAILY LOSS LIMIT HIT</b>

<b>Current Loss:</b> {daily_loss_pct:.2%}
<b>Limit:</b> {limit_pct:.2%}

🚫 No new positions for today

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_weekly_loss_limit(self, weekly_loss_pct: float, limit_pct: float):
        """Alert when weekly loss limit triggers size reduction."""
        message = f"""
⚠️ <b>WEEKLY LOSS LIMIT</b>

<b>Week Loss:</b> {weekly_loss_pct:.2%}
<b>Limit:</b> {limit_pct:.2%}

📉 Position size reduced by 50%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    # ========== Performance Reports ==========

    def send_daily_summary(
        self,
        total_trades: int,
        wins: int,
        losses: int,
        daily_pnl: float,
        daily_pnl_pct: float,
        open_positions: int,
        current_equity: float
    ):
        """Send daily performance summary."""
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        emoji = "🟢" if daily_pnl >= 0 else "🔴"

        message = f"""
📊 <b>DAILY SUMMARY</b>

<b>Trades Today:</b> {total_trades}
<b>Wins:</b> {wins} | <b>Losses:</b> {losses}
<b>Win Rate:</b> {win_rate:.1f}%

{emoji} <b>Daily P&L:</b> ${daily_pnl:+,.2f} ({daily_pnl_pct:+.2%})

<b>Open Positions:</b> {open_positions}
<b>Current Equity:</b> ${current_equity:,.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def send_weekly_summary(
        self,
        total_trades: int,
        total_pnl: float,
        win_rate: float,
        profit_factor: float,
        max_drawdown_pct: float,
        best_trade_pnl: float,
        worst_trade_pnl: float
    ):
        """Send weekly performance summary."""
        emoji = "🟢" if total_pnl >= 0 else "🔴"

        message = f"""
📈 <b>WEEKLY SUMMARY</b>

<b>Total Trades:</b> {total_trades}
{emoji} <b>Total P&L:</b> ${total_pnl:+,.2f}
<b>Win Rate:</b> {win_rate:.1%}
<b>Profit Factor:</b> {profit_factor:.2f}

<b>Max Drawdown:</b> {max_drawdown_pct:.2%}
<b>Best Trade:</b> ${best_trade_pnl:+,.2f}
<b>Worst Trade:</b> ${worst_trade_pnl:+,.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    # ========== System Alerts ==========

    def alert_system_start(self, config: dict = None):
        """Alert when system starts."""
        message = f"""
🤖 <b>SYSTEM STARTED</b>

<b>Mode:</b> Paper Trading
<b>Exchange:</b> Bybit Testnet

{self._format_config(config) if config else ''}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_system_stop(self):
        """Alert when system stops."""
        message = f"""
🛑 <b>SYSTEM STOPPED</b>

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    def alert_error(self, error_type: str, error_message: str, context: str = None):
        """Alert on system errors."""
        message = f"""
❌ <b>ERROR</b>

<b>Type:</b> {error_type}
<b>Message:</b> {error_message}
{f'<b>Context:</b> {context}' if context else ''}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_message(message.strip())

    # ========== Helper Methods ==========

    def _format_config(self, config: dict) -> str:
        """Format config dict for display."""
        if not config:
            return ""

        lines = []
        for key, value in config.items():
            formatted_key = key.replace('_', ' ').title()
            lines.append(f"<b>{formatted_key}:</b> {value}")

        return "\n".join(lines)

    def get_chat_id(self) -> Optional[str]:
        """
        Get chat ID from bot updates.
        Send a message to your bot first, then call this.
        """
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get('ok') and data.get('result'):
                # Get chat_id from latest message
                latest = data['result'][-1]
                chat_id = latest['message']['chat']['id']
                return str(chat_id)

        except Exception as e:
            print(f"Error getting chat ID: {e}")

        return None


if __name__ == "__main__":
    print("="*60)
    print("TELEGRAM BOT SETUP")
    print("="*60)

    # Initialize bot
    bot = TelegramBot()

    if not bot.enabled:
        print("\n📱 To set up Telegram alerts:")
        print("\n1. Create a bot:")
        print("   - Open Telegram and search for @BotFather")
        print("   - Send: /newbot")
        print("   - Follow prompts to get your bot token")
        print("\n2. Get your chat ID:")
        print("   - Search for your bot on Telegram")
        print("   - Send: /start")
        print("   - Run this script with bot token to get chat ID")
        print("\n3. Set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")

    else:
        print("\n✓ Telegram bot configured!")
        print(f"Chat ID: {bot.chat_id}")

        # Test message
        print("\nSending test message...")
        success = bot.send_message("🤖 <b>Test Message</b>\n\nTelegram bot is working!")

        if success:
            print("✓ Test message sent successfully!")
        else:
            print("✗ Failed to send test message")

        # If user needs chat ID
        if bot.bot_token and not bot.chat_id:
            print("\nGetting chat ID...")
            print("Make sure you've sent /start to your bot first!")
            chat_id = bot.get_chat_id()
            if chat_id:
                print(f"\n✓ Your chat ID: {chat_id}")
                print(f"Set it with: export TELEGRAM_CHAT_ID='{chat_id}'")
