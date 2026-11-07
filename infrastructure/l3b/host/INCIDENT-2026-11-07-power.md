# Incident: unexplained shutdowns and a stalled backup mount, 7 November 2026

## Summary

The host powered off twice, 18:28 and 19:00 IST, then stayed off for 3 h 16 m.
Both shutdowns were orderly and were triggered by **ACPI power-button events**,
not by a crash, thermal event, OOM, watchdog or software shutdown. No keyboard is
attached, so the events came from the chassis power-button circuit; the second
shutdown logged nine presses in seven seconds, consistent with contact bounce in
a failing switch. Separately, the `/BACKUP` disk failed to mount on both boots
because the UAS rebind raced the mount, leaving Time Machine paused for about
four hours.

There is no evidence of data loss. `e2fsck -fn` on `/BACKUP` was clean, and the
290 GB Time Machine sparsebundle is intact.

## Timeline (IST)

| Time | Event |
| --- | --- |
| 1 Nov 21:01 | Boot; host runs for 5 d 21 h |
| 7 Nov 18:28:48 | `systemd-logind: Power key pressed short.` then `Powering off...` |
| 18:29:42 | Clean poweroff (`poweroff.target` reached, journals stopped) |
| 18:33:41 | Power on |
| 18:33:42 | `BACKUP.mount` starts; 18:33:43 `usb-uas-rebind.service` starts |
| 18:33:43 | `EXT4-fs (sdb1): mount failed`; mount unit fails (exit 32). Backups stop |
| 19:00:11 | `Power key pressed short.` again, then `Powering off...` |
| 19:00:16–18 | Seven more power-key events during shutdown (bounce/stuck button) |
| 19:00:19 | Clean poweroff; host stays off |
| 22:16:21 | Power on |
| 22:16:27 | `/BACKUP` mounts, then at 22:16:28 the UAS rebind removes the device: `device offline error`, `JBD2: I/O error`, ext4 aborts, mount unit inactive |
| 22:21 | Filesystem checked read-only (clean) and mounted manually; sparsebundle verified |

## Evidence

- `journalctl -b -2` and `-b -1`: `systemd-logind: Power key pressed short` is the
  only trigger before each shutdown; no `systemctl poweroff`, no scheduled
  shutdown unit, no `shutdown -` command.
- No thermal, MCE, hardware-error, OOM, hung-task or GPU-hang entries before
  either shutdown; `/sys/fs/pstore` empty; kernel taint only `[U]=USER`.
- Input devices are only the two ACPI `Power Button` nodes (front panel and fixed
  power button), plus sleep/WMI/HDA devices. No USB or Bluetooth keyboard is
  connected.
- `journalctl -b -2` shows one unrelated non-fatal kernel `WARNING` in
  `i915_sample`/`hrtimer_forward` at 18:29:57 on 6 November, a day earlier. It is
  a GPU busyness-sampling timer warning, not a hang and not connected to the
  shutdowns.
- The UAS race is reproducible from the boot logs: the mount starts before
  `usb-uas-rebind.service` finishes, and the bridge switches from `usb-storage`
  to `uas` underneath the mounted filesystem.

## Root cause

1. **Shutdowns:** hardware power-button events. With no keyboard attached and no
   software shutdown, the source is the chassis button or its wiring. The burst
   of events during the second shutdown points to an intermittent/bouncing
   switch rather than a single deliberate press. A person pressing the button
   cannot be ruled out from logs alone, but the owner states nobody did.
2. **Backup outage:** an ordering bug. `BACKUP.mount` and `usb-uas-rebind.service`
   are both triggered by the same USB add event, and the mount runs while the
   driver is being switched, so the device disappears mid-mount.

## Impact

- All services offline 19:00–22:16 (3 h 16 m).
- `/BACKUP` unmounted 18:33–22:21, so Time Machine could not write.
- No filesystem damage; no data loss found.

## Remediation applied

- `/etc/systemd/logind.conf.d/10-ignore-powerkey.conf`: `HandlePowerKey=ignore`.
  Short presses no longer power the host off; a long press still forces power off
  in hardware. Intentional shutdowns use `sudo poweroff`.
- `/etc/fstab`: `/BACKUP` now waits for the rebind through
  `x-systemd.requires=usb-uas-rebind.service,x-systemd.after=usb-uas-rebind.service`
  and allows a 30 s device timeout. Verified by unmount/remount; boot ordering
  will be confirmed at the next reboot.
- `/BACKUP` remounted, `e2fsck -fn` clean, sparsebundle present (290 GB).
- Backup of the previous fstab kept at `/etc/fstab.bak-2026-11-07`.

## Follow-ups

- Physically inspect and reseat the front-panel power-button connector; replace
  the switch or front panel if events recur. Consider leaving the button
  disconnected and using Wake-on-LAN.
- **BIOS 1.32.0 is excluded.** The owner previously ran it on this OptiPlex 5060
  and found it unstable enough to roll back to 1.31.0, which is retained
  deliberately (recorded in
  [../HANDOFF-2026-11-01.md](../HANDOFF-2026-11-01.md): "The owner reports BIOS
  1.32.0 was unstable and explicitly retained 1.31.0"). No specific symptom was
  recorded, and Dell publishes no known-issues list for 1.32.0. Do not recommend
  or apply that update; keep 1.31.0 unless the owner decides otherwise. Note the
  trade-off: 1.32.0 carries Dell security advisory DSA-2024-030 fixes, so 1.31.0
  stays exposed at the firmware level.
- Instead of a BIOS change, check "Restore on AC Power Loss" and Wake-on-LAN in
  the existing 1.31.0 setup so the host returns after a real outage.
- A UPS would cover short mains events, though this incident was not a mains
  loss: the shutdowns were orderly.
- Optional: alert on `Power key pressed` in the journal so the next event has a
  timestamp and an owner.
