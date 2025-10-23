# Testing Guide

Complete guide to testing your trading system before going live.

---

## 🎯 Overview

This guide walks you through testing your system in the correct order:

1. **Connection Test** - Verify API access (read-only)
2. **Execution Test** - Test real order placement with fake signal
3. **System Test** - Run the full trading system

---

## ✅ Step 1: Connection Test

**Purpose:** Verify your API credentials work and exchange responds.

**No trades placed** - completely safe.

```bash
python3 test_connection.py
```

### What It Tests:

- ✓ Exchange initialization
- ✓ Health check
- ✓ Market data (public endpoint)
- ✓ Account balance (private endpoint)
- ✓ Position queries

### Expected Output:

```
================================================================================
EXCHANGE CONNECTION TEST
================================================================================

Mode: 🟡 DEMO TRADING
API Endpoint: https://api-demo.bybit.com
Capital (configured): $10,000.00

1. Connecting to exchange...
   ✓ Exchange initialized

2. Running health check...
   ✓ Health check passed

3. Testing public endpoint (market data)...
   ✓ BTC Price: $65,432.10
   ✓ 24h Volume: 1,234,567 contracts

4. Testing private endpoint (account balance)...
   ✓ Account Type: UNIFIED
   ✓ USDT Equity: $10,000.00
   ✓ USDT Available: $10,000.00

5. Testing position query...
   ✓ Open Positions: 0

================================================================================
✓ CONNECTION TEST PASSED
================================================================================
```

### Troubleshooting:

**"API key not found"**
- Check your `.env` file has correct credentials
- Verify you're in the right mode (demo/live)

**"Health check failed"**
- Check internet connection
- Verify API endpoint is correct
- Try regenerating API keys

---

## 🧪 Step 2: Execution Test

**Purpose:** Test complete order flow with a fake signal.

**⚠️ WARNING: This places REAL orders!** Use DEMO mode first.

```bash
python3 test_exchange_execution.py
```

### What It Tests:

1. ✓ Exchange connection
2. ✓ Balance fetch
3. ✓ Market data
4. ✓ Position sizing calculation
5. ✓ Fake signal creation
6. ✓ **Real order placement**
7. ✓ Position verification
8. ✓ Position close

### Test Flow:

The script will:
1. Connect to exchange
2. Fetch your balance
3. Get current BTC price
4. Create a fake trading signal
5. Calculate position size
6. **Ask for confirmation** before placing order
7. Place a real market buy order
8. Verify the position opened
9. **Ask for confirmation** before closing
10. Close the position

### Expected Output:

```
================================================================================
EXCHANGE EXECUTION TEST SUITE
================================================================================

Mode: 🟡 DEMO TRADING
Exchange: https://api-demo.bybit.com

⚠️  This will place REAL orders on your exchange account!
   Make sure you're using DEMO mode for testing.

   Continue? (yes/no): yes

... [connection and balance tests] ...

================================================================================
TEST 6: ORDER EXECUTION
================================================================================
⚠️  WARNING: This will place a REAL order on your account!
   Mode: 🟡 DEMO
   Symbol: BTCUSDT
   Quantity: 0.0076
   Approximate Cost: $500.00

   Proceed with order? (yes/no): yes

   Placing order...
✓ Order Executed:
   Order ID: abc123...
   Entry Price: $65,432.10
   Stop Loss: $58,888.89

... [position check] ...

   Close the test position? (yes/no): yes

   Closing position...
✓ Position Closed

================================================================================
✓ ALL TESTS COMPLETED
================================================================================
```

### Safety Notes:

- **Always test in DEMO mode first**
- The script asks for confirmation before each order
- You can cancel at any prompt by typing "no"
- Positions are closed at the end (if you confirm)

---

## 🚀 Step 3: System Test

**Purpose:** Run the actual trading system.

**Uses real signals** - will trade automatically when signals appear.

```bash
python3 trading_system.py
```

### What It Does:

- Fetches your balance from exchange
- Initializes all components (database, alerts, risk management)
- Starts monitoring loop (every 4 hours)
- Scans for entry signals
- Executes trades when signals appear
- Manages positions with trailing stops
- Enforces risk limits

