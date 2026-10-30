#!/usr/bin/env python3
"""Make cluster peer resolution independent of guest DNS; dry-run by default."""
import argparse
import ipaddress
import os
from pathlib import Path
import re
import tempfile


def build_hosts(text, config):
    peers = {}
    for block in re.findall(r"\bnode\s*\{([^{}]*)\}", config):
        fields = dict(re.findall(r"^\s*(name|ring0_addr):\s*(\S+)", block, re.MULTILINE))
        name = fields.get("name", "")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9-]*", name):
            raise ValueError("Missing or invalid Corosync node name")
        address = str(ipaddress.ip_address(fields["ring0_addr"]))
        if name in peers or address in peers.values():
            raise ValueError("Duplicate cluster identity")
        peers[name] = address
    if len(peers) < 2:
        raise ValueError("Expected a multi-node Corosync configuration")
    result = text.rstrip("\n") + "\n"
    for name, address in sorted(peers.items()):
        matches = [line.split("#", 1)[0].split() for line in text.splitlines()
                   if name in line.split("#", 1)[0].split()[1:]]
        if len(matches) > 1 or any(fields[0] != address for fields in matches):
            raise ValueError(f"Review conflicting existing mapping for {name}")
        if not matches:
            result += f"{address} {name}.local {name}\n"
    return result, sorted(peers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    target = Path("/etc/hosts")
    original = target.read_text()
    updated, peers = build_hosts(original, Path("/etc/pve/corosync.conf").read_text())
    print("Validated peers:", ", ".join(peers))
    if updated == original:
        print("No changes required")
    elif args.apply:
        if os.geteuid() != 0:
            raise PermissionError("Apply requires root")
        stat = target.stat()
        filename = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, delete=False) as handle:
                filename = handle.name
                handle.write(updated)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(filename, stat.st_mode & 0o777)
            os.chown(filename, stat.st_uid, stat.st_gid)
            os.replace(filename, target)
        finally:
            if filename and Path(filename).exists():
                Path(filename).unlink()
        print("Peer mappings applied")
    else:
        print("Missing peer mappings; rerun with --apply")


if __name__ == "__main__":
    main()
