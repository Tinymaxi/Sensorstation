#!/usr/bin/env python

import time
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

# Setup
pir = MotionSensor(PIR_PIN)
backlight = Backlight()

i2c = board.I2C()
light_sensor = adafruit_tsl2591.TSL2591(i2c)
light_sensor.gain = adafruit_tsl2591.GAIN_MED
light_sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS

# Start with screen off
backlight.power = False
screen_off_time = 0

while True:
    if pir.is_active:
        try:
            lux = light_sensor.lux
        except Exception:
            lux = 0

        if lux >= LUX_THRESHOLD:
            if not backlight.power:
                backlight.power = True
            if lux >= LUX_BRIGHT_THRESHOLD:
                backlight.brightness = BRIGHTNESS_BRIGHT
            else:
                backlight.brightness = BRIGHTNESS_DIM
            screen_off_time = time.time() + SCREEN_ON_SECONDS

    # Turn off screen after timeout
    if backlight.power and time.time() >= screen_off_time:
        backlight.power = False

    time.sleep(0.5)
