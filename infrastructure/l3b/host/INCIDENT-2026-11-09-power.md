# Unclean power-offs, 9 November 2026

## What happened

The host rebooted uncleanly at least eight times between 08:30 and 09:43 IST.
`last -x` marks every boot as `crash`; there is no shutdown record:

```
09:43, 09:30, 09:28, 09:24, 09:21, 09:18, 08:34, 08:30
```

Thirteen boots are recorded for the day. The current boot started 09:43.

## Evidence gathered

- No kernel panic, no thermal trip, no MCE, no OOM in the journal; logs end
  mid-startup, which is a hard power loss rather than an OS shutdown.
- Package temperature at the time of checking: 63 C (high 94 C, crit 100 C), so
  not thermal.
- `HandlePowerKey=ignore` is present in
  `/etc/systemd/logind.conf.d/10-powerkey-ignore.conf` and active
  (`busctl get-property ... HandlePowerKey` returns `ignore`), so the power
  button is not shutting the host down.
- The powerkey watcher recorded one press at 09:28:35, matching the 09:28 boot.
- Journald is persistent, but each crash leaves the current journal corrupted,
  so per-boot evidence is lost.

## Working hypotheses

1. **BIOS power bug recurrence on 1.31.0.** The same host was power-cycling on
   BIOS 1.32.0 and was downgraded to 1.31.0 with a watch until 14 November.
   Today's cluster is the first recurrence.
2. **Power delivery under load.** The crashes line up with heavy work on the
   host (image builds, container deploys, Chrome with VA-API encoding). A
   failing or marginal PSU would explain hard cuts under load with no logs.

## Immediate actions taken

- Confirmed the power-key ignore drop-in is active.
- Stopped doing concurrent heavy image builds while the host is unstable.
- Recorded this incident; BIOS watch review moved forward from 14 November.

## Next steps

1. Avoid concurrent heavy builds/encodes until stable; watch uptime.
2. Downgrade BIOS 1.31.0 -> 1.30.0 (documented first candidate), by Dell EXE on
   a FAT USB through F12 -> BIOS Flash Update. This needs physical presence.
3. If power-offs continue on 1.30.0, test/replace the PSU before further
   software work. Next BIOS candidates: 1.29.0, floor 1.28.0.

## Diagnostics added 9 November

- `journald`: `Storage=persistent`, `SyncIntervalSec=1s`, `SystemMaxUse=2G`,
  `SystemMaxFileSize=200M` in `/etc/systemd/journald.conf` (the drop-in was not
  picked up by this systemd). Logs survive a power cut to within about a second.
- `/usr/local/sbin/crash-record.sh` + `crash-record.service` run at every boot
  and write the previous boot's last 200 journal lines, reboot history and
  temperatures to `/var/log/crash-history/<timestamp>.txt`, mirrored to
  `/data/apps/diagnostics/crash-history/` (persistent SATA data).
- Verified: first run captured 33 KB including the 09:37 boot tail.

Still missing (hardware):
- No UPS is visible on USB (`lsusb` finds none), so NUT cannot read input power
  or battery state. Connect the UPS data cable to enable it.
- No remote syslog host yet; shipping logs off-box would survive a dead host.
- Dell BIOS event log (F2 -> Maintenance) is the firmware-side record of a
  power loss and should be checked after the next event.

## RAPL power logging

The UPS is a basic model with no data port, so NUT cannot read it. Added
`/usr/local/sbin/power-log.py` + `power-log.service`, which reads Intel RAPL
package energy, package temperature and load every second, fsyncs each line and
writes to `/data/apps/diagnostics/power/power-YYYYMMDD.csv` (SATA data disk).

Reading the last rows after a cut:
- watts peak then silence -> load-triggered power delivery fault (PSU suspect);
- steady low watts then cut -> BIOS/power-state fault, not load.

Verified: idle package draw 7-9 W at 63 C, lines arriving every second.

Still needed for real mains evidence: a metering smart plug (Shelly/Tasmota) on
the UPS output, logged through Home Assistant, and the Dell BIOS event log
(F2 -> Maintenance) after the next event.

## RAPL evidence, 10:04 and 10:07 cuts

| Boot | Started | Package power at cut | Load at cut | Temp |
|---|---|---|---|---|
| 142ccf99 | 10:03 | 16-20 W | 0.72 | 63-66 C |
| ac7bd081 | 10:07 | 29-31 W | 15.1 | 69-71 C |

