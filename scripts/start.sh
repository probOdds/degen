#!/bin/bash
cd /opt/probodds/degen

# Load Telegram credentials from .env (not in git)
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Kill existing processes
pkill -f "observe_graduations.py" 2>/dev/null
pkill -f "track_prices.py" 2>/dev/null
pkill -f "observe_pregrad.py" 2>/dev/null
pkill -f "status_api:app" 2>/dev/null
sleep 1

# Start observer
nohup python3 -u scripts/observe_graduations.py > /tmp/degen-observer.log 2>&1 &
echo $! > /tmp/degen-observer.pid
echo "Observer PID: $(cat /tmp/degen-observer.pid)"

# Start price tracker
nohup python3 -u scripts/track_prices.py > /tmp/degen-tracker.log 2>&1 &
echo $! > /tmp/degen-tracker.pid
echo "Tracker PID: $(cat /tmp/degen-tracker.pid)"

# Start pre-graduation observer
nohup python3 -u scripts/observe_pregrad.py > /tmp/degen-pregrad.log 2>&1 &
echo $! > /tmp/degen-pregrad.pid
echo "Pre-Grad Observer PID: $(cat /tmp/degen-pregrad.pid)"

# Start status API (port 8004)
nohup uvicorn scripts.status_api:app --host 127.0.0.1 --port 8004 --workers 1 > /tmp/degen-status-api.log 2>&1 &
echo $! > /tmp/degen-status-api.pid
echo "Status API PID: $(cat /tmp/degen-status-api.pid)"
