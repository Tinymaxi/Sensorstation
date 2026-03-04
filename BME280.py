#!/usr/bin/env python

from influxdb import InfluxDBClient
import time as t
import datetime
import board
from adafruit_bme280 import basic as adafruit_bme280

t.sleep(30)

# influx configuration - edit these
ifuser = "grafana"
ifpass = "<passwordhere>"
ifdb   = "SCD30Stats"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "BME280Stats"

# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

print("\nTemperature: %0.1f C" % bme280.temperature)
print("Humidity: %0.1f %%" % bme280.relative_humidity)
print("Pressure: %0.1f hPa" % bme280.pressure)
print("Altitude = %0.2f meters" % bme280.altitude)

bmetemp = float("%0.1f" % bme280.temperature)
bmerh = float("%0.1f" % bme280.relative_humidity)
bmepres = float("%0.1f" % bme280.pressure)
bmealt = float("%0.2f" % bme280.altitude)

body = [
    {
        "measurement": measurement_name,
        "time": datetime.datetime.utcnow(),
        "fields": {
            "bmetemp": bmetemp,
            "bmerh": bmerh,
            "bmepres": bmepres,
            "bmealt": bmealt
        }
    }
]

ifclient = InfluxDBClient(ifhost, ifport, ifuser, ifpass, ifdb)
ifclient.write_points(body)
