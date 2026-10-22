# Samsung AC dashboard surface

Target: infrastructure/homeassistant/dashboard-samsung-ac.yaml
Mode: Operate. Native Home Assistant UI, used on iPhone and desktop.
Scope: separate AC-only dashboard; existing dashboards untouched.
Owner confirmed Control/Care views and direct native-card implementation.

## Direction contract

THESIS: One local AC controller, organized around daily operation and care,
not a wall of engineering entities or a copy of unverified cloud features.

OWN-WORLD: Inherit HA's light/dark theme, native type, controls, spacing and
icons. No new visual world, custom CSS, third-party cards or decorative imagery.

STORY: See current operation, set comfort and airflow, then inspect maintenance
and history. Clearly distinguish unavailable device capabilities and unmapped
cloud features. Maintenance/reset actions are never adjacent to power controls.

FIRST VIEWPORT: Control tab opens with thermostat/power and live room temperature,
followed by compact mode, fan and comfort controls. Airflow and optional schedule
follow in named sections. Care starts with honest alarm/filter status, not a
fabricated diagnostic score. Native sections collapse to one column on phones.

FORM: Owner-pinned native Control/Care composition. Seed not run: precisely
specified extension inside the established HA visual world, not a concept round.
Code-first per explicit owner selection. Signature interaction: independent
airflow axes and device-supported fixed positions, grouped as one task.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

This ordinary extension preserves native HA design; documentation records that
inheritance rather than inventing a global theme. No shipping raster assets.
