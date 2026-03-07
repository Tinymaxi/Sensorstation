#!/bin/bash
# Wait for Grafana to be ready before opening Chromium
while ! curl -s http://localhost:3000/api/health | grep -q ok; do
    sleep 2
done
sleep 2

# Hide cursor by creating a transparent cursor pixmap
xdotool mousemove 10000 10000

chromium-browser --noerrdialogs --disable-infobars --kiosk \
    --touch-events=enabled --touch-devices=6 \
    "http://localhost:3000/d/u3WosoWRz/all-sensor-data?kiosk"
