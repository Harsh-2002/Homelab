# Samsung AC local-control investigation

Investigation date: 2026-10-22. Owner wants LAN control through Home Assistant,
not another SmartThings cloud integration. Do not change AC power, setpoint,
mode, pairing, ownership, firmware or network settings just to discover it.

**Operational:** LocalThings installed, native config entry loaded, live climate
state available as **`climate.samsung_room_ac`**, device name **Samsung Room AC**.
Setup, live readback, private HTTPS API and integration reload verified.
No actuator commands or full WAN-outage test performed.

## Reference device

- Owner-confirmed model: **AR50H18D14HNNA**, Samsung room air conditioner.
- Owner uses Samsung SmartThings on iPhone (initially called Samsung SmartApp).
- Owner-reported software: One UI 7.0 Air conditioner, Tizen Lite 4.0,
  controller RAC.5.3.20. SmartThings says current for the device/account;
  global/latest firmware availability has **not** been independently verified.
- Owner-reported firmware lines: `02825A260710`,
  `02812A25111800,FFFFFFFFFFFFFF`, `02813A25101500,FFFFFFFFFFFFFF`,
  `FFFFFFFFFFFFFF,FFFFFFFFFFFFFF`.
- IP **10.1.1.241**, MAC **34:55:E5:0A:80:D7**, directly correlated in the
  dev VM's neighbor table. Ping responded, including one duplicate reply;
  that alone is not evidence of an address conflict.
- The serial supplied privately by the owner is unnecessary for control and
  is intentionally not repeated in this runbook, public content or memory.

## What is actually verified

Twelve bounded TCP connection checks to 80,443,1883,2878,8000,8001,8080,8443,
8883,8888,8889,9090 timed out. This does not prove there are no TCP services.
Plain CoAP discovery probes to 5683 and 49152–49160 produced a 15-byte reply
from 49154; TShark decode-as identifies a fatal DTLS handshake-failure alert
because plain CoAP is not DTLS. Other unanswered probes do not prove closed UDP.

`smartthings-local` 0.1.24 stateless ClientHello tests proved DTLS liveness:

- Probe 49154: HelloVerifyRequest, about 92 ms, reply from 49154.
- Probe 5684: HelloVerifyRequest, about 79 ms, **reply from 49154**.
  Do not assume that the response must use the original destination port.

A freshly generated client certificate using the upstream documented
AC14K_M-compatible path completed a DTLS session on 49154. Read-only GETs:

- `/oic/d`: 2.05, `oic.d.airconditioner`, name Samsung Room A/C.
- `/oic/p`: 2.05, manufacturer Samsung Electronics, hardware Realtek,
  firmware `ARA-WW-TP1-26-AR6X00MG_11260710`, platform family
  `TP1X_DA-AC-RAC-01011_0000`.
- `/oic/res`: 2.05, resource directory. This root directory does not enumerate
  all appliance controls; `/device/0` returns the actual collection.
- `/device/0`: 2.05, 7,857 bytes of CBOR including live appliance resources.

Observed snapshot, not a commanded setting: power On, Dry mode, room 29 C,
target 18 C. Advertised modes Auto/Cool/Dry/Fan, fan Auto/Low/Mid/High/Turbo,
presets Off/Sleep/Quiet/Speed, and vertical/horizontal Swing/Fix with angle
options. These are protocol-reported capabilities, not exhaustive physical
acceptance tests. Do not invent Heat or WindFree from brand/model assumptions.

Useful resource paths include `/power/vs/0`, `/mode/vs/0`,
`/mode/convenient/vs/0`, `/temperatures/vs/0`, `/wind/strength/vs/0`,
`/wind/oscillation/vs/0`, filter, energy and auto-clean resources.
Only GETs were issued. Diagnostic sessions explicitly closed with the
library's orderly DTLS close; no lingering scanner/controller was started.
Do not read or write ownership/security/Wi-Fi resources as a shortcut.

## Evidence and private artifacts

REA 6.7.0 CLI was used because the active session exposes no REA MCP tools;
scoped Codex doctor reports healthy. Wireshark/TShark and capinfos 4.4.19.

- Discovery capture: 25 frames, private
  `~/.local/state/samsung-ac-investigation/discovery-20261022.pcap`, SHA256
  `8c0eb4b7ae92830f886dae51e47efcd291f0e9839506c76f73af08b43cdf3964`.
  REA Evidence `ev_f7f3e3279be6c51dbff1ebd8ae4bf950ff83d4ba28dedbd4d364274dddad6d87`.
- Stateless handshake capture: 8 frames (four ARP, four DTLS), 964 bytes,
  `dtls-probe-20261022.pcap` under the same private directory, SHA256
  `27a88ed2e9eb186a3c9f36885e24909e8a72750eee97b0a4fd6f338e9967aa49`.
  REA Evidence `ev_322e7ee9003d9b32fff2208ea0efc03fe145c75cfd796dcfa0ad4a3637589174`.
  Complete record retained locally as `dtls-probe-evidence.json`.
- Actual HA integration reload/state-traffic capture on px30 vmbr0:
  `ha-local-session-20261022.pcap`, 100 frames, 31,269 bytes, SHA256
  `b036eb80c554e150a156bf0ed975403ce7faee68c2fd468e49d23ca53cd0defb`.
  REA Evidence `ev_2df3116aeece127f8bf7ed907c31c4b8b8a9f0e5da2e812119824618f4e0feec`.
  TShark identified 84 DTLS application-data frames:43 HA13→AC241 and41 reverse.
  This proves actual local integration communication/read traffic, not an
  actuator write test or absence of separate appliance-cloud communication.
