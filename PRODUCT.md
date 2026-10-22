# Home Assistant AC dashboard product context

<!-- impeccable:product-schema 1 -->

This record is scoped only to the Samsung AC dashboard under
`infrastructure/homeassistant`. It does not replace requirements for other
Homelab services or their interfaces.

## Platform

web

## Users

Anurag controls his bedroom Samsung AR50H18D14HNNA from the Home Assistant
iPhone companion app and browser, including when internet access is unavailable.

## Product Purpose

A separate AC-only Home Assistant dashboard with Control and Care views,
using the verified local integration rather than a separate web application.
Expose real controls, distinguish platform features from device capabilities,
and preserve existing dashboards.

## Operating Context

Private Home Assistant, native authentication, LocalThings over LAN DTLS/CoAP.
The owner provided a SmartThings feature/UI summary and explicitly approved
native HA cards, two AC-only views, and direct code-first implementation.

## Capabilities and Constraints

Known: climate power/mode/temperature/fan/presets/swing, live temperature,
filter usage, energy, display, beep and auto-clean. Extra local fields require
validated mappings, not invented commands. No unsolicited compressor cycling,
temperature/mode changes, reset, cleaning or diagnostic execution during setup.
Cloud schedules/statistics and unverified standby-monitoring semantics must not
be represented as working local equivalents. Serial numbers and keys stay private.

## Brand Commitments

Use Home Assistant's existing native interface and the owner's Control/Care
organization. Do not introduce custom themes, CSS, images, frontend dependencies
or a separate service to mimic Samsung's app.

## Evidence on Hand

`infrastructure/homeassistant/SAMSUNG-AC-LOCAL.md`, actual HA states/resources,
and the owner's SmartThings screenshot summary. Physical write acceptance and
extended WAN-outage behavior are not yet verified.

## Product Principles

- Honest feature coverage beats cosmetic parity.
- Daily controls stay easy to reach on a phone.
- Destructive maintenance actions require explicit confirmation.
- Deployment and capability changes are reproducible from Git.
