# ZimaOS

ZimaOS is assigned `10.1.1.14` on the homelab LAN. Its web gateway listens on HTTP port 80. The existing Caddy proxy exposes the UI privately at `https://zima.l3b.cc.cd` and forwards requests to `10.1.1.14:80`.

The hostname uses the existing wildcard DNS record, which resolves through Caddy at `10.1.1.3`, and the existing wildcard TLS certificate. The Caddy handler applies the standard LAN/Tailscale source restriction. ZimaOS keeps its own authentication; no additional proxy, OIDC provider, or Tinyauth layer was added. The Caddy-to-ZimaOS hop is plain HTTP on the trusted LAN. Do not publish an explicit public DNS record or expose port 80 directly.

The IP `.14` was formerly assigned to the deleted Coolify VM and was reassigned after confirming ZimaOS responds there. The router DHCP pool/reservation was not verified; reserve `.14` or exclude it from DHCP to prevent a future address conflict.

Validate the origin and proxy routes:

```sh
curl -fsS -H 'Host: zima.l3b.cc.cd' http://10.1.1.14/
curl -fsS https://zima.l3b.cc.cd/
getent ahostsv4 zima.l3b.cc.cd
```

The final command should resolve the hostname to Caddy `10.1.1.3` inside the homelab.
