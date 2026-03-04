#!/usr/bin/env python

from influxdb import InfluxDBClient
import time as t
import datetime
import board
import adafruit_tsl2591

# influx configuration - edit these
ifuser = "grafana"
ifpass = "<passwordhere>"
ifdb   = "SCD30Stats"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "StatsTSL2591"

# take a timestamp for this measurement
time = datetime.datetime.utcnow()

# Create sensor object, communicating over the board's default I2C bus
i2c = board.I2C()  # uses board.SCL and board.SDA

# Initialize the sensor.
sensor = adafruit_tsl2591.TSL2591(i2c)

# You can optionally change the gain and integration time:
# sensor.gain = adafruit_tsl2591.GAIN_LOW (1x gain)
sensor.gain = adafruit_tsl2591.GAIN_MED #(25x gain, the default)
# sensor.gain = adafruit_tsl2591.GAIN_HIGH (428x gain)
# sensor.gain = adafruit_tsl2591.GAIN_MAX (9876x gain)
sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS #(100ms, default)
# sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_200MS (200ms)
# sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_300MS (300ms)
# sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_400MS (400ms)
# sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_500MS (500ms)
# sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_600MS (600ms)

# Read the total lux, IR, and visible light levels and print it every two seconds.
while True:
    # Read and calculate the light level in lux.
    lux = sensor.lux
    print("Total light: {0}lux".format(lux))
    # You can also read the raw infrared and visible light levels.
    # These are unsigned, the higher the number the more light of that type.
    # There are no units like lux.
    # Infrared levels range from 0-65535 (16-bit)
    infrared = sensor.infrared
    print("Infrared light: {0}".format(infrared))
    # Visible-only levels range from 0-2147483647 (32-bit)
    visible = sensor.full_spectrum
    print("Visible light: {0}".format(visible))
    # Full spectrum (visible + IR) also range from 0-2147483647 (32-bit)
    full_spectrum = sensor.full_spectrum
    print("Full spectrum (IR + visible) light: {0}".format(full_spectrum))
    t.sleep(2)

    tsllux= float("%0.2f" % sensor.lux)
    stlinfrared = int(sensor.infrared)
    tslvisible = int(sensor.visible)
    tslfull_spectrum = int(sensor.full_spectrum)
    
    # format the data as a single measurement for influx
    body = [
        {
            "measurement": measurement_name,
            "time": time,
            "fields": {

                "tsllux": tsllux,
                "stlinfrared": stlinfrared,
                "tslvisible": tslvisible,
                "tslfull_spectrum": tslfull_spectrum

            }
        }
    ]

    # connect to influx
    ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)
    # write the measurement
    ifclient.write_points(body)
    break
    