# Caddy proxy

The tracked `Caddyfile` is the desired configuration for proxy LXC `10.1.1.3`.

`store.l3b.cc.cd` is a deliberately public static Astro storefront served by Caddy directly from `/srv/store`; it has no container or authentication gate. Build source is `git@github.com:Harsh-2002/store.git`, not this infrastructure repo. Rebuild with `npm ci && npm run build`, copy the generated `dist/` contents into `/srv/store` on `proxy` (owned by `root:caddy`, directories `0750`, files `0640`), and verify the public URL and static assets. Its browser enquiry form posts to Orva; never submit a real enquiry as a deployment smoke test. Public Cloudflare has a DNS-only `store` A record at `150.129.31.154`; internal DNS resolves the same name to proxy `10.1.1.3` via the Unbound exception. This hostname no longer denotes the PBS VM, though the `store` SSH alias still targets `10.1.1.12`.

The static site was rebuilt from source commit `a370a33300e7495960fbee88e63812617f413214` on 2026-09-24 and verified through the public URL. This source revision also includes an Orva handler change; the static redeploy did not deploy or validate that backend.

Secrets are not stored in Git. The proxy loads `/etc/caddy/cloudflare.env` through the systemd drop-in `/etc/systemd/system/caddy.service.d/10-cloudflare-env.conf`. This protected file contains the Cloudflare values and `FRIGATE_PROXY_AUTH_SECRET`; the latter must match the Frigate Stack environment exactly.

The minimal `cf` CLI is tracked at `scripts/cf` and installed on `dev` as `/usr/local/bin/cf`. It reads `CF_API_TOKEN` and `CF_ZONE` from the environment, or from `CF_ENV_FILE` (default `/etc/caddy/cloudflare.env`). The default cache is `~/.cf-zone-id`; override it with `CF_CACHE_FILE`. Keep `CF_ZONE=l3b.cc.cd` alongside the existing Cloudflare token in `/etc/caddy/cloudflare.env` so Caddy and `cf` use one non-Git configuration path.

Deploy and validate:

```bash
scp infrastructure/proxy/Caddyfile proxy:/etc/caddy/Caddyfile.new
ssh proxy 'set -a; . /etc/caddy/cloudflare.env; set +a; caddy validate --config /etc/caddy/Caddyfile.new --adapter caddyfile'
ssh proxy 'install -o root -g caddy -m 0640 /etc/caddy/Caddyfile.new /etc/caddy/Caddyfile && rm /etc/caddy/Caddyfile.new && systemctl reload caddy'
```

A Caddyfile-only change needs a reload. Any change to `/etc/caddy/cloudflare.env` needs `systemctl restart caddy`, because a reload does not rebuild the service process environment. Verify only that the Frigate key is present without printing it:

```bash
ssh proxy 'caddy_pid=$(pidof caddy); tr "\0" "\n" < /proc/$caddy_pid/environ | grep -q "^FRIGATE_PROXY_AUTH_SECRET="'
```

Post-deployment checks:

```bash
ssh proxy 'systemctl is-enabled caddy; systemctl is-active caddy'
curl --resolve argocd.l3b.cc.cd:443:10.1.1.3 https://argocd.l3b.cc.cd/
curl --resolve portainer.l3b.cc.cd:443:10.1.1.3 https://portainer.l3b.cc.cd/api/status
curl --resolve s3.l3b.cc.cd:443:10.1.1.3 https://s3.l3b.cc.cd/health/ready
curl --resolve rustfs.l3b.cc.cd:443:10.1.1.3 https://rustfs.l3b.cc.cd/rustfs/admin/v3/oidc/providers
curl --resolve beszel.l3b.cc.cd:443:10.1.1.3 https://beszel.l3b.cc.cd/api/health
curl --resolve l3b.cc.cd:443:10.1.1.3 https://l3b.cc.cd/
curl --resolve frigate.l3b.cc.cd:443:10.1.1.3 -I https://frigate.l3b.cc.cd/
curl --resolve cairn.l3b.cc.cd:443:10.1.1.3 https://cairn.l3b.cc.cd/
curl --resolve cairn-s3.l3b.cc.cd:443:10.1.1.3 https://cairn-s3.l3b.cc.cd/
curl --resolve n8n.l3b.cc.cd:443:10.1.1.3 https://n8n.l3b.cc.cd/
curl --resolve drive.l3b.cc.cd:443:10.1.1.3 https://drive.l3b.cc.cd/healthz
curl --resolve docs.l3b.cc.cd:443:10.1.1.3 -I https://docs.l3b.cc.cd/
curl --resolve media.l3b.cc.cd:443:10.1.1.3 -I https://media.l3b.cc.cd/
curl --resolve downloads.l3b.cc.cd:443:10.1.1.3 https://downloads.l3b.cc.cd/healthz
curl --resolve orva.l3b.cc.cd:443:10.1.1.3 -I https://orva.l3b.cc.cd/
curl -i https://registry.l3b.cc.cd/v2/
```

