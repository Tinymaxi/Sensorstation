#!/usr/bin/env python

import time
import subprocess
import serial
from gpiozero import Button

# DIP switch GPIO pins
SWITCH_1 = 27   # SDS011 particle sensor on/off
SWITCH_2 = 17   # CO2 sensor calibration
SWITCH_3 = 4    # WiFi on/off
SWITCH_4 = 24   # System shutdown

# Outdoor CO2 reference level (ppm)
CO2_OUTDOOR_PPM = 420

SDS011_SCRIPT = '/home/pi/Sensorstation/SDS011.py'
SDS011_PORT = '/dev/ttyUSB0'
SDS011_CMD_SLEEP = bytes([0xaa,0xb4,0x06,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xa1,0x60,0x08,0xab])

# WiFi settings (tuned for weak signal)
WIFI_CONNECT_TIMEOUT = 90     # seconds to wait for association
WIFI_DHCP_TIMEOUT = 30        # seconds to wait for DHCP
WIFI_MAX_RETRIES = 3          # retries per enable attempt
POLL_INTERVAL = 1             # seconds between DIP switch polls
HEALTH_CHECK_INTERVAL = 30    # seconds between WiFi health checks

switch_one = Button(SWITCH_1)
switch_two = Button(SWITCH_2)
switch_three = Button(SWITCH_3)
switch_four = Button(SWITCH_4)

sds011_proc = None
sds011_sleeping = False
wifi_on = False


def sds011_start():
    global sds011_proc, sds011_sleeping
    if sds011_proc and sds011_proc.poll() is None:
        return
    print("SDS011: starting...")
    sds011_proc = subprocess.Popen(['python', SDS011_SCRIPT])
    sds011_sleeping = False


def sds011_sleep():
    """Send sleep command to SDS011 to stop the fan."""
    try:
        ser = serial.Serial(SDS011_PORT, 9600, timeout=1)
        ser.reset_input_buffer()
        # Send sleep command multiple times — sensor may ignore
        # commands sent right after power-on
        for i in range(3):
            ser.write(SDS011_CMD_SLEEP)
            time.sleep(1)
        ser.close()
        print("SDS011: sent sleep command")
    except Exception as e:
        print("SDS011: could not send sleep: {}".format(e))


def sds011_stop():
    global sds011_proc, sds011_sleeping
    if sds011_proc and sds011_proc.poll() is None:
        print("SDS011: stopping...")
        sds011_proc.terminate()
        sds011_proc.wait(timeout=10)
        sds011_proc = None
    if not sds011_sleeping:
        sds011_sleep()
        sds011_sleeping = True


def run(cmd, timeout=15):
    """Run a shell command, return (success, output)."""
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=timeout)
        return True, out.decode().strip()
    except Exception as e:
        return False, str(e)


def is_wifi_blocked():
    ok, out = run(['rfkill', 'list', 'wifi'])
    return ok and 'Soft blocked: yes' in out


def wpa_state():
    """Return wpa_supplicant state string, e.g. 'COMPLETED', 'SCANNING'."""
    ok, out = run(['wpa_cli', '-i', 'wlan0', 'status'])
    if not ok:
        return 'UNKNOWN'
    for line in out.split('\n'):
        if line.startswith('wpa_state='):
            return line.split('=', 1)[1]
    return 'UNKNOWN'


def is_wifi_connected():
    return wpa_state() == 'COMPLETED'


def has_valid_ip():
    ok, out = run(['ip', 'addr', 'show', 'wlan0'])
    if not ok:
        return False
    for line in out.split('\n'):
        if 'inet ' in line and '169.254.' not in line:
            return True
    return False


def wait_for_connection(timeout):
    """Wait up to timeout seconds for WiFi association. Returns True if connected."""
    for i in range(timeout):
        if is_wifi_connected():
            return True
        if not switch_three.is_pressed:
            print("WiFi: switch turned off during connect, aborting")
            return False
        time.sleep(1)
    return False


def wait_for_ip(timeout):
    """Wait up to timeout seconds for a valid DHCP IP. Returns True if got one."""
    for i in range(timeout):
        if has_valid_ip():
            return True
        time.sleep(1)
    return False


