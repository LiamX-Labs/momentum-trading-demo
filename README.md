# Momentum Breakout Trading System
## "Apex Momentum" - 4H Altcoin Breakout Strategy

**Automated trading system that captures high-quality breakout opportunities in cryptocurrency markets**

---

## 📊 Performance Summary

**Backtest Results (27 months: Aug 2023 - Oct 2025)**
- **Total Return:** +252%
- **Total Trades:** 306
- **Win Rate:** 37.6%
- **Profit Factor:** 2.18
- **Max Drawdown:** -23.11%
- **Sharpe Ratio:** 0.67
- **Best Trade:** +297.8% (BLESSUSDT)

---

## 🎯 Strategy Overview

### Core Philosophy
Capture explosive momentum moves in altcoins by identifying volatility compression zones and entering only when risk/reward is heavily in our favor.

### Entry Criteria
1. **Volatility Compression** - BBWidth below 35th percentile
2. **Risk/Reward Setup** - RVR > 2.0 (2x+ reward vs risk)
3. **Momentum Confirmation** - Price action on 4H timeframe
4. **Position Sizing** - 5% risk per trade, max 3 positions

### Exit Strategy
- **Primary: MA Exit** - Closes when price crosses below 20-period MA (~71% of trades)
- **Backup: 10% Trailing Stop** - Exchange-managed, 24/7 protection (~29% of trades)
- **Hybrid Protection** - Software + exchange-side redundancy
- **Dynamic Risk Management** - Daily/weekly loss limits

### Risk Management
- **Daily Loss Limit:** -3% (stops new entries)
- **Weekly Loss Limit:** -8% (reduces size 50%)
- **Max Positions:** 3 concurrent
- **Position Size:** 5% per trade

---

## 🚀 Quick Start

### 1. Installation

```bash
cd /path/to/momentum
conda activate
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file:
```bash
BYBIT_DEMO_API_KEY=your_demo_key
BYBIT_DEMO_API_SECRET=your_demo_secret
BYBIT_LIVE_API_KEY=your_live_key
BYBIT_LIVE_API_SECRET=your_live_secret

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=true
```

### 3. Set Trading Mode

Edit `config/trading_config.py`:
```python
TRADING_MODE = TradingMode.DEMO  # or TradingMode.LIVE
```

### 4. Run

```bash
# Start trading
python trading_system.py

# Setup performance reports (runs at 00:00 UTC daily)
./scripts/setup_cron.sh
```

---

## ⚙️ Configuration

### Strategy Parameters

```python
# Entry Filters
bbwidth_threshold = 0.35      # 35th percentile
rvr_threshold = 2.0           # Minimum 2:1 reward/risk
ma_period = 20                # 20-period MA
lookback_period = 90          # 90-period lookback

# BTC Regime Filter
use_btc_regime_filter = False # DISABLED (proven to reduce performance)

