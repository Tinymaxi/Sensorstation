# Sensorstation GPIO Pinout

## Pin Layout (J8 Header)

```
           3V3  (1)  (2)  5V
  [I2C] GPIO2  (3)  (4)  5V
  [I2C] GPIO3  (5)  (6)  GND
  [SW3] GPIO4  (7)  (8)  GPIO14
           GND  (9)  (10) GPIO15
  [SW2] GPIO17 (11) (12) GPIO18
  [SW1] GPIO27 (13) (14) GND
  [PIR] GPIO22 (15) (16) GPIO23
           3V3 (17) (18) GPIO24 [SW4]
        GPIO10 (19) (20) GND
         GPIO9 (21) (22) GPIO25
        GPIO11 (23) (24) GPIO8
           GND (25) (26) GPIO7
         GPIO0 (27) (28) GPIO1
         GPIO5 (29) (30) GND
         GPIO6 (31) (32) GPIO12
        GPIO13 (33) (34) GND
        GPIO19 (35) (36) GPIO16
        GPIO26 (37) (38) GPIO20
           GND (39) (40) GPIO21
```

## DIP Switches

| Switch | GPIO | Physical Pin | Function                        |
|--------|------|--------------|---------------------------------|
| 1      | 27   | 13           | SDS011 particle sensor on/off   |
| 2      | 17   | 11           | Unassigned                      |
| 3      | 4    | 7            | WiFi on/off                     |
| 4      | 24   | 18           | System shutdown                 |

## Sensors

| Device   | GPIO / Bus         | Physical Pin(s) | Function                          |
|----------|--------------------|-----------------|-----------------------------------|
| PIR      | GPIO 22            | 15              | Motion detection for screen wake  |
| BME280   | I2C (GPIO 2 + 3)   | 3, 5            | Temperature, humidity, pressure   |
| SCD30    | I2C (GPIO 2 + 3)   | 3, 5            | CO2, temperature, humidity        |
| TSL2591  | I2C (GPIO 2 + 3)   | 3, 5            | Light / lux                       |
| DS3231   | I2C (GPIO 2 + 3)   | 3, 5            | Real-time clock                   |
| SDS011   | USB serial         | /dev/ttyUSB0    | Particulate matter PM2.5 / PM10   |

## I2C Bus

- Bus: `/dev/i2c-1`
- SDA: GPIO 2 (pin 3)
- SCL: GPIO 3 (pin 5)
- Devices: BME280, SCD30, TSL2591, DS3231 (0x68, claimed by kernel as RTC)

## DSI Display

- Backlight control: `/sys/class/backlight/rpi_backlight/`
- Woken by PIR (GPIO 22) + TSL2591 lux >= 5
- Stays on 60 seconds after last motion