def ensure_dhcp():
    """Make sure we have a valid IP, force dhclient if needed."""
    if has_valid_ip():
        return True
    print("WiFi: waiting for DHCP...")
    if wait_for_ip(WIFI_DHCP_TIMEOUT):
        return True
    # dhcpcd didn't deliver, force it
    print("WiFi: forcing dhclient...")
    run(['sudo', 'dhclient', '-1', '-timeout', '20', 'wlan0'], timeout=25)
    time.sleep(2)
    return has_valid_ip()


def ensure_wpa_supplicant():
    """Make sure wpa_supplicant is running on wlan0. After rfkill block + reboot,
    it may not be attached to the interface."""
    ok, _ = run(['wpa_cli', '-i', 'wlan0', 'ping'])
    if ok:
        return
    print("WiFi: wpa_supplicant not responding, restarting...")
    # Kill any stale instance, then start fresh
    run(['sudo', 'killall', 'wpa_supplicant'], timeout=5)
    time.sleep(1)
    run(['sudo', 'wpa_supplicant', '-B', '-i', 'wlan0',
         '-c', '/etc/wpa_supplicant/wpa_supplicant.conf'], timeout=10)
    time.sleep(3)
    ok, _ = run(['wpa_cli', '-i', 'wlan0', 'ping'])
    if ok:
        print("WiFi: wpa_supplicant started")
    else:
        print("WiFi: wpa_supplicant still not responding")


