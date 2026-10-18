# Anchor retirement

Anchor was removed on 2026-10-18 at the owner's explicit request. Nivra remains
the notes service at https://notes.l3b.cc.cd and must not be removed with Anchor.

Retirement targets: Portainer stack `anchor` (154, endpoint 2), container `anchor`,
its `anchor_default` network, `/data/apps/anchor`, the container-owned anonymous
PostgreSQL volume, unused image, Caddy handler, Pocket ID client `anchor`, and
Homepage card. The Anchor vault item is archived rather than permanently erased.

Live data deletion is permanent. Existing whole-CTR backups may contain historical
copies; they also contain other services and are not deleted as part of this task.
Historical Compose/configuration is retained in Git history only. The OIDC setup
script no longer recreates the client.
