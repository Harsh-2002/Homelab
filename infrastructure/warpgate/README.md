# Warpgate retired

The owner explicitly requested complete removal on 2026-10-01. Warpgate is no longer an active service and there is no replacement browser SSH gateway.

Removed Portainer stack `warpgate` (156, endpoint 2), container and dedicated network, `/data/apps/warpgate` including SQLite/configuration/SSH keys/TLS keys, and its unused image. Removed the `remote.l3b.cc.cd` Caddy handler/import and dedicated upstream trust certificate. Removed its Homepage Applications card, Pocket ID client `warpgate`, HomeLab vault item `Warpgate`, and the dedicated `homelab-warpgate` entry in dev's `authorized_keys`. No other SSH key or application was removed.

Active Compose/configuration/certificate files are deleted from the repository. Git history retains historical configuration, not an active deployment. Host data deletion is irreversible through this cleanup; vault deletion follows 1Password deleted-item retention. Historical Notion/memory records are superseded by this decommission decision, not silently erased. The shared wildcard DNS/certificate infrastructure is not Warpgate-specific and remains untouched.

Earlier SSH target provisioning and full SSO testing were incomplete. Those tasks are now cancelled, not pending work.
