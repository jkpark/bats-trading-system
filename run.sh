#!/bin/bash

# BATS Trading System - Build & Run Script
# This script ensures a clean restart of the background service.

PROJECT_DIR="/Users/jkpark/.openclaw/workspace-jeff/bats-trading-system"
SERVICE_NAME="bats-trading-system"

# 1. Navigate to project directory
cd "$PROJECT_DIR" || exit

echo "🏗️ [1/4] Stopping current BATS process..."
# Stop the systemd service
sudo systemctl stop $SERVICE_NAME 2>/dev/null
# Ensure no manual processes are lingering
pkill -f "src/main.py" 2>/dev/null

echo "🧹 [2/4] Cleaning build artifacts..."
# Remove python cache files
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "📦 [3/4] Checking dependencies..."
# Ensure requirements are satisfied (using system python as per environment setup)
pip install -r requirements.txt --break-system-packages --quiet

echo "🚀 [4/4] Starting BATS service..."
sudo systemctl start $SERVICE_NAME

# Check if it started successfully
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ BATS is running in the background."
    echo "--------------------------------------------------"
    echo "Last logs:"
    sudo systemctl status $SERVICE_NAME --no-pager | grep "Active:"
    echo "--------------------------------------------------"
    echo "💡 Tip: Use 'tail -f bats.log' to monitor real-time."
else
    echo "❌ Failed to start BATS service. Check 'journalctl -u $SERVICE_NAME' for details."
    exit 1
fi
