#!/usr/bin/env python3
"""Write the Quick dashboard (storage dashboard `quick-actions`) config as JSON.

Usage: generate-overview.py OUTPUT.json

The JSON is sent with the `lovelace/config/save` WebSocket call. Native Sections
cards only. The status strip reuses the threshold-coloured tiles from
generate-nodes.py.
"""
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("nodes", Path(__file__).with_name("generate-nodes.py"))
nodes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nodes)

NODES = {"action": "navigate", "navigation_path": "/homelab-status/nodes"}


def tile(entity, name=None, icon=None, columns=6, **extra):
    card = {"type": "tile", "entity": entity, "grid_options": {"columns": columns}}
    if name:
        card["name"] = name
    if icon:
        card["icon"] = icon
    card.update(extra)
    return card


def linked(cards, columns=6):
    for card in cards:
        card["grid_options"] = {"columns": columns}
        card["tap_action"] = NODES
    return cards


def build():
    room = [
        nodes.heading("Room", "mdi:sofa"),
        tile("light.behind_monitor_bulb", "Bulb", columns=12, features=[{"type": "light-brightness"}]),
        tile(
            "climate.samsung_room_ac",
            "Room AC",
            columns=12,
            features=[
                {"type": "climate-hvac-modes", "hvac_modes": ["off", "auto", "cool", "dry", "fan_only"]},
                {"type": "target-temperature"},
            ],
        ),
    ]
    outdoor = [
        nodes.heading("Outdoor", "mdi:cctv"),
        {
            "type": "picture-entity",
            "entity": "camera.outdoor",
            "name": "Outdoor",
            "camera_view": "auto",
            "show_state": False,
            "grid_options": {"columns": 12},
        },
    ]
    switches = [
        nodes.heading("Switches", "mdi:toggle-switch-outline"),
        tile("switch.outdoor_detect", "Detection"),
        tile("switch.outdoor_recordings", "Recording"),
        tile("switch.outdoor_snapshots", "Snapshots"),
        tile("switch.outdoor_review_alerts", "Camera alerts"),
        tile("input_boolean.samsung_ac_daily_schedule", "AC schedule", "mdi:calendar-clock"),
        tile("input_boolean.samsung_ac_local_alerts", "AC alerts", "mdi:bell-outline"),
    ]

    status = [nodes.heading("Homelab", "mdi:server")]
    for cards in (
        nodes.graded("sensor.host_cpu", "CPU", "mdi:cpu-64-bit", (0, 100), 70, 90),
        nodes.graded("sensor.host_memory", "Memory", "mdi:memory", (0, 100), 80, 92),
        nodes.graded("sensor.host_temperature", "Temperature", "mdi:thermometer", (20, 100), 75, 90),
        nodes.graded("sensor.host_disk_root", "Root, NVMe", "mdi:harddisk", (0, 100), 75, 90),
        nodes.graded("sensor.host_disk_data", "Data, SATA", "mdi:database", (0, 100), 80, 92),
        nodes.graded("sensor.host_disk_backup", "Backup, USB", "mdi:backup-restore", (0, 100), 80, 92),
    ):
        status += linked(cards)
    status += linked([nodes.tile("sensor.host_containers", "Containers running", "mdi:docker", "blue")], 18)
    status += linked(nodes.alert("sensor.host_unhealthy", "Unhealthy containers", "mdi:alert-circle-outline", "red"), 18)

    sections = [{"type": "grid", "cards": cards} for cards in (room, outdoor, switches)]
    sections.append({"type": "grid", "column_span": 3, "cards": status})
    return {
        "title": "Quick",
        "views": [
            {"title": "Quick", "path": "quick", "type": "sections", "max_columns": 3, "sections": sections}
        ],
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    Path(sys.argv[1]).write_text(json.dumps(build()))
