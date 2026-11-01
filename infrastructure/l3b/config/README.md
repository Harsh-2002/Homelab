# Non-secret l3b configuration reference

Captured from the running node on **2 November 2026**, without changing the
host. See [manifest.json](manifest.json) for the exact source allowlist, original
owner/mode and SHA-256 of every snapshot. The `etc/` subtree mirrors the selected
absolute source paths. Nothing in this directory automatically deploys itself.

The `/etc/hosts` snapshot/hash was refreshed after Homepage deployment corrected
the apex hostname from loopback to the node's existing LAN address. This allows
the host itself to reach the private HTTPS dashboard; the host listener remains
LAN-only. WireGuard profiles and DNS were not changed.

Read the [current agent handoff](../HANDOFF-2026-11-02.md) before using these
files. The complete [baseline handoff](../HANDOFF-2026-11-01.md) explains the
original decisions; live snapshots can reflect later authorized changes by the
separate restoration workflow.

## Included

- Interface/static LAN setup, current resolver, local host names, persistent
  filesystem/swap mounts.
- Setup-owned SSH and sudo policy, targeted sysctls and CPU/THP service.
- Docker daemon configuration, storage dependency and WireGuard reconciliation
  hook; WireGuard unit boot ordering.
- Shared toolchain environment fragment, no-resume policy and custom MOTD.
- Setup-owned Backports/Claude APT entries.
- Only the three menu settings from /etc/default/grub, as an intentional
  **fragment**, not a complete replacement file.

The source modes in the manifest describe the live files. Repository snapshots
are non-secret readable text. Restore the proper live ownership/mode when an
authorized deployment calls for it; for example sudoers must retain its strict
permissions. Compare first rather than blindly copying the full tree to /.
Network, fstab and SSH changes require particular care on a remotely managed
node. This request authorized documentation capture, not reapplication.

## Excluded deliberately

- The live WireGuard directory, all private/preshared keys, retained client
  profiles and private manager JSON.
- SSH identity/authorized-key contents, OAuth/session stores, API/service-account
  tokens, 1Password authentication material, credential files and shell history.
- Raw agent configuration that may contain resolved credentials, complete
  environment files and runtime application data.
- Existing external backup data and unrelated restoration files.

Key-free WireGuard [server](../wireguard/wg0.conf.example) and
[client](../wireguard/client.conf.example) examples show the structure. They are
documentation with placeholders, not deployable secret-bearing files. The
profile manager generates real identities locally. Source scripts alone cannot
recover an existing server's private identity; see the recovery boundary in the
handoff.

## Reinstalling the WireGuard scripts

The following reproduces program placement only, from the repository root:

```bash
sudo install -d -m 755 /usr/local/libexec
sudo install -o root -g root -m 755 infrastructure/l3b/wireguard/manager.py /usr/local/libexec/l3b-wg-manager
sudo install -o root -g root -m 755 infrastructure/l3b/wireguard/firewall.sh /usr/local/libexec/l3b-wg-firewall
sudo install -o root -g root -m 755 infrastructure/l3b/wireguard/wg.sh /usr/local/bin/wg.sh
```

Those commands do not initialize, replace or restore private state, change
firewall rules, create profiles or restart services. On the existing node the
installed scripts already match these files; no reinstall is required. A fresh
deployment also needs the Debian wireguard-tools package, reviewed unit/drop-in
placement, forwarding, router/DNS configuration and deliberate identity setup
described in the [WireGuard runbook](../wireguard/README.md).
