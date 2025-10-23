# Volatility Breakout System - Build Catalog

## PHASE 1: FOUNDATION (Days 1-7)

### Day 1: Data Infrastructure
**Task 1.1: Set up data pipeline**
- Choose exchange API (Binance or Coinbase - both have good free tiers)
- Write functions to fetch OHLCV data (Open, High, Low, Close, Volume)
- Store historical data: 90 days minimum for 20 altcoins
- Test data quality: check for gaps, verify timestamps

**Task 1.2: Select asset universe**
- Pick 20 liquid altcoins (minimum $50M daily volume)
- Document trading pairs (most will be vs USDT)
- Verify each has sufficient historical data
- Create asset configuration file

**Deliverable:** Working data fetcher that updates daily

---

### Day 2-3: Core Indicators
**Task 2.1: Build Bollinger Band calculator**
- 20-period simple moving average
- 2 standard deviations for bands
- Calculate BBWidth: (Upper Band - Lower Band) / Middle Band
- Test on historical data, verify math

**Task 2.2: Build volume analyzer**
- 20-day average volume
- Relative Volume Ratio (RVR): Current Volume / Avg Volume
- Store rolling calculations

**Task 2.3: Moving average filters**
- 20-day MA for trend
- 50-day MA for regime filter
- Apply to both altcoins and BTC

**Deliverable:** Indicator library with unit tests

---

### Day 4-5: Signal Generation
**Task 3.1: Entry signal logic**
```
Function: check_entry_signal(asset, date)
  1. Calculate BBWidth percentile (90-day lookback)
  2. Check if BBWidth < 25th percentile
  3. Check if close > upper_band
  4. Check if RVR > 2.0
  5. Check if price > 20-day MA
  6. Return: True/False + signal strength
```

**Task 3.2: Exit signal logic**
```
Function: check_exit_signal(position, current_price)
  1. Calculate trailing stop (20% from peak)
  2. Check if price < trailing_stop
  3. Alternative: check if price < 20-day MA
  4. Return: True/False + exit reason
```

**Task 3.3: Market regime filter**
- Check BTC position relative to 50-day MA
- Only allow entries when BTC uptrend confirmed
- Flag "no-trade" periods

**Deliverable:** Signal generator with clear entry/exit rules

---

### Day 6-7: Backtesting Framework
**Task 4.1: Build backtester**
- Loop through historical data day-by-day
- Check signals for all 20 assets daily
- Execute simulated trades
- Track: entry price, exit price, holding period, P&L

**Task 4.2: Position sizing**
- Calculate 2% risk per trade
- Account for 20% stop distance
- Max 5 concurrent positions
- Handle position limit logic

**Task 4.3: Performance metrics**
- Win rate
- Average win/loss
- Profit factor
- Max drawdown
- Sharpe ratio
- Total trades

**Deliverable:** Working backtest showing 1 year of simulated trades

---

## PHASE 2: VALIDATION (Days 8-14)

### Day 8-9: Backtest Analysis
**Task 5.1: Run baseline backtest**
- Test on full 1-year dataset
- Document all trades in spreadsheet
- Calculate performance metrics
- Identify best/worst performing assets

**Task 5.2: Sensitivity analysis**
- Test BBWidth threshold: 20th, 25th, 30th percentiles
- Test RVR threshold: 1.5, 2.0, 2.5
- Test trailing stop: 15%, 20%, 25%
- Document which parameters are robust

**Task 5.3: Walk-forward testing**
- Split data: first 6 months train, last 6 months test
- Optimize on training, validate on test
- Check if performance holds out-of-sample

**Deliverable:** Documented backtest results with parameter analysis

---

### Day 10-11: Risk Management
**Task 6.1: Implement capital controls**
- Position size calculator
- Maximum portfolio exposure limits
- Per-asset exposure limits
- Correlation checks (basic)

**Task 6.2: Drawdown protection**
- Track running max equity
- Calculate current drawdown
- Halt trading if drawdown > 15%
- Resume logic after recovery

