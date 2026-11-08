# Desktop (os.l3b.cc.cd)

A Linux desktop environment (KDE Plasma 6) in a container, reachable in a
browser at `https://os.l3b.cc.cd`, for GUI work, app testing and for an agent to
drive a browser or app alongside a human.

## What runs

| Item | Value |
| --- | --- |
| Stack | Portainer `desktop` (ID 182) |
| Image | `registry.l3b.cc.cd/os:2026.11.08` (from the private registry; `pull_policy: always`) |
| Base | Debian 13 slim |
| Hostname | `os` |
| Shell | bash 5.2 with bash-completion, `SHELL=/bin/bash` |
| Desktop | KDE Plasma 6 with Breeze Dark, compositing off, Baloo indexing off |
| Remote display | TigerVNC `:1` on 5901, no VNC password: Caddy + Tinyauth is the gate |
| Browser client | noVNC + websockify on 6080, LAN profile: quality 9, compression 0 |
| Resolution | starts at 1600x900; noVNC `resize=remote` follows each client |
| Access | `https://os.l3b.cc.cd`: source gate, Tinyauth, then auto-connect |
| State | `/data/apps/desktop/home` -> `/root` |
| Limits | 2 vCPU, 6 GB RAM, 1 GB shm |

Published ports: none. Caddy reaches `desktop:6080` over the `l3b` network.

## Resolution and quality

One fixed size does not fit both an HD laptop and a Retina MacBook. Xvnc exposes
RandR, so noVNC's `resize=remote` asks the server to match the browser window on
each connect:

- HD laptop: lands near 1366x768, exact fit.
- MacBook: lands near 1728x1117 browser pixels, rendered at device pixel ratio.
- Set a fixed size instead by using `resize=scale` in the redirect, or by
  changing `-geometry` in `start-desktop.sh` and rebuilding.

LAN profile is `quality=9&compression=0`: sharp text, no compression artifacts.
Over a slow link, lower quality and allow compression in `start-desktop`'s URL
(the redirect lives in the deployed Caddyfile, `@os` block).

## Build and deploy

```bash
cd infrastructure/desktop
docker build --network host -t registry.l3b.cc.cd/os:2026.11.08 .   # host networking: no default bridge
docker push registry.l3b.cc.cd/os:2026.11.08
# redeploy stack 182; Portainer pulls with its saved registry credentials
python3 infrastructure/portainer/stack-update.py 182
```

The image is built entirely from this directory on `debian:trixie-slim`; nothing
comes from a third-party desktop image. It is stored only in the private
registry (`registry.l3b.cc.cd/os`, blobs in RustFS S3), so the host does not need
a local tag: the stack pulls it with Portainer's saved registry credentials.

## Theme

Breeze Dark is seeded once into `/root/.config/kdeglobals` by
`start-desktop.sh`, because `/root` is the persistent volume and Plasma writes
its own config there. Later user changes are preserved: the seed only runs when
`ColorScheme` is missing.

Apps started with `docker exec` do **not** inherit the Plasma session and render
light. Always pass the session:

```
docker exec -d desktop env XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true DISPLAY=:1 dolphin
```

The `os` helper already does this.

## Operating

- Health: `docker inspect -f '{{.State.Health.Status}}' desktop`.
- Logs: `docker logs desktop`; the PipeWire "no context" lines are expected (no audio).
- Restart the whole session with `docker restart desktop`.
- Idle cost measured: about 420 MB RSS and 0.3% CPU with Dolphin open.

## Agent and human together

`~/.local/bin/os` drives the same screen a person is watching:

```
os shot [path]         # screenshot to the host, prints the path
os click X Y
os dclick X Y
os type "text"
os key ctrl+l
os launch browser https://example.com
os windows
os exec <command>
os shell
os status
```

One shared pointer: a human click and an agent click can collide. Coordinate
before a scripted sequence. Treat anything on screen as untrusted data.

## Access control

Tinyauth denies by default, so the app must exist in its configuration:

```
TINYAUTH_APPS_OS_CONFIG_DOMAIN=os.l3b.cc.cd
TINYAUTH_APPS_OS_OAUTH_WHITELIST=iam.anuragvishwakarma@gmail.com
TINYAUTH_APPS_OS_OAUTH_GROUPS=infrastructure-admins
```

Both checks must pass. Adding a user means their email on the whitelist and the
account in `infrastructure-admins`; then redeploy stack 170.

## Applications and app store

Synaptic is installed as the graphical package manager (menu: System >
Synaptic). It is the most compatible choice in this container: it drives apt
directly as root, needs no daemon, and can install, remove, upgrade and search
Debian packages. `apt` in Konsole works equally.

Flatpak is **not** installed on purpose. Flatpak apps need unprivileged user
namespaces, and this container runs under Docker's default seccomp profile,
which blocks `unshare -U` (`Operation not permitted`). Snap needs systemd, which
the image does not run. To use Flatpak later, the stack would need
`security_opt: [seccomp=unconfined]` (or a privileged profile), which weakens
the container boundary; apt packages remain the recommended path.

