#!/usr/bin/env python3
"""One-time guarded kernel cleanup; dry-run unless --apply is supplied."""
import argparse
import fcntl
import os
import re
import shutil
import subprocess
from pathlib import Path


def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def older(left, right):
    return subprocess.run(["dpkg", "--compare-versions", left, "lt", right]).returncode == 0


def candidates(packages, current):
    pattern = re.compile(r"proxmox-(?:kernel|headers)-(\d[\d.]*-\d+)-pve(?:-signed)?$")
    return sorted(name for name in packages
                  if (match := pattern.fullmatch(name)) and older(match[1], current))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError("Run as root")
    with open("/run/homelab-kernel-cleanup.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        current = os.uname().release
        if not re.fullmatch(r"\d[\d.]*-\d+-pve", current):
            raise RuntimeError("Unrecognized running kernel")
        version = current.removesuffix("-pve")
        if older(version, "7.0.14-26"):
            raise RuntimeError("Wait for successful boot into the updated kernel")
        if float(Path("/proc/uptime").read_text().split()[0]) < 180:
            raise RuntimeError("Wait for three minutes of uptime")
        for unit in ("pve-cluster", "pveproxy", "pvedaemon", "pve-ha-lrm"):
            run("systemctl", "is-active", "--quiet", unit)
        if not re.search(r"Quorate:\s+Yes", run("pvecm", "status")):
            raise RuntimeError("Cluster must have quorum")
        health = run("zpool", "list", "-H", "-o", "health").split()
        if not health or any(value != "ONLINE" for value in health):
            raise RuntimeError("All local pools must be ONLINE")
        if run("dpkg", "--audit").strip():
            raise RuntimeError("Resolve dpkg audit before cleanup")
        rows = run("dpkg-query", "-W", "-f=${binary:Package}\t${db:Status-Abbrev}\n")
        packages = [line.split("\t")[0] for line in rows.splitlines()
                    if "\t" in line and line.split("\t")[1].startswith("ii")]
        if not any(name in packages for name in
                   (f"proxmox-kernel-{current}", f"proxmox-kernel-{current}-signed")):
            raise RuntimeError("Running kernel package is not installed")
        if not Path(f"/boot/vmlinuz-{current}").is_file() or not Path(f"/boot/initrd.img-{current}").is_file():
            raise RuntimeError("Running kernel boot artifacts missing")
        old = candidates(packages, version)
        print(f"Preserve running kernel {current}; older packages: {old}", flush=True)
        if old:
            plan = run("apt-get", "-s", "purge", *old)
            removals = set(re.findall(r"^(?:Remv|Purg) (\S+)", plan, re.MULTILINE))
            if not removals or not removals.issubset(set(old)) or re.search(r"^(?:Inst|Conf) ", plan, re.MULTILINE):
                raise RuntimeError("Refuse unexpected package removal plan")
            print(plan, flush=True)
            if args.apply:
                subprocess.run(["apt-get", "-y", "-o", "DPkg::Lock::Timeout=30", "purge", *old],
                               check=True, env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
        if args.apply:
            run("apt-get", "clean")
            for base in (Path("/var/lib/apt/lists"), Path("/var/cache/apt")):
                for path in base.iterdir():
                    if path.name in ("lock", "archives", "partial"):
                        continue
                    if path.is_dir() and not path.is_symlink():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            run("proxmox-boot-tool", "status")
            Path("/var/lib/homelab-kernel-cleanup").mkdir(mode=0o700, exist_ok=True)
            Path("/var/lib/homelab-kernel-cleanup/completed").write_text(current + "\n")
            run("systemctl", "disable", "--now", "homelab-kernel-cleanup.timer")
            print("Cleanup completed; timer disabled", flush=True)


if __name__ == "__main__":
    main()
