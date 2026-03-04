#!/usr/bin/env python

import serial
import time
import datetime
import psutil
from influxdb import InfluxDBClient
from gpiozero import Button
from subprocess import check_call

ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600 , bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE , timeout=1)

button_one = Button(27)
button_two = Button(17)
button_three = Button(4)
button_four = Button(24)

def sensor_work():
#     print("Sensor going to work. **********************************")
    global rList
    # Send command, set the sensor with ID A160 to work.
    rList = [0xaa,0xb4,0x06,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x09,0xab]
    return rList

def sensor_sleep():
#     print("Sensor going to sleep. *********************************")
    global rList
    # Send command, set the sensor with ID A160 to sleep.
    rList = [0xaa,0xb4,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x08,0xab]
    return rList

def continuos_mode():
#     print('Sensor in continuos mode. *******************************')
    global rList
    # Send command to set the working period of sensor with ID A160 to 0, it will work continuosly.
    rList = [0xaa,0xb4,0x08,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0a,0xab]
    return rList

def one_minute_intervall():
#     print('Sensor in one minute intervall mode. ********************')
    global rList
    # Send command to set the working period of sensor with ID A160 to 1 minute.
    rList = [0xaa,0xb4,0x08,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0b,0xab]    
    return rList

def ten_minute_intervall():
#     print('Sensor in 10 minute intervall mode. ****************')
    global rList
    # Send command to set the working period of sensor with ID A160 to 10 minute.
    rList = [0xaa,0xb4,0x08,0x01,0x0a,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x14,0xab]  
    return rList

def thirty_minute_intervall():
#     print('Sensor in thirty minute interva ll mode. *****************')
    global rList
    # Send command to set the working period of sensor with ID A160 to 30 minute.
    rList = [0xaa,0xb4,0x08,0x01,0x1e,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x28,0xab]
    return rList

def shutdown():
#     print('Sensor is goint to sleep and Raspberry pi is doint shutdown.')   
    # Send command, set the sensor with ID A160 to sleep.
    rList = [0xaa,0xb4,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x08,0xab]
    ser.write(bytes(rList))
    time.sleep(5)
    check_call(['sudo', 'poweroff'])



checksum_old = 0

# PC sensd command, set the sensor with ID A160 to report active mode.
# Report active mode.
rList = [0xaa,0xb4,0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x04,0xab]

while True:
#     ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600 , bytesize=serial.EIGHTBITS,
#                     parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE , timeout=1)
    

    button_one.when_pressed = sensor_work
    
    button_one.when_released = sensor_sleep
    
    button_two.when_pressed = continuos_mode
    
    button_two.when_released = one_minute_intervall
    
    button_three.when_pressed = ten_minute_intervall
    
    button_three.when_released = thirty_minute_intervall
    
    button_four.when_pressed = shutdown
    
    button_four.when_released = shutdown
    
    
    ser.write(bytes(rList))
    rList = [] 
    time.sleep(4)
    Data = bytes(ser.read(10))
    time.sleep(4)
#     print('')
#     print(bytes(rList))
#     print(Data.hex())
             
    if len(Data) == 0:
#         print('No data recived from sensor')
        checksum_new = 0
    elif len(Data) == 10:
        checksum_new = int(hex(sum(Data[2:8])) ,16)
#          print('New data recived from sensor')
    
#     print ('New checksum is %i, old checksum is %i' % (checksum_new,checksum_old))
        
    CommandID = (hex(sum(Data[1:2])))
#     print(CommandID)
    
    if checksum_new != checksum_old and CommandID == '0xc0':
        checksum_old = checksum_new
#         print(hex(sum(Data[0:1])))
#         print(hex(sum(Data[1:2])))
#         print(hex(sum(Data[2:3])))
#         print(hex(sum(Data[3:4])))
#         print(hex(sum(Data[4:5])))
#         print(hex(sum(Data[5:6])))
#         print(hex(sum(Data[6:7])))
#         print(hex(sum(Data[7:8])))
#         print(hex(sum(Data[8:9])))
#         print(hex(sum(Data[9:10])))
#         print('')

        checksum = hex(sum(Data[2:8]))
        LastByte = int(f'0x{(checksum[-2:])}',16)
#         print(LastByte)
#         print(Data[8])
        if LastByte == Data[8]:
            
            b = (str(Data[2]))
            a = (str(Data[3]))
            d = (str(Data[4]))
            c = (str(Data[5]))
            dataTWO_FIVE = int(f"{a}{b}")/10
            dataTEN = int (f"{c}{d}")/10
#             print(f"PM2.5 = {dataTWO_FIVE} PM10 = {dataTEN}")
#             print('')
#             print('')
            PM25 = f"PM2.5 = {dataTWO_FIVE} "
            PM10 = f"PM10 = {dataTEN}"
        else:
            dataTWO_FIVE = 0
            dataTWO_FIVE = 0

        # influx configuration - edit these
        ifuser = "grafana"
        ifpass = "<passwordhere>"
        ifdb   = "SCD30Stats"
        ifhost = "127.0.0.1"
        ifport = 8086
        measurement_name = "SDS011Stats"

        # take a timestamp for this measurement
        timestamp = datetime.datetime.utcnow()
#         print(timestamp)
#         print('')
        # format the data as a single measurement for influx
        body = [
            {
                "measurement": measurement_name,
                "time": timestamp,
                "fields": {
                    "PM2.5": dataTWO_FIVE,
                    "PM10": dataTEN
                }
            }
        ]

        # connect to influx
        ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

        # write the measurement
        ifclient.write_points(body)


# PC sensd command, query the current working mode.
# rList = [0xaa,0xb4,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xff,0xff,0x00,0xab]

# PC sensd command, set the sensor with ID A160 to report active mode.
# Report active mode.
# rList = [0xaa,0xb4,0x02,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x04,0xab]

# PC sensd command, set the sensor with ID A160 to report query mode.
# Report query mode. Needs a send data request command to return data.
# rList = [0xaa,0xb4,0x02,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x05,0xab]

# Send a data request command to sensor with all ID.
# rList = [0xaa,0xb4,0x04,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xff,0xff,0x02,0xab]

# Send a data request command to sensor with ID A160.
# rList = [0xaa,0xb4,0x04,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x05,0xab]

# Send command, set the sensor with ID A160 to sleep.
# rList = [0xaa,0xb4,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x08,0xab]

# Send command, set the sensor with ID A160 to work.
# rList = [0xaa,0xb4,0x06,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x09,0xab]

# Send command to set the working period of sensor with ID A160 to 1 minute.
# rList = [0xaa,0xb4,0x08,0x01,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0b,0xab]

# Send command to set the working period of sensor with ID A160 to 2 minute.
# rList = [0xaa,0xb4,0x08,0x01,0x02,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0c,0xab]

# Send command to set the working period of sensor with ID A160 to 3 minute.
# rList = [0xaa,0xb4,0x08,0x01,0x03,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0d,0xab]

# Send command to set the working period of sensor with ID A160 to 15 minute.
# rList = [0xaa,0xb4,0x08,0x01,0x0f,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x13,0xab]

# Send command to set the working period of sensor with ID A160 to 30 minute.
# rList = [0xaa,0xb4,0x08,0x01,0x1e,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x1c,0xab]

# Send command to set the working period of sensor with ID A160 to 0, it will work continuosly.
# rList = [0xaa,0xb4,0x08,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x0a,0xab]

# Needed this for getting the checksum of the command 
# checksum = hex(sum(rList[2:17]))
# print(int(checksum, 16))
# LastByte = int(f'0x{(checksum[-2:])}',16)
# print('Last byte = %x' % LastByte)











