# Test Exchange Execution Script

## Overview

The `scripts/test_exchange_execution.py` script tests the complete order execution flow, **exactly matching the production trading system**.

## What Changed

### Before (Incorrect) ❌
```python
# Placed order with fixed stop loss in one call
order = exchange.place_order(
    symbol=symbol,
    side="Buy",
    order_type="Market",
    qty=quantity,
    stop_loss=stop_loss  # Fixed stop loss
)
```

**Problems:**
- Used fixed stop loss, not trailing
- Didn't match production system behavior
- Single-step process

### After (Correct) ✅
```python
# Step 1: Place market order (no stop loss)
order = exchange.place_order(
    symbol=symbol,
    side="Buy",
    order_type="Market",
    qty=quantity
)

# Step 2: Set trailing stop on the position
exchange.set_trading_stop(
    symbol=symbol,
    trailing_stop=trailing_stop_distance,  # Trailing stop!
    category="linear",
    position_idx=0
)
```

**Benefits:**
- ✅ Matches production system exactly
- ✅ Uses exchange-side trailing stop
- ✅ Two-step process (order → trailing stop)
- ✅ Includes fallback to fixed stop if trailing fails

## Test Flow

The script now tests the **exact production flow**:

### 1. Exchange Connection
- Connects to Bybit API
- Validates credentials
- Health check

### 2. Fetch Balance
- Gets USDT balance
- Shows equity and available funds
- Determines trading capital

### 3. Market Data
- Fetches BTC ticker
- Gets orderbook
- Shows current price

### 4. Position Sizing
- Calculates position size (5% risk)
- Determines contract quantity
- Shows risk amount

### 5. Create Signal
- Generates fake signal for testing
- Sets entry price
- Adds signal strength

### 6. Order Execution ⭐ (Matches Production)
**Step 1: Place Market Order**
```python
order = exchange.place_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Market",
    qty=contracts
)
```

**Step 2: Set Trailing Stop**
```python
exchange.set_trading_stop(
    symbol="BTCUSDT",
    trailing_stop=distance,  # 10% distance
    category="linear",
    position_idx=0
)
```

**Step 3: Fallback (if trailing fails)**
```python
# If trailing stop fails, set fixed stop as backup
exchange.set_trading_stop(
    symbol="BTCUSDT",
    stop_loss=initial_stop,
    category="linear",
    position_idx=0
)
```

### 7. Position Verification
- Checks position exists
- Shows entry price
- Displays unrealized P&L

### 8. Close Position
- Closes test position
- Market order execution
- Verifies closure

## Running the Test

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env file with API credentials
BYBIT_DEMO_API_KEY=your_demo_key
BYBIT_DEMO_API_SECRET=your_demo_secret
```

### Execute Test
```bash
cd /home/william/STRATEGIES/Alpha/momentum
python3 scripts/test_exchange_execution.py
```

### Expected Output
```
================================================================================
EXCHANGE EXECUTION TEST SUITE
================================================================================

Mode: 🟡 DEMO TRADING
Exchange: https://api-demo.bybit.com

⚠️  This will place REAL orders on your exchange account!
   Make sure you're using DEMO mode for testing.

   Continue? (yes/no): yes

================================================================================
TEST 1: EXCHANGE CONNECTION
================================================================================
✓ Exchange connection healthy

================================================================================
TEST 2: FETCH BALANCE
================================================================================
✓ USDT Balance:
   Equity: $5,000.00
   Available: $5,000.00
   Used Margin: $0.00

...

================================================================================
TEST 6: ORDER EXECUTION
================================================================================
⚠️  WARNING: This will place a REAL order on your account!
   Mode: 🟡 DEMO
   Symbol: BTCUSDT
   Quantity: 0.0050
   Approximate Cost: $250.00

   Proceed with order? (yes/no): yes

   Step 1: Placing market order...
   ✓ Order placed - ID: abc123

   Step 2: Setting trailing stop (10.0%)...
   ✓ Trailing stop set: $6500.00 distance
      (Will trigger if price drops 10.0% from peak)

✓ Order Execution Complete:
   Order ID: abc123
   Entry Price: $65,000.00
   Initial Stop: $58,500.00
   Trailing Distance: $6,500.00

