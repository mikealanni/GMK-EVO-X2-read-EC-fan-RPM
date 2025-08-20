#!/usr/bin/env python3
import struct
import time
import sys
import tty, termios
import select

EC_PATH = "/sys/kernel/debug/ec/ec0/io"

# RPM registers from your previous scan
RPM_OFFSETS = [0x28, 0x34, 0x36]

# Candidate PWM offsets
PWM_OFFSETS = [0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E]

def read_byte(offset):
    with open(EC_PATH, "rb") as f:
        f.seek(offset)
        return struct.unpack("B", f.read(1))[0]

def read_word(offset):
    with open(EC_PATH, "rb") as f:
        f.seek(offset)
        return struct.unpack("<H", f.read(2))[0]

def write_byte(offset, value):
    with open(EC_PATH, "r+b") as f:
        f.seek(offset)
        f.write(struct.pack("B", value))

# Non-blocking keyboard read
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# Map fan index to a chosen PWM offset (manually from scan)
FAN_PWM_MAP = {
    0: 0x07,  # SysFan
    1: 0x08,  # Fan1
    2: 0x09,  # Fan2
}

# Initialize PWM values
PWM_VALUES = {fan: read_byte(offset) for fan, offset in FAN_PWM_MAP.items()}

print("Monitoring EC fans. Press Ctrl+C to exit. Use 1-3 to select fan, arrows to adjust PWM.")
print("Format: SysFan: RPM | Fan1: RPM | Fan2: RPM | PWM: val")

try:
    selected_fan = 0
    while True:
        # Read current RPMs
        rpms = [read_word(off) for off in RPM_OFFSETS]

        # Print in one line
        sys.stdout.write(f"\rSysFan: {int(rpms[0]/22):5} | Fan1: {rpms[1]:5} | Fan2: {rpms[2]:5} | PWM: {PWM_VALUES[selected_fan]:3} ")
        sys.stdout.flush()

        # Non-blocking input check
        time.sleep(0.5)
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            c = getch()
            if c in ["1", "2", "3"]:
                selected_fan = int(c) - 1
            elif c == "w":  # increase PWM
                PWM_VALUES[selected_fan] = min(PWM_VALUES[selected_fan] + 10, 255)
                write_byte(FAN_PWM_MAP[selected_fan], PWM_VALUES[selected_fan])
            elif c == "s":  # decrease PWM
                PWM_VALUES[selected_fan] = max(PWM_VALUES[selected_fan] - 10, 0)                write_byte(FAN_PWM_MAP[selected_fan], PWM_VALUES[selected_fan])

except KeyboardInterrupt:
    print("\nExiting, restoring original PWM values...")
    for fan, offset in FAN_PWM_MAP.items():
        write_byte(offset, PWM_VALUES[fan])
