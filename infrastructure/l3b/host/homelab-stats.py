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
            ["docker", "ps", "-a", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=8, check=False,
        ).stdout
    except Exception:
        return None
    lines = [line.lower() for line in out.splitlines() if line.strip()]
    running = sum(1 for line in lines if line.startswith("up"))
    result = {
        "running": running,
        "total": len(lines),
        "stopped": len(lines) - running,
        "unhealthy": sum(1 for line in lines if "unhealthy" in line),
        "restarting": sum(1 for line in lines if "restarting" in line),
    }
    try:
        images = subprocess.run(
            ["docker", "images", "-q"],
            capture_output=True, text=True, timeout=8, check=False,
        ).stdout
        result["images"] = len({line for line in images.splitlines() if line.strip()})
    except Exception:
        result["images"] = None
    return result


def failed_units():
    try:
        out = subprocess.run(
            ["systemctl", "--failed", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=8, check=False,
        ).stdout
    except Exception:
        return None
    return len([line for line in out.splitlines() if line.strip()])


NET_IFACE = "eno1"
_net_rate = {"rx_mbs": None, "tx_mbs": None}


def _net_bytes():
    with open("/proc/net/dev") as fh:
        for line in fh:
            name, _, rest = line.partition(":")
            if name.strip() == NET_IFACE:
                cols = rest.split()
                return int(cols[0]), int(cols[8])
    return None


def _net_sampler():
    last, last_t = _net_bytes(), time.monotonic()
    while True:
        time.sleep(5)
        now, now_t = _net_bytes(), time.monotonic()
        if last and now and now_t > last_t:
            dt = now_t - last_t
            _net_rate["rx_mbs"] = round((now[0] - last[0]) / dt / 1e6, 2)
            _net_rate["tx_mbs"] = round((now[1] - last[1]) / dt / 1e6, 2)
        last, last_t = now, now_t


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


def powerkey_state():
    """ACPI power-key events recorded by powerkey-watch.service."""
    try:
        with open("/var/lib/powerkey-watch/state.json") as fh:
            data = json.load(fh)
        return {
            "powerkey_events": int(data.get("count", 0)),
            "powerkey_last": data.get("last") or None,
        }
    except (OSError, ValueError, TypeError):
        return {"powerkey_events": None, "powerkey_last": None}


POCKETID_DB = "/data/apps/pocket-id/data/pocket-id.db"


def pocketid_counts():
    """Read-only counts from Pocket ID's SQLite database."""
    import sqlite3
    try:
        con = sqlite3.connect(f"file:{POCKETID_DB}?mode=ro", uri=True, timeout=2)
        try:
            def count(table):
                return con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            return {
                "users": count("users"),
                "passkeys": count("webauthn_credentials"),
                "clients": count("oidc_clients"),
                "groups": count("user_groups"),
            }
        finally:
            con.close()
    except Exception:
        return {"users": None, "passkeys": None, "clients": None, "groups": None}


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
        "cpus": os.cpu_count(),
        "failed_units": failed_units(),
        "net_down_mbs": _net_rate["rx_mbs"],
        "net_up_mbs": _net_rate["tx_mbs"],
    }
    data.update(powerkey_state())
    data.update(meminfo())
    data.update(containers() or {"running": None, "total": None, "stopped": None,
                                 "unhealthy": None, "restarting": None, "images": None})
    return data


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/pocketid":
            body = json.dumps(pocketid_counts()).encode()
        elif path in ("/stats", "/"):
            try:
                body = json.dumps(payload()).encode()
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
        else:
            self.send_error(404)
            return
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
    threading.Thread(target=_net_sampler, daemon=True).start()
    ThreadingHTTPServer(LISTEN, Handler).serve_forever()
