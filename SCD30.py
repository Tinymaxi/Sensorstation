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

#take a timestamp for this measurement
time = datetime.datetime.utcnow()

# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

while True:
    bmepres = int(bme280.pressure)
    bmealt = int(bme280.altitude)
    print(bmepres)
    print(bmealt)
    t.sleep(2)
    break








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

            # format the data as a single measurement for influx
            body = [
                {
                    "measurement": measurement_name,
                    "time": time,
                    "fields": {
                        "CO2": CO2,
                        "temp": temp,
                        "rh": rh,
                    }
                }
            ]

            # connect to influx
            ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)
            # write the measurement
            ifclient.write_points(body)

            
            t.sleep(2)
            break
        else:
            t.sleep(0.2)
