# BTC Regime Filter Analysis

**Date:** October 21, 2025
**Analysis Period:** August 3, 2023 - October 21, 2025 (27 months)
**Decision:** Proceeding **WITHOUT** BTC Regime Filter

---

## Executive Summary

We conducted a comprehensive backtest comparison to evaluate the impact of the BTC Regime Filter on our momentum trading strategy. The filter was designed to only take trades when Bitcoin is in a favorable market regime (price above 200-day MA and ADX > 25), with the hypothesis that altcoin momentum trades perform better during strong BTC trends.

**Key Finding:** The BTC regime filter **dramatically reduced** strategy performance - cutting trades by **87.6%** (from 306 to 38 trades) and reducing returns from **252%** to just **15%**.

**Decision:** We will proceed **WITHOUT** the BTC regime filter. The filter was too restrictive, filtering out 85-95% of quality signals and significantly underperforming the unfiltered strategy.

---

## Performance Results

### With BTC Regime Filter **ENABLED**

| Metric | Value |
|--------|-------|
| **Total Trades** | **38** |
| **Win Rate** | 50.00% |
| **Total Return** | **+14.66%** |
| **Final Equity** | **$11,465.77** |
| **Profit Factor** | 1.76 |
| **Max Drawdown** | -8.37% |
| **Sharpe Ratio** | 0.26 |
| **Sortino Ratio** | 0.08 |

### With BTC Regime Filter **DISABLED**

| Metric | Value |
|--------|-------|
| **Total Trades** | **306** |
| **Win Rate** | 37.58% |
| **Total Return** | **+252.22%** |
| **Final Equity** | **$35,221.66** |
| **Profit Factor** | 2.18 |
| **Max Drawdown** | -23.11% |
| **Sharpe Ratio** | 0.67 |
| **Sortino Ratio** | 1.07 |

### Performance Comparison

| Metric | With Filter | Without Filter | Difference | Impact |
|--------|-------------|----------------|------------|--------|
| **Total Trades** | 38 | 306 | **-268 (-87.6%)** | ❌ Massive reduction |
| **Total Return** | +14.66% | +252.22% | **-237.56%** | ❌ **17x worse** |
| **Final Equity** | $11,465.77 | $35,221.66 | **-$23,755.89** | ❌ Lost $23.7k profit |
| **Win Rate** | 50.00% | 37.58% | +12.42% | Higher but irrelevant |
| **Profit Factor** | 1.76 | 2.18 | -0.42 | ❌ Lower |
| **Max Drawdown** | -8.37% | -23.11% | +14.74% | ✓ Lower DD |
| **Sharpe Ratio** | 0.26 | 0.67 | **-0.41 (-61%)** | ❌ Much worse |
| **Sortino Ratio** | 0.08 | 1.07 | **-0.99 (-92%)** | ❌ Terrible |

---

## Critical Insights

### 1. The Filter Was TOO Restrictive

The BTC regime filter blocked **85-95% of all signals** across tokens. Out of hundreds of potential trades, only 38 passed the filter over 27 months. This means the strategy sat idle for months at a time, missing quality altcoin momentum opportunities.

### 2. Missed Massive Winners

**Without filter:** Captured BLESSUSDT for +297.8% gain
**With filter:** This trade was filtered out - **NEVER TAKEN**

The strategy without the filter captured 15 trades in 1000BONKUSDT (+64.8% total), 11 trades in SUIUSDT (+61.7% total), and 12 trades in SOLUSDT (+34.4% total). With the filter, most of these opportunities were blocked.

### 3. Win Rate is a Red Herring

The filter showed **50% win rate** vs 37.58% without filter, BUT this is meaningless because:
- It only took 38 trades vs 306 trades
- The few trades had smaller average wins (+8.97% vs +13.70%)
- It missed the strategy's edge: letting winners run big
- Final equity tells the truth: **$11,466 vs $35,222**

### 4. Risk-Adjusted Returns Were Much Worse

- **Sharpe Ratio:** 0.26 vs 0.67 (filter was **61% worse**)
- **Sortino Ratio:** 0.08 vs 1.07 (filter was **92% worse**)
- **Return/Drawdown ratio:** 1.75 vs 10.91 (**6.2x worse**)

Despite lower max drawdown with the filter, the returns were so poor that risk-adjusted performance was terrible.

### 5. Capital Sat Idle

**With Filter:** 38 trades over 826 days = capital idle 95% of the time
**Without Filter:** 306 trades over 826 days = healthy deployment

From Aug 2023 to Feb 2024 (6 months), the filtered strategy took **0 trades** - sitting completely idle while opportunities existed.

---

## Why the Filter Failed

### 1. Altcoins Can Move Independent of BTC Regime

Many altcoins have strong momentum moves even when BTC is below its 200 MA or in low ADX conditions. Our BBWidth and RVR filters already identify tokens with compression and strong risk/reward - these can occur in any BTC regime.

