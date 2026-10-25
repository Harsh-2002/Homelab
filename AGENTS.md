# Homelab operating instructions

Preserve credentials, private state and unrelated work. Never print expanded
credential-bearing agent configurations. Keep shared tooling synchronized across
Codex, Claude Code, Hermes and OpenCode, preserving native memory integrations.
Run `python3 infrastructure/agents/check-integrations.py` after agent changes.

## Living architecture

Material changes to hosts, VM/LXC placement, services, network access, storage,
identity, HA or integrations must update `docs/architecture/inventory.json` and
the affected relationships in `docs/architecture/build.mjs`, alongside service
runbooks. Rebuild with `node docs/architecture/build.mjs`, validate with
`node docs/architecture/check.mjs`, and visually inspect the changed diagrams.
Refresh exported PNG/PDF files when publishing a new architecture snapshot.

Keep the public SVGs and inventory share-safe. The optional private address
source and internal exports are Git-ignored; never force-add them. Do not infer
hardware, cabling, health, failover guarantees or service existence from old
runbooks or example diagrams. Check actual current state where relevant.

Record meaningful changes in the Homelab Notion runbook and OpenViking, then
commit and push the completed scoped work. Do not leave those steps for the
owner to request again. Follow the owner's requested branch workflow and
preserve concurrent changes. Verify remote HEAD before claiming a push.
