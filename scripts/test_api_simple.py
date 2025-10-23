"""
Simple API Test - No Dependencies

Tests basic connection to Bybit without requiring pandas or other dependencies.
Just tests if your API credentials work.
"""

import os
import sys
from pathlib import Path

# Load .env manually
def load_env():
    env_path = Path(__file__).parent / '.env'
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

load_env()

# Get credentials
api_key = os.getenv('BYBIT_DEMO_API_KEY', '')
api_secret = os.getenv('BYBIT_DEMO_API_SECRET', '')
base_url = 'https://api-demo.bybit.com'

print("="*80)
print("SIMPLE API CONNECTION TEST")
print("="*80)
print(f"\nAPI Endpoint: {base_url}")
print(f"API Key: {api_key[:10]}..." if api_key else "API Key: NOT SET")

if not api_key or not api_secret:
    print("\n❌ ERROR: API credentials not found in .env file")
    print("\nPlease:")
    print("  1. Copy .env.example to .env")
    print("  2. Add your Bybit demo API credentials")
    sys.exit(1)

# Test with requests
import requests
import time
import hmac
import hashlib
import json

def generate_signature(params_str, timestamp):
    """Generate HMAC SHA256 signature."""
    recv_window = 5000
    param_str = str(timestamp) + api_key + str(recv_window) + params_str
    return hmac.new(
        api_secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# Test 1: Public endpoint (no auth)
print("\n1. Testing public endpoint...")
try:
    response = requests.get(f"{base_url}/v5/market/tickers?category=linear&symbol=BTCUSDT", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('retCode') == 0:
            ticker = data['result']['list'][0]
            price = float(ticker['lastPrice'])
            print(f"   ✓ BTC Price: ${price:,.2f}")
        else:
            print(f"   ✗ API Error: {data.get('retMsg')}")
    else:
        print(f"   ✗ HTTP Error: {response.status_code}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 2: Private endpoint (with auth)
print("\n2. Testing private endpoint (account balance)...")
try:
    timestamp = int(time.time() * 1000)
    params = "accountType=UNIFIED"

    signature = generate_signature(params, timestamp)

    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": signature,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{base_url}/v5/account/wallet-balance?{params}",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('retCode') == 0:
            print("   ✓ Authentication successful")

            # Try to parse balance
            result = data.get('result', {})
            if 'list' in result and len(result['list']) > 0:
                account = result['list'][0]
                print(f"   ✓ Account Type: {account.get('accountType', 'Unknown')}")

                if 'coin' in account:
                    for coin in account['coin']:
                        if coin['coin'] == 'USDT':
                            equity_str = coin.get('equity', '0')
                            available_str = coin.get('availableToWithdraw', '0')

                            equity = float(equity_str) if equity_str and equity_str != '' else 0.0
                            available = float(available_str) if available_str and available_str != '' else 0.0

                            print(f"   ✓ USDT Equity: ${equity:,.2f}")
                            print(f"   ✓ USDT Available: ${available:,.2f}")

                            if equity == 0.0:
                                print("   ⚠️  Balance is $0.00 - Account is empty")
                                print("      This is normal for a new demo account")
                            break
            else:
                print("   ⚠️  No account data in response")
        else:
            print(f"   ✗ API Error: {data.get('retMsg')}")
            print(f"      Code: {data.get('retCode')}")
    else:
        print(f"   ✗ HTTP Error: {response.status_code}")
        print(f"      Response: {response.text[:200]}")

except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Position query
print("\n3. Testing position query...")
try:
    timestamp = int(time.time() * 1000)
    params = "category=linear&settleCoin=USDT"

    signature = generate_signature(params, timestamp)

    headers = {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-SIGN": signature,
        "X-BAPI-SIGN-TYPE": "2",
        "X-BAPI-TIMESTAMP": str(timestamp),
        "X-BAPI-RECV-WINDOW": "5000",
        "Content-Type": "application/json"
    }

    response = requests.get(
        f"{base_url}/v5/position/list?{params}",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('retCode') == 0:
            positions = data['result']['list']
            open_positions = [p for p in positions if float(p.get('size', 0)) > 0]

            print(f"   ✓ Open Positions: {len(open_positions)}")

            if open_positions:
                print("   Position Details:")
                for pos in open_positions:
                    symbol = pos.get('symbol')
                    size = float(pos.get('size', 0))
                    side = pos.get('side')
                    avg_price = float(pos.get('avgPrice', 0))
                    unrealized_pnl = float(pos.get('unrealisedPnl', 0))

                    print(f"      • {symbol}: {side} {size} @ ${avg_price:,.2f}")
                    print(f"        Unrealized P&L: ${unrealized_pnl:+,.2f}")
            else:
                print("   ℹ️  No open positions")
        else:
            print(f"   ✗ API Error: {data.get('retMsg')}")
    else:
        print(f"   ✗ HTTP Error: {response.status_code}")

except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "="*80)
print("✓ ALL TESTS COMPLETE")
print("="*80)
print("\nIf all tests passed, your API credentials work perfectly!")
print("\nNext step: Install dependencies")
print("  pip install pandas numpy requests pybit")
