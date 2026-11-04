# Retirement backup record (31 October 2026)

Compact copy of the verification record from the 4 TB Crucial `HOMELAB_BACKUP`
disk, taken before that disk was formatted on 4 November 2026 for reuse.

The disk itself is gone; this directory keeps the evidence that the restore was
verified: restore instructions, per-phase SHA-256 manifests, progress markers and
the small helper scripts. The multi-hundred-megabyte `*.jsonl` file inventories
were intentionally **not** copied — they listed every backed-up path and had no
value once the media comparison passed.

Verification before formatting:

- Media on the backup matched `/data/apps/smb` exactly (72 files, only an empty
  `.store-volume` marker differed).
- All services had already been restored and were running from live data.
- SMART for the drive: PASSED, 9104 power-on hours, 0 reallocated, 0 pending,
  0 uncorrectable, 0 CRC errors, 50 °C.

The replacement backup target is a separate USB 3.0 SSD; see
[../../smb/README.md](../../smb/README.md) for the share layout.
