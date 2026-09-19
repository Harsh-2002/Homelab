# DNS

DNS LXC `10.1.1.2` runs:

- AdGuard Home `v0.107.79` on TCP/UDP 53 and management port 3000.
- Unbound `v1.26.1` on `127.0.0.1:5335` as the recursive upstream.
- HaGeZi Multi PRO and HaGeZi TIF Medium blocklists.

The protected active configuration is `/opt/AdGuardHome/AdGuardHome.yaml`. It is not copied into Git because it contains the administrator password hash and operational state.

Required local rewrites for the proxy-managed services:

| Name | Answer | Backend through Caddy |
| --- | --- | --- |
| `dns.l3b.cc.cd` | `10.1.1.3` | `10.1.1.2:3000` |
| `argocd.l3b.cc.cd` | `10.1.1.3` | `10.1.1.171:80` |
| `px.l3b.cc.cd` | `10.1.1.3` | Healthy Proxmox nodes on `:8006` |
| `px10.l3b.cc.cd` | `10.1.1.3` | `10.1.1.10:8006` |
| `px20.l3b.cc.cd` | `10.1.1.3` | `10.1.1.20:8006` |
| `px30.l3b.cc.cd` | `10.1.1.3` | `10.1.1.30:8006` |

Validation:

```bash
ssh dns 'getent ahostsv4 argocd.l3b.cc.cd'
ssh dns 'systemctl is-enabled AdGuardHome unbound; systemctl is-active AdGuardHome unbound'
```

Do not commit the active YAML, administrator hash, temporary reset files, or backups.

`px.l3b.cc.cd` is the load-balanced cluster entry point. Caddy actively checks `/` every 10 seconds, excludes unhealthy backends, and also performs passive failure handling. The node-specific names remain available for deterministic maintenance access.
