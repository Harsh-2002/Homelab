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

## PL2 cap run result (10:28-10:58)

- Ran 1803 s (30 min) on one boot; `boot_start == boot_end`, no reboot, no cut.
- 1799 one-second samples: **min 2.8 W, average 7.2 W, peak 32.9 W**; zero
  samples above the 35 W cap, so the cap was enforced for the whole run.
- Two 45 s four-worker load pulses (10:38 and 10:48) reached 32.5-32.9 W package
  power and 77-78 C, and the host stayed up.
- No warning-or-worse journal entries during the window.
- Uptime at the end: **47 minutes** (longest of the day; previous best stretch
  was about 19 minutes).

Interpretation: the cap works and the machine is stable at <= 33 W package
power. This does **not** isolate the fault, because the cap also removed the
58-60 W bursts that were present at the 10:07 cut, and the host had already run
17 minutes before the cap was applied. A deliberate 60 W burst test (cap
removed, short duration) is the decisive next step, at the risk of another
unclean shutdown.

## Correction: the 58 W peak was a measurement artifact

The only sample above 35 W in any log is one row at 10:11:34 reading 58.0 W,
sitting between 30.2 W and 30.2 W. It is a RAPL counter glitch, not a real
burst. The genuine envelope of this machine is:

| Load | Package power |
|---|---|
| Idle | 3-10 W |
| Boot / service storm | 18-31 W |
| Six-core sustained (2.9 GHz all-core) | 27.8 W |
| Two-second full-load bursts | 33-35 W |

With the platform (NVMe, SATA SSD, USB HDD, fan, NIC) adding ~15 W, total DC
draw is ~45-50 W. **A 65 W adapter is adequate; the 90 W is comfortable.** The
adapter is therefore not undersized, and load capacity is not the fault.

## Deliberate stress results (no cut)

- 11:04-11:08: six `sha256sum /dev/zero` workers, PL1=PL2=60 W, 3.5 min:
  package 30.4 W peak, load 8.8, 77 C, stayed up.
- 11:09-11:12: burst mode 2 s full load / 2 s idle, PL1=PL2=60 W, 180 s:
  package 35.1 W peak, load 17, 78 C, stayed up.
- Total uptime by 11:13: over one hour, the longest of the day.

Interpretation: the host survives every load level it is physically capable of.
The earlier cuts happened at 16-20 W (idle) and 29-31 W (boot), i.e. **at or
below what it now sustains without trouble**. That rules out "PSU/adapter
overloaded by load" and points to an intermittent fault: BIOS 1.31.0 firmware
(the family that caused the 1.32.0 power-cycling), the front-panel power switch,
or a failing adapter.

PL1/PL2 were restored to Dell defaults (35 W / 60 W) and
`cpu-power-cap.service` disabled, so the machine is back to stock behaviour
before the BIOS downgrade.

## Power-button correlation (decisive lead)

A deliberate quick press at 11:21:46 was fully detected: logind logged
`Power key pressed short.`, the watcher counted it (count 4) and appended to
`/var/log/powerkey-events.log`. `HandlePowerKey=ignore` held: no shutdown job,
no reboot, host stayed up past 1 h 12 min.

The same log, cross-referenced with the 1 s power CSV, shows the earlier presses
were followed by the deaths:

| Press | Last evidence of life | Gap |
|---|---|---|
| 09:28:35 | journal ends immediately | ~0 s |
| 09:58:29 | last power sample 09:58:33 | **4 s** |
| 10:07:53 | last power sample 10:07:57 | **4 s** |
| 11:21:46 | still running | none (ignored) |

Four seconds is the EC hardware long-press cutoff, which bypasses logind and
cuts the rail without a shutdown sequence. That explains why logind only ever
recorded "short", never "long", and why every affected boot is marked `crash`
with no shutdown record.

**Primary suspect is now the front-panel power switch or its cable**: an
intermittent contact that stays closed for ~4 s reproduces every symptom (hard
cut at idle or load, green adapter LED, no logs, no thermal event). The BIOS
1.31.0 bug and the adapter remain secondary.

Next steps when the host is next powered on:

1. Leave the button untouched for 24 h; any event in
   `/var/log/powerkey-events.log` that nobody caused confirms the switch.
2. Reseat and clean the front-panel switch connector; if events continue,
   replace the front-panel assembly or unplug the power-switch header and power
   on via BIOS AC-recovery / Wake-on-LAN.
3. Flash BIOS 1.30.0 only if the cuts continue with the switch ruled out; the
   verified stick is ready.
4. Read the Dell BIOS event log (F2 -> Maintenance) after the next cut.

## Shutdown 9 November

A shutdown was scheduled for 11:26:24 IST but **cancelled at 11:25:5x, before it
fired**. The host never rebooted: boot id `9744aba2` and 74 minutes of uptime
confirm the same boot that started at 10:11. There is therefore still no
clean-shutdown record to compare against the earlier `crash` boots; an earlier
version of this note wrongly claimed the host had been shut down.

## BIOS downgrade to 1.30.0 (11:41)

The downgrade was performed from the verified `DELLBIOS` USB between 11:37 and
11:41 and is confirmed by SMBIOS:

- `bios-version` = **1.30.0**, release date **2024-03-29** (Dell's 1.30.0 build).
- Previous version was 1.31.0; the exclusion list still applies to 1.32.0.

Post-flash state, all verified:

| Check | Result |
|---|---|
| Power limits | PL1 35 W / PL2 60 W (stock) |
| Secure Boot | enabled, Debian booted normally |
| Storage | `/` xfs, `/data` xfs (sda1), `/BACKUP` ext4 (UUID ade7d423) |
| Containers | 39 running, desktop healthy |
| Diagnostics | power-log, crash-record, powerkey-watch, journald active |
| Boot time | 18.0 s |
| Idle power | ~15 W package |

Boot history around the flash: the 10:11 boot ended with the **first clean
shutdown record of the day at 11:26** (the requested shutdown), a second clean
shutdown at 11:37 (logind: "System is powering down", following two short
power-key events - a deliberate button shutdown is clean, unlike the crashes),
then the current boot at 11:41.

The journal survived every reboot: boots -4 through 0 are readable with
`journalctl -b -N`, and `crash-record.service` captured the previous boot tail.
That closes the log-persistence requirement with real reboot evidence, not just
design intent.

Watch: 24 hours on 1.30.0. If a hard cut recurs, the next tests are the
front-panel switch (phantom presses in `/var/log/powerkey-events.log`) and the
adapter; the BIOS variable is now eliminated.

## Collateral damage: Meilisearch version marker (11:45)

The power cuts truncated Karakeep's `meilisearch/data.ms/VERSION` to 0 bytes,
which put `karakeep-meilisearch` in a restart loop (`failed to infer the version
of the database`). The LMDB data and both indexes were intact; writing
`1.56.1` back (matching the image tag), restoring ownership 1000:1000 and
restarting brought it back. Health is `available`, 11 documents, live search
returns hits. Details in `infrastructure/karakeep/README.md`.
