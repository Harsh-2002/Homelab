# Coolify VM preparation

Owner-created Debian 13 VM 108 `coolify` runs on px10 at `10.1.1.14/24`, gateway `10.1.1.1`, internal DNS `10.1.1.2`, search domain `l3b.cc.cd`. Its MAC `BC:24:11:0F:1C:55` matches the live guest. The VM has two cores, 4096 MiB maximum / 2048 MiB minimum RAM, a 50 GiB `local-zfs` root disk, `vmbr0` with firewall enabled, and `onboot: 1`. These were existing settings and were not changed during preparation.

On 2026-09-30, added the following alias to dev's `/home/dev/.ssh/config`, preserving all existing hosts:

```sshconfig
Host coolify
    HostName 10.1.1.14
    User root
```

Root SSH key login was already available and verified. No password, SSH policy or key was changed. Ran `apt-get update` and `apt-get -y upgrade`: zero upgrades or packages held back. Installed Debian's `qemu-guest-agent` version `1:10.0.13+ds-0+deb13u1` and started its service. `dpkg --audit` was clean. Proxmox already had `agent: 1` and the live virtio guest-agent channel; neither a configuration change nor cold start was required.

The Debian service is static, not a manually enabled service. The packaged `/usr/lib/udev/rules.d/60-qemu-guest-agent.rules` requests it through systemd when `org.qemu.guest_agent.0` appears at boot. This provides automatic startup; no custom unit, cron job or unnecessary enablement symlink was created. Verified `systemctl is-active qemu-guest-agent`, `qm guest cmd 108 ping` and `qm guest cmd 108 get-host-name` (returned `coolify`). Boot startup is configured by the package but a reboot test was not performed.

## Remaining work

- A reboot requirement already existed before this task: installed kernel `6.12.111+deb13-cloud-amd64`, running kernel `6.12.107+deb13-cloud-amd64`. Reboot during an approved window, then verify SSH and agent ping again. No reboot was performed here.
- Coolify application installation, proxy/domain, authentication, HA/replication and backup/monitoring enrollment were not requested or configured in this preparation task. Do not describe the named VM as a deployed Coolify application.

Check:

```sh
ssh coolify 'hostname; uname -r; systemctl is-active qemu-guest-agent'
ssh px10 'qm guest cmd 108 ping; qm guest cmd 108 get-host-name'
```