# Risk Management
risk_per_trade_pct = 0.05     # 5% per trade
max_positions = 3             # Max 3 concurrent
stop_loss_pct = 0.10          # 10% trailing
daily_loss_limit_pct = 0.03   # 3% daily
weekly_loss_limit_pct = 0.08  # 8% weekly
```

---

## 📁 Project Structure

```
momentum/
├── trading_system.py          # Main production system
├── Dockerfile                 # Docker container config
├── docker-compose.unified.yml # Docker compose setup
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not tracked)
├── .gitignore                 # Git ignore rules
│
├── config/                    # Configuration files
│   ├── trading_config.py      # DEMO/LIVE switch & parameters
│   ├── assets.py              # Asset definitions
│   ├── universe.json          # Trading universe
│   └── static_universe.json   # 44-token universe
│
├── data/                      # Data management
│   ├── bybit_api.py           # Exchange data fetching
│   ├── data_loader.py         # Historical data loading
│   ├── data_validator.py      # Data quality checks
│   └── data_updater.py        # Data refresh utilities
│
├── signals/                   # Signal generation
│   ├── entry_signals.py       # Entry logic
│   ├── exit_signals.py        # Exit logic
│   ├── regime_filter.py       # Market regime detection
│   └── btc_regime_filter.py   # BTC-specific filters
│
├── indicators/                # Technical indicators
│   ├── moving_averages.py     # MA calculations
│   ├── bollinger_bands.py     # BBands & BBWidth
│   ├── adx.py                 # ADX indicator
│   └── volume.py              # Volume metrics
│
├── backtest/                  # Backtesting engine
│   ├── realistic_backtester.py # Main backtester
│   ├── backtester.py          # Basic backtester
│   ├── position_sizer.py      # Position sizing logic
│   └── performance.py         # Performance metrics
│
├── exchange/                  # Exchange integration
│   └── bybit_exchange.py      # Bybit API wrapper
│
├── database/                  # Trade database
│   └── trade_database.py      # SQLite trade logging
│
├── alerts/                    # Notification system
│   └── telegram_bot.py        # Telegram integration
│
├── scripts/                   # Utility scripts
│   ├── run_realistic_backtest.py    # Run backtests
│   ├── run_backtest.py              # Basic backtest runner
│   ├── performance_analysis.py      # Daily/weekly reports
│   ├── check_btc_regime.py          # Check BTC regime
│   ├── test_connection.py           # Test exchange connection
│   ├── test_api_simple.py           # Simple API test
│   ├── test_exchange_execution.py   # Test order execution
│   ├── setup_cron.sh                # Setup cron jobs
│   └── start_trading.sh             # Start trading script
│
├── tests/                     # Unit tests
│   ├── test_data_loader.py
│   ├── test_indicators.py
│   ├── test_data_validator.py
│   └── test_signals.py
│
├── docs/                      # Documentation
│   ├── BTC_REGIME_FILTER_ANALYSIS.md # Filter analysis
│   ├── DOCKER_DEPLOYMENT.md          # Docker guide
│   ├── DOCKER_SUMMARY.md             # Docker summary
│   └── PROGRESS.md                   # Development log
│
├── archive/                   # Archived documents
├── logs/                      # Application logs
├── results/                   # Backtest results
└── cache/                     # Data cache
```

---

## 📈 Performance Analysis

### Automated Reports

Runs daily at **00:00 UTC**:
- **Daily Report** - Last 24 hours
- **Weekly Report** - Mondays only

Setup:
```bash
./scripts/setup_cron.sh
```

Manual run:
```bash
python scripts/performance_analysis.py
```

---

## 🕐 Trading Schedule

### 4H Candle Alignment (UTC)
- **00:00** - Candle open
- **04:00** - Candle open
- **08:00** - Candle open
- **12:00** - Candle open
- **16:00** - Candle open
- **20:00** - Candle open

System automatically aligns checks with these times.

---

## 🔄 DEMO ↔ LIVE Switch

**One line change:**

Edit `config/trading_config.py`:
```python
TRADING_MODE = TradingMode.LIVE  # Change from DEMO
```

That's it! System validates config and confirms mode at startup.

---

## 📊 BTC Regime Filter Decision

**Tested:** BTC filter (price > 200 MA AND ADX > 25)
**Result:** Reduced performance by **17x**

| Metric | Without Filter | With Filter |
|--------|---------------|-------------|
| Return | +252% | +15% |
| Trades | 306 | 38 |
| Sharpe | 0.67 | 0.26 |

**Decision:** Run WITHOUT filter.

**Why:** Too restrictive, missed massive winners, capital idle for months. Our BBWidth + RVR filters already select quality setups.

See: [docs/BTC_REGIME_FILTER_ANALYSIS.md](docs/BTC_REGIME_FILTER_ANALYSIS.md)

---

## 🎛️ Risk Controls

### Position Level
- **MA Exit** - Primary exit when momentum fades (71% of trades)
- **10% Trailing Stop** - Exchange-managed backup (29% of trades)
- **Dual Protection** - Software + exchange redundancy
- **Max 3 Concurrent** positions

### Account Level
- **Daily:** -3% limit (stops new entries)
- **Weekly:** -8% limit (reduces size 50%)
- **Monthly:** -15% limit (halts trading)
- **Max DD:** -20% (system shutdown)

---

## 📱 Telegram Alerts

Notifications for:
- ✅ Trade entries/exits
- ✅ Daily/weekly reports
- ⚠️ Risk limit breaches
- ❌ System errors

---

## 🧪 Testing

```bash
# Test exchange connection (read-only)
python scripts/test_connection.py

# Test full execution flow (places real orders!)
python scripts/test_exchange_execution.py

# Run backtest
python scripts/run_realistic_backtest.py

# Check BTC regime
python scripts/check_btc_regime.py
```

**Important:** `test_exchange_execution.py` places REAL orders on the exchange. Always test in DEMO mode first!

---

## ⚠️ Important Notes

1. **Start with DEMO** - Test first
2. **Monitor Closely** - Especially first weeks
3. **Trust the Filters** - Don't force trades
4. **Let Winners Run** - Trailing stops work
5. **Respect Limits** - Risk controls protect you

---

## 📚 Documentation

- **README.md** - This file (quick reference)
- **[docs/PROGRESS.md](docs/PROGRESS.md)** - Development history, decisions, learnings
- **[docs/BTC_REGIME_FILTER_ANALYSIS.md](docs/BTC_REGIME_FILTER_ANALYSIS.md)** - Filter testing results
- **[docs/EXIT_MECHANISMS_ANALYSIS.md](docs/EXIT_MECHANISMS_ANALYSIS.md)** - Complete exit strategy breakdown
- **[docs/TRAILING_STOP_IMPLEMENTATION.md](docs/TRAILING_STOP_IMPLEMENTATION.md)** - Exchange-side trailing stops
- **[docs/SIMPLIFIED_ORDER_EXECUTION.md](docs/SIMPLIFIED_ORDER_EXECUTION.md)** - One-call order + trailing stop
- **[docs/TEST_EXECUTION_SCRIPT.md](docs/TEST_EXECUTION_SCRIPT.md)** - Test script documentation
- **[docs/SCRIPTS_PATH_FIX.md](docs/SCRIPTS_PATH_FIX.md)** - Running scripts from any directory
- **[docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)** - Docker deployment guide
- **[docs/DOCKER_SUMMARY.md](docs/DOCKER_SUMMARY.md)** - Docker summary

---

## System Name Suggestions

**Current:** "Momentum Breakout Trading System"

**Suggestions:**
1. **Apex Momentum** - Professional, sharp, conveys top-tier performance
2. **Compression Alpha** - Highlights the BBWidth edge
3. **Breakout Edge** - Simple, clear, describes what it does
4. **Momentum Nexus** - Modern, tech-forward
5. **Volatility Harvester** - Descriptive of the strategy

**Recommended:** **Apex Momentum** 🎯

---

**Built with Claude Code**
**Last Updated:** October 21, 2025
