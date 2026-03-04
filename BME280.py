#!/usr/bin/env python

from influxdb import InfluxDBClient
from scd30_i2c import SCD30
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

# take a timestamp for this measurement
time = datetime.datetime.utcnow()

# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

while True:
    print("\nTemperature: %0.1f C" % bme280.temperature)
    print("Humidity: %0.1f %%" % bme280.relative_humidity)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    print("Altitude = %0.2f meters" % bme280.altitude)

    bmetemp = float("%0.1f" % bme280.temperature)
    bmerh = float("%0.1f" % bme280.relative_humidity)
    bmepres = float("%0.1f" % bme280.pressure)
    bmealt = float("%0.2f" % bme280.altitude)

    # format the data as a single measurement for influx
    body = [
        {
            "measurement": measurement_name,
            "time": time,
            "fields": {

                "bmetemp": bmetemp,
                "bmerh": bmerh,
                "bmepres": bmepres,
                "bmealt": bmealt

            }
        }
    ]

    # connect to influx
    ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)
    # write the measurement
    ifclient.write_points(body)

    
    t.sleep(2)
    break