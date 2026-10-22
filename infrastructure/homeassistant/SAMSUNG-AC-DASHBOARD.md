# Samsung AC dashboard

Deployed 2026-10-22 on Home Assistant Core 2026.10.2. Owner selected a separate
AC-only dashboard with **Control** and **Care**, built directly with native
cards. Existing dashboards, authentication and theme are unchanged.

- [Control](https://home.l3b.cc.cd/samsung-ac/control)
- [Care](https://home.l3b.cc.cd/samsung-ac/care)
- Device and protocol evidence: [SAMSUNG-AC-LOCAL.md](SAMSUNG-AC-LOCAL.md).
- Native UI inheritance and component rules: [DESIGN.md](DESIGN.md).

## Feature coverage

| Feature | Implementation and limits |
|---|---|
| Power, mode, temperature, fan | Native climate/thermostat; device-advertised options, target18–30C. |
| Comfort | One exclusive selector: Normal, Good Sleep, Quiet, MAX (Fast). Not independent toggles. |
| Vertical/horizontal airflow | Independent swing selectors; fixed vertical positions1–6 and horizontal1–5. Positions are indices, not degrees. Selecting a fixed position stops that axis. |
| Horizontal sweep | Full sweep, Left side, Right side, from device-supported values. |
| Five-step cooling | Standard100%,80%,60%,40%,Power120%; shown only in Cool mode. These are compressor-operation levels, not live power-consumption percentages. |
| Display, beep, auto clean | Existing native entities. Auto clean means drying after use, not starting a cleaning cycle immediately. |
| Schedule | New HA daily on/off schedule, disabled initially. Asia/Kolkata, distinct times required, turn-on retains last operating settings. Existing SmartThings schedule is not imported. Avoid conflicting schedules. |
| Alarms | Actual device alarm code and enabled-monitoring state. Monitoring enabled is not an active overload. Optional HA persistent notifications, disabled initially, not iOS push. |
| Self-check | Actual ready/result/error fields, with absent result shown honestly. Starting requires UI confirmation and may affect operation. |
| Filter | Remaining interval =100 minus device usage percentage. Initially68%,96hours of300hour reminder interval. Maintenance counter, not measured filter quality. Reset requires confirmation after physical maintenance. |
| Cleaning | Running/progress; stop button only shown while active and confirmation-protected. |
| History | HA-recorded temperature, available-sample mean up to24h, cumulative energy and reported saved energy. Not imported Samsung history. |
| Welcome Cooling | Not mapped: location/notification workflow, not a verified local AC toggle. |
| Always-on sensor | Standby-monitoring command unverified; no humidity resource reported locally. |
| Cloud care score/schedules | No fabricated eight-check score or copied historical screenshot values. |

Official model reference: [Samsung AR50H18D14HNNA](https://www.samsung.com/in/air-conditioners/split-ac/bespoke-ai-inverter-split-ac-4-8-kw-4-star-ar50h18d14hnna/).
No WindFree, motion sensor, FreezeWash or humidity capability was invented.

## Reproduce and maintain

Source of truth:

- `dashboard-samsung-ac.yaml` → `/config/dashboards/samsung-ac.yaml`.
- `packages/samsung_ac.yaml` → `/config/packages/samsung_ac.yaml`.
- Existing `/config/configuration.yaml` includes `homeassistant.packages: !include_dir_named packages`.
  Merge this into an existing `homeassistant` mapping, never duplicate/overwrite it.
- `localthings/` contains the small model-gated extension and exact upstream patches.
- `samsung-ac-dashboard.py` performs read-only native API verification; optional
  `--apply-names` normalizes only the seven new entity IDs in the specified entry.

Stage the pinned component in a new absolute directory:

```bash
bash infrastructure/homeassistant/stage-localthings.sh /tmp/samsung-ac-new-stage
```

The script verifies the upstream v0.34.0 archive SHA256, checks archive members,
applies patches without fuzz, validates translations, compiles and runs six
offline tests. It does not install into HA or send any device commands. Requires
Python3.12+ for safe tar extraction, curl, patch and sha256sum.

Patch only the confirmed platform family `TP1X_DA-AC-RAC-01011_0000` and bind
only fields with device-advertised supported options. The seven added selectors
use native coordinator/entity writes, validate options, reject changes while
off, and require Cool for cooling capacity. Fixed-position writes set only that
axis to Fix. The write shape is inferred from the live protocol schema, not
positive physical acceptance. Do not expose arbitrary raw-resource writes.

Do not blindly overwrite this component with a HACS/upstream update. Rebase the
patches onto the intended release, repeat staging/tests and owner-approved
physical acceptance. Upstream v0.34.0 contains manifest version0.33.0; this is
an upstream mismatch, not a reason to silently edit the manifest.

Before installation, take a native HA backup, preserve the old component/config,
then copy staged component and YAML, run `ha core check`, and perform a controlled
Core restart. Never edit `.storage` registries directly. If entity IDs change
after re-pairing, resolve the new registry entries and update YAML explicitly.

Read-only live check on this development host (uses HASS_URL/HASS_TOKEN from the
existing protected Hermes environment in memory, never displays credentials):

```bash
/tmp/samsung-ac-investigation-venv/bin/python infrastructure/homeassistant/samsung-ac-dashboard.py
```

That diagnostic venv is temporary; recreate with `websockets` if absent. It
verifies native WebSocket authentication, entity presence and both dashboard
views, not physical actuator behavior.

## Deployment evidence and acceptance boundary

- Native pre-change partial HA configuration/database backup **8b832ad0**,
  `before-samsung-dashboard-20261022`, completed (9,809,920bytes).
- Old component preserved at `/config/localthings.before-dashboard-20261022`.
- Native configuration check passed; one controlled Core restart completed.
- LocalThings entry `01M5HQ6SAA45N3EFXRNMQBS25B` loaded, now35 registered
  entities including seven added selectors; two original entities remain disabled.
- Live selector values/options and climate availability verified through HA.
- Six offline payload/model-gating/range/power/mode tests passed.
- Off-state selector requests returned HTTP400 before any DTLS write. Power and
  target18C unchanged; no successful actuator command was issued.
- Control/Care rendered at desktop1440 and phone390 widths. No horizontal
  overflow or native error cards. Initial findings corrected in one batch:
  text tab labels, short schedule labels, human-readable missing self-check result.
- Shared four-agent MCP parity checker passed. No harness/MCP/plugin config changed.

**Not tested:** positive physical power/mode/fan/swing/comfort/cleaning writes,
scheduled execution, alarm delivery, or actual WAN outage/cold start. Obtain
owner agreement for a safe physical test, record previous state and restore it;
do not repeatedly cycle the compressor. Exposure of a selector is not proof of
correct physical behavior. Keep SmartThings registration as the upstream
integration warns unlinking can reset device Wi-Fi.

## Rollback

Disable the new schedule/alerts first if enabled later. Remove only this package
and dashboard YAML, restore the saved LocalThings component, check configuration
and restart Core. Preserve native auth, the existing AC entry/certificate and
bulb integration. Remove the package include only if no other packages use it.
The native backup is a broader recovery option, not the default rollback after
newer HA changes. No firmware/reset/unpair/WAN-block operation is required.
