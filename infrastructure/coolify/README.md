# Coolify retired

The owner explicitly requested complete removal on 2026-09-30 and chose Termix instead.

Removed HA resource `vm:108`, cleanly shut down VM 108 on px10, then destroyed it with `qm destroy 108 --purge 1 --destroy-unreferenced-disks 1`. The 50 GiB root disk `local-zfs:vm-108-disk-0` and VM configuration are gone. The earlier 4 MiB cloud-init disk had already been deleted. Checked px20 and px30: neither had a VM 108 replica disk. No replication job, HA affinity rule or scheduled backup included VM 108. No other guest or disk was changed.

Removed the Coolify handler/import from Caddy and its SSH alias from dev. Coolify had not been added to Homepage. Deleted the exact HomeLab vault item `Coolify`; 1Password retains deleted items for 30 days. No Coolify-specific OIDC client or project wildcard namespace had been created.

`10.1.1.14` is no longer assigned to this VM. Verify network use before allocating it. The deleted VM disk is not recoverable through Proxmox; no backup job covered it.

Replacement: [Termix](../termix/README.md), private `https://remote.l3b.cc.cd`, on ctr through Portainer. This is a historical decommission record, not an active runbook.