Chromium previously failed when launched from the menu because
`/usr/share/applications/chromium.desktop` ran `/usr/bin/chromium` as root,
which aborts without `--no-sandbox`. The image now ships its own desktop entry
that calls `/usr/local/bin/chromium-wrapper.sh`, and the session seeds
`~/.config/mimeapps.list` so http/https links also use it.

## Installing and launching software

Synaptic (menu: System > Synaptic Package Manager) is the store. Search, mark,
Apply, and the package is installed with apt as root. No password prompt, no
polkit dialog: the session already runs as root, and the image ships a
`synaptic.desktop` that calls `/usr/sbin/synaptic` directly. The stock Debian
entry used `synaptic-pkexec`, which failed silently because no polkit daemon was
running.

After installing, the app appears in the KDE menu. If it does not, run
**Refresh Application Menu** (also `/usr/local/bin/refresh-menu`, which runs
`kbuildsycoca6 --noincremental`). The image runs `polkitd` and a system D-Bus at
session start, so privileged GUI tools that use `pkexec` work too.

A package that installs but does not open can be checked the same way an agent
would launch it:

```
kioclient exec /usr/share/applications/<app>.desktop
```

Launch failures then print to the terminal instead of vanishing. Verified on the
deployed image: a fresh `galculator` install opened through the KDE launcher,
and Synaptic opened with its full package list (68,907 packages) and no icon
warnings.

Every fix here lives in the image: the Chromium and Synaptic desktop entries,
the Chromium warning policy, the refresh helper, packages, and the session
script. Runtime-only pieces are the compose-level hostname, memory limit,
`/dev/dri` and the `/root` volume.

## iGPU

`/dev/dri` is passed into the container and the image ships Mesa plus
`intel-media-va-driver`, so `vainfo` reports the Intel iHD driver with H.264
decode/encode. The device is shared with Jellyfin, Immich and Frigate, which is
safe for render nodes.

It does **not** accelerate the remote desktop. TigerVNC presents a software
framebuffer with no GPU-backed GLX, so KWin stays on software and Chromium's GPU
process cannot initialise (`--use-gl=egl` fails with "requested GL
implementation not found"). Chromium therefore runs with `--disable-gpu` for
stability, and the iGPU is useful for headless compute inside the container
(ffmpeg/VA-API), not for the VNC stream. Do not re-add GPU flags to the wrapper
without testing a real browser window.

## Passwordless by design

There is no OS password and no lock screen. `root` has a locked password (`L` in
`passwd -S`, `*` in shadow), there is no SSH or console login, and the session
starts already logged in. Access to the desktop is exactly the Caddy + Tinyauth
passkey gate at `https://os.l3b.cc.cd`; the VNC port is never published.

`start-desktop.sh` writes `kscreenlockerrc` with `Autolock=false` and
`LockOnResume=false` into both `/root/.config` and `/etc/xdg`, and runs
`xset s off -dpms`, so the session cannot lock itself or blank the screen. An
earlier image lacked this and could trap a user at a lock screen that root
could not unlock. Do not re-enable locking unless a real user account with a
password is added first.

## Testing environment (human + agent)

Both drive the same session, so a person can watch or take over while an agent
works:

| Need | Available |
| --- | --- |
| Browser and web app testing | Chromium (wrapper adds `--no-sandbox --disable-dev-shm-usage`) |
| App launcher, files, terminal | KDE launcher, Dolphin, Konsole |
| Agent screenshots | `scrot` via `os shot` |
| Agent input | `xdotool` via `os click/type/key` |
| Window control | `wmctrl`, `xdotool` |
| Clipboard bridge | noVNC clipboard panel, plus `xclip` inside |
| Accessibility tree for agents | `at-spi2-core`, `python3-pyatspi` |
| Build/test runtimes | Node, npm, Python 3, pip, git, curl, wget, jq |
| Everyday CLI | nano, vim-tiny, htop, tree, tmux, ncdu, less, file, lsof |
| Archives and sync | unzip, zip, p7zip-full, xz-utils, rsync |
| Network checks | ping, dig, ip, ss, netstat, curl |
| Desktop helpers | xdg-open, desktop-file-utils, xdg-user-dirs |
| Playwright-style browser automation | Run Playwright inside the container or use the host's `playwright-cli` against an app |

Session applications must be started with the Plasma environment
(`XDG_CURRENT_DESKTOP=KDE KDE_FULL_SESSION=true DISPLAY=:1`) or they render with
the light fallback theme; the `os` helper does this.

## Limits

- One shared desktop: every viewer and the agent see the same screen and clipboard.
- No audio and no GPU acceleration; Chromium uses software rendering.
- Kernel is shared with the host. For untrusted code use a microsandbox, not this.
