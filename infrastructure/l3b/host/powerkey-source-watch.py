#!/usr/bin/env python3
"""Record KEY_POWER events from ACPI button inputs without grabbing them."""
import os
from pathlib import Path
import select
import struct
import time

EVENT = struct.Struct("@llHHi")
SOURCES = {"PNP0C0C", "LNXPWRBN"}

while True:
    devices = {}
    try:
        for node in sorted(Path("/sys/class/input").glob("event*")):
            try:
                phys = (node / "device/phys").read_text().strip()
                if phys.split("/", 1)[0] in SOURCES:
                    fd = os.open("/dev/input/" + node.name, os.O_RDONLY)
                    devices[fd] = (node.name, phys)
            except OSError:
                continue
        if devices:
            print("Watching:", ", ".join(f"{node} {phys}" for node, phys in devices.values()), flush=True)
        while devices:
            for fd in select.select(list(devices), [], [])[0]:
                data = os.read(fd, EVENT.size)
                if len(data) != EVENT.size:
                    raise OSError("Input device disconnected")
                _, _, kind, code, value = EVENT.unpack(data)
                if kind == 1 and code == 116:
                    node, phys = devices[fd]
                    action = {0: "release", 1: "press", 2: "repeat"}.get(value, value)
                    print(f"KEY_POWER {action} device={node} source={phys}", flush=True)
    except OSError:
        print("Input changed; rediscovering ACPI buttons", flush=True)
    finally:
        for fd in devices:
            os.close(fd)
    time.sleep(5)
