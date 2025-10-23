#!/bin/bash
#
# Setup cron jobs for automated trading system
#
# This script sets up:
# 1. Daily performance analysis at 00:00 UTC (12 AM)
# 2. Weekly performance analysis on Mondays at 00:00 UTC
#

# Get the absolute path to this directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Path to Python in conda environment
PYTHON_PATH="$HOME/anaconda3/bin/python"

# Check if conda Python exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Conda Python not found at $PYTHON_PATH"
    echo "Please update PYTHON_PATH in this script"
    exit 1
fi

echo "=================================="
echo "Setting up cron jobs"
echo "=================================="
echo ""
echo "Directory: $SCRIPT_DIR"
echo "Python: $PYTHON_PATH"
echo ""

# Create cron entry
CRON_ENTRY="0 0 * * * cd $SCRIPT_DIR && $HOME/anaconda3/etc/profile.d/conda.sh && conda activate && $PYTHON_PATH $SCRIPT_DIR/performance_analysis.py >> $SCRIPT_DIR/logs/performance_$(date +\%Y\%m).log 2>&1"

# Check if cron entry already exists
(crontab -l 2>/dev/null | grep -F "performance_analysis.py") && {
    echo "⚠️  Cron job already exists for performance_analysis.py"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "performance_analysis.py"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove old entry
    crontab -l | grep -v "performance_analysis.py" | crontab -
}

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✓ Cron job installed successfully!"
echo ""
echo "Schedule:"
echo "  - Daily analysis: Every day at 00:00 UTC"
echo "  - Weekly analysis: Mondays at 00:00 UTC (automatic)"
echo ""
echo "Logs will be saved to: $SCRIPT_DIR/logs/performance_YYYYMM.log"
echo ""
echo "To view current cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -e"
echo "  (then delete the line containing 'performance_analysis.py')"
echo ""
