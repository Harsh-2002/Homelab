# Dev VM disk maintenance

Public development URL: `https://dev.l3b.cc.cd`, via existing Caddy to `10.1.1.5:3000`. The owner requested public exposure on 2026-10-05 and manages the backend application. Bind the dev server to `0.0.0.0:3000` and allow this hostname where its framework requires it. Internal DNS points this hostname to Caddy, not directly to the VM; SSH alias `dev` still uses `10.1.1.5`.

`dev` is VM 100 at `10.1.1.5`. Its ext4 root disk is 99 GiB. On 2026-09-29 it reached 72% usage (68 GiB used). A read-only audit found 33 GiB in `/var/lib/containerd`, mostly Docker BuildKit cache from Orva builds, and 8 GiB in `/home/dev/.cache/go-build`. The Homelab repo was only 14 MiB; Cairn, Hermes, Codex, and Orva project/state directories were not cleanup targets.

The safe cleanup was:

```bash
docker system df
docker builder prune --all --force --filter until=72h
go env GOCACHE
go clean -cache
df -hT /
```

It reclaimed about 16 GiB and reduced root usage to 56% (52 GiB used, 43 GiB free). Docker still had about 19 GiB of more recent reclaimable build cache, deliberately retained for active development. The cleanup did not remove running containers, images in use, Docker volumes, source trees, agent state, or application databases. Future builds may recompile/re-download cached layers. If space rises again, measure `docker system df` and `du` before pruning; do not delete `/var/lib/containerd` directly or use `docker system prune --volumes`.
