# Installation Instructions

## ✅ What's Already Done

Your system is **configured and tested**! All API connections work perfectly.

**Current Status:**
- ✅ API credentials configured
- ✅ Exchange connection tested ($5,000 balance detected)
- ✅ All API endpoints working
- ✅ Code fixes applied
- ⏳ **Only missing: Python dependencies**

---

## 🚀 Final Installation Steps

### Step 1: Install Python Dependencies

You need to install pandas, numpy, requests, and pybit.

**Choose ONE method below:**

### Method A: Using pip (Recommended)

```bash
pip install pandas numpy requests pybit
```

### Method B: Using conda

```bash
conda install pandas numpy requests
pip install pybit
```

### Method C: System package manager (Ubuntu/Debian)

```bash
sudo apt install python3-pandas python3-numpy python3-requests
pip install --user pybit
```

---

## 🧪 Verify Installation

After installing, test everything works:

```bash
# Test 1: Verify packages installed
python3 -c "import pandas, numpy, requests; print('✓ All packages installed')"

# Test 2: Full connection test
python3 test_connection.py

# Test 3: Optional execution test (places real orders!)
python3 test_exchange_execution.py
```

---

## 🎯 Expected Results

### Test 1: Package Check
```
✓ All packages installed
```

### Test 2: Connection Test
```
================================================================================
EXCHANGE CONNECTION TEST
================================================================================

Mode: 🟡 DEMO TRADING
API Endpoint: https://api-demo.bybit.com
Capital (configured): $5,000.00

1. Connecting to exchange...
   ✓ Exchange initialized

2. Running health check...
   ✓ Health check passed

3. Testing public endpoint (market data)...
   ✓ BTC Price: $107,xxx.xx
   ✓ 24h Volume: xxx,xxx contracts

4. Testing private endpoint (account balance)...
   ✓ Account Type: UNIFIED
   ✓ USDT Equity: $5,000.00
   ✓ USDT Available: $0.00

5. Testing position query...
   ✓ Open Positions: 0

================================================================================
✓ CONNECTION TEST PASSED
================================================================================
```

### Test 3: Execution Test
```
... (walks through creating a test trade)

⚠️  This will place REAL orders on your demo account!
Asks for confirmation at each step.
```

---

## 🚀 Start Trading

Once all tests pass:

```bash
python3 trading_system.py
```

The system will:
1. Fetch your $5,000 balance automatically
2. Start monitoring every 4 hours
3. Execute trades when signals appear
4. Log everything to database
5. Send Telegram alerts (if enabled)

---

## 🐛 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'pandas'"

**Solution:** Install pandas:
```bash
pip install pandas
```

### Problem: "externally-managed-environment"

**Solution:** Use `--break-system-packages` (safe for development):
```bash
pip install --break-system-packages pandas numpy requests pybit
```

**OR** create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas numpy requests pybit
```

### Problem: "Permission denied"

**Solution:** Install for user only:
```bash
pip install --user pandas numpy requests pybit
```

### Problem: pip not found

**Solution:** Install pip:
```bash
sudo apt install python3-pip
```

---

## 📋 Complete Checklist

Before running trading system:

- [ ] Python 3.8+ installed (`python3 --version`)
- [ ] pip installed (`pip --version`)
- [ ] pandas installed (`python3 -c "import pandas"`)
- [ ] numpy installed (`python3 -c "import numpy"`)
- [ ] requests installed (`python3 -c "import requests"`)
- [ ] pybit installed (optional but recommended)
- [ ] `.env` file configured with API keys
- [ ] Connection test passing (`python3 test_connection.py`)
- [ ] Ready to trade!

---

## 🎉 You're Almost There!

**One command away from trading:**

```bash
pip install pandas numpy requests pybit
```

Then:

```bash
python3 trading_system.py
```

---

## 📞 Quick Reference

### Test without dependencies (works now):
```bash
python3 test_api_simple.py
```

### Test with dependencies (after installing):
```bash
python3 test_connection.py
```

### Start trading (after installing):
```bash
python3 trading_system.py
```

### Emergency stop:
```
Ctrl+C
```

---

**System Status:** ✅ Ready (pending dependency installation)

**Next Step:** Install pandas and numpy

**Time Required:** 1-2 minutes
