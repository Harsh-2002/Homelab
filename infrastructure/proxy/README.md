# Caddy proxy

The tracked `Caddyfile` is the desired configuration for proxy LXC `10.1.1.3`.

The Cloudflare token is not stored in Git. The proxy loads it from `/etc/caddy/cloudflare.env` through the systemd drop-in `/etc/systemd/system/caddy.service.d/10-cloudflare-env.conf`.

Deploy and validate:

```bash
scp infrastructure/proxy/Caddyfile proxy:/etc/caddy/Caddyfile.new
ssh proxy 'set -a; . /etc/caddy/cloudflare.env; set +a; caddy validate --config /etc/caddy/Caddyfile.new --adapter caddyfile'
ssh proxy 'install -o root -g caddy -m 0640 /etc/caddy/Caddyfile.new /etc/caddy/Caddyfile && rm /etc/caddy/Caddyfile.new && systemctl reload caddy'
```

Post-deployment checks:

```bash
ssh proxy 'systemctl is-enabled caddy; systemctl is-active caddy'
curl --resolve argocd.l3b.cc.cd:443:10.1.1.3 https://argocd.l3b.cc.cd/
curl --resolve komodo.l3b.cc.cd:443:10.1.1.3 https://komodo.l3b.cc.cd/
```

## Apple iCloud Private Relay

Do not add Apple Private Relay address ranges to Caddy's private-source allowlist. Relay addresses are temporary, rotate between sessions, and are shared with other Private Relay customers. Allowing an Apple relay range would therefore grant access based on service membership rather than household identity.

For private services, use one of these paths:

- on the trusted home Wi-Fi, disable **Limit IP Address Tracking** for that network so Safari uses the household connection
- use Tailscale and keep `100.64.0.0/10` in the private policy
- temporarily choose **Reload and Show IP Address** for a specific site when appropriate

Keep the existing LAN, Tailscale, and explicitly trusted household WAN/hairpin sources as the access boundary. Do not treat an observed Private Relay address as static.
