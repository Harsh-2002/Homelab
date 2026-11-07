# Custom Caddy binary

The `caddy` container does not run the stock binary. A custom build with two
plugins is bind-mounted over `/usr/bin/caddy`:

| Mount | Purpose |
| --- | --- |
| `/data/apps/caddy/caddy` → `/usr/bin/caddy` | custom binary (Caddy core + plugins) |
| `/data/apps/caddy/Caddyfile` → `/etc/caddy/Caddyfile` | configuration |
| `/data/apps/caddy/data`, `/config` | certificates and runtime state |

Plugins (versions pinned to the tested combination):

- `github.com/mholt/caddy-l4@v0.1.2` — layer 4 listeners
- `github.com/caddy-dns/cloudflare@v0.2.4` — DNS-01 for the wildcard certificate

Because the binary lives outside the image, **Watchtower and image bumps do not
update Caddy**. The Portainer stack (`proxy`, stack 171) pins the stock base image
by digest only to supply the runtime; upgrades are a binary rebuild.

## Rebuild and replace (used 7 November 2026: 2.11.4 → 2.11.9)

1. Back up: the current binary, the Caddyfile, and `data`/`config` to `/BACKUP`.
2. Build with the official builder image on the `l3b` network (the default Docker
   bridge is disabled on this host, so a plain `docker run` has no network):

   ```bash
   mkdir -p /tmp/caddy-build && cd /tmp/caddy-build
   docker run --rm --network l3b -v /tmp/caddy-build:/out caddy:<version>-builder sh -c '
     xcaddy build v<version> \
       --with github.com/mholt/caddy-l4@v0.1.2 \
       --with github.com/caddy-dns/cloudflare@v0.2.4 \
       --output /out/caddy'
   ```

3. Check the result: `./caddy version` and
   `./caddy list-modules --versions | grep -E 'layer4|cloudflare'`.
4. Validate the live Caddyfile with the new binary in a throwaway container, using
   the running container's env (never print it):

   ```bash
   docker inspect caddy --format '{{range .Config.Env}}{{println .}}{{end}}' \
     | grep -vE '^(PATH|XDG_|CADDY_VERSION)=' > /tmp/caddy.env   # umask 077
   docker run --rm --network l3b --env-file /tmp/caddy.env \
     -v /tmp/caddy-build/caddy:/usr/bin/caddy:ro \
     -v /data/apps/caddy/Caddyfile:/etc/caddy/Caddyfile:ro \
     -v /data/apps/caddy/data:/data -v /data/apps/caddy/config:/config \
     --entrypoint caddy caddy:<running-stock-tag> \
     validate --config /etc/caddy/Caddyfile --adapter caddyfile
   rm -f /tmp/caddy.env
   ```

5. `install -m 0755 -o root -g docker` the new binary to
   `/data/apps/caddy/caddy` (via a temp name and `mv`), then
   `docker restart caddy`.
6. Verify every public and private site (`401`/`302` from auth gates are expected),
   the wildcard certificate dates, and zero `"level":"error"` log lines.
7. **Roll back** by copying the saved binary back and restarting the container.

Read the release notes for breaking changes first. 2.11.6 added idle read/write
timeouts and 2.11.8/2.11.9 changed FastCGI behaviour; neither affected this
configuration.
