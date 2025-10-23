"""
Bybit Demo Trading Integration using V5 API.

This module handles:
- Authentication with Bybit demo account
- Order placement (market/limit)
- Position management
- Account balance tracking
- Real-time market data

API Documentation: https://bybit-exchange.github.io/docs/v5/intro
Note: Bybit uses "demo" trading (not testnet) for paper trading
"""

import os
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class BybitTestnet:
    """
    Bybit Demo Trading API V5 client for paper trading.

    Demo Trading URL: https://bybit.com (with demo mode enabled)
    API Base: https://api-demo.bybit.com
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        """
        Initialize Bybit demo trading client.

        Args:
            api_key: Demo API key (get from https://bybit.com > Demo Trading)
            api_secret: Demo API secret
        """
        self.api_key = api_key or os.getenv('BYBIT_DEMO_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_DEMO_API_SECRET')

        # V5 API endpoints for demo
        self.base_url = "https://api-demo.bybit.com"
        self.recv_window = 5000  # 5 seconds

        # Session for connection pooling
        self.session = requests.Session()

        print(f"Bybit Demo Trading V5 Client Initialized")
        print(f"Base URL: {self.base_url}")

    def _generate_signature(self, params_str: str, timestamp: str) -> str:
        """
        Generate HMAC SHA256 signature for V5 API.

        V5 Signature format: timestamp + api_key + recv_window + params_str
        """
        param_str = str(timestamp) + self.api_key + str(self.recv_window) + params_str

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def _send_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        auth_required: bool = False
    ) -> Dict:
        """
        Send HTTP request to Bybit V5 API.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (e.g., /v5/market/tickers)
            params: Request parameters
            auth_required: Whether authentication is required

        Returns:
            Response JSON
        """
        url = self.base_url + endpoint
        params = params or {}

        headers = {
            "Content-Type": "application/json"
        }

        if auth_required:
            timestamp = int(time.time() * 1000)

            # Convert params to query string for signature
            if method == "GET":
                params_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
            else:
                params_str = json.dumps(params) if params else ""

            signature = self._generate_signature(params_str, timestamp)

            headers.update({
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-SIGN-TYPE": "2",
                "X-BAPI-TIMESTAMP": str(timestamp),
                "X-BAPI-RECV-WINDOW": str(self.recv_window)
            })

        try:
            if method == "GET":
                response = self.session.get(url, params=params, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            result = response.json()

            # Check Bybit response code
            if result.get('retCode') != 0:
                raise Exception(f"Bybit API Error: {result.get('retMsg', 'Unknown error')}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise

    # ========== Market Data Methods ==========

    def get_ticker(self, symbol: str, category: str = "linear") -> Dict:
        """
        Get latest ticker information.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            category: Product type ('linear' for USDT perpetual)

        Returns:
            Ticker data
        """
        params = {
            "category": category,
            "symbol": symbol
        }

        result = self._send_request("GET", "/v5/market/tickers", params)
        return result['result']['list'][0] if result['result']['list'] else {}

    def get_orderbook(self, symbol: str, category: str = "linear", limit: int = 25) -> Dict:
        """
        Get order book depth.

        Args:
            symbol: Trading pair
            category: Product type
            limit: Depth limit (1-200)

        Returns:
            Order book data
        """
        params = {
            "category": category,
            "symbol": symbol,
            "limit": limit
        }

        result = self._send_request("GET", "/v5/market/orderbook", params)
        return result['result']

    def get_kline(
        self,
        symbol: str,
        interval: str = "240",
        category: str = "linear",
        limit: int = 200
    ) -> List[Dict]:
        """
        Get candlestick data.

        Args:
            symbol: Trading pair
            interval: Kline interval (1, 3, 5, 15, 30, 60, 120, 240, D, W, M)
            category: Product type
            limit: Number of candles (max 1000)

        Returns:
            List of kline data
        """
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        result = self._send_request("GET", "/v5/market/kline", params)
        return result['result']['list']

    # ========== Account Methods ==========

    def get_wallet_balance(self, account_type: str = "UNIFIED") -> Dict:
        """
        Get wallet balance.

        Args:
            account_type: Account type (UNIFIED, CONTRACT)

        Returns:
            Balance information
        """
        params = {
            "accountType": account_type
        }

        result = self._send_request("GET", "/v5/account/wallet-balance", params, auth_required=True)
        return result['result']

    # ========== Trading Methods ==========

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        qty: float,
        price: Optional[float] = None,
        category: str = "linear",
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_on_trigger: bool = False
    ) -> Dict:
        """
        Place an order.

        Args:
            symbol: Trading pair
            side: Buy or Sell
            order_type: Market or Limit
            qty: Order quantity
            price: Order price (required for Limit)
            category: Product type
            time_in_force: GTC, IOC, FOK
            reduce_only: Reduce only flag
            close_on_trigger: Close on trigger

        Returns:
            Order result
        """
        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(qty),
            "timeInForce": time_in_force,
        }

        if price:
            params["price"] = str(price)

        if reduce_only:
            params["reduceOnly"] = True

        if close_on_trigger:
            params["closeOnTrigger"] = True

        result = self._send_request("POST", "/v5/order/create", params, auth_required=True)
        return result['result']

    def cancel_order(
        self,
        symbol: str,
        order_id: str = None,
        order_link_id: str = None,
        category: str = "linear"
    ) -> Dict:
        """
        Cancel an order.

        Args:
            symbol: Trading pair
            order_id: Order ID (either order_id or order_link_id required)
            order_link_id: User customized order ID
            category: Product type

        Returns:
            Cancel result
        """
        params = {
            "category": category,
            "symbol": symbol
        }

        if order_id:
            params["orderId"] = order_id
        elif order_link_id:
            params["orderLinkId"] = order_link_id
        else:
            raise ValueError("Either order_id or order_link_id must be provided")

        result = self._send_request("POST", "/v5/order/cancel", params, auth_required=True)
        return result['result']

    def get_open_orders(
        self,
        symbol: str = None,
        category: str = "linear",
        limit: int = 50
    ) -> List[Dict]:
        """
        Get open orders.

        Args:
            symbol: Trading pair (optional, get all if not specified)
            category: Product type
            limit: Limit (max 50)

        Returns:
            List of open orders
        """
        params = {
            "category": category,
            "limit": limit
        }

        if symbol:
            params["symbol"] = symbol

        result = self._send_request("GET", "/v5/order/realtime", params, auth_required=True)
        return result['result']['list']

    def get_positions(
        self,
        symbol: str = None,
        category: str = "linear"
    ) -> List[Dict]:
        """
        Get position information.

        Args:
            symbol: Trading pair (optional)
            category: Product type

        Returns:
            List of positions
        """
        params = {
            "category": category
        }

        if symbol:
            params["symbol"] = symbol

        result = self._send_request("GET", "/v5/position/list", params, auth_required=True)
        return result['result']['list']

    def set_trading_stop(
        self,
        symbol: str,
        stop_loss: float = None,
        take_profit: float = None,
        trailing_stop: float = None,
        category: str = "linear",
        position_idx: int = 0
    ) -> Dict:
        """
        Set stop loss, take profit, or trailing stop.

        Args:
            symbol: Trading pair
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop: Trailing stop distance
            category: Product type
            position_idx: Position index (0 for one-way mode)

        Returns:
            Result
        """
        params = {
            "category": category,
            "symbol": symbol,
            "positionIdx": position_idx
        }

        if stop_loss:
            params["stopLoss"] = str(stop_loss)

        if take_profit:
            params["takeProfit"] = str(take_profit)

        if trailing_stop:
            params["trailingStop"] = str(trailing_stop)

        result = self._send_request("POST", "/v5/position/trading-stop", params, auth_required=True)
        return result['result']

    # ========== Helper Methods ==========

    def get_account_info(self) -> Dict:
        """
        Get comprehensive account information.

        Returns:
            Account summary with balance and positions
        """
        balance = self.get_wallet_balance()
        positions = self.get_positions()
        open_orders = self.get_open_orders()

        return {
            "balance": balance,
            "positions": positions,
            "open_orders": open_orders,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Test connection
    print("Testing Bybit Demo Trading V5 API...\n")

    # You can test without API keys for public endpoints
    client = BybitTestnet()

    # Test public endpoint
    print("1. Testing ticker (public endpoint)...")
    ticker = client.get_ticker("BTCUSDT")
    print(f"   BTC Price: ${float(ticker.get('lastPrice', 0)):,.2f}\n")

    # Test with API keys if available
    if client.api_key and client.api_secret:
        print("2. Testing account info (authenticated)...")
        try:
            account = client.get_account_info()
            print(f"   ✓ Account info retrieved successfully")
            print(f"   Positions: {len(account['positions'])}")
            print(f"   Open Orders: {len(account['open_orders'])}")
        except Exception as e:
            print(f"   ✗ Authentication error: {e}")
            print("\n   To use authenticated endpoints:")
            print("   1. Go to https://bybit.com")
            print("   2. Enable Demo Trading mode")
            print("   3. Generate Demo API keys")
            print("   4. Set environment variables:")
            print("      export BYBIT_DEMO_API_KEY='your_key'")
            print("      export BYBIT_DEMO_API_SECRET='your_secret'")
    else:
        print("2. Skipping authenticated endpoints (no API keys)")
        print("\n   To test authenticated endpoints:")
        print("   1. Go to https://bybit.com")
        print("   2. Enable Demo Trading mode")
        print("   3. Generate Demo API keys")
        print("   4. Set environment variables:")
        print("      export BYBIT_DEMO_API_KEY='your_key'")
        print("      export BYBIT_DEMO_API_SECRET='your_secret'")

    print("\n✓ Bybit Demo Trading integration ready!")
