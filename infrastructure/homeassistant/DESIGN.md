---
name: Samsung AC Home Assistant dashboard
description: An AC-only Control and Care dashboard built from Home Assistant's native interface.
---

# Design System: Samsung AC Home Assistant dashboard

## Overview

This dashboard is an ordinary extension of Home Assistant's existing visual
system. The active Home Assistant theme and frontend own colors, typography,
spacing, native control styling, icon rendering, shapes, and elevation; the YAML
selects semantic MDI icon names where needed. The dashboard source adds no
theme, CSS, frontend dependency, custom card, or image, and therefore defines
no local design tokens. Values visible in a capture are not global Samsung AC
tokens; they can vary with the active Home Assistant theme and frontend version.

The interface is organized into the owner's two native views: **Control** for
daily operation and **Care** for maintenance, alarms, and locally recorded
history. Device capabilities and unmapped cloud features are described next to
the relevant controls so the interface does not imply unsupported behavior.

Evidence reviewed: [product context](../../PRODUCT.md),
[surface direction](dashboard-direction.md), [dashboard source](dashboard-samsung-ac.yaml),
[implementation notes](SAMSUNG-AC-DASHBOARD.md), and the supporting
[Home Assistant package](packages/samsung_ac.yaml). The four review captures
show Control and Care at desktop (1440 px) and phone (390 px) widths:
[Control desktop](../../.impeccable/review/samsung-ac/desktop.png),
[Control phone](../../.impeccable/review/samsung-ac/mobile.png),
[Care desktop](../../.impeccable/review/samsung-ac/care-desktop.png), and
[Care phone](../../.impeccable/review/samsung-ac/care-mobile.png). They show
the light theme; dark-theme appearance is owned by Home Assistant and is not
specified by these captures.

## Colors

Use the active Home Assistant light or dark theme. Theme colors and state
colors belong to Home Assistant; this dashboard does not define or override
color values. In particular, do not promote the colors in the light-theme
captures into a separate palette.

## Typography

Use Home Assistant's native type family, scale, weights, and control labels.
The dashboard declares no font or type-size tokens. Keep section headings
short and use native card labels; place capability explanations in nearby
native Markdown cards.

## Layout

Both views use native Sections dashboards with a maximum of three columns.
At desktop width, the sections place the main task groups side by side. At the
captured 390 px phone width, they flow into one column in reading order.

Control leads with the bedroom thermostat and current room temperature, then
fan and comfort settings, independent up/down and left/right airflow controls,
mode-limited cooling capacity, everyday settings, and the optional local
schedule. Care groups reported alarms and self-check, filter and cleaning,
then local history and items not mapped to the LAN integration. Keep the
maintenance tasks in Care, separate from the power controls in Control. Keep a
qualification next to the control or measurement it qualifies.

## Elevation & Depth

Cards, separators, and tonal surfaces use Home Assistant's native treatment.
The dashboard sets no shadow, elevation, or motion values. Let the active
theme and native cards provide grouping and state feedback.

## Shapes

Corner treatment, borders, clipping, and control silhouettes come from the
active Home Assistant theme and native card types. There are no local radius
tokens or shape overrides.

## Components

Use native components as declared in `dashboard-samsung-ac.yaml`:

- **Thermostat and fan:** The native thermostat is the primary power, target
  temperature, and HVAC-mode control. A native climate tile exposes fan modes
  as a dropdown. Keep the current room temperature visible with the thermostat.
- **Comfort and airflow:** Comfort is one exclusive selector, not independent
  switches. Group vertical and horizontal swing with each axis's fixed-position
  control; horizontal sweep belongs with left/right airflow. Fixed positions
  are numbered device steps, not degrees, and selecting one stops swing on that
  axis. Explain these behaviors beside the selectors.
- **Cooling capacity:** Show the selector only in Cool mode. Describe its
  device-supported levels as compressor operating levels, not live power
  consumption.
- **Everyday settings:** Use native entity controls for display lighting, beep,
  and auto-clean-after-use. Explain that auto clean dries the unit after use;
  it does not start a cleaning cycle immediately.
- **Local schedule and alerts:** Both are opt-in through their native enable
  toggles; the reviewed captures show both off, and their automations require
  the corresponding toggle to be on. The local schedule uses Asia/Kolkata
  time, requires different on and off times, and turns on with the AC's last
  operating settings. It does not import the SmartThings schedule. HA alarm
  notifications are persistent HA notifications, not iOS push.
- **Care actions:** Keep the self-check action in Care and show the actual
  status, stored result, and reported error. Starting self-check has a native
  confirmation because it may affect operation. Show Stop auto clean only
  while cleaning is running, and require confirmation to stop it. Require
  confirmation to reset the filter counter, and explain that reset is for
  after filter cleaning or replacement.
- **Filter and history:** The gauge is a maintenance interval calculated as
  100 minus the AC-reported usage percentage; it is not a filter-quality or
  airflow measurement. History is data Home Assistant records locally, not
  imported Samsung usage history. The observed mean uses available samples.
- **Unavailable features:** Label unmapped cloud workflows and unverified
  standby monitoring as unavailable locally. Do not imply the Samsung care
  score, humidity, or other unreported capabilities are present.

## Do's and Don'ts

- Do use the active Home Assistant theme and built-in cards for consistent
  browser and companion-app behavior.
- Do preserve the Control/Care organization and keep maintenance actions away
  from daily power controls.
- Do keep the schedule and notifications opt-in, and retain confirmation for
  self-check, cleaning stop, and filter-counter reset.
- Do describe what the local integration actually reports, including units,
  operating conditions, and unavailable or unverified features.
- Don't add a dashboard-specific palette, typography, spacing, radius, shadow,
  or motion system.
- Don't add custom CSS, third-party cards, decorative images, or a separate
  frontend to imitate Samsung's app.
- Don't represent cloud schedules, usage history, care scores, or unverified
  device features as local capabilities.
