#!/usr/bin/env python3
"""Tiny read-only host stats endpoint for the Homepage dashboard.

Serves JSON on 10.1.3.1:8099 so containers on the l3b bridge can reach it
without exposing anything on the LAN. No writes, no external calls.
"""
import json
import os
import subprocess
import threading
from pathlib import Path
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = ("10.1.3.1", 8099)
_last_cpu = None
_lock = threading.Lock()


def cpu_sample():
    with open("/proc/stat") as fh:
        parts = fh.readline().split()[1:]
    vals = [int(x) for x in parts]
    idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
    return sum(vals), idle


def cpu_percent():
    global _last_cpu
    total, idle = cpu_sample()
    with _lock:
        if _last_cpu is None:
            _last_cpu = (total, idle)
            time.sleep(0.25)
            total, idle = cpu_sample()
        pt, pi = _last_cpu
        dt, di = total - pt, idle - pi
        _last_cpu = (total, idle)
    if dt <= 0:
        return 0.0
    return round(100.0 * (dt - di) / dt, 1)


def meminfo():
    info = {}
    with open("/proc/meminfo") as fh:
        for line in fh:
            key, _, rest = line.partition(":")
            info[key] = int(rest.split()[0]) * 1024
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    used = total - avail
    swap_total = info.get("SwapTotal", 0)
    swap_used = swap_total - info.get("SwapFree", 0)
    return {
        "mem_total_gb": round(total / 1e9, 1),
        "mem_used_gb": round(used / 1e9, 1),
        "mem_pct": round(100.0 * used / total, 1) if total else 0.0,
        "swap_pct": round(100.0 * swap_used / swap_total, 1) if swap_total else 0.0,
    }


def disk_pct(path):
    try:
        st = os.statvfs(path)
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        total = st.f_blocks * st.f_frsize
        return round(100.0 * used / total, 1) if total else 0.0
    except OSError:
        return None


def containers():
    try:
        out = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=8, check=False,
        ).stdout
    except Exception:
        return None
    lines = [line for line in out.splitlines() if line.strip()]
    unhealthy = sum(1 for line in lines if "unhealthy" in line.lower())
    restarting = sum(1 for line in lines if "restarting" in line.lower())
    return {"running": len(lines), "unhealthy": unhealthy, "restarting": restarting}


def _read_temp(path):
    try:
        with open(path) as fh:
            value = int(fh.read().strip()) / 1000.0
    except Exception:
        return None
    return value if 10 <= value <= 120 else None


def temperatures():
    """Return the CPU package temperature, preferring coretemp."""
    fallback = None
    for hwmon in sorted(Path("/sys/class/hwmon").glob("hwmon*")):
        try:
            name = (hwmon / "name").read_text().strip()
        except OSError:
            continue
        value = _read_temp(hwmon / "temp1_input")
        if value is None:
            continue
        if name in ("coretemp", "k10temp"):
            return round(value, 1)
        if fallback is None:
            fallback = value
    return round(fallback, 1) if fallback else None


def uptime_hours():
    with open("/proc/uptime") as fh:
        return round(float(fh.read().split()[0]) / 3600.0, 1)


def payload():
    data = {
        "cpu_pct": cpu_percent(),
        "load1": round(os.getloadavg()[0], 2),
        "uptime_hours": uptime_hours(),
        "disk_root_pct": disk_pct("/"),
        "disk_data_pct": disk_pct("/data"),
        "disk_backup_pct": disk_pct("/BACKUP"),
        "temp_c": temperatures(),
    }
    data.update(meminfo())
    data.update(containers() or {"running": None, "unhealthy": None, "restarting": None})
    return data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] not in ("/stats", "/"):
            self.send_error(404)
            return
        try:
            body = json.dumps(payload()).encode()
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    cpu_sample()
    ThreadingHTTPServer(LISTEN, Handler).serve_forever()
