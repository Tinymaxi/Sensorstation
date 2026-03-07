#!/bin/bash
# Daily time sync script
# Enables WiFi, syncs time via NTP, writes to RTC
# Only disables WiFi afterwards if DIP switch 3 is OFF

# Unblock and bring up WiFi
rfkill unblock wifi
ip link set wlan0 up
iw dev wlan0 set power_save off

# Kick wpa_supplicant to reload config and connect cleanly
wpa_cli -i wlan0 reconfigure > /dev/null 2>&1
sleep 2
wpa_cli -i wlan0 enable_network 0 > /dev/null 2>&1
wpa_cli -i wlan0 reassociate > /dev/null 2>&1

# Wait for association (up to 60 seconds for weak signal)
for i in $(seq 1 60); do
    if wpa_cli -i wlan0 status | grep -q 'wpa_state=COMPLETED'; then
        break
    fi
    sleep 1
done

# Wait for DHCP IP (up to 30 seconds)
for i in $(seq 1 30); do
    if ip addr show wlan0 | grep -q 'inet ' && ! ip addr show wlan0 | grep -q '169.254.'; then
        break
    fi
    sleep 1
done

# If still no IP, force DHCP
if ! ip addr show wlan0 | grep -q 'inet ' || ip addr show wlan0 | grep -q '169.254.'; then
    dhclient -1 -timeout 15 wlan0 2>/dev/null
    sleep 2
fi

# Sync time via NTP and write to RTC
if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
    systemctl restart systemd-timesyncd
    sleep 5
    hwclock -w
    echo "$(date): Time sync successful" >> /var/log/timesync.log
else
    echo "$(date): Time sync FAILED - no internet" >> /var/log/timesync.log
fi

# Only disable WiFi if DIP switch 3 is OFF
# GPIO 4 sysfs value: 0 = switch ON (pulled low), 1 = switch OFF (pulled high)
# Re-read in case switch changed during sync
DIP_WIFI=$(cat /sys/class/gpio/gpio4/value 2>/dev/null)
if [ "$DIP_WIFI" != "0" ]; then
    dhclient -r wlan0 2>/dev/null
    ip link set wlan0 down
    rfkill block wifi
fi
