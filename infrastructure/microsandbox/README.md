# microsandbox

Host-wide microVM runtime for running untrusted or throwaway workloads on
`l3b`. Each sandbox is a real Linux VM with its own kernel (libkrun + KVM), not
a container sharing the host kernel.

Installed 2026-11-03 as a **global host tool**, not a service and not a Docker
stack. Version **0.7.13**, Apache-2.0.

## Why it is on the host

Coding agents run tools, install packages and execute generated code with more
ambient access than they should have. microsandbox gives that work a VM
boundary with an explicit filesystem, network and secret policy, without a
daemon, root or a second orchestrator.

It is deliberately **not** a Docker replacement: no compose, restart policies,
healthchecks, Caddy service-name routing or Portainer. All existing services
stay on Docker.

## Installation layout

```text
/opt/microsandbox/bin/msb                 0.7.13 binary (root:root 0755)
/opt/microsandbox/lib/libkrunfw.so.5.6.1  guest kernel loader
/opt/microsandbox/VERSION                 pinned version string
/usr/local/bin/msb                        symlink into PATH
```

`msb` resolves `libkrunfw` through its `$ORIGIN/../lib` RUNPATH, so the symlink
is safe. Runtime state is **per user** in `~/.microsandbox` (or `$MSB_HOME`);
there is no shared writable state directory.

The release tarball and `checksums.sha256` come from
`github.com/superradcompany/microsandbox` releases. Verify before installing —
the 0.7.13 x86_64 tarball is
`c41aeefc050e97f42cd55ce55cc139efc13c6ee2dc371e8d30c325a305a5c3b1`.

Requirements: x86_64 Linux with `/dev/kvm`; the invoking user must be in the
`kvm` group. `dev` already is (gid 993).

## Verification

```sh
msb --version
msb doctor
msb run --no-tty debian -- uname -r
```

`msb doctor` must report `Host setup is ready`, KVM read/write and the
`libkrunfw` path under `/opt/microsandbox`. A harmless warning about Intel
APICv being disabled by KVM policy is expected on this host; it does not affect
correctness or isolation and the fix requires unloading KVM for every guest, so
it is intentionally left alone.

## Security defaults

- Public internet is allowed; **private networks, the host, loopback,
  link-local and cloud metadata are blocked** unless explicitly reopened.
- Inbound traffic requires a published port.
- `--no-net` removes network access entirely.
- `--secret ENV@HOST` gives the guest a placeholder; the host substitutes the
  real value only on HTTPS requests to the named hosts. Never pass secrets
  with `-e`.
- Do not mount `~/.ssh`, `~/.config`, `~/.aws` or other credential paths into
  untrusted workloads.

## Common commands

```sh
msb run debian -- sh                        # ephemeral, deleted on exit
msb run --no-net python -- python -c '...'  # no network at all
msb create --name dev debian                # persistent (image is positional)
msb exec dev -- apt-get update              # sandbox name is positional
msb stop dev
msb rm dev
msb ls
```

`msb create` refuses no image argument, and `msb rm` refuses a running sandbox —
stop it first, or pass `--force`. The sandbox name is positional on `exec`,
`stop`, `rm`, `logs`, `metrics` and `inspect`; there is no `--name` flag on
those subcommands.

## Agent skill

The official skill is installed once and shared:

```text
~/.agents/skills/microsandbox/                 canonical copy (SKILL.md + references)
~/.claude/skills/microsandbox -> ...           Claude Code
~/.hermes/skills/microsandbox -> ...           Hermes
```

OpenCode reads `~/.agents/skills` directly through the `skills` array in
`~/.config/opencode/opencode.json`, so it needs no extra link. Codex CLI is
absent on this host.

Source: `github.com/superradcompany/skills`, directory `microsandbox`. The skill
teaches agents the CLI, the security model and the SDK references.

Verify with `hermes skills list | grep microsandbox` and by confirming OpenCode
lists `microsandbox` in its available skills.

## Upgrading

1. Download the new `microsandbox-linux-x86_64.tar.gz` and `checksums.sha256`
   from the release page; verify the checksum.
2. Install over the existing files:

   ```sh
   sudo install -m 0755 msb /opt/microsandbox/bin/msb
   sudo install -m 0644 libkrunfw.so.* /opt/microsandbox/lib/
   echo vX.Y.Z | sudo tee /opt/microsandbox/VERSION
   ```

3. Run `msb doctor` and one ephemeral sandbox as `dev`.
4. Refresh the shared skill from the upstream repo if `SKILL.md` changed.
5. Update this runbook, the host table, Notion and OpenViking; commit and push.

## Agent test policy

All agents are told to use `msb` for tests that would otherwise mutate the host,
with a fixed default shape:

```sh
msb create --name <task>-test --cpus 2 --memory 4G --root-disk 20G <image>
msb exec <task>-test -- <command>
msb rm <task>-test
```

- Size to the test; 2 vCPU / 4 GB / 20 GB is the default, raise only when needed.
- Install test dependencies inside the sandbox, never on the host.
- Delete the sandbox when the work is finished; idle boxes are not acceptable.
- `--no-net` when the test does not need the network.
- Sandboxes are disposable and are never used for production services.

This policy is in `~/.config/opencode/AGENTS.md` and `~/.claude/CLAUDE.md`, so it
applies to new turns without repeating it per session.

## Limits

- Requires KVM; unusable inside a container without nested virtualisation.
- One host, no scheduler or cluster: concurrency is bounded by RAM and vCPUs
  (6 vCPU / 31 GB here). The default guest is 1 vCPU; pin `--cpus`/`--memory`
  for anything long-running.
- Per-user state is not backed up; sandboxes are treated as disposable.
- Not used by any production service; it exists for agent and untrusted-code
  workloads only.
