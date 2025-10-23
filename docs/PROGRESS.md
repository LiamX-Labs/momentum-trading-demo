# Development Progress & Decisions
## Apex Momentum Trading System

**Complete development history, key decisions, and learnings**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Development Timeline](#development-timeline)
3. [Key Technical Decisions](#key-technical-decisions)
4. [Backtest Results](#backtest-results)
5. [BTC Regime Filter Analysis](#btc-regime-filter-analysis)
6. [Universe Selection](#universe-selection)
7. [Risk Management Evolution](#risk-management-evolution)
8. [Deployment Setup](#deployment-setup)
9. [Lessons Learned](#lessons-learned)

---

## System Overview

**Name:** Apex Momentum
**Strategy Type:** 4H Altcoin Momentum Breakout
**Markets:** Cryptocurrency (Bybit USDT perpetuals)
**Timeframe:** 4-hour candles

### Core Edge

The system's edge comes from:
1. **Volatility Compression Detection** - BBWidth at 35th percentile identifies tight consolidations
2. **Risk/Reward Filtering** - Only trades with 2:1+ RVR (filters out 70-80% of setups)
3. **Trailing Stops** - Captures explosive moves while cutting losses quickly
4. **Static Quality Universe** - 44 tokens selected for consistency and volume

---

## Development Timeline

### Phase 1: Strategy Design (Oct 2025)

**Initial Concept:**
- Trade altcoin momentum breakouts on 4H timeframe
- Use Bollinger Band width to identify compression
- Enter on breakouts with favorable risk/reward

**Key Decisions:**
- ✅ 4H timeframe chosen (balance between signals and noise)
- ✅ BBWidth percentile approach (relative measure, adapts to market)
- ✅ RVR threshold of 2.0 (ensures quality over quantity)
- ✅ Trailing stop vs fixed stop (lets winners run)

### Phase 2: Backtesting Engine (Oct 2025)

**Initial Backtest:**
- Static universe from warehouse data
- Simple simulation without slippage
- Results: Promising but unrealistic

**Realistic Backtest Development:**
- ✅ Live API data from Bybit
- ✅ Dynamic universe updates
- ✅ Symbol availability checks
- ✅ Realistic fills and slippage
- ✅ 27-month test period (Aug 2023 - Oct 2025)

**Result:** 252% return over 27 months with 0.67 Sharpe ratio

### Phase 3: Production System (Oct 2025)

**Built:**
- Unified DEMO/LIVE system (single config switch)
- Database logging for all trades
- Telegram alerts for all events
- Multi-level risk management
- Health monitoring
- Graceful shutdown handling

**Integration:**
- Bybit exchange API
- SQLite database
- Telegram bot
- Cron scheduling for reports

### Phase 4: BTC Regime Filter Testing (Oct 21, 2025)

**Hypothesis:** Only trade when BTC is bullish (price > 200 MA AND ADX > 25)

**Test Results:**
- WITH filter: +15% return, 38 trades
- WITHOUT filter: +252% return, 306 trades
- **Filter reduced performance by 17x**

**Decision:** Run WITHOUT BTC regime filter

See: [BTC_REGIME_FILTER_ANALYSIS.md](BTC_REGIME_FILTER_ANALYSIS.md)

### Phase 5: Finalization (Oct 21, 2025)

**Completed:**
- ✅ Performance analysis script (daily/weekly reports)
- ✅ UTC candle alignment verification
- ✅ Cron job setup for automation
- ✅ Documentation consolidation
- ✅ Project cleanup

**Status:** Ready for production deployment

---

## Key Technical Decisions

### 1. BBWidth Percentile vs Absolute Threshold

**Options:**
- A) Use absolute BBWidth value (e.g., < 0.05)
- B) Use percentile ranking (e.g., < 35th percentile)

**Decision:** Percentile ranking ✅

**Rationale:**
- Adapts to changing market volatility
- Works across different price levels
- Relative measure is more robust
- Avoids recalibration as markets evolve

### 2. RVR Threshold: 1.5 vs 2.0 vs 2.5

**Tested:**
- RVR 1.5: More trades, lower quality
- RVR 2.0: Good balance
- RVR 2.5: Too few trades

**Decision:** RVR 2.0 ✅

**Rationale:**
- Filters ~75% of setups (quality over quantity)
- Ensures favorable asymmetric risk/reward
- Provides enough trade frequency (11 trades/month)
- Profit factor of 2.18 validates the threshold

### 3. Position Sizing: Fixed vs Risk-Based

**Options:**
- A) Fixed percentage (e.g., always 5% of capital)
- B) Risk-based (e.g., risk 2% to stop loss)

**Decision:** Risk-based at 5% position size ✅

**Rationale:**
- Normalizes risk across different setups
- Larger positions when stops are tight
- Smaller positions when stops are wide
- Max 3 positions = max 15% capital deployed

### 4. Exit: Fixed Stop vs Trailing vs MA-Based

**Tested:**
- Fixed stop: Missed big winners
- Trailing only: Good but some premature exits
- MA-based only: Late exits on reversals

**Decision:** Hybrid (Trailing + MA) ✅

**Rationale:**
- 10% trailing stop protects capital
- MA exit captures momentum fades (71% of exits)
- Combination lets winners run while cutting losers
- Best trade: +297% (captured with trailing stop)

### 5. Timeframe Selection

**Options:**
- 1H: Too noisy, overtrading
- 4H: Sweet spot ✅
- Daily: Too slow, missed moves

**Decision:** 4-hour candles ✅

**Rationale:**
- Filters noise while capturing momentum
- 6 candles per day = enough checks
- Aligns with natural market rhythm
- Enough signals (306 trades in 27 months)

### 6. BTC Regime Filter

**Hypothesis:** Filter trades when BTC regime is unfavorable

**Test:** Extensive 27-month backtest

**Decision:** DISABLED ✅

**Rationale:**
- Reduced performance by 17x (-237% return)
- Too restrictive (blocked 87.6% of trades)
- Missed +297% winner
- Altcoins can move independently of BTC
- Our existing filters (BBWidth + RVR) sufficient

---

## Backtest Results

### Realistic Backtest (Final Configuration)

**Period:** August 3, 2023 - October 21, 2025 (27 months)
**Data Source:** Live Bybit API
**Universe:** Static 44 tokens

#### Performance Metrics

| Metric | Value |
|--------|-------|
| **Total Return** | +252.22% |
| **Total Trades** | 306 |
| **Win Rate** | 37.58% |
| **Winning Trades** | 115 |
| **Losing Trades** | 191 |
| **Profit Factor** | 2.18 |
| **Max Drawdown** | -23.11% |
| **Sharpe Ratio** | 0.67 |
| **Sortino Ratio** | 1.07 |
| **Average Win** | +13.70% |
| **Average Loss** | -3.99% |
| **Max Win** | +297.81% (BLESSUSDT) |
| **Max Loss** | -11.93% |
| **Avg Holding** | 13.5 days |
| **Median Holding** | 10.0 days |

#### Exit Breakdown

- **MA Exit:** 218 trades (71.2%)
- **Trailing Stop:** 87 trades (28.4%)
- **End of Backtest:** 1 trade (0.3%)

#### Top Performing Symbols

1. **BLESSUSDT:** 1 trade, 100% win rate, +297.8% return
2. **1000BONKUSDT:** 15 trades, 26.7% win rate, +64.8% return
3. **SUIUSDT:** 11 trades, 36.4% win rate, +61.7% return
4. **AVAXUSDT:** 8 trades, 37.5% win rate, +56.5% return
5. **XRPUSDT:** 12 trades, 50.0% win rate, +49.5% return

#### Key Insights

1. **Low Win Rate is OK** - 37.6% win rate but 252% return (winners are BIG)
2. **Let Winners Run** - Max win of 297% shows trailing stops work
3. **Cut Losers Fast** - Avg loss only -4%, max loss -11.9%
4. **Quality Over Quantity** - 11.3 trades/month is sufficient
5. **Consistency Matters** - 44-token static universe provides steady opportunities

---

## BTC Regime Filter Analysis

### Hypothesis

"Altcoin momentum trades perform better when Bitcoin is in a strong bullish regime (price > 200-day MA AND ADX > 25)."

### Test Setup

- **Period:** 27 months (Aug 2023 - Oct 2025)
- **Filter Logic:** Only take trades when BTC price > 200 MA AND ADX > 25
- **Comparison:** Same strategy with/without filter

### Results

| Metric | Without Filter | With Filter | Difference |
|--------|---------------|-------------|------------|
| **Total Trades** | 306 | 38 | -87.6% |
| **Total Return** | +252% | +15% | **-237%** |
| **Final Equity** | $35,222 | $11,466 | -$23,756 |
| **Win Rate** | 37.6% | 50.0% | +12.4% |
| **Profit Factor** | 2.18 | 1.76 | -0.42 |
| **Sharpe Ratio** | 0.67 | 0.26 | -61% |
| **Sortino Ratio** | 1.07 | 0.08 | -92% |
| **Max Drawdown** | -23.1% | -8.4% | +14.7% |

### Key Findings

1. **Massively Reduced Trade Frequency**
   - Filter blocked 268 out of 306 trades (87.6%)
   - Filtered 85-95% of signals per token
   - System sat idle for months at a time

2. **Missed Huge Winners**
   - BLESSUSDT +297% trade was filtered out
   - Many other strong winners blocked
   - Lost $23,756 in potential profits

3. **Win Rate Misleading**
   - Higher win rate (50% vs 37.6%) but much worse returns
   - Filter selected fewer trades but they weren't better quality
   - Small sample size (38 trades) not statistically significant

4. **Poor Capital Utilization**
   - Capital idle 95% of the time with filter
   - Only 38 trades over 27 months = 1.4 trades/month
   - Extremely poor opportunity cost

### Why It Failed

1. **BTC Regime Too Restrictive**
   - BTC rarely had BOTH price > 200 MA AND ADX > 25
   - Most of 27-month period didn't meet criteria
   - Filter was essentially "off" most of the time

2. **Altcoins Move Independently**
   - Strong altcoin momentum can occur when BTC is neutral/weak
   - Our BBWidth + RVR filters already identify quality setups
   - Adding BTC filter was redundant and harmful

3. **Timeframe Mismatch**
   - We trade 4H altcoin moves
   - Filter checked daily BTC regime
   - Short-term alt momentum != daily BTC regime

### Decision

**Run WITHOUT BTC regime filter.**

The empirical evidence is overwhelming - the filter reduced performance by 17x and provided no benefit.

---

## Universe Selection

### Approach

**Static Universe** - 44 tokens selected for consistency and volume

### Selection Criteria

1. **Volume Consistency** - Present in top volume rankings 70%+ of time
2. **Minimum Volume** - $15M+ daily trading volume
3. **Quality** - Established projects with liquidity
4. **Diversity** - Mix of L1s, DeFi, memecoins, etc.

### Final Universe (44 Tokens)

ADAUSDT, AIAUSDT, APEXUSDT, APTUSDT, ARBUSDT, ASTERUSDT, ATOMUSDT, AVAXUSDT, BLESSUSDT, BNBUSDT, BTCUSDT, COAIUSDT, DOGEUSDT, DOTUSDT, EIGENUSDT, ENAUSDT, ETHUSDT, FARTCOINUSDT, GALAUSDT, HYPEUSDT, LDOUSDT, LINKUSDT, LTCUSDT, MYXUSDT, NEARUSDT, ONDOUSDT, OPUSDT, PENGUUSDT, PUMPFUNUSDT, SEIUSDT, SOLUSDT, SPXUSDT, SUIUSDT, TAOUSDT, TRUMPUSDT, USELESSUSDT, WIFUSDT, WLFIUSDT, WLDUSDT, XAUTUSDT, XRPUSDT, 1000BONKUSDT, 1000PEPEUSDT, (44 total)

### Why Static vs Dynamic?

**Static Pros:**
- ✅ Consistent opportunity set
- ✅ No universe churn
- ✅ Easier to backtest
- ✅ Predictable behavior

**Dynamic Cons:**
- ❌ Universe changes introduce instability
- ❌ Forced exits when tokens removed
- ❌ Harder to backtest realistically
- ❌ More complex to manage

**Decision:** Static universe with 70% consistency threshold

---

## Risk Management Evolution

### Position Level

**Initial:** Fixed 5% of capital per trade
**Final:** 5% risk-based sizing + trailing stop ✅

**Features:**
- Position size adjusts based on stop distance
- 10% trailing stop on all positions
- Max 3 concurrent positions (max 15% deployed)

### Account Level

**Daily Loss Limit:** -3%
- Stops new entries for rest of day
- Existing positions remain open
- Resets at 00:00 UTC

**Weekly Loss Limit:** -8%
- Reduces position size by 50%
- Prevents compounding losses
- Resets on Mondays

**Monthly Loss Limit:** -15%
- Further size reduction
- Warning alert sent
- Manual review required

**Max Drawdown:** -20%
- System halt
- Requires manual intervention
- Prevents catastrophic losses

### Why Multi-Level?

**Philosophy:** Defense in depth

1. **Daily limit** catches bad days quickly
2. **Weekly limit** prevents weekly drawdown spirals
3. **Monthly limit** protects against prolonged bad periods
4. **Max DD** is final circuit breaker

This approach prevents the single bad week from destroying the account.

---

## Deployment Setup

### Production Components

1. **Trading System** (`trading_system.py`)
   - Main production system
   - Runs continuously
   - Auto-aligns with 4H UTC candles
   - Handles all trading logic

2. **Performance Analysis** (`performance_analysis.py`)
   - Runs daily at 00:00 UTC
   - Weekly reports on Mondays
   - Automated via cron
   - Sends Telegram alerts

3. **Database** (SQLite)
   - Logs all trades
   - Tracks equity curve
   - Stores system events
   - Backs up automatically

4. **Telegram Bot**
   - Entry/exit alerts
   - Daily/weekly reports
   - Error notifications
   - Risk limit warnings

### Cron Schedule

```bash
# Daily performance analysis at 00:00 UTC
0 0 * * * cd /path/to/momentum2 && python performance_analysis.py

# Weekly backups (Sundays 01:00 UTC)
0 1 * * 0 cd /path/to/momentum2 && ./backup.sh
```

### Monitoring

**Health Checks:**
- System runs `run_once()` every 4H
- API connectivity verified each iteration
- Database integrity checked
- Balance verified before trades

**Alerts:**
- Telegram for all trades
- Email for system errors (optional)
- SMS for critical failures (optional)

---

## Lessons Learned

### 1. More Filters ≠ Better Performance

**Lesson:** Adding the BTC regime filter seemed logical but reduced performance by 17x.

**Takeaway:** Test every assumption. Sometimes simpler is better. Our BBWidth + RVR filters were already sufficient.

### 2. Win Rate Can Be Misleading

**Lesson:** BTC filter had 50% win rate vs 37.6% without, but 17x worse returns.

**Takeaway:** Focus on total return and risk-adjusted metrics, not win rate. A few big winners > many small winners.

### 3. Let Winners Run

**Lesson:** Best trade was +297% (BLESSUSDT). Trailing stop captured this.

**Takeaway:** Don't take profits too early. Trailing stops let you capture explosive moves while protecting capital.

### 4. Static Universe Works

**Lesson:** 44-token static universe provided 306 trades over 27 months.

**Takeaway:** Don't need dynamic universe churn. Quality tokens provide consistent opportunities.

### 5. Context Matters for Filters

**Lesson:** BTC regime filter might work for daily BTC trading, but not for 4H altcoin momentum.

**Takeaway:** Filters must match your timeframe and asset class. Don't blindly copy strategies.

### 6. Empirical Testing > Intuition

**Lesson:** BTC filter seemed logical but data proved it wrong.

**Takeaway:** Always backtest assumptions. Data beats intuition.

### 7. Risk Management is Essential

**Lesson:** Multi-level risk limits (daily/weekly/monthly) prevented catastrophic losses.

**Takeaway:** Defense in depth. Don't rely on single risk control.

### 8. Simplicity in Production

**Lesson:** Single config file to switch DEMO ↔ LIVE makes deployment safe.

**Takeaway:** Production systems should be simple to operate. Complexity breeds errors.

### 9. Documentation Matters

**Lesson:** Comprehensive docs make future changes easier.

**Takeaway:** Document decisions and rationale. Future you will thank past you.

### 10. Test Before Live

**Lesson:** Extensive backtesting caught the BTC filter issue before going live.

**Takeaway:** Always test thoroughly. Better to catch issues in backtest than with real money.

---

## Next Steps (Post-Deployment)

### Week 1-2: Observation
- Monitor all trades closely
- Verify execution quality
- Check alert system
- Validate risk limits trigger correctly

### Month 1: Initial Assessment
- Compare live results to backtest
- Check for any unexpected behavior
- Optimize execution if needed
- Fine-tune alerts

### Month 3: First Review
- Full performance analysis
- Compare to backtest expectations
- Consider parameter adjustments
- Review universe (add/remove tokens?)

### Month 6: Major Review
- Comprehensive performance report
- Re-run backtest with updated data
- Consider strategy enhancements
- Decide on capital scaling

---

## Version History

**v1.0** (Oct 21, 2025) - Initial Production Release
- Complete backtesting (27 months)
- BTC regime filter testing and decision
- Production system ready
- Documentation complete
- Ready for deployment

---

**System Status:** Production Ready ✅
**Recommended Name:** Apex Momentum 🎯
**Last Updated:** October 21, 2025
