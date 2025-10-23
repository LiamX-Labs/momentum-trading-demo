# Trailing Stop Implementation

## Overview

The trading system now uses **Bybit's native trailing stop** feature for position protection, ensuring 24/7 server-side stop loss management.

## How It Works

### 1. Position Entry
When a position is opened:
```python
# Calculate trailing stop distance (10% by default)
trailing_stop_distance = entry_price * 0.10

# Set trailing stop on Bybit's servers
exchange.set_trading_stop(
    symbol=symbol,
    trailing_stop=trailing_stop_distance,
    category="linear",
    position_idx=0
)
```

### 2. Server-Side Management
- **Bybit manages the trailing stop 24/7** on their servers
- Stop automatically trails up as price moves higher
- Triggers automatically when price drops by 10% from peak
- **No software intervention needed** - runs even if your bot is offline

### 3. Position Monitoring
The bot checks positions every 5 minutes to:
- Detect when exchange has closed positions (trailing stop hit)
- Update peak price tracking for reporting
- Sync local state with exchange state

## Benefits

✅ **24/7 Protection** - Stops work even if bot crashes or disconnects
✅ **Instant Execution** - Exchange executes stops immediately (no 5-min delay)
✅ **Reliable** - No software bugs can prevent stop execution
✅ **Reduced API Calls** - Don't need to constantly update stops manually
✅ **Lower Latency** - Exchange-side execution is faster than software

## Previous Implementation (RISKY)

### What It Was:
- Software-based trailing stop checking
- Only checked every 5 minutes (later improved to check every 5 min when positions open)
- Could fail if bot crashes
- 5-minute delay between price drop and execution

### Problems:
1. **Gap Risk**: Price could crash between checks
2. **Software Failure**: Bot crash = no stop protection
3. **Execution Delay**: Up to 5 minutes to detect stop condition
4. **Slippage**: Manual closure on market price after detection

## New Implementation (SAFE)

### What It Is:
- Exchange-side trailing stop set on position entry
- Bybit monitors and executes stops 24/7
- Bot syncs with exchange to detect closed positions
- Instant execution when stop is hit

### Advantages:
1. **Instant Protection**: Stop set immediately on entry
2. **Zero Downtime**: Works even if bot is offline
3. **Immediate Execution**: Exchange executes within milliseconds
4. **Better Fills**: Exchange uses limit orders for stop execution
5. **Professional**: Standard institutional approach

## Configuration

The trailing stop percentage is configured in `config/trading_config.py`:

```python
class RiskConfig:
    stop_loss_pct: float = 0.10  # 10% trailing stop
```

## Position Flow

### Opening Position:
1. Signal detected → Entry order placed
2. Order fills at entry price
3. **Trailing stop set on exchange** (10% distance)
4. Position tracked in local state
5. Telegram notification sent

### While Position Open:
1. Bybit monitors price continuously
2. If price rises, trailing stop automatically moves up
3. Bot checks every 5 minutes for peak tracking
4. Peak updates logged for analysis

### Closing Position:
1. **Exchange detects trailing stop hit**
2. Exchange executes stop loss order
3. Bot detects position closed on next check
4. Records exit in database
5. Telegram notification sent
6. Capital updated with P&L

## Fallback Strategy

If setting trailing stop fails:
1. Attempts to set **fixed stop loss** as fallback
2. Logs warning message
3. Position still protected (non-trailing)
4. Telegram alert sent about fallback mode

## Testing

To verify trailing stop is working:

```bash
# 1. Open a position
python trading_system.py

# 2. Check position on Bybit
# Go to Positions tab
# Verify "Trailing Stop" is set

# 3. Monitor in terminal
# Look for: "✓ Trailing stop set: 10% ($X.XXXX)"

# 4. Test execution (demo mode)
# Watch position as price moves
# Verify stop trails upward
# Verify stop triggers on pullback
```

## Monitoring

The system logs trailing stop events:
- Entry: "✓ Trailing stop set: 10%"
- Peak updates: "{symbol}: New peak ${price}"
- Exit: "Exchange Stop Loss" reason
- Failures: Warning messages with fallback actions

## Important Notes

1. **One-Way Mode**: System uses `position_idx=0` (one-way mode)
2. **Linear Contracts**: Works with USDT perpetual contracts
3. **Demo vs Live**: Works identically in both modes
4. **Network Required**: Exchange must be reachable when setting stop
5. **API Permissions**: Requires "Position" permission in API key

## Troubleshooting

### "Could not set trailing stop"
- Check API key has Position permission
- Verify position_idx setting (0 for one-way mode)
- Ensure position is actually open on exchange
- System falls back to fixed stop automatically

### Stop Not Trailing
- Verify position_idx matches your account mode
- Check Bybit position settings (one-way vs hedge mode)
- Ensure trailing_stop value is valid for symbol

### Position Closed Unexpectedly
- Check if trailing stop was hit
- Review exit reason in logs ("Exchange Stop Loss")
- Verify stop distance was appropriate for volatility

## Future Improvements

Potential enhancements:
- [ ] Dynamic trailing stop % based on volatility
- [ ] Time-based stop tightening (e.g., tighter after 24h)
- [ ] Partial profit taking with remaining trailing
- [ ] Webhook integration for instant close notifications

---

**Last Updated**: October 23, 2025
**Status**: Production Ready ✅
