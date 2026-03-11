#!/bin/bash
# Wait for Grafana to be ready before opening Chromium
while ! curl -s http://localhost:3000/api/health | grep -q ok; do
    sleep 2
done
sleep 2

# Start Chromium with remote debugging so we can inject touch-scroll JS
chromium-browser --noerrdialogs --disable-infobars --kiosk \
    --remote-debugging-port=9222 \
    "http://localhost:3000/d/u3WosoWRz/all-sensor-data?kiosk" &

# Wait for page to load, then inject drag-to-scroll via DevTools
sleep 15
python3 /home/pi/Sensorstation/inject-touch-scroll.py
