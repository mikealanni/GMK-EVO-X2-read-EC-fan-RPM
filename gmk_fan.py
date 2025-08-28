#!/usr/bin/env python3
import os
import time
import struct

EC_PATH = "/sys/kernel/debug/ec/ec0/io"

def read_ec():
    try:
        with open(EC_PATH, "rb") as f:
            return f.read(256)
    except Exception as e:
        print(f"Read failed: {e}")
        return None

def write_ec(offset, value):
    """Write a byte to EC register"""
    try:
        with open(EC_PATH, "r+b") as f:
            f.seek(offset)
            f.write(bytes([value & 0xFF]))
        return True
    except Exception as e:
        return False

def get_byte(data, offset):
    try:
        return data[offset]
    except:
        return 0

def get_rpm_little_endian(data, offset):
    """Get RPM value as little-endian 16-bit"""
    try:
        return struct.unpack("<H", data[offset:offset+2])[0]
    except:
        return 0

def monitor_all_fans():
    """Monitor all fans with your exact calculations"""
    data = read_ec()
    if not data:
        print("Cannot read EC data")
        return

    # Your exact RPM calculations
    fan1_rpm_raw = get_byte(data, 0x37)  # Fan 1 RPM byte
    fan2_rpm_raw = get_byte(data, 0x35)  # Fan 2 RPM byte
    sysfan_rpm_raw = get_byte(data, 0x28)  # Sysfan RPM byte (0x28, not 0x29)

    # Convert to actual RPM values based on your mapping
    # Fan 1 & 2: 0x0F = ~4000 RPM, 0x0D = ~3200 RPM, etc.
    # Sysfan: 0x06 = ~1900 RPM, 0x05 = ~1500 RPM, etc.

    # Approximate RPM calculations based on your values
    fan1_rpm = fan1_rpm_raw * 267  # 0x0F=15 * 267 = ~4000 RPM
    fan2_rpm = fan2_rpm_raw * 267  # 0x0F=15 * 267 = ~4000 RPM
    sysfan_rpm = sysfan_rpm_raw * 317  # 0x06=6 * 317 = ~1900 RPM

    # Control Values
    fan1_enable = get_byte(data, 0x23)
    fan1_speed = get_byte(data, 0x24)
    fan2_enable = get_byte(data, 0x21)
    fan2_speed = get_byte(data, 0x22)
    sysfan_enable = get_byte(data, 0x25)
    sysfan_speed = get_byte(data, 0x26)

    # Calculate approximate percentages based on your mappings
    fan1_pct_map = {34: 20, 35: 40, 36: 60, 37: 80, 38: 100}
    fan2_pct_map = {22: 100, 21: 80, 20: 60, 19: 40, 18: 20}
    sysfan_pct_map = {54: 100, 53: 80, 52: 60, 51: 40, 50: 20}

    fan1_pct = fan1_pct_map.get(fan1_speed, 0)
    fan2_pct = fan2_pct_map.get(fan2_speed, 0)
    sysfan_pct = sysfan_pct_map.get(sysfan_speed, 0)

    print("=== Complete Fan Status ===")
    print(f"Fan 1:   {fan1_rpm:>4} RPM | PWM: {fan1_pct:3d}% (0x24={fan1_speed}) [Enable: 0x23={fan1_enable}]")
    print(f"Fan 2:   {fan2_rpm:>4} RPM | PWM: {fan2_pct:3d}% (0x22={fan2_speed}) [Enable: 0x21={fan2_enable}]")
    print(f"Sysfan:  {sysfan_rpm:>4} RPM | PWM: {sysfan_pct:3d}% (0x26={sysfan_speed}) [Enable: 0x25={sysfan_enable}]")
    print()
    print("=== Fan Control System ===")
    print("1. Fan 1: 0x23=33 (enable) + 0x24=34-38 (20-100%)")
    print("2. Fan 2: 0x21=17 (enable) + 0x22=18-22 (20-100%)")
    print("3. Sysfan: 0x25=49 (enable) + 0x26=50-54 (20-100%)")
    print()
    print("=== RPM Details (Your Exact Values) ===")
    print(f"Fan 1 RPM: 0x37 = {fan1_rpm_raw:02X} = {fan1_rpm} RPM")
    print(f"Fan 2 RPM: 0x35 = {fan2_rpm_raw:02X} = {fan2_rpm} RPM")
    print(f"Sysfan RPM: 0x28 = {sysfan_rpm_raw:02X} = {sysfan_rpm} RPM")
    print()
    print("=== Your RPM Mappings ===")
    print("Fan 1 & 2: 0x0F=4000RPM, 0x0D=3200RPM, 0x0B=2400RPM, 0x09=1600RPM, 0x07=800RPM")
    print("Sysfan: 0x06=1900RPM, 0x05=1500RPM, 0x04=1200RPM, 0x03=800RPM, 0x02=400RPM")