- Private directory mode0700, capture/key files protected with umask077.
  Never commit packet files or client keys. Captures are restricted to the
  target as visible to dev; they do not prove absence of WAN traffic.
- Temporary diagnostic environment `/tmp/samsung-ac-investigation-venv`:
  smartthings-local0.1.24, cbor2 6.1.5, pyOpenSSL26.4.0. No global package changes.
- Reviewed upstream `setup_cert.py` was downloaded at research commit
  `aa65b8a01a47fe2323f1e47709281a9a9bd4b8fc`. Generated private client credentials
  under `~/.local/state/samsung-ac-investigation/certs`. Ran without `--test`
  to avoid its ACL-read diagnostic; our own probes used ordinary device GETs.

## Home Assistant integration preparation

Reuse existing HA API/Hermes integration, not a new public API, broker or bridge.
Community **LocalThings** supports the observed OCF appliance resource family.
Initial automatic credential setup makes a public Samsung TLS-certificate UUID
lookup; this is a setup dependency, not a cloud round trip for every command.
Keep the AC registered in SmartThings: upstream warns that deleting the device
there can reset Wi-Fi settings when it next contacts Samsung.

- Current HA Core checked **2026.10.2**, HAOS18.3, host10.1.1.13.
- Native pre-change partial backup **0b406e2d**, name
  `before-localthings-20261022`, successful, 8,488,960 bytes, Core2026.10.2.
  Contains HA configuration/database, not a claim of whole-VM backup.
- Official latest release tag checked: **v0.34.0**, published2026-10-11,
  commit `26c96a1fe28af2325508bc708fb4246f04e4a1d2`. Its manifest reports
  **0.33.0**; preserve this upstream discrepancy instead of editing it locally.
  HACS floor2025.1.0, requirements cbor2>=5.4.6, smartthings-local>=0.1.23.
- Source archive SHA256
  `1968cdc055388e99142ad8c4fd894d38a227a0bb77920393f33d663526197e33`.
  Validated 112 integration members for traversal/symlinks before extraction.
- Copied only `custom_components/localthings` to the previously absent HA
  destination. Native configuration check passed; controlled Core restart
  completed successfully to load the component. Existing Tuya bulb entry also
  returned loaded. No HA version upgrade, VM reboot or HACS installation.

## Operational completion

Native config flow accepted only `host: 10.1.1.241`, generated its own client
certificate and created entry **01M5HQ6SAA45N3EFXRNMQBS25B**. The standalone
diagnostic certificate was not imported. No SmartThings user account/password,
PAT or cloud OAuth token was required. Native config contains generated client
credential material; never print expanded config entries.

- Integration entry loaded. 28 entities registered, 26 enabled by default.
- Renamed the new climate entity from the generated long platform-model ID to
  **climate.samsung_room_ac**, friendly name **Samsung Room AC**; updated the
  device's user-visible name using native HA registry APIs, not storage editing.
- Home Assistant exposes modes off/auto/cool/dry/fan_only; target range18–30C;
  fan auto/low/medium/high/turbo; presets none/sleep/quiet/speed; swing
  off/both/vertical/horizontal. Native API showed Dry, setpoint18C, fan auto,
  preset none, swing off. Room temperature changed naturally29→28→27C while
  observing. No setpoint/power/mode command was issued by this investigation.
- Enabled entities also include energy, filter, alarms, temperature, display,
  beep and auto-clean controls/diagnostics. Exposure is not exhaustive physical
  validation of all vendor features. Do not trigger maintenance/reset buttons.
- Native integration reload returned `require_restart: false`; climate returned
  available Dry with unchanged target18C. Authenticated API read through private
  **https://home.l3b.cc.cd** passed. Existing bulb remains available; no bulb
  control command was sent.
- Backed up the **actual native LocalThings** client certificate/private key
  concealed in **HomeLab → Samsung AC - Room**, verified both against HA.
  Vault item `credential` is the private key, `client-certificate` is its leaf.
  These are not a Samsung account password or a public API bearer token.
- Existing Hermes HA plugin and other agents' authorized HA API access can use
  this climate entity. No new per-agent MCP/provider/skill or public webhook.
  Four-agent integration parity checker passes; no harness config was changed.

For later owner-approved automation, HA's native climate services are the API
boundary, for example `POST /api/services/climate/set_temperature` with JSON
`{"entity_id":"climate.samsung_room_ac","temperature":24}`. This is a usage
example, **not an executed acceptance test**. Keep the HA token private.

## Acceptance boundaries and rollback

Read-only protocol authentication/capability access and HA setup/state mapping
are verified. No power/setpoint/mode change or
physical WAN-outage test has been performed. Do not promise every SmartThings
feature maps correctly, or that complete long-duration offline behavior passed.

Before any controlled write acceptance, agree a safe change with the owner and
restore the original visible settings afterward. Never repeatedly power-cycle
the compressor to test automation.

If installation must be rolled back, remove only this new config entry through
HA, then only the new localthings component directory, check configuration and
restart Core. Preserve the existing bulb integration, native auth and other
components. Restore backup0b406e2d only if broader recovery is required and
newer HA changes have been considered. No firmware flash/reset/unpair/WAN block.

Sources: [LocalThings](https://github.com/mbillow/localthings),
[protocol compatibility](https://github.com/mbillow/SmartThings-Local/blob/main/docs/appliance-compatibility.md),
[certificate path](https://github.com/mbillow/SmartThings-Local/blob/main/docs/certificates.md),
[release v0.34.0](https://github.com/mbillow/localthings/releases/tag/v0.34.0).
