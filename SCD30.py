#!/usr/bin/env python

from influxdb import InfluxDBClient
from scd30_i2c import SCD30
import time as t
import datetime
import board
from adafruit_bme280 import basic as adafruit_bme280

# influx configuration - edit these
ifuser = "grafana"
ifpass = "<passwordhere>"
ifdb   = "SCD30Stats"
ifhost = "127.0.0.1"
ifport = 8086
measurement_name = "SCD30Stats"

# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

# Read BME280 pressure and altitude to calibrate SCD30
bmepres = int(bme280.pressure)
bmealt = int(bme280.altitude)
print(bmepres)
print(bmealt)





scd30 = SCD30()

scd30.ambient_pressure = bmepres
print("Ambient Pressure:", scd30.ambient_pressure)

scd30.altitude = bmealt
print("Altitude:", scd30.altitude, "meters above sea level")

scd30.set_measurement_interval(2)
scd30.start_periodic_measurement()

t.sleep(2)

while True:
    if scd30.get_data_ready():
        m = scd30.read_measurement()
        if m is not None:
            print(f"CO2: {m[0]:.2f}ppm, temp: {m[1]:.2f}'C, rh: {m[2]:.2f}%")
            CO2 = float(f'''{m[0]:.2f}''')
            temp = float(f'''{m[1]:.2f}''')
            rh = float(f'''{m[2]:.2f}''')

            body = [
                {
                    "measurement": measurement_name,
                    "time": datetime.datetime.utcnow(),
                    "fields": {
                        "CO2": CO2,
                        "temp": temp,
                        "rh": rh,
                    }
                }
            ]

            ifclient = InfluxDBClient(ifhost, ifport, ifuser, ifpass, ifdb)
            ifclient.write_points(body)
            break
    t.sleep(0.2)
