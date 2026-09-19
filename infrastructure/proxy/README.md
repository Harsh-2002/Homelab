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
```
