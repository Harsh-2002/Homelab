# Caddy proxy

The tracked `Caddyfile` is the desired configuration for proxy LXC `10.1.1.3`.

The Cloudflare token is not stored in Git. The proxy loads it from `/etc/caddy/cloudflare.env` through the systemd drop-in `/etc/systemd/system/caddy.service.d/10-cloudflare-env.conf`.

The minimal `cf` CLI is tracked at `scripts/cf` and installed on `dev` as `/usr/local/bin/cf`. It reads `CF_API_TOKEN` and `CF_ZONE` from the environment, or from `CF_ENV_FILE` (default `/etc/caddy/cloudflare.env`). The default cache is `~/.cf-zone-id`; override it with `CF_CACHE_FILE`. Keep `CF_ZONE=l3b.cc.cd` alongside the existing Cloudflare token in `/etc/caddy/cloudflare.env` so Caddy and `cf` use one non-Git configuration path.

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
curl --resolve portainer.l3b.cc.cd:443:10.1.1.3 https://portainer.l3b.cc.cd/api/status
curl --resolve minio.l3b.cc.cd:443:10.1.1.3 https://minio.l3b.cc.cd/minio/health/live
curl --resolve beszel.l3b.cc.cd:443:10.1.1.3 https://beszel.l3b.cc.cd/api/health
curl --resolve l3b.cc.cd:443:10.1.1.3 https://l3b.cc.cd/
```

## Private identity flow

Caddy admits only LAN `10.1.1.0/24` and Tailscale `100.64.0.0/10` sources. Pocket ID at `auth.l3b.cc.cd` and Tinyauth at `login.l3b.cc.cd` are subject to the same policy, so remote authentication requires Tailscale.

AdGuard Home, Longhorn, and the Homepage portal at `l3b.cc.cd` import the reusable `authenticate` block. Caddy calls Tinyauth at `10.1.1.6:3000/api/auth/caddy`; successful sessions return identity headers before the request reaches the backend. Headlamp, Argo CD, Proxmox, Komodo, Beszel, Immich, and Portainer use their own application authentication flows instead. Immich is private-network-only at `https://photos.l3b.cc.cd`; its API is not placed behind Tinyauth so the native web and mobile clients can authenticate normally. Portainer is private-network-only at `https://portainer.l3b.cc.cd` and keeps its own authenticated session plus reverse-proxy trusted-origin policy.

MinIO is also private-network-only: `minio.l3b.cc.cd` serves the S3 API and `minio-console.l3b.cc.cd` serves the native console. Caddy handles WebSocket upgrades and immediate streaming for the console; MinIO's `MINIO_BROWSER_REDIRECT_URL` must remain the console hostname.

Expected unauthenticated behavior:

```text
browser request: 302 to login.l3b.cc.cd
non-browser request: 401 with x-tinyauth-location
```

Do not expose a protected application publicly while leaving its Pocket ID or Tinyauth callback private. The current design intentionally keeps all three parts private and uses Tailscale outside the LAN.

## Argo CD GitHub webhook

Only `POST https://argocd.l3b.cc.cd/api/webhook` is public. Caddy limits its request body to 1 MiB and proxies it to Argo CD without the shared private-source or browser-auth handlers. Every other Argo CD path remains LAN/Tailscale-only.

The endpoint is authenticated by GitHub's HMAC signature. Its secret is held in the separate Kubernetes Secret `argocd-github-webhook`, labelled as an Argo CD secret, and referenced by `argocd-secret` as `$argocd-github-webhook:secret`; the actual value is stored in 1Password and never committed. Argo CD's `webhook.maxPayloadSizeMB` is set to `1`.

GitHub webhook configuration:

```text
Payload URL: https://argocd.l3b.cc.cd/api/webhook
Content type: application/json
Events: Pushes only
```

Cloudflare public DNS has an explicit DNS-only A record for `argocd.l3b.cc.cd` so GitHub can reach this webhook. The apex and wildcard remain private by default. This record does not make the Argo CD UI public: Caddy still rejects every path except the signed webhook POST.

## Apple iCloud Private Relay

Do not add Apple Private Relay address ranges to Caddy's private-source allowlist. Relay addresses are temporary, rotate between sessions, and are shared with other Private Relay customers. Allowing an Apple relay range would therefore grant access based on service membership rather than household identity.

For private services, use one of these paths:

- on the trusted home Wi-Fi, disable **Limit IP Address Tracking** for that network so Safari uses the household connection
- use Tailscale and keep `100.64.0.0/10` in the private policy
- temporarily choose **Reload and Show IP Address** for a specific site when appropriate

Keep the existing LAN, Tailscale, and explicitly trusted household WAN/hairpin sources as the access boundary. Do not treat an observed Private Relay address as static.
