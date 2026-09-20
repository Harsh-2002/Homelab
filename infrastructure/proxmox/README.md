# Proxmox hosts

All three Proxmox nodes use AdGuard Home as the primary resolver and Cloudflare as the availability fallback. The `l3b.cc.cd` search suffix expands short hostnames such as `px10` to `px10.l3b.cc.cd`. DNS is configured per node in `/etc/resolv.conf`; `systemd-resolved` is inactive.

Deploy the tracked resolver file to `px10`, `px20`, and `px30`:

```bash
scp infrastructure/proxmox/resolv.conf px10:/etc/resolv.conf
scp infrastructure/proxmox/resolv.conf px20:/etc/resolv.conf
scp infrastructure/proxmox/resolv.conf px30:/etc/resolv.conf
```

Validate private, public, and fallback resolution:

```bash
getent ahostsv4 komodo.l3b.cc.cd
getent ahostsv4 github.com
dig @1.1.1.1 example.com A +short
```
