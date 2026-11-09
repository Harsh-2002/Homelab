# Gaming PC smart plug: local integration preparation

## Safety boundary

The owner reports a new Wipro smart plug supplying the gaming PC. **Do not
toggle its relay, reset/re-pair it, change timers/protection/restore settings,
or power-cycle it during discovery or troubleshooting.** No such writes were
performed on 2026-11-09. Prefer read-only sensors in the eventual dashboard;
protect any separately exposed power control against accidental activation.

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

## Pending owner authorization and verification

No local key for this new device exists in the HomeLab vault. The bulb's key
cannot authenticate another device. A Tuya Local add-integration flow was opened
and is at the cloud-assisted `user_code` step. Flow state is private temporary
state under `/tmp/opencode/plug-flow.json`; it may expire. No new config entry,
relay command, dashboard or telemetry entities have been created yet.

Next: owner provides the controlling app/account User Code and approves its QR
link (Smart Life: Me → Settings → Account and Security → User Code). Match the
account device to the discovered identity before selecting it. Obtain and store
the local key concealed; never print keys or QR tokens. Continue with local
status reads only, choose the profile using actual datapoints, and confirm units
before displaying power/current/voltage/energy. One-time setup may need cloud
authorization; routine operation must use local Tuya, as with the bulb.

REA was queried: its packet tools currently report `provider_missing` because
TShark is not configured. No REA packet analysis or firmware/app decompilation
was completed; the observations above are router/TinyTuya evidence, not REA
Evidence. Do not claim WAN-outage acceptance or complete feature coverage.
