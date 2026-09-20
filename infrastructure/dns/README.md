# DNS

DNS LXC `10.1.1.2` runs:

- AdGuard Home `v0.107.79` on TCP/UDP 53 and management port 3000.
- Unbound `v1.26.1` on `127.0.0.1:5335` as the recursive upstream.
- HaGeZi Multi PRO and HaGeZi TIF Medium blocklists.

The protected active configuration is `/opt/AdGuardHome/AdGuardHome.yaml`. It is not copied into Git because it contains the administrator password hash and operational state. The safe desired DNS fragments are tracked as `adguard-rewrites.yaml` and `unbound-local.conf`.

Proxy-managed DNS uses one apex A rewrite and one wildcard CNAME rewrite:

| Name | Type | Answer |
| --- | --- | --- |
| `l3b.cc.cd` | A | `10.1.1.3` |
| `*.l3b.cc.cd` | CNAME | `l3b.cc.cd` |

Adding a new Caddy hostname requires only a Caddy route; no additional AdGuard rewrite is required.

Direct-host exceptions use AdGuard CNAME-exception entries that pass through to exact local A records in Unbound:

| Name | Answer |
| --- | --- |
| `dev.l3b.cc.cd` | `10.1.1.5` |
| `k8s.l3b.cc.cd` | `10.1.1.200` |
| `k8s-201.l3b.cc.cd` | `10.1.1.201` |
| `k8s-202.l3b.cc.cd` | `10.1.1.202` |
| `k8s-203.l3b.cc.cd` | `10.1.1.203` |

Do not replace these pass-through entries with exact A rewrites: AdGuard Home v0.107.79 gives the wildcard legacy rewrite precedence. Unbound owns the exception A records.

Validation:

```bash
ssh dns 'dig @127.0.0.1 komodo.l3b.cc.cd A +noall +answer'
ssh dns 'dig @127.0.0.1 k8s.l3b.cc.cd A +noall +answer'
ssh dns 'systemctl is-enabled AdGuardHome unbound; systemctl is-active AdGuardHome unbound'
```

Do not commit the active YAML, administrator hash, temporary reset files, or backups.

`px.l3b.cc.cd` is the load-balanced cluster entry point. Caddy uses the `pve_lb` cookie to keep a browser session on one healthy node, selects another node and replaces the cookie if that backend becomes unavailable, actively checks `/` every 10 seconds, and also performs passive failure handling. The node-specific names remain available for deterministic maintenance access.
