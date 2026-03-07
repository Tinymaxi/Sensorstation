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

# Station altitude in meters
ALTITUDE = 435.0

bmetemp = float("%0.1f" % bme280.temperature)
bmerh = float("%0.1f" % bme280.relative_humidity)
bmeraw = bme280.pressure

# Convert station pressure to sea-level pressure using barometric formula
bmepres = float("%0.1f" % (bmeraw / (1 - (0.0065 * ALTITUDE) / (bmetemp + 0.0065 * ALTITUDE + 273.15)) ** 5.257))
bmealt = ALTITUDE

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
