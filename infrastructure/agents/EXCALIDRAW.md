# Excalidraw CLI

Official `@excalidraw/cli` **0.2.0** installed 2026-10-25 for the dev user:
`~/.local/bin/excalidraw`, package in `~/.local/lib/node_modules/@excalidraw/cli`.
Node.js 22+ required; this machine uses Node 26. No API key or account configured.
No MCP server, public listener, cloud login or diagram upload was added.

Install/update reproducibly without changing other global npm settings:

```bash
npm install --global --prefix /home/dev/.local @excalidraw/cli
excalidraw --version
excalidraw render --help
```

The package manages Excalidraw+ workspaces and renders local scenes. Local
rendering does **not** require Excalidraw+. Do not confuse it with an AI scene
generator, an auto-discovery tool, a local editor or a self-hosted server.

The shared `excalidraw-local` skill is symlinked under Codex, Claude, Hermes and
the shared `.agents/skills` root, which OpenCode already discovers. Existing
MCPs, memory plugins, model choices and auth settings are unchanged. A new agent
session may be needed to refresh its skill list.

For diagrams, keep editable `.excalidraw` scene JSON and export locally. Native
shapes, text, arrows and bindings must remain editable, not one embedded image.
The renderer uses existing Chromium. This machine's versioned browser lives
under `~/.cache/ms-playwright`; the Homelab render script discovers the newest
installed Chromium or accepts `EXCALIDRAW_BROWSER_PATH` explicitly. No extra
browser download or persistent browser profile is needed.

```bash
node docs/architecture/excalidraw-build.mjs --internal
node docs/architecture/excalidraw-render.mjs --internal
```

The internal address maps and scene/exports are Git-ignored. The default build
omits addresses and does not read either private map. All 21 frames are tested
through the official renderer. The owner's preferred artifact is the internal
tree and flow board; the old presentation-sheet layout was rejected.

Graphviz `dot` is installed as a local layout helper: it computes positions,
which are converted to native Excalidraw shapes and bound arrows. Excalidraw CLI
is the actual scene renderer. Install Graphviz with Debian's `graphviz` package
if rebuilding on another machine. The CLI alone does not lay out scene graphs.

Cloud commands require separate Excalidraw+ authorization. Do not run login,
scenes create/put/patch or other workspace writes for these internal files
without explicit owner approval. No key is required for the setup above.

Sources: [official CLI](https://github.com/excalidraw/cli), installed help,
[native scene format](https://docs.excalidraw.com/docs/codebase/json-schema),
[Graphviz hierarchical layout](https://graphviz.org/docs/layouts/dot/).
