
import time
import board
import busio
import adafruit_scd30
import board
from adafruit_bme280 import basic as adafruit_bme280

# SCD-30 has tempremental I2C with clock stretching, datasheet recommends
# starting at 50KHz
i2c = busio.I2C(board.SCL, board.SDA, frequency=50000)
scd = adafruit_scd30.SCD30(i2c)

# Create sensor object, using the board's default I2C bus.
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# change this to match the location's pressure (hPa) at sea level
bme280.sea_level_pressure = 1013.25

# scd.temperature_offset = 10
# print("Temperature offset:", scd.temperature_offset)

scd.measurement_interval = 4
print("Measurement interval:", scd.measurement_interval)

#scd.self_calibration_enabled = True
print("Self-calibration enabled:", scd.self_calibration_enabled)


while True:
    bmepres = int(bme280.pressure)
    bmealt = int(bme280.altitude)
    print(bmepres)
    print(bmealt)
    time.sleep(2)
    break



scd.ambient_pressure = bmepres
print("Ambient Pressure:", scd.ambient_pressure)

scd.altitude = bmealt
print("Altitude:", scd.altitude, "meters above sea level")
scd.forced_recalibration_reference = 412
print("Forced recalibration reference:", scd.forced_recalibration_reference)
print("")

while True:
    data = scd.data_available
    if data:
        print("Data Available!")
        print("CO2:", scd.CO2, "PPM")
        print("Temperature:", scd.temperature, "degrees C")
        print("Humidity::", scd.relative_humidity, "%%rH")
        print("")
        print("Waiting for new data...")
        print("")

    time.sleep(0.5)