### Expected Output:

```
================================================================================
INITIALIZING TRADING SYSTEM
================================================================================

✓ Fetched capital from exchange: $10,000.00

================================================================================
TRADING SYSTEM CONFIGURATION
================================================================================

Mode: 🟡 DEMO TRADING
Exchange: Bybit (https://api-demo.bybit.com)

Capital: $10,000.00
Position Size: 5.0% per trade
Max Positions: 3
Stop Loss: 10.0%

... [configuration details] ...

✓ Trading system initialized successfully

================================================================================
🟡 DEMO TRADING - STARTING
================================================================================

✓ System started. Press Ctrl+C to stop

================================================================================
ITERATION 1 - 2025-10-17 14:00:00
================================================================================

[2025-10-17 14:00:00] Running trading loop...
  Checking exits (0 positions)...
  Scanning for signals...
  BTC regime filter: Not active. Skipping signals.
  No signals found
  Capital: $10,000.00 | Positions: 0

💤 Next check: 2025-10-17 18:00:00
   (4.0 hours)
```

### Monitoring:

- Check Telegram for alerts (if enabled)
- View database: `sqlite3 data/trading.db`
- Monitor logs in terminal
- Press `Ctrl+C` to stop gracefully

---

## 📊 Pre-Live Checklist

Before switching from DEMO to LIVE:

### Minimum Requirements:

- [ ] Connection test passed
- [ ] Execution test passed (with demo account)
- [ ] System ran successfully for 4+ weeks in demo
- [ ] Win rate ≥ 60%
- [ ] Performance matches backtest expectations
- [ ] No unexpected errors or crashes
- [ ] Risk limits working correctly
- [ ] Comfortable with system behavior

### Technical Checks:

- [ ] Telegram alerts working (if enabled)
- [ ] Database logging verified
- [ ] Emergency stop tested (Ctrl+C)
- [ ] Balance fetch working
- [ ] Position sizing correct
- [ ] Stop losses placing correctly

### Mental Preparation:

- [ ] Understand this uses real money
- [ ] Prepared for drawdowns
- [ ] Will not interfere with trades
- [ ] Trust the system
- [ ] Know how to stop immediately

---

## 🔄 Running Tests in Order

### First Time Setup:

```bash
# 1. Install dependencies
pip install pandas numpy requests pybit

# 2. Configure .env
cp .env.example .env
nano .env  # Add your API keys

# 3. Test connection
python3 test_connection.py

# 4. Test execution (DEMO mode!)
python3 test_exchange_execution.py

# 5. Start system (DEMO mode)
python3 trading_system.py
```

### Before Going Live:

```bash
# 1. Re-run connection test with live credentials
python3 test_connection.py

# 2. Re-run execution test with live account (SMALL SIZE!)
python3 test_exchange_execution.py

# 3. Switch to live mode
# Edit config/trading_config.py line 188:
# TRADING_MODE = TradingMode.LIVE

# 4. Start live trading
python3 trading_system.py
```

---

## 🆘 Emergency Procedures

### Stop Trading Immediately:

```bash
# In terminal: Ctrl+C

# Or kill process:
pkill -f trading_system.py
```

### Close All Positions Manually:

1. Go to Bybit dashboard
2. Navigate to Positions
3. Click "Close All"

---

## 📞 Support

If tests fail:

1. **Check logs:** Review terminal output for errors
2. **Verify credentials:** Check `.env` file
3. **Test mode:** Ensure using correct mode (demo/live)
4. **API permissions:** Verify API keys have trading permissions
5. **Internet:** Check connection is stable
6. **Bybit status:** Check if exchange is operational

---

## ✅ Success Criteria

**Connection Test Success:**
- All 5 checks pass
- Balance displays correctly
- No API errors

**Execution Test Success:**
- Order places successfully
- Position appears in account
- Position closes successfully
- No execution errors

**System Test Success:**
- Initializes without errors
- Fetches balance correctly
- Runs for multiple iterations
- No crashes or freezes
- Risk limits working
- Trades execute when signals appear

---

**Last Updated:** 2025-10-17
**Version:** 1.0
