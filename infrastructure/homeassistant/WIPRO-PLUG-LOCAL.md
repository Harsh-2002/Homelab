# Smart plugs: local integration and shared dashboard

Status (2026-11-09): **PC plug configured locally; shared filter dashboard live.**
Private URL: **https://home.l3b.cc.cd/smart-plugs/monitor**.

## Safety boundary

The owner reports a new Wipro smart plug supplying the gaming PC. **Do not
toggle its relay, reset/re-pair it, change timers/protection/restore settings,
or power-cycle it during discovery or troubleshooting.** No such writes were
performed on 2026-11-09. Monitor tiles cannot toggle power. Power, child-lock and
overcharge-protection buttons require confirmation. The power-off dialog was
opened and **cancelled**, with the socket remaining on.

## Verified network observations (2026-11-09)

- Router: TP-Link XC220-G3v; authenticated using the existing HomeLab vault item.
- Candidate: `lwip0`, `10.1.1.242`, MAC `30:48:7D:FA:C1:43`, 2.4 GHz Wi-Fi.
- Bounded TCP connection scan of LAN `/24`, port 6668 only, found `.239`
  (existing bulb) and `.242` (new candidate). No application commands sent.
- TinyTuya discovery with `poll=False`, `forcescan=False` advertised Tuya
  **3.5**, product `keykmm3rjyqy5r8p` for `.242`; the bulb advertised 3.3.
- Installed Tuya Local profile `smartplugv2_energyv3.yaml` lists that product
  identifier. Its manufacturer label is NovaDigital T20A, **not proof of the
  physical Wipro model, current rating, supported sensors or measurement scale**.
- Added an enabled DHCP reservation for the candidate's **current** `.242`
  address, within the existing `.230`–`.249` pool. Navigated away/back and
  verified the saved row and `enable-icon`. Existing reservations unchanged.
  No router reboot, lease release, DNS change or device reconnection requested.

## Authorized setup and actual datapoints

Owner approved the one-time Smart Life QR login. Account device **PC Smart Plug
(10Amp Smart Plug)** matched the discovery identity. Local key is concealed in
**HomeLab → Wipro Plug - Gaming PC**, never in Git. Native config entry
`01M70EBV0A8ME7E9Q14EV1HQNY` uses protocol **3.5** and only device_id, host,
local_key, poll_only and type fields; no cloud token is persisted in that entry.
Routine operation is Tuya Local over LAN TCP 6668, not a cloud integration.

Profile **smartplugv2_energyv2** was selected from actual authenticated datapoints,
not just the broadcast product ID. Cloud product ID is `wur5oqppiylaxefq`.
DP44 is an empty **string**, whereas the superficially similar energyv3 profile
expects base64. The selected profile matched at 100% in the setup log.

| DP | Meaning / observed mapping | Entity |
| --- | --- | --- |
| 1 | relay on | `switch.pc_smart_plug` |
| 9 | countdown, 0 | `time.pc_smart_plug_timer` |
| 18 | current, mA | `sensor.pc_smart_plug_current` |
| 19 | power, raw / 10 W | `sensor.pc_smart_plug_power` |
| 20 | voltage, raw / 10 V | `sensor.pc_smart_plug_voltage` |
| 26 | fault bitfield, 0 / OK | `binary_sensor.pc_smart_plug_problem` |
| 38 | power-restore mode, memory | `select.pc_smart_plug_initial_state` |
| 39 | overcharge protection, false | `switch.pc_smart_plug_overcharge_protection` |
| 40 | indicator, relay / state | `select.pc_smart_plug_light_mode` |
| 41 | child lock, false / unlocked | `lock.pc_smart_plug_child_lock` |

DP17 (energy total), DP47 (temperature), cycle/random timers and DP66 refresh
were not reported. Do not enable hidden energy entities or expose unavailable
refresh buttons as working features. Calibration values were read, not changed.
Native integration reload returned `require_restart: false` and readings resumed;
no HA/container/PC restart was required. Sample readings were around 3–4 W,
126–127 mA and 201–203 V; these are device-reported, not independently calibrated.

## One common dashboard, filtered by plug

The owner's final choice is **one sidebar dashboard, one view, one dropdown**,
not individual dashboards or tabs for each plug. Native Home Assistant Sections
layout adapts from three desktop columns to one on phones. No custom cards,
frontend dependencies or additional service were installed.

- Source: [dashboard-smart-plugs.yaml](dashboard-smart-plugs.yaml).
- Storage dashboard `smart-plugs`, view `monitor`; sidebar title Smart Plugs.
- Selector: `input_select.smart_plug`, currently only **PC**, as requested.
  Dashboard titles and the filter do not include the amp rating.
- All plug-specific sections have visibility tied to the selector value.
- Live state, W, mA, V and fault; energy estimates; power history, with
  voltage/current history accessible through their tiles; settings and guarded
  power/protection/child-lock controls. No scheduled shutdown automation added.
- All 14 referenced entities existed and were available. Desktop 1440px and
  phone 390px layouts checked. Dropdown selection checked; power-off cancelled.

The owner also has **another 10A plug and a 16A plug**. They are not identified
or paired yet. Add them to this same dropdown after matching MAC/device ID/key
and validating their own datapoints. Add conditional sections using their own
entity IDs. Never duplicate dashboards, add fake entities, reuse the PC key,
infer 16A capability from a generic profile, or target all plugs as a group.

To reproduce the native storage dashboard, parse the tracked YAML, then use
authenticated HA WebSocket `lovelace/dashboards/create` (only if absent) with
url_path `smart-plugs`, title Smart Plugs, icon `mdi:power-plug`,
show_in_sidebar true and require_admin false. Send the parsed config through
`lovelace/config/save` with that url_path. Read the live revision before replacing
an existing dashboard; preserve user edits. Credentials stay in the vault.

Sidebar, selector and socket use the bundled `mdi:power-plug` icon. The previous
`mdi:power-socket-in` name did not render. Copy is deliberately short; the energy
note remains explicit that consumption is estimated from power since setup.

## Energy estimates, not a hardware meter

[smart-plugs-helpers.json](smart-plugs-helpers.json) records the exact helper
inputs. The selector uses native WebSocket `input_select/create`; the energy
helper uses the `integration` config flow, and daily/monthly counters use
`utility_meter` config flows. Check for existing helper entities before creating.

- `sensor.pc_smart_plug_estimated_energy`: left Riemann integration of W into
  kWh, 4 decimals, maximum sub-interval 1 minute, device class energy.
- `sensor.pc_smart_plug_estimated_energy_today`: daily utility meter.
- `sensor.pc_smart_plug_estimated_energy_month`: monthly utility meter.

All three report numeric kWh. Local recording begins at setup, not purchase;
first day/month are partial. Missing readings are not measured consumption.
Accuracy depends on the plug's power readings and sampling. There is no imported
Smart Life history, tariff/cost claim, energy-counter reset, or new cloud feed.

## Verification limits

REA was queried: its packet tools currently report `provider_missing` because
TShark is not configured. No REA packet analysis or firmware/app decompilation
was completed; the observations above are router/TinyTuya evidence, not REA
Evidence. Do not claim WAN-outage acceptance or complete feature coverage.
No physical relay/child-lock/protection/timer tests, WAN-block test, independent
meter comparison, host reboot or firmware extraction was performed. The owner
later reported finishing the gaming session; that was not treated as permission
to cut power. Other plug pairing remains outstanding.
