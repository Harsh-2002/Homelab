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

## Disk cleanup, 2026-10-28

Owner requested cleanup of this dev node, especially project folders. Root
filesystem use dropped from 84% to 50%: 84,054,851,584 bytes used before and
49,621,848,064 after, reclaiming **32.07 GiB** physically according to df.
Available space rose from 17,076,056,064 to 51,509,059,584 bytes (about48GiB).
These are dated measurements, not current monitoring values.

Removed only regenerable build/cache material and old archived system journals:

- Cairn dev-profile build artifacts under /home/dev/Cairn/target; Cargo reported
  16,534 files /25.8GiB logical artifact size. The project folder fell from
  about26GiB to1.2GiB. The release profile was retained.
- Dev-profile artifacts in /var/tmp/cairn-wt/target; Cargo reported8,324 files
  /3.7GiB logical artifact size. This path contained generated output, not a
  registered Git worktree or source checkout.
- Go build cache, npm download cache and APT package archives. npm's _npx
  packages and all project node_modules were preserved.
- Archived systemd journals vacuumed to512MiB; observed total afterward464MiB.
  This was a one-off vacuum, not a new persistent retention policy.

Before cleanup, no Cargo/rustc/Go build process or executable from Cairn target
was active. Both Cargo deletions were previewed with --dry-run and scoped with
explicit --target-dir and --profile dev. Used --frozen to avoid dependency or
lockfile changes. All retained release-file inodes/sizes and six checked
repositories' Git worktree statuses matched before/after. Existing untracked
Cairn research notes and Nivra reports/research files were preserved.

The active Nivra .next output, all project dependencies, databases, uploads,
rollback/recovery material, agent conversations/authentication, Git branches and
Docker containers/images/volumes were left in place. OpenCode and both Hermes
services remained active; no service restart or infrastructure topology change.
No application build was rerun because that would recreate the removed cache.
The next debug/Go build will regenerate its required artifacts.

For a future cleanup, inspect disk usage and process/build activity again; do
not schedule blind deletions of active development outputs. Native commands used:

```bash
cargo clean --manifest-path /home/dev/Cairn/Cargo.toml \
  --target-dir /home/dev/Cairn/target --profile dev --frozen --dry-run
cargo clean --manifest-path /home/dev/Cairn/Cargo.toml \
  --target-dir /home/dev/Cairn/target --profile dev --frozen
cargo clean --manifest-path /home/dev/Cairn/Cargo.toml \
  --target-dir /var/tmp/cairn-wt/target --profile dev --frozen --dry-run
cargo clean --manifest-path /home/dev/Cairn/Cargo.toml \
  --target-dir /var/tmp/cairn-wt/target --profile dev --frozen
go clean -cache
npm cache clean --force
sudo apt-get clean
sudo journalctl --vacuum-size=512M
```

Review paths before running these again. There was no source, application or
agent configuration change, so architecture diagrams and integration settings
did not require modification.
