# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi environmental sensor station. Python scripts read from hardware sensors and write measurements to a local InfluxDB database (visualized via Grafana). A 4-position DIP switch controls WiFi, SDS011 power, and system shutdown. A PIR sensor + light level controls a DSI display backlight.

## Running Scripts

Scripts run directly on the Pi as root or pi user. There is no build step, test suite, or virtual environment.

- **Cron-scheduled** (once per minute): `SCD30.py`, `BME280.py`, `TSL2591.py`
- **Long-running daemons** (started at boot): `SDS011.py`, `DipSwitch.py`, `ScreenControl.py`
- Crontab is documented in `crontab.txt`; install with `crontab crontab.txt`
- `timesync.sh` runs daily to enable WiFi, sync NTP, write to RTC, then optionally disable WiFi

## Architecture

### Sensor scripts (BME280, SCD30, TSL2591, SDS011)
Each script reads from its sensor and writes to InfluxDB. They share a common pattern:
- InfluxDB connection: host `127.0.0.1:8086`, user `grafana`, database `SCD30Stats`
- Each uses a different `measurement_name` for its data
- I2C sensors use `board.I2C()` via Adafruit CircuitPython libraries
- SDS011 uses USB serial (`/dev/ttyUSB0`) with a custom binary protocol
- SCD30 and BME280 read once and exit; TSL2591 reads once and exits; SDS011 runs continuously

### DipSwitch.py (long-running daemon)
Controls WiFi (switch 3 on GPIO 4) and shutdown (switch 4 on GPIO 24) via a polling loop. Manages WiFi using `rfkill`, `wpa_cli`, and `dhclient` with retry logic for weak signals. Health-checks WiFi every 30 poll cycles.

### ScreenControl.py (long-running daemon)
Uses PIR motion sensor (GPIO 22) + TSL2591 light sensor to wake/sleep the DSI display backlight. Screen turns on for 60 seconds after motion if lux >= 5.

### DIP Switch to GPIO mapping
| Switch | GPIO | Function |
|--------|------|----------|
| 1 | 27 | SDS011 on/off |
| 2 | 17 | Unassigned |
| 3 | 4 | WiFi on/off |
| 4 | 24 | System shutdown |

## Key Dependencies

- `influxdb` (Python client for InfluxDB v1)
- Adafruit CircuitPython libraries: `adafruit-circuitpython-bme280`, `adafruit-circuitpython-tsl2591`, `adafruit-circuitpython-ds3231`
- `scd30_i2c` (SCD30 CO2 sensor)
- `gpiozero` (GPIO buttons/motion sensor)
- `rpi_backlight` (DSI display control)
- `pyserial` (SDS011 serial communication)

## Hardware Notes

- All I2C sensors share the bus on GPIO 2 (SDA) / GPIO 3 (SCL)
- DS3231 RTC is kernel-claimed at `0x68`; accessed via `hwclock` in `timesync.sh`
- Station altitude is hardcoded at 435m in `BME280.py` for sea-level pressure conversion
- Full GPIO pinout is in `GPIO_PINOUT.md`
