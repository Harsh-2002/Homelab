# Paperless-ngx

Paperless-ngx is planned for `https://docs.l3b.cc.cd`, private to LAN and
Tailscale and guarded by Caddy/Tinyauth. The Portainer Stack must be named
`paperless` on the `ctr` endpoint (`10.1.1.4`, Portainer endpoint ID 2).
The repository's `compose.yaml` is the non-secret source of truth; deploy
it using Portainer Stack variables `PAPERLESS_SECRET_KEY` and
`PAPERLESS_ADMIN_PASSWORD`, never by committing those values.

## Manual Portainer deployment

1. In Portainer, select the `ctr` environment, then **Stacks → Add stack**.
   Name it `paperless`, select **Web editor**, and paste this repository's
   [`compose.yaml`](compose.yaml) exactly. Do not deploy to any other endpoint.
2. Add exactly two Stack environment variables:
   `PAPERLESS_SECRET_KEY` and `PAPERLESS_ADMIN_PASSWORD`. Their generated
   values are already in root-only `/data/apps/paperless/stack.env` on `ctr`.
   Read them in your own terminal with
   `ssh ctr 'sudo cat /data/apps/paperless/stack.env'`; do not paste the
   output into chat or commit it. Both values are required, including the
   admin password. Do not change the secret key after first deployment.
3. Click **Deploy the stack**. No host paths or Docker networks need to be
   created: the `/data/apps/paperless` directories and external `docknet`
   network already exist. The initial image pull may take several minutes.
4. Tell the agent once Portainer shows both containers running. The agent
   will then verify application health, enable the private Caddy route and
   Homepage tile, and complete authentication and backup validation.

The Stack's application port is `10.1.1.4:8010`. Do not create a public
Cloudflare DNS record for `docs.l3b.cc.cd`.

The live layout is `/data/apps/paperless/{data,media,consume,export,valkey}`
on `ctr`'s persistent `/data` disk. SQLite and the search index live in
`data`; originals, archives, and thumbnails live in `media`; Valkey is the
required task broker. Only Paperless port `8010` is published on
`10.1.1.4` for Caddy. Valkey is internal to the Compose network.

Paperless-ngx does **not** document a supported native S3 media backend.
`PAPERLESS_MEDIA_ROOT` is a filesystem directory. Do not put a RustFS bucket
under it using s3fs/rclone/FUSE: Paperless renames and moves files as part
of document management, and an object-store mount does not provide reliable
POSIX semantics. RustFS may later receive a backup/export copy, but the
authoritative live state is both `data` and `media` together. Back up those
directories consistently; copying only the media files is not a restore.

The initial local administrator is `iam-anuragvishwakarma`, with the
canonical email `iam.anuragvishwakarma@gmail.com`. Pocket ID OIDC is a
follow-up: the available Portainer API key is the read-only `homepage` user,
and the `op` CLI on `dev` is not currently authenticated, so an admin-capable
Portainer API key and vault access are needed to finish the Portainer-owned
deployment and store the bootstrap credential. Do not deploy this stack
directly with `docker compose`; that would violate the chosen management
model. The image is pinned to Paperless-ngx `3.2.1` and the broker tracks
the upstream Valkey `9-alpine` template.

Validation after Portainer deploy:

```bash
ssh ctr 'docker ps --filter name=paperless --format "{{.Names}} {{.Status}}"'
ssh ctr 'curl -sS -o /dev/null -w "%{http_code}\n" http://10.1.1.4:8010/'
curl --resolve docs.l3b.cc.cd:443:10.1.1.3 -I https://docs.l3b.cc.cd/
```

Do not enable public DNS for this service. Test login, upload of a sample
PDF, OCR/search, download of the original, and an export/restore procedure
before considering it fully operational.
