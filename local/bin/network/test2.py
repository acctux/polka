#!/usr/bin/python3
import dbus
import sys
import time

# Initialize the DBus system bus
bus = dbus.SystemBus()

# Get the ObjectManager interface of ConnMan to list all available network interfaces
manager = dbus.Interface(
    bus.get_object("net.connman.iwd", "/"), "org.freedesktop.DBus.ObjectManager"
)

# Get the device path for the Station (Network Device)
device_path = "/net/connman/iwd/0/4"  # Adjust as needed based on your device path
device = dbus.Interface(
    bus.get_object("net.connman.iwd", device_path), "net.connman.iwd.Station"
)

# Trigger a scan
print("Scanning for available networks...")
device.Scan()

# Wait for the scan to complete
time.sleep(5)

# Fetch the managed objects again, possibly with signal strength
print("Available Networks (After Scan):")
for path, interfaces in manager.GetManagedObjects().items():
    if "net.connman.iwd.Network" not in interfaces:
        continue

    # Extract network details
    network = interfaces["net.connman.iwd.Network"]
    network_name = network.get("Name", "Unknown Network")

    # Fetch signal strength from the network, if available
    signal_strength = network.get("Strength", "N/A")

    # Print network and signal strength
    print(f"[ {network_name} ]")
    print(f"    Signal Strength: {signal_strength} dBm")

