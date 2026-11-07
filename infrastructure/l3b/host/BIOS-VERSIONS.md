# OptiPlex 5060 BIOS versions and downgrade options

Host: `l3b`, Dell OptiPlex 5060 (i5-9400T). Current BIOS **1.31.0**, build date
2024-07-31. Latest Dell release is **1.32.0**; the June 2026 Dell catalog still
lists 1.32.0 as current, so **no 1.33.x exists**.

Dates are Dell's published release dates (driver IDs in brackets), not the BIOS
build date stamped in SMBIOS.

| Version | Released | Notes |
| --- | --- | --- |
| 1.19.0 | 2022-05-10 | first version in fwupd tracking |
| 1.22.1 | 2022-10-11 | `vyyhm` |
| 1.24.0 | 2023-01-12 | `vjmnh` |
| 1.25.0 | 2023-05-16 | `frnkc` |
| 1.26.0 | 2023-09-12 | `ddwjw` |
| 1.27.0 | 2023-11-09 | `ytphh` |
| 1.28.0 | 2024-02-02 | `mttnc`; minimum version for DSA-2024-036 |
| 1.29.0 | 2024-04-12 | `npvjf`; last version Dell published to LVFS |
| 1.30.0 | 2024-06-11 | `dtckr`; **first downgrade candidate** |
| 1.31.0 | 2024-09-10 | `ygwmg`; **installed now** |
| 1.32.0 | 2024-11-11 | `npkrw`; **excluded**: repeated power on/off cycles |

Versions 1.20.0, 1.21.0 and 1.23.0 were not surfaced by Dell's index during this
check; earlier releases exist back to 1.0 (2018) and 1.7.1 (2020-07-17).

## Field notes

- **1.32.0 is unusable here.** The owner reports the machine repeatedly powered
  itself on and off, so the server could not stay running; rolling back to 1.31.0
  restored stability. That is the reason 1.32.0 must not be recommended.
- **1.31.0** has been the working version since the rollback. On 2026-11-07 it
  logged ACPI power-key events that shut it down twice (see
  [INCIDENT-2026-11-07-power.md](INCIDENT-2026-11-07-power.md)). Those were short
  presses, now ignored by logind, so they no longer power the host off. Whether
  they are a firmware regression or a failing chassis switch is still open.

## If a downgrade is attempted

Order of preference, keeping the biggest security fix that still predates the
observed problems:

1. **1.30.0** (2024-06-11) — immediate predecessor of the current version.
2. **1.29.0** (2024-04-12) — last version published to LVFS, widely deployed.
3. **1.28.0** (2024-02-02) — floor: the oldest version that includes
   DSA-2024-036. Do not go below it unless the security trade-off is accepted.

Security mapping: 1.28.0 or later carries DSA-2024-036. DSA-2024-243 is fixed
only in 1.32.0, so every usable version lacks it.

### Procedure

1. Schedule downtime; the host is production. Stop services cleanly and confirm
   `/data` and `/BACKUP` are unmounted or synced.
2. Download both files for the target version from Dell: `OptiPlex_5060_<ver>.exe`
   and `BIOS_IMG.rcv` (the recovery image).
3. Copy them to a FAT32 USB stick. Verify Dell's SHA-256 for the EXE.
4. In BIOS setup (F2), ensure **Allow BIOS Downgrade** is enabled under
   Security → UEFI Capsule Firmware Updates.
5. F12 → **BIOS Flash Update** → select the EXE → flash. Keep power connected
   throughout; the host reboots several times.
6. After boot, confirm `sudo dmidecode -s bios-version` matches the target, then
   check storage, NIC, containers and the power-button behaviour for at least
   24 hours.
7. Keep 1.31.0 available on the same USB stick to roll forward again.

Because `HandlePowerKey=ignore` already prevents short presses from shutting the
host down, a downgrade is a hypothesis test: if power events continue at the same
rate on 1.30.0, the switch is the likelier cause; if they stop, firmware is.

## Observation window, 7–14 November 2026

Decision: **stay on 1.31.0 and watch for one week.** The host had been running
continuously for more than five days before the 7 November power-key events, so
one occurrence is not enough evidence to blame firmware. If a power-key event or
an unexpected power-off recurs during the window, downgrade to **1.30.0** (then
1.29.0; floor 1.28.0), following the procedure above.

Monitoring in place:

- `powerkey-watch.service` follows the journal and records every
  `Power key pressed` line with a timestamp in `/var/log/powerkey-events.log`,
  plus a persistent count in `/var/lib/powerkey-watch/state.json` (survives
  reboot).
- `homelab-stats` exposes `powerkey_events` and `powerkey_last`;
  Home Assistant has `sensor.host_powerkey_events` and
  `sensor.host_powerkey_last`.
- Automation `l3b power-button event` sends an iPhone notification and a
  persistent notification whenever the count rises, so a press that the logind
  guard absorbs is still visible.
- The path was tested on 7 November with one synthetic event (count reached 1,
  iPhone notification fired); the counter and log were then reset to zero.

Review date: **14 November 2026**. A clean week means keep 1.31.0; any recurrence
means flash 1.30.0.

## Security note

The usable versions (1.28.0–1.31.0) carry DSA-2024-036. DSA-2024-243 is fixed
only in 1.32.0, which is excluded for the power-cycling defect, so that advisory
stays unfixed on this host for now.
