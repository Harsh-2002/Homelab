# Coolify VM preparation

Owner-created Debian 13 VM 108 `coolify` runs on px10 at `10.1.1.14/24`, gateway `10.1.1.1`, internal DNS `10.1.1.2`, search domain `l3b.cc.cd`. Its MAC `BC:24:11:0F:1C:55` matches the live guest. The VM has two cores, 4096 MiB maximum / 2048 MiB minimum RAM, a 50 GiB `local-zfs` root disk, `vmbr0` with firewall enabled, and `onboot: 1`. These were existing settings and were not changed during preparation.

On 2026-09-30, added the following alias to dev's `/home/dev/.ssh/config`, preserving all existing hosts:

```sshconfig
Host coolify
    HostName 10.1.1.14
    User root
```

Root SSH key login was already available and verified. No password, SSH policy or key was changed. Ran `apt-get update` and `apt-get -y upgrade`: zero upgrades or packages held back. Installed Debian's `qemu-guest-agent` version `1:10.0.13+ds-0+deb13u1` and started its service. `dpkg --audit` was clean. Proxmox already had `agent: 1` and the live virtio guest-agent channel; neither a configuration change nor cold start was required.

The Debian service is static, not a manually enabled service. The packaged `/usr/lib/udev/rules.d/60-qemu-guest-agent.rules` requests it through systemd when `org.qemu.guest_agent.0` appears at boot. No custom unit, cron job or unnecessary enablement symlink was created. Verified `systemctl is-active qemu-guest-agent`, `qm guest cmd 108 ping` and `qm guest cmd 108 get-host-name` (returned `coolify`), including after the clean restart below.

## Provisioning-drive cleanup and final restart

The owner then requested removal of completed provisioning drives and a final reboot. Cloud-init reported done with no errors (only the image's deprecated `user` setting warning). Static addressing was already persisted in `/etc/netplan/50-cloud-init.yaml`; root SSH key login had been verified. Installed `/etc/cloud/cloud-init.disabled` to prevent further cloud-init provisioning after removing its datasource, retaining the current network and SSH settings. This is a disable marker, not a backup or service script.

The owner had already queued removal of `ide0: local-zfs:vm-108-cloudinit`. Removed the additional empty `ide2: none,media=cdrom`, set boot order to `scsi0;net0`, then requested a clean shutdown. Inspection discovered the owner had already registered VM 108 with Proxmox HA. `qm shutdown 108` therefore requested an HA stop; waited for the actual stopped state and for pending drive removal to apply. Confirmed the cloud-init volume was no longer referenced, permanently removed only `local-zfs:vm-108-cloudinit` (4 MiB), then used `qm start 108` to restore the HA resource to started. No other disks, guest or HA policy was altered. The independent 50 GiB root volume remains `local-zfs:vm-108-disk-0`; no CD-ROM, cloud-init or unused disk is attached.

Verified after restart: SSH works, system state is running, active kernel is `6.12.111+deb13-cloud-amd64`, agent starts automatically and responds to Proxmox, static address remains `10.1.1.14/24`, DNS remains `10.1.1.2`, cloud-init is disabled, no reboot requirement remains, and HA reports `service vm:108 (px10, started)`. Future network/key updates must be made inside the guest, not assumed to propagate through Proxmox cloud-init metadata. To reintroduce cloud-init later, deliberately attach a datasource and remove the disable marker with a reviewed reprovisioning plan.

## Remaining work

- Coolify application installation, proxy/domain, authentication, replication and backup/monitoring enrollment were not requested or configured in this preparation task. Existing owner-configured HA registration was retained, not created here. Do not describe the named VM as a deployed Coolify application or claim replication/backup coverage without checking.

Check:

```sh
ssh coolify 'hostname; uname -r; systemctl is-active qemu-guest-agent'
ssh px10 'qm guest cmd 108 ping; qm guest cmd 108 get-host-name'
```