## Private identity flow

Caddy admits only LAN `10.1.1.0/24` and Tailscale `100.64.0.0/10` sources. Pocket ID at `auth.l3b.cc.cd` and Tinyauth at `login.l3b.cc.cd` are subject to the same policy, so remote authentication requires Tailscale.

AdGuard Home, Longhorn, Homepage, Frigate, and Uptime Kuma import the reusable `authenticate` block. Caddy calls Tinyauth at `10.1.1.6:3000/api/auth/caddy` before a protected request reaches its backend. Frigate additionally receives a shared proxy-secret header and a fixed identity/group after that gate succeeds: it has one exact Pocket ID allowlisted user, so this guarantees a stable Frigate admin identity even when its proxy-auth UI mishandles forwarded identity headers. Headlamp, Argo CD, Proxmox, PBS, Beszel, Immich, OpenCloud, Portainer, Cairn, Orva, and n8n use their own application authentication flows instead. n8n remains private-network-only and uses its native login with MFA. OpenCloud is private-network-only at `https://drive.l3b.cc.cd`; Tinyauth is deliberately absent so its web, desktop, iOS, Android, WebDAV, and public-share flows reach native OIDC directly. Immich and Orva are deliberate public DNS exceptions at `photos.l3b.cc.cd` and `orva.l3b.cc.cd`; Caddy forwards them without Tinyauth so their native APIs and authentication work normally. Portainer is private-network-only at `https://portainer.l3b.cc.cd` and keeps its own authenticated session plus reverse-proxy trusted-origin policy. Cairn's console and S3 API are private-network-only; the S3 route deliberately avoids Tinyauth so signed S3 clients continue to work.

Motrix is private-network-only at `https://downloads.l3b.cc.cd`. Caddy sends `/mdxp` and its subpaths to the MDXP upstream on `ctr:16801`, and everything else to the Web UI/API on `ctr:8080`. Motrix uses its own operator token and device pairing, so this route does not import Tinyauth. `MOTRIX_PUBLIC_URL` must match the HTTPS browser origin exactly; see `infrastructure/motrix/README.md`.

Jellyfin at `media.l3b.cc.cd` is a deliberate public DNS-only exception. It
uses its own application login; Caddy does not put Tinyauth in front of
streaming clients. Its upstream is `10.1.1.4:8096` on `ctr`.

Paperless-ngx at `docs.l3b.cc.cd` is private-network-only and uses its own
Pocket ID OIDC login; its Caddy route does not import Tinyauth.

## Public Docker Registry

`registry.l3b.cc.cd` is an explicit public DNS-only Cloudflare record. It intentionally bypasses the private-source and Tinyauth handlers because Docker uses the Registry's retained Basic authentication credentials. Caddy terminates TLS and does not response-compress the Registry route. The unauthenticated `/v2/` endpoint must return `401` with `Docker-Distribution-Api-Version: registry/2.0`.

RustFS is private-network-only as well: `s3.l3b.cc.cd` serves its S3 API and `rustfs.l3b.cc.cd` its native OIDC-capable console. The API route deliberately does not use response compression, which avoids altering object-transfer semantics or signed S3 responses. Neither hostname is publicly exposed by DNS; making the API public requires an explicit later decision and a hostname-specific Cloudflare A record.

`cairn-s3.l3b.cc.cd` is an explicit public DNS-only Cloudflare record pointing to `150.129.31.154`. Caddy forwards the Cairn S3 API to `10.1.1.8:7373` without the private-source gate or response compression so signed S3 requests work. Cairn's own S3 authentication and bucket policies remain in force. `cairn.l3b.cc.cd` is still private-network-only and has no public DNS exception; a public-IP test returned 403. Do not confuse Cairn's public API with the separate private RustFS API. The temporary `share` hostname and object route were removed.

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
