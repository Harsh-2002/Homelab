---
name: excalidraw-local
description: Create, edit and locally render editable Excalidraw diagrams with the official Excalidraw CLI. Use for architecture maps, topology trees and flow diagrams.
---

Use the official `excalidraw` CLI installed for the dev user. Check
`excalidraw render --help` for current rendering flags. Local rendering needs
no account or API key. The CLI renders scene JSON; it does not automatically
discover infrastructure or generate accurate scenes from prose.

Keep `.excalidraw` as the editable source. Preserve IDs and arrow bindings when
editing an existing scene. Inspect rendered results before claiming success.
Before regenerating an existing scene, preserve any manual user edits; rendering
alone is safe for geometry and does not rebuild the scene.
Prefer rendering individual frames for a large scene, using `--frame-id`.
Excalidraw already provides pan/zoom and editing; do not add another service
unless the user asks for hosting/collaboration.

On this machine Chromium is installed under `~/.cache/ms-playwright/`.
If native browser discovery fails, supply its actual executable with
`--browser-path` or `EXCALIDRAW_BROWSER_PATH`. Do not download another browser
just to bypass discovery. Use `--fonts-url none` for an offline render when
downloadable CJK fonts are unnecessary.

For the Homelab, read `docs/architecture/README.md`. The owner's primary purpose
is understanding the full internal physical → VM/LXC → Docker/Kubernetes tree
and actual traffic/data flows, with IP:port labels. Do not replace that with
presentation cards or paragraphs. Unknown switch/AP models/cabling stay unknown;
Docker services may use a host-published port or internal DNS rather than a
unique stable IP. Protect credentials and keep IP-bearing scenes/exports in
Git-ignored `docs/architecture/internal/`.

Cloud workspace commands (`login`, `scenes`, `collections`, `workspace`) require
Excalidraw+ credentials and can send private diagrams outside the machine. Do
not log in or upload local infrastructure diagrams without explicit approval.
To update this user-prefix install, use
`npm install --global --prefix /home/dev/.local @excalidraw/cli`.
