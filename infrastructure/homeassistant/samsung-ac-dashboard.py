#!/usr/bin/env python3
"""Verify the native AC dashboard; optionally normalize its new selector IDs.

Requires websockets. Reads the existing protected Hermes HASS environment;
never prints credentials or a complete configuration entry.
"""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from websockets.sync.client import connect

ENTRY_ID = "01M5HQ6SAA45N3EFXRNMQBS25B"
SELECTORS = {
    "homelab_vertical_swing": "vertical_swing",
    "homelab_horizontal_swing": "horizontal_swing",
    "homelab_vertical_position": "vertical_position",
    "homelab_horizontal_position": "horizontal_position",
    "homelab_horizontal_sweep": "horizontal_sweep",
    "homelab_cooling_capacity": "cooling_capacity",
    "homelab_comfort_mode": "comfort_mode",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-names", action="store_true")
    parser.add_argument("--entry-id", default=ENTRY_ID)
    parser.add_argument("--env", type=Path, default=Path.home() / ".hermes/.env")
    args = parser.parse_args()
    values = {}
    for line in args.env.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key in ("HASS_URL", "HASS_TOKEN"):
            values[key] = value.strip().strip("\"'")
    if not values.get("HASS_URL") or not values.get("HASS_TOKEN"):
        raise SystemExit("Existing protected HASS_URL/HASS_TOKEN are required")
    url = urlsplit(values["HASS_URL"])
    endpoint = urlunsplit(("wss" if url.scheme == "https" else "ws", url.netloc, "/api/websocket", "", ""))
    with connect(endpoint, proxy=None, open_timeout=15, close_timeout=3) as ws:
        if json.loads(ws.recv())["type"] != "auth_required":
            raise SystemExit("Unexpected authentication handshake")
        ws.send(json.dumps({"type": "auth", "access_token": values["HASS_TOKEN"]}))
        if json.loads(ws.recv())["type"] != "auth_ok":
            raise SystemExit("Home Assistant rejected the existing credential")
        msgid = 0

        def command(type_, **fields):
            nonlocal msgid
            msgid += 1
            ws.send(json.dumps({"id": msgid, "type": type_, **fields}))
            response = json.loads(ws.recv())
            if not response.get("success"):
                raise SystemExit(f"HA command failed: {type_}; {response.get('error', {}).get('code')}")
            return response.get("result")

        entries = command("config/entity_registry/list")
        by_id = {entry["entity_id"]: entry for entry in entries}
        matching = {entry.get("translation_key"): entry for entry in entries if entry.get("config_entry_id") == args.entry_id}
        for key, suffix in SELECTORS.items():
            entity = matching.get(key)
            if not entity:
                raise SystemExit(f"Expected model-specific selector absent: {key}")
            target = "select.samsung_ac_" + suffix
            if entity["entity_id"] != target:
                if target in by_id:
                    raise SystemExit(f"Refusing entity-ID collision: {target}")
                if args.apply_names:
                    command("config/entity_registry/update", entity_id=entity["entity_id"], new_entity_id=target)
                else:
                    raise SystemExit(f"Selector needs normalization: {target}; use --apply-names")
            print("Selector ready:", target)
        dashboard = command("lovelace/config", url_path="samsung-ac", force=True)
        titles = [view.get("title") for view in dashboard.get("views", [])]
        if titles != ["Control", "Care"]:
            raise SystemExit("Unexpected AC dashboard views")
        print("Native dashboard ready: /samsung-ac/control; views Control/Care")
        print("No appliance control commands sent.")


if __name__ == "__main__":
    main()