### 2. Our Existing Filters Are Sufficient

The unfiltered strategy already has robust entry criteria:
- **BBWidth at 35th percentile** - identifies volatility compression
- **RVR > 2.0** - ensures favorable risk/reward setup
- **MA-based exits** - protects profits and cuts losses
- **Daily/weekly loss limits** - protects against adverse periods

### 3. Opportunity Cost Was Enormous

By sitting out 268 trades:
- Lost $23,755 in potential profits
- Missed +297% winner (BLESSUSDT)
- Missed dozens of other strong momentum moves
- Capital sat idle for months earning 0%

### 4. Timing Mismatch

We trade 4H altcoin momentum but filtered on DAILY BTC regime. Short-term altcoin moves don't correlate perfectly with daily BTC regime. A 4H breakout can happen even when daily BTC is "neutral."

---

## Decision Rationale

### Why We're Proceeding WITHOUT the BTC Regime Filter

1. **Massive Performance Difference** - 17x better returns without filter (252% vs 15%)
2. **Filter Was Over-Restrictive** - Blocked 87.6% of trades, sat idle for months
3. **Missed Strategy's Core Edge** - Strategy's edge is capturing big winners (like +297%)
4. **Risk-Adjusted Performance Was Terrible** - Sharpe 61% worse, Sortino 92% worse
5. **Our Core Filters Work** - BBWidth + RVR already select quality setups in ALL market regimes
6. **Operational Simplicity** - Simpler system, fewer API calls, more trading opportunities
7. **Real-World Practicality** - 38 trades over 27 months (1.4/month) is too low; 306 trades (11.3/month) is healthy

---

## Key Learnings

### 1. More Filters ≠ Better Performance

Adding the BTC regime filter did NOT improve returns, Sharpe ratio, Sortino ratio, or profit factor. It DID reduce drawdown but at catastrophic cost to returns.

### 2. Win Rate Can Be Misleading

50% win rate (filter) vs 37.58% (no filter), but filter had **17x worse returns**. What matters: **total return and risk-adjusted return**, not win rate.

### 3. Let Your Winners Run

- Strategy WITHOUT filter: Max win +297%, multiple +50%+ winners
- Strategy WITH filter: Max win +23%, missed big movers
- **Don't filter out your potential home runs**

### 4. Context Matters

The filter might work for daily BTC trading with weaker entry filters. But for THIS strategy (4H altcoin momentum with strong BBWidth/RVR filters), the BTC regime filter was counterproductive.

---

## Drawdown Acknowledgment

**Drawdown WITH filter:** -8.37%
**Drawdown WITHOUT filter:** -23.11%

The filter DID reduce max drawdown by 14.74 percentage points. However, this came at the cost of losing 237% in returns.

**Return/Drawdown ratio:**
- With filter: 14.66% / 8.37% = **1.75**
- Without filter: 252.22% / 23.11% = **10.91**
- **Without filter is 6.2x better on this metric**

To get 252% returns, a -23% drawdown is very acceptable. Our daily (-3%) and weekly (-8%) loss limits already protect against catastrophic losses.

---

## Final Configuration

```python
# Strategy Configuration
use_btc_regime_filter = False     # ✓✓✓ DISABLED ✓✓✓

# Core Filters (Sufficient)
bbwidth_threshold = 0.35          # 35th percentile
rvr_threshold = 2.0               # Minimum RVR
ma_period = 20                    # 20-period MA
lookback_period = 90              # 90-period lookback

# Risk Management
risk_per_trade_pct = 0.05         # 5% per trade
max_positions = 3                 # Max concurrent positions
stop_loss_pct = 0.10              # 10% trailing stop
daily_loss_limit_pct = 0.03       # 3% daily loss limit
weekly_loss_limit_pct = 0.08      # 8% weekly loss limit
```

---

## Conclusion

After rigorous testing over 27 months of data, the results are unequivocal: **the BTC Regime Filter severely damaged strategy performance.**

**The Numbers:**
- **-87.6% fewer trades** (38 vs 306)
- **-237% lower returns** (15% vs 252%)
- **-$23,755 less profit**
- **17x worse performance overall**

**Why It Failed:**
- Too restrictive (filtered out 85-95% of signals)
- Missed massive winners (including +297% gain)
- Poor capital utilization (sat idle most of the time)
- Altcoin momentum doesn't require bullish BTC regime
- Our existing filters already select quality setups

We are proceeding **WITHOUT** the BTC regime filter. Our core filters (BBWidth percentile, RVR threshold, MA-based exits, and risk limits) are sufficient and have delivered outstanding performance: **252% returns over 27 months with 0.67 Sharpe ratio**.

**Sometimes the best filter is no filter at all - especially when your existing filters already work.**

---

**Approved for Production:** Yes - **WITHOUT BTC Regime Filter**
**Implementation Date:** October 21, 2025
**Confidence Level:** Very High (empirical evidence is overwhelming)
