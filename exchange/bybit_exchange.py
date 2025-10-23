"""
Production-Ready Bybit Exchange Interface.

Unified interface for demo and live trading.
Mode is controlled by configuration - no code changes needed.
"""

import os
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json
import sys
import math
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.trading_config import TradingMode


class BybitExchange:
    """
    Production Bybit exchange client.

    Automatically uses correct API endpoint based on trading mode.
    All methods work identically for demo and live.
    """

    def __init__(self, mode: TradingMode, api_key: str, api_secret: str, base_url: str):
        """
        Initialize exchange client.

        Args:
            mode: Trading mode (DEMO or LIVE)
            api_key: API key
            api_secret: API secret
            base_url: API base URL
        """
        self.mode = mode
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.recv_window = 20000  # Increased to handle clock skew (system time issue)

        self.session = requests.Session()

        self.instrument_info_cache: Dict[str, Dict] = {}

        mode_str = "🟡 DEMO" if mode == TradingMode.DEMO else "🔴 LIVE"
        print(f"Bybit Exchange initialized: {mode_str}")
        print(f"API Endpoint: {self.base_url}")

    def _generate_signature(self, params_str: str, timestamp: str) -> str:
        """Generate HMAC SHA256 signature for V5 API."""
        param_str = str(timestamp) + self.api_key + str(self.recv_window) + params_str
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _send_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        auth_required: bool = False
    ) -> Dict:
        """Send HTTP request to Bybit V5 API."""
        url = self.base_url + endpoint
        params = params or {}

        headers = {"Content-Type": "application/json"}

        if auth_required:
            timestamp = int(time.time() * 1000)

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

            if result.get('retCode') != 0:
                raise Exception(f"Bybit API Error: {result.get('retMsg', 'Unknown error')}")

            return result

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise

    # ========== Market Data ==========

    # Add a cache for instrument info to avoid repeated API calls

    def get_instrument_info(self, symbol: str, category: str = "linear") -> Dict:
        """Gets and caches instrument rules (lot size, price filter)."""
        if symbol in self.instrument_info_cache:
            return self.instrument_info_cache[symbol]

        params = {"category": category, "symbol": symbol}
        result = self._send_request("GET", "/v5/market/instruments-info", params)
        
        info = result['result']['list'][0]
        self.instrument_info_cache[symbol] = info
        return info

    def get_ticker(self, symbol: str, category: str = "linear") -> Dict:
        """Get latest ticker."""
        params = {"category": category, "symbol": symbol}
        result = self._send_request("GET", "/v5/market/tickers", params)
        return result['result']['list'][0] if result['result']['list'] else {}

    def get_orderbook(self, symbol: str, category: str = "linear", limit: int = 25) -> Dict:
        """Get order book."""
        params = {"category": category, "symbol": symbol, "limit": limit}
        result = self._send_request("GET", "/v5/market/orderbook", params)
        return result['result']

    def get_kline(
        self,
        symbol: str,
        interval: str = "240",
        category: str = "linear",
        limit: int = 200,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict]:
        """Get candlestick data."""
        params = {
            "category": category,
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }

        if start_time:
            params['start'] = int(start_time.timestamp() * 1000)
        if end_time:
            params['end'] = int(end_time.timestamp() * 1000)

        result = self._send_request("GET", "/v5/market/kline", params)
        return result['result']['list']

    # ========== Account ==========

    def get_wallet_balance(self, account_type: str = "UNIFIED") -> Dict:
        """Get wallet balance."""
        params = {"accountType": account_type}
        result = self._send_request("GET", "/v5/account/wallet-balance", params, auth_required=True)
        return result['result']

    def get_positions(self, symbol: str = None, category: str = "linear", settle_coin: str = "USDT") -> List[Dict]:
        """
        Get positions.

        Args:
            symbol: Specific symbol (optional)
            category: linear, inverse, or option
            settle_coin: Settlement coin (USDT, USDC, etc.) - required if symbol not provided

        Note: Bybit V5 API requires either symbol OR settleCoin parameter.
        """
        params = {"category": category}

        if symbol:
            params["symbol"] = symbol
        else:
            # If no symbol specified, use settleCoin to get all positions for that settlement
            params["settleCoin"] = settle_coin

        result = self._send_request("GET", "/v5/position/list", params, auth_required=True)
        return result['result']['list']

    # ========== Trading ==========

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
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: Optional[float] = None,  # Trailing stop distance (set after order fills)
        position_idx: int = 0  # 0 for one-way mode, 1/2 for hedge mode
    ) -> Dict:
        """
        Place an order with automatic quantity formatting.

        Args:
            trailing_stop: If provided, will set trailing stop on position after order placement.
                          Note: This is the distance (in price), not percentage.
                          Example: For BTC at $60,000 with 10% trailing, pass 6000.
        """
        # 1. Fetch instrument rules
        try:
            info = self.get_instrument_info(symbol, category)
            lot_size_filter = info['lotSizeFilter']
            qty_step = float(lot_size_filter['qtyStep'])
        except Exception as e:
            print(f"Warning: Could not fetch instrument info for {symbol}. Error: {e}")
            formatted_qty = qty
        else:
            # 2. Format the quantity
            precision = str(qty_step).count('0') if '.' in str(qty_step) else 0
            formatted_qty = round(math.floor(qty / qty_step) * qty_step, precision)

        print(f"Original Qty: {qty}, Formatted Qty for {symbol}: {formatted_qty}")

        # 3. Build the parameters dictionary
        params = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(formatted_qty),
            "timeInForce": time_in_force,
        }

        # 4. Add optional parameters IF they are provided
        if price:
            params["price"] = str(price)
        if reduce_only:
            params["reduceOnly"] = True
        if stop_loss:
            params["stopLoss"] = str(stop_loss)
        if take_profit:
            params["takeProfit"] = str(take_profit)

        # 5. Send the request
        result = self._send_request("POST", "/v5/order/create", params, auth_required=True)
        order_result = result['result']

        # 6. Set trailing stop on position if requested
        # Note: Bybit API requires trailing stop to be set AFTER order fills, not during order creation
        if trailing_stop is not None and not reduce_only:
            try:
                # Small delay to ensure order fills
                import time
                time.sleep(0.5)

                # Set trailing stop on the position
                self.set_trading_stop(
                    symbol=symbol,
                    trailing_stop=trailing_stop,
                    category=category,
                    position_idx=position_idx
                )
                order_result['trailing_stop_set'] = True
                order_result['trailing_stop_distance'] = trailing_stop
            except Exception as e:
                # Don't fail the order if trailing stop fails, just log warning
                print(f"Warning: Order placed but could not set trailing stop: {e}")
                order_result['trailing_stop_set'] = False
                order_result['trailing_stop_error'] = str(e)

        return order_result

    def cancel_order(
        self,
        symbol: str,
        order_id: str = None,
        order_link_id: str = None,
        category: str = "linear"
    ) -> Dict:
        """Cancel an order."""
        params = {"category": category, "symbol": symbol}

        if order_id:
            params["orderId"] = order_id
        elif order_link_id:
            params["orderLinkId"] = order_link_id
        else:
            raise ValueError("Either order_id or order_link_id required")

        result = self._send_request("POST", "/v5/order/cancel", params, auth_required=True)
        return result['result']

    def cancel_all_orders(self, symbol: str = None, category: str = "linear") -> Dict:
        """Cancel all orders."""
        params = {"category": category}
        if symbol:
            params["symbol"] = symbol

        result = self._send_request("POST", "/v5/order/cancel-all", params, auth_required=True)
        return result['result']

    def get_open_orders(
        self,
        symbol: str = None,
        category: str = "linear",
        limit: int = 50
    ) -> List[Dict]:
        """Get open orders."""
        params = {"category": category, "limit": limit}
        if symbol:
            params["symbol"] = symbol

        result = self._send_request("GET", "/v5/order/realtime", params, auth_required=True)
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
        """Set stop loss / take profit."""
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

    def get_account_info(self, settle_coin: str = "USDT") -> Dict:
        """
        Get comprehensive account snapshot.

        Args:
            settle_coin: Settlement coin for positions (default: USDT)
        """
        balance = self.get_wallet_balance()
        positions = self.get_positions(settle_coin=settle_coin)
        open_orders = self.get_open_orders()

        return {
            "mode": self.mode.value,
            "balance": balance,
            "positions": positions,
            "open_orders": open_orders,
            "timestamp": datetime.now().isoformat()
        }

    def close_position(
        self,
        symbol: str,
        qty: float = None,
        category: str = "linear"
    ) -> Dict:
        """
        Close a position (market order).

        If qty not specified, closes entire position.
        """
        # Get current position
        positions = self.get_positions(symbol, category)
        if not positions:
            raise ValueError(f"No open position for {symbol}")

        position = positions[0]
        pos_qty = abs(float(position['size']))
        pos_side = position['side']

        # Determine close side
        close_side = "Sell" if pos_side == "Buy" else "Buy"
        close_qty = qty if qty else pos_qty

        # Place market order to close
        return self.place_order(
            symbol=symbol,
            side=close_side,
            order_type="Market",
            qty=close_qty,
            category=category,
            reduce_only=True
        )

    def health_check(self) -> Dict:
        """
        Perform health check.

        Returns status and any issues.
        """
        issues = []

        try:
            # Test market data (public)
            ticker = self.get_ticker("BTCUSDT")
            if not ticker:
                issues.append("Failed to get market data")

            # Test account access (private)
            balance = self.get_wallet_balance()
            if not balance:
                issues.append("Failed to get account balance")

        except Exception as e:
            issues.append(f"Health check error: {str(e)}")

        return {
            "healthy": len(issues) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    """Test exchange connection."""
    from config.trading_config import config

    print(f"\nTesting {config.get_mode_display()}...")

    exchange = BybitExchange(
        mode=config.TRADING_MODE,
        api_key=config.exchange.api_key,
        api_secret=config.exchange.api_secret,
        base_url=config.exchange.base_url
    )

    # Test public endpoint
    print("\n1. Testing market data (public)...")
    ticker = exchange.get_ticker("BTCUSDT")
    print(f"   BTC Price: ${float(ticker.get('lastPrice', 0)):,.2f}")

    # Test private endpoints if keys available
    if exchange.api_key and exchange.api_secret:
        print("\n2. Testing account access (private)...")
        try:
            account = exchange.get_account_info()
            print(f"   ✓ Account access successful")
            print(f"   Open Positions: {len(account['positions'])}")
            print(f"   Open Orders: {len(account['open_orders'])}")
        except Exception as e:
            print(f"   ✗ Account access failed: {e}")

        # Health check
        print("\n3. Running health check...")
        health = exchange.health_check()
        if health['healthy']:
            print("   ✓ All systems healthy")
        else:
            print(f"   ✗ Issues detected: {health['issues']}")
    else:
        print("\n⚠️  No API credentials - skipping private endpoints")

    print("\n✓ Exchange interface ready")
