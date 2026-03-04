#!/usr/bin/env python

import serial
import time
import datetime
from influxdb import InfluxDBClient
from gpiozero import Button
from subprocess import check_call

# Serial connection to SDS011
ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

# Dip switches
switch_one  = Button(27)   # ON = sensor active, OFF = sensor sleep
switch_four = Button(24)   # ON = shutdown

# SDS011 commands for sensor ID A160
CMD_ACTIVE_MODE = [0xaa,0xb4,0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x04,0xab]
CMD_CONTINUOUS  = [0xaa,0xb4,0x08,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0a,0xab]
CMD_WORK        = [0xaa,0xb4,0x06,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x09,0xab]
CMD_SLEEP       = [0xaa,0xb4,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x08,0xab]

# InfluxDB configuration
ifuser           = "grafana"
ifpass           = "<passwordhere>"
ifdb             = "SCD30Stats"
ifhost           = "127.0.0.1"
ifport           = 8086
measurement_name = "SDS011Stats"

# Initialise sensor: active report mode, continuous measurement
ser.write(bytes(CMD_ACTIVE_MODE))
time.sleep(1)
ser.write(bytes(CMD_CONTINUOUS))
time.sleep(1)

sensor_running = False
checksum_old = 0

while True:
    # Switch 4 ON = shutdown
    if switch_four.is_pressed:
        ser.write(bytes(CMD_SLEEP))
        time.sleep(2)
        check_call(['sudo', 'poweroff'])

    # Switch 1 controls sensor on/off
    if switch_one.is_pressed:
        if not sensor_running:
            ser.write(bytes(CMD_WORK))
            sensor_running = True
    else:
        if sensor_running:
            ser.write(bytes(CMD_SLEEP))
            sensor_running = False

    if not sensor_running:
        time.sleep(1)
        continue

    # Read 10-byte data packet from sensor
    Data = bytes(ser.read(10))

    if len(Data) != 10:
        continue

    CommandID = hex(Data[1])
    if CommandID != '0xc0':
        continue

    checksum_new = sum(Data[2:8]) & 0xFF
    if checksum_new == checksum_old:
        continue
    checksum_old = checksum_new

    if checksum_new != Data[8]:
        continue

    # Combine low and high bytes correctly
    dataTWO_FIVE = (Data[3] * 256 + Data[2]) / 10
    dataTEN      = (Data[5] * 256 + Data[4]) / 10

    timestamp = datetime.datetime.utcnow()
    body = [
        {
            "measurement": measurement_name,
            "time": timestamp,
            "fields": {
                "PM2.5": dataTWO_FIVE,
                "PM10":  dataTEN
            }
        }
    ]

    ifclient = InfluxDBClient(ifhost, ifport, ifuser, ifpass, ifdb)
    ifclient.write_points(body)