def wifi_enable():
    """Enable WiFi with retries for weak signal."""
    global wifi_on
    print("WiFi: enabling...")

    # Unblock radio if blocked
    if is_wifi_blocked():
        run(['sudo', 'rfkill', 'unblock', 'wifi'])
        time.sleep(2)

    # Bring interface up
    run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'])
    time.sleep(1)

    # Make sure wpa_supplicant is running (may be missing after offline boot)
    ensure_wpa_supplicant()

    # Disable power saving — critical for weak signal
    run(['sudo', 'iw', 'dev', 'wlan0', 'set', 'power_save', 'off'])

    # Force wpa_supplicant to reload config cleanly
    # This fixes TEMP-DISABLED state after rfkill cycles
    run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
    time.sleep(2)

    for attempt in range(1, WIFI_MAX_RETRIES + 1):
        print("WiFi: attempt {}/{}".format(attempt, WIFI_MAX_RETRIES))

        if not switch_three.is_pressed:
            print("WiFi: switch turned off, aborting")
            return

        # Enable network and kick association
        run(['wpa_cli', '-i', 'wlan0', 'enable_network', '0'])
        run(['wpa_cli', '-i', 'wlan0', 'reassociate'])

        if wait_for_connection(WIFI_CONNECT_TIMEOUT):
            print("WiFi: associated with AP")
            if ensure_dhcp():
                ok, out = run(['ip', '-4', 'addr', 'show', 'wlan0'])
                ip_line = [l.strip() for l in out.split('\n') if 'inet ' in l]
                print("WiFi: connected - {}".format(ip_line[0] if ip_line else "OK"))
                wifi_on = True
                return
            else:
                print("WiFi: DHCP failed on attempt {}".format(attempt))
        else:
            if not switch_three.is_pressed:
                return
            print("WiFi: association failed on attempt {}".format(attempt))

        # Between retries: bounce the interface to reset driver state
        if attempt < WIFI_MAX_RETRIES:
            print("WiFi: resetting interface for retry...")
            run(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'])
            time.sleep(3)
            run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'])
            time.sleep(2)
            run(['sudo', 'iw', 'dev', 'wlan0', 'set', 'power_save', 'off'])
            run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
            time.sleep(2)

    print("WiFi: all attempts failed, will retry in health check")
    wifi_on = True  # Stay in "on" mode so health check keeps trying


def wifi_disable():
    """Disable WiFi cleanly."""
    global wifi_on
    print("WiFi: disabling...")

    run(['sudo', 'dhclient', '-r', 'wlan0'])
    run(['wpa_cli', '-i', 'wlan0', 'disconnect'])
    time.sleep(1)
    run(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'])
    time.sleep(1)
    run(['sudo', 'rfkill', 'block', 'wifi'])

    wifi_on = False
    print("WiFi: disabled")


def wifi_health_check():
    """Re-establish connection if WiFi is on but dropped (common with weak signal)."""
    if is_wifi_connected() and has_valid_ip():
        return  # All good

    state = wpa_state()
    print("WiFi: health check — state={}, has_ip={}".format(state, has_valid_ip()))

    # Make sure wpa_supplicant is still running
    ensure_wpa_supplicant()

    # Disable power saving (may have been re-enabled)
    run(['sudo', 'iw', 'dev', 'wlan0', 'set', 'power_save', 'off'])

    if state == 'COMPLETED':
        # Connected but no IP — just need DHCP
        ensure_dhcp()
        return

    if state in ('TEMP-DISABLED', 'INACTIVE', 'DISCONNECTED', 'INTERFACE_DISABLED'):
        # Broken state — reconfigure to start fresh
        print("WiFi: bad state '{}', reconfiguring...".format(state))
        run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
        time.sleep(2)

    # Try to reconnect
    run(['wpa_cli', '-i', 'wlan0', 'enable_network', '0'])
    run(['wpa_cli', '-i', 'wlan0', 'reassociate'])

    if wait_for_connection(WIFI_CONNECT_TIMEOUT):
        print("WiFi: re-associated")
        ensure_dhcp()
    else:
        # Full interface reset as last resort
        print("WiFi: reassociate failed, resetting interface...")
        run(['sudo', 'ip', 'link', 'set', 'wlan0', 'down'])
        time.sleep(3)
        run(['sudo', 'ip', 'link', 'set', 'wlan0', 'up'])
        time.sleep(2)
        run(['sudo', 'iw', 'dev', 'wlan0', 'set', 'power_save', 'off'])
        run(['wpa_cli', '-i', 'wlan0', 'reconfigure'])
        time.sleep(2)
        run(['wpa_cli', '-i', 'wlan0', 'enable_network', '0'])
        run(['wpa_cli', '-i', 'wlan0', 'reassociate'])

        if wait_for_connection(WIFI_CONNECT_TIMEOUT):
            print("WiFi: re-associated after reset")
            ensure_dhcp()
        else:
            print("WiFi: still not connected, will retry next cycle")


def co2_calibrate():
    """Force-calibrate the SCD30 CO2 sensor to outdoor level using I2C command 0x5204."""
    try:
        from scd30_i2c import SCD30
        scd = SCD30()
        scd._send_command(0x5204, num_response_words=0, arguments=[CO2_OUTDOOR_PPM])
        print("CO2: calibrated to {} ppm".format(CO2_OUTDOOR_PPM))
    except Exception as e:
        print("CO2: calibration failed: {}".format(e))


def shutdown():
    """Safely shut down the system."""
    print("Shutdown switch activated, powering off...")
    run(['sudo', 'poweroff'])


# --- Boot: sync state with physical switches ---

print("DipSwitch: starting, checking initial switch states...")

if switch_one.is_pressed:
    sds011_start()
else:
    # Sensor needs time after USB power-on before it accepts sleep commands
    print("SDS011: waiting 30s for sensor to initialize before sleeping...")
    time.sleep(30)
    sds011_sleep()

if switch_three.is_pressed:
    wifi_enable()
else:
    if not is_wifi_blocked():
        wifi_disable()

health_check_counter = 0
co2_cal_was_on = switch_two.is_pressed
if co2_cal_was_on:
    print("CO2 cal: switch is ON at boot, ignoring until toggled off then on")
shutdown_was_on = switch_four.is_pressed
if shutdown_was_on:
    print("Shutdown: switch is ON at boot, ignoring until toggled off then on")

# --- Main loop ---

print("DipSwitch: monitoring switches...")

while True:
    try:
        # Switch 1: SDS011 particle sensor
        if switch_one.is_pressed:
            sds011_start()
        else:
            sds011_stop()

        # Switch 2: CO2 calibration (only on OFF→ON transition)
        if switch_two.is_pressed:
            if not co2_cal_was_on:
                co2_calibrate()
            co2_cal_was_on = True
        else:
            co2_cal_was_on = False

        # Switch 4: shutdown (only on OFF→ON transition)
        if switch_four.is_pressed:
            if not shutdown_was_on:
                shutdown()
                time.sleep(10)
            shutdown_was_on = True
        else:
            shutdown_was_on = False

        # Switch 3: WiFi toggle
        if switch_three.is_pressed:
            if not wifi_on:
                wifi_enable()
            else:
                health_check_counter += 1
                if health_check_counter >= HEALTH_CHECK_INTERVAL:
                    health_check_counter = 0
                    wifi_health_check()
        else:
            if wifi_on:
                wifi_disable()
            health_check_counter = 0

    except Exception as e:
        print("DipSwitch error: {}".format(e))

    time.sleep(POLL_INTERVAL)