...

================================================================================
✓ ALL TESTS COMPLETED
================================================================================

Summary:
  ✓ Exchange connection
  ✓ Balance fetch
  ✓ Market data
  ✓ Position sizing
  ✓ Signal creation
  ✓ Order execution (market order)
  ✓ Trailing stop setup (exchange-side)
  ✓ Position verification
  ✓ Position close

🎉 Your system is ready to trade!

Note: This test mimics the production trading system flow:
  1. Place market order
  2. Set trailing stop on exchange
  3. Monitor position
  4. Close when needed
```

## Comparison: Test vs Production

| Aspect | Test Script | Production System | Match |
|--------|-------------|-------------------|-------|
| **Order Type** | Market | Market | ✅ |
| **Stop Loss Type** | Trailing | Trailing | ✅ |
| **Stop Setup** | 2-step process | 2-step process | ✅ |
| **Fallback** | Fixed stop | Fixed stop | ✅ |
| **Position Check** | Manual | Every 5 min | ✅ |
| **Exit Method** | Manual close | MA + Trailing | ⚠️ Manual only |

**Note:** The test script uses manual close for testing. Production uses:
1. MA exit (primary, 71% of trades)
2. Exchange trailing stop (backup, 29% of trades)

## Safety Features

### 1. Confirmation Prompts
```
Continue? (yes/no):
Proceed with order? (yes/no):
Close the test position? (yes/no):
```

### 2. Mode Display
```
🟡 DEMO TRADING  - Safe testing
🔴 LIVE TRADING  - Real money!
```

### 3. Error Handling
- Try/except on all API calls
- Detailed error messages
- Stack traces for debugging
- Warnings for missing stops

### 4. Position Protection
- Always sets trailing stop
- Fallback to fixed stop
- Warns if no stop set
- Prompts before close

## What Gets Tested

✅ **API Connection** - Credentials work
✅ **Balance Access** - Can fetch account info
✅ **Market Data** - Can get tickers/orderbook
✅ **Position Sizing** - Calculations correct
✅ **Order Placement** - Can place market orders
✅ **Trailing Stop** - Exchange-side setup works
✅ **Fallback Logic** - Fixed stop if trailing fails
✅ **Position Query** - Can check open positions
✅ **Position Close** - Can close positions

## Troubleshooting

### "Could not set trailing stop"
**Possible causes:**
- Account in hedge mode (need one-way mode)
- Wrong position_idx parameter
- Position not yet filled
- API permissions issue

**Solution:**
- Check Bybit account settings (one-way vs hedge mode)
- Verify API key has "Position" permission
- Script will fallback to fixed stop automatically

### "No position found"
**Possible causes:**
- Order not yet filled
- Symbol mismatch
- Position already closed

**Solution:**
- Wait a few seconds after order
- Check symbol spelling
- Verify order actually filled

### Order execution failed
**Possible causes:**
- Insufficient balance
- Invalid quantity (too small/large)
- Symbol not available
- API rate limits

**Solution:**
- Check account balance
- Verify quantity meets min/max limits
- Use valid perpetual contract symbol
- Wait between API calls

## Best Practices

1. **Always test in DEMO first**
   ```python
   TRADING_MODE = TradingMode.DEMO
   ```

2. **Use small test amounts**
   - BTC might be expensive even in demo
   - Consider cheaper tokens for testing

3. **Verify trailing stop set**
   - Check Bybit web interface
   - Look for "Trailing Stop" in position

4. **Close test positions**
   - Don't leave positions open
   - Verify closure in exchange

5. **Monitor logs**
   - Read all output messages
   - Check for warnings
   - Note any errors

## Integration with CI/CD

This test can be automated (in DEMO mode):

```bash
# In CI pipeline
export BYBIT_DEMO_API_KEY=$DEMO_KEY
export BYBIT_DEMO_API_SECRET=$DEMO_SECRET

# Run test with auto-confirmation (for CI)
echo "yes\nyes\nyes" | python3 scripts/test_exchange_execution.py
```

**Note:** Automated testing only works in DEMO mode. Live mode requires manual confirmation for safety.

---

**Last Updated:** October 23, 2025
**Status:** Production-Ready ✅
