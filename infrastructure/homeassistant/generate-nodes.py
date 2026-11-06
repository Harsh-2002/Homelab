#!/usr/bin/env python3
"""Regenerate the Nodes view in a Home Assistant dashboard file.

Usage: generate-nodes.py DASHBOARD.yaml

Everything from the line `  - title: Nodes` to the end of the file is replaced;
the Cameras view above it is kept. Output is native Sections cards only.
Threshold colouring uses card `visibility` numeric_state conditions: one tile
variant per state, and Home Assistant shows exactly one of them.
"""
import sys
from pathlib import Path

import yaml

MARKER = "  - title: Nodes"


def tile(entity, name, icon, color, bar=None, visibility=None):
    card = {
        "type": "tile",
        "entity": entity,
        "name": name,
        "icon": icon,
        "color": color,
        "grid_options": {"columns": 6},
    }
    if bar:
        card["features"] = [{"type": "bar-gauge", "min": bar[0], "max": bar[1]}]
    if visibility:
        card["visibility"] = visibility
    return card


def numeric(entity, above=None, below=None):
    cond = {"condition": "numeric_state", "entity": entity}
    if above is not None:
        cond["above"] = above
    if below is not None:
        cond["below"] = below
    return cond


def unavailable(entity):
    return {"condition": "state", "entity": entity, "state": ["unavailable", "unknown"]}


def graded(entity, name, icon, bar, warn, crit):
    """Green / orange / red variants plus a grey one while the sensor is down."""
    eps = 0.0001
    return [
        tile(entity, name, icon, "green", bar, [numeric(entity, below=warn)]),
        tile(entity, name, icon, "orange", bar, [numeric(entity, above=warn - eps, below=crit)]),
        tile(entity, name, icon, "red", bar, [numeric(entity, above=crit - eps)]),
        tile(entity, name, icon, "grey", bar, [unavailable(entity)]),
    ]


def alert(entity, name, icon, bad_color):
    """Green at zero, bad_color above zero."""
    return [
        tile(entity, name, icon, "green", None, [numeric(entity, below=0.5)]),
        tile(entity, name, icon, bad_color, None, [numeric(entity, above=0.4999)]),
        tile(entity, name, icon, "grey", None, [unavailable(entity)]),
    ]


def history(entities):
    return {
        "type": "history-graph",
        "hours_to_show": 6,
        "show_names": True,
        "grid_options": {"columns": 12},
        "entities": [{"entity": e, "name": n} for e, n in entities],
    }


def heading(text, icon):
    return {"type": "heading", "heading": text, "icon": icon}


def build():
    host = [heading("l3b", "mdi:server")]
    host += graded("sensor.host_cpu", "CPU", "mdi:cpu-64-bit", (0, 100), 70, 90)
    host += graded("sensor.host_memory", "Memory", "mdi:memory", (0, 100), 80, 92)
    host += graded("sensor.host_swap", "Swap", "mdi:swap-horizontal", (0, 100), 60, 85)
    host += graded("sensor.host_temperature", "Temperature", "mdi:thermometer", (20, 100), 75, 90)
    host += graded("sensor.host_disk_root", "Root, NVMe", "mdi:harddisk", (0, 100), 75, 90)
    host += graded("sensor.host_disk_data", "Data, SATA", "mdi:database", (0, 100), 80, 92)
    host += graded("sensor.host_disk_backup", "Backup, USB", "mdi:backup-restore", (0, 100), 80, 92)
    host += graded("sensor.host_load", "Load, 1 min", "mdi:speedometer", (0, 9), 6, 9)

    docker = [heading("Docker and system", "mdi:docker")]
    docker += [
        tile("sensor.host_containers", "Running", "mdi:docker", "blue"),
        tile("sensor.host_containers_total", "Total containers", "mdi:view-list", "cyan"),
        tile("sensor.host_containers_stopped", "Stopped", "mdi:stop-circle-outline", "grey"),
    ]
    docker += alert("sensor.host_unhealthy", "Unhealthy", "mdi:alert-circle-outline", "red")
    docker += alert("sensor.host_failed_units", "Failed services", "mdi:alert-octagon-outline", "red")
    docker += [
        tile("sensor.host_net_down", "Network down", "mdi:download-network-outline", "green"),
        tile("sensor.host_net_up", "Network up", "mdi:upload-network-outline", "teal"),
        tile("sensor.host_uptime_hours", "Uptime", "mdi:clock-outline", "grey"),
    ]

    recent = [
        heading("Last 6 hours", "mdi:chart-line"),
        history([("sensor.host_cpu", "CPU"), ("sensor.host_memory", "Memory")]),
        history([("sensor.host_temperature", "Temperature")]),
        history([("sensor.host_load", "Load, 1 min")]),
        history([("sensor.host_net_down", "Down"), ("sensor.host_net_up", "Up")]),
    ]
    sections = [
        {"type": "grid", "column_span": 4, "cards": cards}
        for cards in (host, docker, recent)
    ]
    return {"title": "Nodes", "path": "nodes", "type": "sections", "max_columns": 4, "sections": sections}


def main(path):
    target = Path(path)
    text = target.read_text()
    head = text[: text.index(MARKER)]
    body = yaml.safe_dump([build()], sort_keys=False, width=200)
    indented = "\n".join("  " + line if line else line for line in body.splitlines())
    target.write_text(head + indented + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
