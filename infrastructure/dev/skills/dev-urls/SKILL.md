---
name: dev-urls
description: Run a local development server, preview or microsandbox service and reach it over HTTPS. Three fixed URLs (dev, preview, sandbox) map to fixed host ports. Use when you start a web app, dev server or sandboxed service the owner wants to open in a browser.
---

# Development URLs

Three private HTTPS URLs proxy to fixed ports on this host. Pick whichever fits;
you do not need to ask. Run `devurl` (in `Homelab/scripts`) to see which are free.

| URL | Host port | Use |
|---|---|---|
| https://dev.l3b.cc.cd | 4100 | Primary dev server |
| https://preview.l3b.cc.cd | 4200 | Showing a build or a second app |
| https://sandbox.l3b.cc.cd | 4300 | Services running in a microsandbox VM, or throwaway experiments |

## Rules

1. Check the port is free first (`devurl` or `ss -ltn 'sport = :4100'`). If in use,
   choose another URL; never kill someone else's process to take a port.
2. Bind the server to `0.0.0.0` or `10.1.3.1`, never only `127.0.0.1`. Caddy runs in
   Docker and reaches the host on `10.1.3.1`; loopback is unreachable.
   Examples: `vite --host 0.0.0.0 --port 4100`, `next dev -H 0.0.0.0 -p 4100`,
   `python3 -m http.server 4100 --bind 0.0.0.0`.
3. Hostname checks: Vite needs `server.allowedHosts: ['dev.l3b.cc.cd']` (or `true`);
   Next/Webpack dev servers may need the host allowed likewise. WebSockets/HMR work.
4. Microsandbox: publish the guest port on the host gateway, then run the service
   inside: `msb create --name X ... -p 10.1.3.1:4300:<guest-port> <image>`.
   Delete the sandbox when finished.
5. These URLs are private: LAN and WireGuard only, no login added. Do not put
   secrets or production data behind them. Stop the server when done.
6. A `502` means nothing is listening on the mapped port yet.
7. Do not add other hostnames, ports or Caddy routes. The mapping is fixed;
   adding new ones needs the owner (Homelab `infrastructure/dev/README.md`).
