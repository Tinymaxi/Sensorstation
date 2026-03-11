#!/usr/bin/env python

import time
import threading
import board
import adafruit_tsl2591
from gpiozero import MotionSensor
from rpi_backlight import Backlight

# Configuration
PIR_PIN = 22
LUX_THRESHOLD = 3       # screen stays off below this
LUX_BRIGHT_THRESHOLD = 50  # above this: full brightness
BRIGHTNESS_DIM = 40     # brightness % in dim light
BRIGHTNESS_BRIGHT = 100 # brightness % in bright light
SCREEN_ON_SECONDS = 60   # how long screen stays on after motion
TOUCH_ON_SECONDS = 40    # how long screen stays on after touch

TOUCH_DEVICE = "/dev/input/event0"

# Setup
pir = MotionSensor(PIR_PIN)
backlight = Backlight()

i2c = board.I2C()
light_sensor = adafruit_tsl2591.TSL2591(i2c)
light_sensor.gain = adafruit_tsl2591.GAIN_MED
light_sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS

# Track last touch time from background thread
last_touch = 0

def touch_listener():
    """Read raw input events from touchscreen to detect touches."""
    global last_touch
    with open(TOUCH_DEVICE, "rb") as f:
        while True:
            f.read(24)  # each input event is 24 bytes
            last_touch = time.time()

t = threading.Thread(target=touch_listener, daemon=True)
t.start()

# Start with screen off
backlight.power = False
screen_off_time = 0

while True:
    try:
        lux = light_sensor.lux
    except Exception:
        lux = 0

    # Turn off immediately if too dark (unless kept on by touch)
    touch_active = last_touch > 0 and time.time() < last_touch + TOUCH_ON_SECONDS
    if backlight.power and lux < LUX_THRESHOLD and not touch_active:
        backlight.power = False
        screen_off_time = 0

    # Touch wakes screen regardless of light level
    if last_touch > time.time() - 1:
        if not backlight.power:
            backlight.power = True
            backlight.brightness = BRIGHTNESS_DIM
        screen_off_time = max(screen_off_time, last_touch + TOUCH_ON_SECONDS)

    # Motion wakes screen
    if pir.is_active and lux >= LUX_THRESHOLD:
        if not backlight.power:
            backlight.power = True
        if lux >= LUX_BRIGHT_THRESHOLD:
            backlight.brightness = BRIGHTNESS_BRIGHT
        else:
            backlight.brightness = BRIGHTNESS_DIM
        screen_off_time = time.time() + SCREEN_ON_SECONDS

    # Turn off screen after timeout
    if backlight.power and screen_off_time > 0 and time.time() >= screen_off_time:
        backlight.power = False

    time.sleep(0.5)