One cut happened **near idle** (20 W, load 0.7), the other during the startup
storm (31 W, load 15). Package power never approached what a 200 W PSU would
strain at, and there was no thermal event. That weakens the "PSU overloaded by
load" theory and strengthens an intermittent power-rail or firmware fault.

## BIOS stick prepared

USB `sdb1`, FAT32 label `DELLBIOS`, contents verified by SHA-256:

- `OptiPlex_5060_1.30.0.exe` — 3ee54ced...b1251 (Dell)
- `BIOS_IMG.rcv` (1.30.0) — 7c7aa3af...0cc6 (Dell)
- `OptiPlex_5060_1.31.0.exe` — 2efbb193...c9c31 (roll-forward)
- `BIOS_IMG_1.31.0.rcv` — 2fc3b295...f51c01
- `OptiPlex_5060_1.32.0.exe` removed (excluded version).

Procedure: F2 -> Security -> UEFI Capsule Firmware Updates -> allow downgrade;
F12 -> BIOS Flash Update -> select `OptiPlex_5060_1.30.0.exe`; keep UPS power;
host reboots several times; then `sudo dmidecode -s bios-version` must read 1.30.0.

## Exact model and power envelope

- Chassis: **OptiPlex 5060 Micro (MFF)**, SMBIOS SKU `085B`, chassis "Desktop".
- **No internal PSU.** SMBIOS type 39 is absent and `/sys/class/power_supply`
  is empty, so the whole machine runs from the external brick.
- Dell spec for this model: **65 W or 90 W AC adapter**, 19.5 V DC
  (65 W = 3.34 A, 90 W = 4.62 A), 4.5 x 2.9 mm barrel, input 100-240 V AC
  50/60 Hz. Micro configs with a 35 W CPU are specified with the 90 W brick.
- Installed brick: genuine Dell, **DP/N 0KX650**, green LED lit. The LED is on
  the AC side only; it says nothing about DC output health.

Measured envelope on this unit (RAPL):

| Limit | Value |
|---|---|
| PL1 long term | 35 W |
| PL2 short term | 60 W |
| Package peak observed | 58 W |
| Package average (this boot) | 9.3 W |

Rest of the box adds roughly 12-18 W at peak: NVMe + SATA SSD + USB 1.7 TB HDD
(spin-up 5-7 W) + fan + NIC + board. So **peak DC draw is ~70-78 W**, which a
65 W brick cannot cover and a 90 W brick covers with little headroom. If the
installed brick turns out to be 65 W, that alone explains hard cuts during boot
storms and turbo bursts.

## PL2 cap experiment (10:28 onwards)

To separate "load-driven power delivery fault" from "firmware/idle fault", the
CPU burst limit was capped at the sustained limit:

- `/sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw` = 35000000
  (PL2 = PL1 = 35 W; previously PL2 60 W). Applied at 10:28.
- Persisted by `cpu-power-cap.service` (enabled, oneshot before
  multi-user.target), which reapplies the cap at every boot and logs the result
  to `/data/apps/diagnostics/power/cap.log`.
- Revert: `sudo systemctl disable --now cpu-power-cap.service` then
  `echo 60000000 | sudo tee /sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw`.

30-minute stability run started 10:28 (`pl2-test.service`, transient unit):

- heartbeat every 10 s to `/data/apps/diagnostics/pl2-test/run-*.log`, each line
  fsynced (`sync -f`), so a cut leaves the tail on disk;
- 45 s four-worker load pulse at ~10 min and ~20 min, logged as LOAD-START /
  LOAD-END, to prove the rail holds under sustained PL1 load;
- a clean run ends with a `SUMMARY` line; a cut simply stops the heartbeat.

An ADAPTER of 65 W would be stressed by the 70-78 W peak; if the 30-minute run
survives both load pulses at 35 W but cut before at 60 W bursts, power delivery
is confirmed as the fault domain and the brick must be checked or replaced.

## Log durability verification

- `/var/log/journal` is persistent on the XFS root (`Storage=persistent`) with
  `SyncIntervalSec=1s`.
- Verified without manual sync: a `logger` marker at 10:28:24 was on disk by
  10:28:26 (journal file mtime advanced), so the journal tail survives a cut
  with at most ~1-2 s of loss.
- `/data/apps/diagnostics/power/power-YYYYMMDD.csv` fsyncs every line (1 s).
- `pl2-test` log fsyncs every heartbeat (10 s).
- `crash-record.service` is enabled and mirrors the previous boot tail to
  `/data/apps/diagnostics/crash-history/` on every start.
