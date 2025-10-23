# Scripts Path Fix

## Issue
When running scripts from the `scripts/` directory, they were failing with:
```
ModuleNotFoundError: No module named 'config'
```

## Root Cause
Scripts in the `scripts/` directory had incorrect path configuration:
```python
sys.path.append(str(Path(__file__).parent))  # ❌ Wrong - adds scripts/ dir
```

This added the `scripts/` directory to the path, but the imports expect to run from the project root.

## Fix Applied
Changed all scripts to add the project root (parent of scripts/) to the path:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))  # ✅ Correct - adds project root
```

## Files Fixed
- ✅ `scripts/test_exchange_execution.py`
- ✅ `scripts/performance_analysis.py`
- ✅ `scripts/run_backtest.py`
- ✅ `scripts/test_connection.py`
- ✅ `scripts/check_btc_regime.py`
- ✅ `scripts/run_realistic_backtest.py`
- ℹ️  `scripts/test_api_simple.py` - No fix needed (doesn't import project modules)

## How to Run Scripts

### Option 1: From Project Root (Recommended)
```bash
cd /home/william/STRATEGIES/Alpha/momentum
python3 scripts/test_connection.py
python3 scripts/test_exchange_execution.py
```

### Option 2: From Scripts Directory
```bash
cd /home/william/STRATEGIES/Alpha/momentum/scripts
python3 test_connection.py
python3 test_exchange_execution.py
```

Both now work correctly!

## Environment Setup

Before running scripts, ensure dependencies are installed:

```bash
# Activate conda environment (if using conda)
conda activate

# Or create a new environment
conda create -n trading python=3.11
conda activate trading

# Install dependencies
cd /home/william/STRATEGIES/Alpha/momentum
pip install -r requirements.txt
```

## Testing the Fix

Test that imports work:
```bash
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('scripts/test_connection.py').parent.parent))
from config.trading_config import config
print('✓ Imports working correctly')
"
```

## Why `sys.path.insert(0, ...)` vs `sys.path.append(...)`?

Using `insert(0, ...)` is better because:
1. **Higher Priority** - Ensures our project modules are found first
2. **Avoids Conflicts** - Prevents system modules from shadowing our code
3. **Cleaner Resolution** - Python checks our path before falling back to system paths

## Path Resolution Example

For script at: `/home/william/STRATEGIES/Alpha/momentum/scripts/test_connection.py`

```python
Path(__file__)                    # /home/.../momentum/scripts/test_connection.py
Path(__file__).parent            # /home/.../momentum/scripts  ❌ Wrong
Path(__file__).parent.parent     # /home/.../momentum          ✅ Correct
```

## Verification

All scripts now properly import project modules:
- ✓ `config.trading_config`
- ✓ `exchange.bybit_exchange`
- ✓ `backtest.backtester`
- ✓ `signals.entry_signals`
- ✓ `data.data_loader`
- etc.

---

**Last Updated:** October 23, 2025
**Status:** Fixed ✅
