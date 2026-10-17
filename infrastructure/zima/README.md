# ZimaOS

**Superseded October18 IST:** VM108/address10.1.1.14 now belong to a new owner-created Supabase VM, not ZimaOS. The old Zima Caddy handler has been removed/replaced with private Supabase8000. Do not run historical origin commands below against the new service or restore the orphaned ISO-backed Zima disk. See `../supabase/README.md`.

**Removed by owner, reported October 18 IST:** VM 108 and its data were deleted. Verified that the VM configuration and PX30 local-ZFS volumes for VM 108 are absent. Do not restore/recreate it during ISO storage recovery. Historical endpoint details below are not evidence of a live service; proxy/DNS cleanup has not been verified in this change.

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
