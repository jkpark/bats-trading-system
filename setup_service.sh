#!/bin/bash

# Configuration
APP_NAME="bats-trading-system"
APP_DIR="/home/jkpark/.openclaw/workspace-jeff/bats-trading-system"
PYTHON_BIN="/usr/bin/python3"
SCRIPT_PATH="$APP_DIR/src/main_lite.py"
USER="jkpark"

SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

echo "Creating systemd service file..."

cat <<EOF | sudo tee $SERVICE_FILE
[Unit]
Description=BATS Trading System Lite
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment="PYTHONPATH=$APP_DIR"
ExecStart=$PYTHON_BIN $SCRIPT_PATH --daemon
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/bats.log
StandardError=append:$APP_DIR/bats.log

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling $APP_NAME service..."
sudo systemctl enable $APP_NAME

echo "Starting $APP_NAME service..."
sudo systemctl start $APP_NAME

echo "Service status:"
sudo systemctl status $APP_NAME --no-pager

echo "Setup complete. Logs are being written to $APP_DIR/bats.log"
