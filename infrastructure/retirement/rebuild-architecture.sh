#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../.."
export PATH="${HOME}/.local/bin:${PATH}"
export PLAYWRIGHT_MODULE="${EXCALIDRAW_CLI_DIR:-$HOME/.local/lib/node_modules/@excalidraw/cli}/node_modules/playwright-core/index.mjs"
export CHROMIUM_EXECUTABLE="${EXCALIDRAW_BROWSER_PATH:-$(node -e 'const fs=require("fs"),os=require("os"),p=require("path"),d=p.join(os.homedir(),".cache/ms-playwright"); process.stdout.write(fs.readdirSync(d).filter(x=>/^chromium-\d+$/.test(x)).sort((a,b)=>Number(b.split("-")[1])-Number(a.split("-")[1])).map(x=>p.join(d,x,"chrome-linux64/chrome")).find(x=>fs.existsSync(x))||"")')}"
test -x "$CHROMIUM_EXECUTABLE"
node docs/architecture/build.mjs
node docs/architecture/build.mjs --internal
node docs/architecture/check.mjs
node docs/architecture/excalidraw-build.mjs
node docs/architecture/excalidraw-build.mjs --internal
node docs/architecture/check-topology.mjs
node docs/architecture/check-topology.mjs --internal
node docs/architecture/excalidraw-render.mjs
node docs/architecture/excalidraw-render.mjs --internal
node docs/architecture/export-formats.mjs
node docs/architecture/export-formats.mjs --internal
node docs/architecture/render.mjs
node docs/architecture/render.mjs --internal
