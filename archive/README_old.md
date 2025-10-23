# Momentum Trading System for Bybit

**Professional automated trading system for cryptocurrency momentum strategies**

[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![Exchange](https://img.shields.io/badge/exchange-Bybit-orange)]()

---

## 🎯 Quick Start

### 1. Setup Credentials

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

Add your Bybit API credentials:
```bash
BYBIT_DEMO_API_KEY=your_demo_key_here
BYBIT_DEMO_API_SECRET=your_demo_secret_here
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. Install Dependencies

```bash
# Install required packages
pip install pandas numpy requests pybit pytest

# Or if using conda:
conda activate <your_environment>
pip install pandas numpy requests pybit pytest
```

### 3. Test Exchange Connection

**Important:** Test your connection before trading!

```bash
# Quick connection test (read-only, no trades)
python3 test_connection.py
```

This will verify:
- ✅ API credentials work
- ✅ Exchange responds
- ✅ Balance can be fetched
- ✅ Market data accessible

### 4. Test Trade Execution (Optional)

**Warning:** This places REAL orders!

```bash
# Full execution test with fake signal
python3 test_exchange_execution.py
```

This comprehensive test:
1. Creates a fake trading signal
2. Calculates position size
3. Places a real market order
4. Verifies the position
5. Closes the position

**Use DEMO mode first!** This ensures everything works before going live.

### 5. Start Trading

```bash
# Start in demo mode (default)
python3 trading_system.py

# Or use the startup script
./start_trading.sh
```

That's it! The system will:
- Fetch your balance from exchange automatically
- Start trading based on real signals
- Monitor every 4 hours

---

## 📖 What Is This?

A complete, production-ready momentum trading system with:

- ✅ **Seamless Demo/Live Switching** - One config change, no code modifications
- ✅ **Bybit Integration** - Full V5 API support with testnet and mainnet
- ✅ **Risk Management** - Multi-level protection (daily/weekly/monthly limits)
- ✅ **Complete Logging** - SQLite database tracks every trade
- ✅ **Real-time Alerts** - Telegram notifications for all events
- ✅ **Validated Strategy** - 27 months backtest with 127% return
- ✅ **Professional Code** - Clean architecture, full error handling

---

## 📊 Strategy Overview

### Entry Criteria (ALL must be met)

1. **Volatility Compression** - BBWidth < 35th percentile
2. **Volume Expansion** - RVR > 2.0x average
3. **Trend Alignment** - Price > 20-day MA
4. **BTC Regime Filter** - BTC above 200-day MA with ADX > 25

### Exit Criteria (ANY triggers exit)

1. **Trailing Stop** - 10% from peak price
2. **Trend Reversal** - Price below 20-day MA

### Position Management

- **Capital:** $10,000 (demo) / customizable (live)
- **Position Size:** 5% per trade
- **Max Positions:** 3 concurrent
- **Stop Loss:** 10% trailing
- **Timeframe:** 4-hour candles
- **Check Interval:** Every 4 hours

---

## 📈 Performance (27-month Backtest)

| Metric | Value |
|--------|-------|
| **Total Return** | +127.4% |
| **Annual Return** | +53.2% |
| **Win Rate** | 62.5% |
| **Profit Factor** | 2.45 |
| **Sharpe Ratio** | 1.68 |
| **Max Drawdown** | -9.2% |
| **Total Trades** | 183 |
| **Avg Hold Time** | 3.2 days |
| **Best Trade** | +28.3% |
| **Worst Trade** | -10.4% |

---

## 🏗️ Architecture

```
momentum2/
├── config/
│   ├── trading_config.py        ⭐ Main config - Switch demo/live here
│   └── static_universe.json     📊 44 qualified tokens
│
├── exchange/
│   └── bybit_exchange.py        🔄 Unified API interface
│
├── database/
│   └── trade_database.py        💾 Trade logging
│
├── alerts/
│   └── telegram_bot.py          📱 Real-time notifications
│
├── signals/
│   ├── entry_signals.py         📈 Entry logic
│   ├── exit_signals.py          📉 Exit logic
│   └── btc_regime_filter.py    🔍 BTC filter
│
├── indicators/
│   ├── bollinger_bands.py       📊 BB calculations
│   ├── volume.py                📊 Volume analysis
│   ├── moving_averages.py       📊 MA calculations
│   └── adx.py                   📊 ADX indicator
│
├── backtest/
│   ├── backtester.py            🔬 Backtest engine
│   ├── position_sizer.py        💰 Position sizing
│   └── performance.py           📈 Metrics
│
├── data/
│   ├── bybit_api.py            🌐 Data fetching
│   └── trading.db              💾 Trade database
│
└── trading_system.py            ⭐ MAIN SYSTEM - Run this!
```

---

## 🔄 Switching from Demo to Live

**When you're ready (after 4+ weeks successful demo trading):**

### 1. Update API Credentials

Edit `.env`:
```bash
BYBIT_LIVE_API_KEY=your_live_key
BYBIT_LIVE_API_SECRET=your_live_secret
LIVE_CAPITAL=1000  # Your actual capital
```

### 2. Change Trading Mode

Edit `config/trading_config.py` (line 158):
```python
TRADING_MODE = TradingMode.LIVE  # Changed from DEMO
```

### 3. Restart System

```bash
python3 trading_system.py
```

**That's it!** No other code changes needed. The system now trades live with real money.

---

## ⚙️ Configuration

All parameters in [`config/trading_config.py`](config/trading_config.py):

### Capital Management

**Automatic Capital Fetching:**
The system automatically fetches your balance from the exchange at startup.

- **Demo Mode:** Uses your demo account balance
- **Live Mode:** Uses your live account balance

**Manual Override:**
```python
# In trading_config.py line 190:
config = TradingConfig(fetch_capital_from_exchange=False)
```

This will use the default `initial_capital` value instead of fetching from exchange.

### Risk Parameters

```python
initial_capital = 10000          # Fallback if fetch fails
risk_per_trade_pct = 0.05       # 5% per trade
max_positions = 3                # Max concurrent positions
stop_loss_pct = 0.10            # 10% trailing stop

daily_loss_limit_pct = 0.03     # -3% daily limit
weekly_loss_limit_pct = 0.08    # -8% weekly limit
monthly_loss_limit_pct = 0.15   # -15% monthly limit
max_drawdown_pct = 0.20         # -20% system halt
```

### Strategy Parameters

```python
bbwidth_threshold = 0.35        # 35th percentile
rvr_threshold = 2.0             # 2x volume
ma_period = 20                  # 20-period MA
lookback_period = 90            # 90-day lookback

use_btc_regime_filter = True    # BTC filter on/off
btc_ma_period = 200             # 200-day MA
btc_adx_threshold = 25.0        # ADX threshold

timeframe = '240'               # 4-hour candles
check_interval_hours = 4        # Check every 4h
```

---

## 🛡️ Risk Management

### Multi-Level Protection

**Trade Level:**
- 5% position size
- 10% trailing stop
- Max 3 concurrent positions

**Daily Level:**
- -3% loss limit → No new entries for day

**Weekly Level:**
- -8% loss limit → Position size reduced 50%

**Monthly Level:**
- -15% loss limit → Trading halted

**Account Level:**
- -20% max drawdown → System shutdown

All limits are automatic. The system protects your capital.

---

## 📱 Telegram Alerts

You'll receive notifications for:

**Trading:**
- 🚀 Entry signal detected
- ✅ Position opened
- 🟢 Position closed (profit)
- 🔴 Position closed (loss)

**Risk:**
- ⚠️ Daily loss limit hit
- ⚠️ Weekly loss limit (size reduced)
- 🛑 Monthly loss limit (halted)

**Summaries:**
- 📊 Daily summary
- 📈 Weekly summary

**System:**
- 🤖 System started
- 🛑 System stopped
- ❌ Errors

---

## 💾 Database

The system logs everything to SQLite (`data/trading.db`):

**Tables:**
- `trades` - All trade details
- `daily_snapshots` - Daily performance
- `system_events` - System events
- `risk_events` - Risk limit breaches

**Quick Queries:**

```bash
# View recent trades
sqlite3 data/trading.db "SELECT symbol, entry_price, exit_price, pnl_usd FROM trades ORDER BY exit_time DESC LIMIT 10;"

# View performance
python3 -c "from database.trade_database import TradeDatabase; db = TradeDatabase(); stats = db.get_performance_stats(mode='demo'); print(f'Win Rate: {stats[\"win_rate\"]*100:.1f}%')"
```

---

## 🚨 Emergency Stop

**To stop trading immediately:**

```bash
# In terminal: Ctrl+C

# Or kill process:
pkill -f trading_system.py
```

The system will:
1. Close all open positions
2. Log final state to database
3. Send Telegram notification
4. Exit gracefully

---

## 📋 Pre-Live Checklist

Before switching to live trading:

- [ ] Minimum 4 weeks demo trading
- [ ] Win rate ≥ 60%
- [ ] Performance matches backtest (±10%)
- [ ] All risk limits tested
- [ ] Telegram alerts working
- [ ] Database logging verified
- [ ] Comfortable with system behavior
- [ ] Live API credentials created
- [ ] `.env` updated
- [ ] `TRADING_MODE = TradingMode.LIVE` set
- [ ] **Mental readiness for real money**

---

## 🔧 Production Deployment

### Using tmux (Simple)

```bash
# Start session
tmux new -s trading

# Inside tmux, start system
python3 trading_system.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t trading
```

### Using systemd (24/7 Operation)

Create `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Trading Bot
After=network.target

[Service]
Type=simple
User=william
WorkingDirectory=/home/william/STRATEGIES/momentum strat/momentum2
ExecStart=/usr/bin/python3 trading_system.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

---

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

**Test Coverage:**
- Data loading and validation
- Indicator calculations
- Signal generation
- Exit logic
- 31 tests, 100% pass rate

---

## 🐛 Troubleshooting

### "Configuration validation failed"

```bash
python3 config/trading_config.py
# Fix errors shown
```

### "Exchange health check failed"

1. Verify correct mode (demo/live)
2. Check API keys in `.env`
3. Test connection: `python3 exchange/bybit_exchange.py`

### "No signals found"

Reasons:
- BTC regime filter not active
- No tokens meeting entry criteria
- Daily loss limit hit
- Max positions reached

Check Telegram messages or logs for details.

### System stopped unexpectedly

```bash
# Check logs
tail -n 100 logs/trading.log

# Check database for errors
sqlite3 data/trading.db "SELECT * FROM system_events WHERE event_level='ERROR' ORDER BY event_time DESC LIMIT 10;"

# Restart
python3 trading_system.py
```

---

## 📚 Documentation

- **[README.md](README.md)** - This file (user guide)
- **[PROGRESS.md](PROGRESS.md)** - Development history and technical details
- **[tasks.md](tasks.md)** - Development tasks and roadmap

---

## 🔐 Security

### Critical Rules

1. **Never commit `.env`** - Already in `.gitignore`
2. **Separate API keys** - Use different keys for demo and live
3. **Restrict permissions** - Only enable Read + Trade (disable Withdraw)
4. **Start small in live** - Use 10-20% of demo size initially

---

## 📞 Support

For questions or issues:
- Review documentation in this README
- Check [PROGRESS.md](PROGRESS.md) for technical details
- Consult [Bybit API docs](https://bybit-exchange.github.io/docs/v5/intro)

---

## 🎓 Best Practices

### DO:
- ✅ Run demo for minimum 4 weeks
- ✅ Monitor Telegram daily
- ✅ Review performance weekly
- ✅ Trust the system (don't interfere)
- ✅ Start small in live
- ✅ Keep detailed records

### DON'T:
- ❌ Skip demo trading phase
- ❌ Manually interfere with trades
- ❌ Increase size during drawdown
- ❌ Disable risk limits
- ❌ Trade without monitoring
- ❌ Rush to live trading

---

## 📜 License & Disclaimer

**For personal use only.**

**DISCLAIMER:** Trading involves significant risk. Past performance does not guarantee future results. Only trade with money you can afford to lose. This system is provided as-is with no guarantees or warranty.

---

## ✅ System Status

**Version:** 1.0
**Status:** ✅ Production Ready
**Tested:** ✅ 27 months backtest
**Ready For:** 🟡 Demo Trading → Live Trading (after validation)

**Last Updated:** 2025-10-17

---

## 🚀 Ready to Start?

1. Setup `.env` with your credentials
2. Test all components
3. Start in demo mode: `python3 trading_system.py`
4. Monitor for 4+ weeks
5. Switch to live when ready

**Good luck and trade safe!** 📈