def set_fan1_percentage(percentage):
    """Set Fan 1 speed"""
    print("Setting Fan 1...")

    # Map percentage to Fan 1 values
    fan1_mapping = {20: 34, 40: 35, 60: 36, 80: 37, 100: 38}
    closest = min(fan1_mapping.keys(), key=lambda x: abs(x - percentage))
    value = fan1_mapping[closest]

    write_ec(0x23, 33)  # Enable Fan 1 control
    write_ec(0x24, value)
    print(f"Set Fan 1 to {closest}% (value: {value})")

def set_fan2_percentage(percentage):
    """Set Fan 2 speed with your exact values"""
    print("Setting Fan 2...")

    # Map percentage to Fan 2 values (your exact mapping)
    # 22=100%, 21=80%, 20=60%, 19=40%, 18=20%
    if percentage <= 20:
        value = 18
    elif percentage <= 40:
        value = 19
    elif percentage <= 60:
        value = 20
    elif percentage <= 80:
        value = 21
    else:
        value = 22  # 100% = 22

    write_ec(0x21, 17)  # Enable Fan 2 control (your exact value)
    write_ec(0x22, value)
    print(f"Set Fan 2 to {percentage}% (0x22={value}, 0x21=17)")

def set_sysfan_percentage(percentage):
    """Set Sysfan speed with your exact values"""
    print("Setting Sysfan...")

    # Map percentage to Sysfan values (your exact mapping)
    # 54=100%, 53=80%, 52=60%, 51=40%, 50=20%
    if percentage <= 20:
        value = 50
    elif percentage <= 40:
        value = 51
    elif percentage <= 60:
        value = 52
    elif percentage <= 80:
        value = 53
    else:
        value = 54  # 100% = 54

    write_ec(0x25, 49)  # Enable Sysfan control (your exact value)
    write_ec(0x26, value)
    print(f"Set Sysfan to {percentage}% (0x26={value}, 0x25=49)")

def set_auto_mode():
    """Set all fans to auto mode"""
    print("Setting all fans to auto mode...")
    write_ec(0x23, 32)  # Disable Fan 1 manual control
    write_ec(0x21, 16)  # Disable Fan 2 manual control
    write_ec(0x25, 48)  # Disable Sysfan manual control (your exact value)
    print("All fans set to auto mode")

def main():
    while True:
        os.system('clear')
        monitor_all_fans()

        print()
        print("=== Fan Control ===")
        print("1. Set Fan 1 percentage")
        print("2. Set Fan 2 percentage")
        print("3. Set Sysfan percentage")
        print("4. Set all fans")
        print("5. Set auto mode (BIOS control)")
        print("6. Monitor continuously")
        print("q. Quit")

        try:
            choice = input("Enter choice: ").strip()

            if choice == 'q':
                break
            elif choice == '1':
                pct = int(input("Enter Fan 1 percentage (20-100): "))
                set_fan1_percentage(pct)
            elif choice == '2':
                pct = int(input("Enter Fan 2 percentage (20-100): "))
                set_fan2_percentage(pct)
            elif choice == '3':
                pct = int(input("Enter Sysfan percentage (20-100): "))
                set_sysfan_percentage(pct)
            elif choice == '4':
                fan1_pct = int(input("Enter Fan 1 percentage (20-100): "))
                fan2_pct = int(input("Enter Fan 2 percentage (20-100): "))
                sysfan_pct = int(input("Enter Sysfan percentage (20-100): "))
                set_fan1_percentage(fan1_pct)
                set_fan2_percentage(fan2_pct)
                set_sysfan_percentage(sysfan_pct)
            elif choice == '5':
                set_auto_mode()
            elif choice == '6':
                print("Monitoring... Press Ctrl+C to return to menu")
                try:
                    while True:
                        os.system('clear')
                        monitor_all_fans()
                        time.sleep(2)
                except KeyboardInterrupt:
                    pass
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