**Task 6.3: Edge case handling**
- What if all 20 assets signal simultaneously?
- What if can't exit at stop price (gaps)?
- What if exchange is down?
- Document procedures for each

**Deliverable:** Risk management module with documented rules

---

### Day 12-14: Paper Trading Setup
**Task 7.1: Build execution simulator**
- Connect to live market data (not historical)
- Run signal checks in real-time
- Log hypothetical trades
- No actual money at risk

**Task 7.2: Create monitoring dashboard**
- Current positions
- Open signals
- Portfolio equity curve
- Daily P&L
- System health checks

**Task 7.3: Alerting system**
- Email/SMS when signal fires
- Alert when position hits stop
- Alert on system errors
- Daily performance summary

**Deliverable:** Paper trading system running live

---

## PHASE 3: LIVE DEPLOYMENT (Days 15-21)

### Day 15-16: Pre-Launch Checklist
**Task 8.1: Code review**
- Check all calculations manually
- Verify order logic
- Test failure scenarios
- Review position sizing math

**Task 8.2: Exchange integration**
- Set up API keys (read + trade permissions)
- Test order placement on testnet
- Verify order fills
- Check fee structure

**Task 8.3: Capital allocation**
- Start with $1000-2000 (not your $10k)
- Calculate max loss per trade ($20-40)
- Verify account can handle 5 positions
- Document risk limits

**Deliverable:** System ready for live trading with small capital

---

### Day 17-18: Launch
**Task 9.1: Go live**
- Deploy with micro positions (1/10th normal size)
- Monitor first 3-5 trades manually
- Verify execution matches backtest logic
- Document any discrepancies

**Task 9.2: Real-time monitoring**
- Check system every 4 hours minimum
- Log all trades immediately
- Compare fills to expectations
- Track slippage and fees

**Deliverable:** First week of live trading data

---

### Day 19-21: Post-Launch Review
**Task 10.1: Compare live vs backtest**
- Win rate matching?
- Slippage within tolerance?
- Any unexpected behaviors?
- System stability issues?

**Task 10.2: Iteration planning**
- What worked well?
- What needs adjustment?
- Which improvements to prioritize?
- Document lessons learned

**Deliverable:** Week 1 performance report + improvement roadmap

---

## PHASE 4: OPTIMIZATION (Month 2+)

### Week 5-6: Incremental Improvements
**Task 11.1: Refine parameters**
- Adjust only if clear edge appears
- Test each change separately
- Require 20+ trades before judging
- Keep changes minimal

**Task 11.2: Add simple enhancements**
- Asset-specific volume thresholds
- Time-of-day filters (avoid low liquidity hours)
- Better trailing stop logic
- Nothing complex yet

---

### Week 7-8: Scale Gradually
**Task 12.1: Increase position size**
- Only if profitable after 30+ trades
- Increase by 25% increments
- Monitor drawdown closely
- Scale back immediately if issues

**Task 12.2: Expand universe**
- Add 5-10 more altcoins
- Test thoroughly in paper trading first
- Maintain same risk per position
- Monitor correlation

---

## CRITICAL RULES

**Never do these:**
1. Don't trade real money until paper trading matches backtest
2. Don't increase position size during losing streak
3. Don't add complexity without proving it helps
4. Don't optimize on less than 50 trades
5. Don't risk more than 2% per trade, ever

**Stop trading if:**
1. Live performance diverges significantly from backtest
2. Drawdown exceeds 15%
3. System has technical failures
4. You can't monitor it properly

---

## Tools You'll Need

**Essential:**
- Python 3.8+ with pandas, numpy, requests
- Exchange API library (ccxt recommended)
- Database (SQLite is fine to start)
- Basic plotting (matplotlib)

**Optional:**
- Jupyter notebooks for analysis
- Cloud server for 24/7 operation (AWS/DigitalOcean)
- Monitoring service (UptimeRobot)

---

This is your 3-week build plan. Don't skip ahead. Each phase builds on the previous. Most failures come from rushing to live trading before proper validation.

Start tomorrow with Day 1, Task 1.1. Actually write the code. Research time is over.