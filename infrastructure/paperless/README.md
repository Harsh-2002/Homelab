# Paperless-ngx

Paperless-ngx runs at `https://docs.l3b.cc.cd`, private to LAN and Tailscale.
Portainer owns Stack `paperless` (ID 149) on the `ctr` endpoint (`10.1.1.4`,
endpoint ID 2). The repository's `compose.yaml` is the non-secret source of
truth. The live Stack has three protected variables:
`PAPERLESS_SECRET_KEY`, `PAPERLESS_ADMIN_PASSWORD`, and
`PAPERLESS_OIDC_CLIENT_SECRET`; never commit their values.

## Portainer recovery

1. In Portainer, select the `ctr` environment, then **Stacks → Add stack**.
   Name it `paperless`, select **Web editor**, and paste this repository's
   [`compose.yaml`](compose.yaml) exactly. Do not deploy to any other endpoint.
2. Add the three protected Stack environment variables listed above. The
   original values are in the existing `HomeLab` 1Password items
   `Paperless-ngx` (local password and secret key) and
   `Pocket ID OIDC - paperless` (client secret). Use `scripts/op-sa` on
   `dev` to access the vault without printing secret values to logs. Do not
   change `PAPERLESS_SECRET_KEY` after deployment. The temporary
   `/data/apps/paperless/stack.env` was removed after the vault and
   Portainer copies were verified.
3. Click **Deploy the stack**. The `/data/apps/paperless` directories already
   exist; Compose creates the stack's own default network. The initial image
   pull may take several minutes.
4. Verify both containers and the app. Caddy's private route is enabled.
   Homepage is Git-managed; sync its Argo CD app after adding the card.

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
canonical email `iam.anuragvishwakarma@gmail.com`. Local login was tested
through Caddy and remains the break-glass path. Native Pocket ID OIDC is
configured with client `paperless`, provider ID `pocketid`, exact callback
`https://docs.l3b.cc.cd/accounts/oidc/pocketid/login/callback/`, and
`client_secret_post`. The client permits only Pocket ID group
`infrastructure-admins`; Paperless auto-provisions admitted users and grants
superuser rights when the group claim is present. The login page and its
redirect to Pocket ID were browser-tested. The existing local Paperless user
is explicitly linked to its matching Pocket ID identity (`provider=pocketid`)
using Paperless's Django ORM after verifying the Pocket ID email and
its OIDC subject from Pocket ID v2.16.0. The profile now lists that connected
social account. A transient SQLite backup was made inside the Paperless
container during the change and removed after the profile check. A fresh
passkey-authenticated OIDC login still needs owner verification. Caddy has no
Tinyauth layer because Paperless has native OIDC. Do not deploy this Stack
directly with `docker compose`; that would violate the chosen management
model. The image is pinned to Paperless-ngx `3.2.1` and the broker tracks the
upstream Valkey `9-alpine` template.

Validation after Portainer deploy:

```bash
ssh ctr 'docker ps --filter name=paperless --format "{{.Names}} {{.Status}}"'
ssh ctr 'curl -sS -o /dev/null -w "%{http_code}\n" http://10.1.1.4:8010/'
curl --resolve docs.l3b.cc.cd:443:10.1.1.3 -I https://docs.l3b.cc.cd/
```

Do not enable public DNS for this service. Owner sign-in through Pocket ID,
upload of a sample PDF, OCR/search, download of the original, and an
export/restore procedure remain functional acceptance checks.
