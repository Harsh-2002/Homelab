# px30 reboot evidence and fast capture

## Verified evidence, October 30, 2026

Live SSH and collected logs identify the replacement as **OptiPlex5060,
i5-9400T, six cores,32GiB RAM, BIOS1.32.0**. This supersedes the reported9500T
and the temporary7040 rollback inventory. Both ZFS pools remain healthy;
px30 stays in HA maintenance, VM203 stopped/onboot0 and services evacuated.
Do not return workloads while the power/reset issue is unresolved.

The first streamed capture received138,151,868 bytes before disconnection.
It was preserved as a partial file; a second complete text capture also arrived.
The input trace caught KEY_POWER(code116), press/release, at14:26:22 IST on
`/dev/input/event2`, named Power Button. Its sysfs path is
`/sys/devices/platform/LNXPWRBN:00/input/input2`, the ACPI fixed-feature power
button input. This is not the USB keyboard's Linux input endpoint. It does not
identify whether firmware, a physical switch or another hardware interaction
generated the underlying signal. The owner reports not pressing the button.
Do not call this a proven defective case button or exclude firmware-level USB
interaction based solely on the input endpoint.

The13:55 boot reached multi-user operation, three-node quorum and healthy
service startup, then logind received a power-key event at13:58:06 and completed
poweroff at13:58:23. Startup Corosync and shutdown teardown errors are not proof
of a quorum-triggered reset. Ordinary `PM: hibernation: Registered nosave memory`
messages are boot bookkeeping, not evidence that hibernation occurred.

A transient10-minute `systemd-inhibit --what=handle-power-key --mode=block`
service was started at14:29:52 to allow inspection, without disabling the HA
watchdog or editing persistent configuration. Its presence was verified.
Boot927ced87 ended after14:31:19 without a clean shutdown sequence; the next
boot021c1363 began at14:33:16. The inhibitor therefore did not survive that reset
and was absent in the next boot. The owner explicitly confirms not touching the
power button or manually restarting during14:31–14:33 IST, so this is an
uncommanded reset in addition to the captured clean power-key shutdown.
No kernel panic or pstore dump was captured; missing persisted output cannot
rule out a crash or hardware/firmware reset.
Do not claim every reset shares the confirmed power-key shutdown trigger, or
claim the temporary inhibitor is still active after a reboot.

## Fast snapshot, measured on the actual replacement

The original diagnostic implementation formatted roughly1.28million historical
journal lines and waited55seconds for live input tracing. That was unsuitable
for a sub-minute availability window. The replacement separates snapshots from
live tracing and copies native journal files instead of formatting all history.

The gzip prototype took14seconds. The deployed Zstandard version took **2seconds
for collection plus upload**, with198,202,576 transfer bytes in1.750426seconds.
The received archive was verified and contains28native journal files with
1,023,410,176uncompressed bytes, plus an independent readable snapshot of current
kernel output and four recent boots. This is an actual measurement, not a
guarantee under disk/network degradation. Live journal files can change while
being copied; the recent text export provides separate evidence.

### Start the temporary receiver on dev

```bash
python3 infrastructure/proxmox/receive-reboot-logs.py \
  --bind 10.1.1.5 --port 18831 \
  --allow-ip 10.1.1.30 --allow-ip 10.1.1.5 \
  --output-dir /home/dev/.local/state/px30-diagnostics \
  --collector infrastructure/proxmox/collect-reboot-logs.sh
```

Keep it running in a terminal/session. Default lifetime is30minutes. Bind only
the LAN interface, not a public listener. The source allowlist is for this
controlled LAN transfer; it is not internet authentication. No Caddy/DNS/public
route, service installation or permanent firewall change is needed.

The incident's active receiver initially used a private copy under the same
state directory; the tracked implementation accepts paths/addresses as arguments
instead of embedding them. Its upload/streaming behavior is the same.

### One command on px30 as root

```bash
curl -fsS http://10.1.1.5:18831/collect.sh | bash
```

This runs the owner's read-only collector served by dev. It exports recent text
logs and fast hardware/network/storage state, then streams a tar archive of all
retained native journals, available traditional system logs and pstore files
using two-thread Zstandard compression. It does not wait for a live trace.
Zstandard and Python/systemd tooling were verified on this Proxmox installation.
Snapshot scratch data is under `/run/px30-snapshot.*` and removed on normal exit.

The receiver writes mode0600 captures in a mode0700directory. Complete uploads
are `.tar.zst`; interrupted transfers remain `.partial.tar.zst`, preserving bytes
already received. A partial compressed archive may have recoverable earlier
members but is not promised to be fully extractable. Earlier plain-text captures
remain `.log`/`.partial.log`. A2GiBupload cap prevents unbounded single requests.
Chunked transfer, interrupted-upload preservation and actual curl streaming were
tested; temporary test captures were removed.

Logs can contain private addresses, identifiers and authentication material.
Keep every capture/extraction outside Git, Notion, public Quick Share and memory.
Publish only a reviewed diagnostic summary. The helper never prints expanded
credential-bearing agent or service configurations.

### Inspect the received archive

```bash
zstd -t /path/to/px30-capture.tar.zst
mkdir -m 700 /path/to/private-extraction
tar --zstd -xf /path/to/px30-capture.tar.zst -C /path/to/private-extraction
journalctl --directory /path/to/private-extraction/var/log/journal --list-boots
```

Select a boot ID from that list for detailed journal inspection. Preserve raw
evidence until the incident is resolved. Stop the temporary receiver after use;
it also expires automatically. No live power-event trace or diagnostic inhibitor
is installed permanently by this snapshot tool.
