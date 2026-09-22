# Orva serverless VM

Orva is the dedicated VM for running serverless functions. VM 106 runs on `px20` and uses `10.1.1.11/24`, gateway `10.1.1.1`, AdGuard `10.1.1.2`, fallback resolver `1.1.1.1`, and search domain `l3b.cc.cd`. The Debian login is `orva`; SSH key authentication is enabled and no login password is required. The administrative SSH alias is `ssh orva`.

| Property | Value |
| --- | --- |
| VM ID and name | `106`, `orva` |
| Preferred node | `px20` |
| Replication target | `px10` |
| Address | `10.1.1.11/24` |
| Public endpoint | `https://orva.l3b.cc.cd` -> `http://10.1.1.11:8443` through Caddy |
| Resources | 2 vCPU, 4 GB maximum RAM, 2 GB balloon minimum, 10 GB local-ZFS disk |
| Guest agent | `qemu-guest-agent`, active through its static systemd unit |
| Boot | `onboot=1`, managed by Proxmox HA |

## HA and replication

Replication job `106-0` copies local-ZFS storage from `px20` to `px10` every five minutes. HA resource `vm:106` is kept in `started` state with two local restart attempts and one relocation attempt. Strict node-affinity rule `vm106-replica-nodes` permits only `px20` at priority 2 and replica node `px10` at priority 1; HA must never select `px30`, where no replica exists.

```sh
ssh px20 'pvesr status | grep 106-0'
ssh px20 'ha-manager status | grep vm:106'
ssh px20 'ha-manager rules config | grep vm106-replica-nodes'
ssh px20 'qm agent 106 ping'
```

## Proxmox-enforced network isolation

VM 106 remains on `vmbr0` with its normal `/24` address. Security is enforced outside the guest by the Proxmox VM firewall, whose tracked baseline is [`106.fw`](106.fw). The VM cannot remove this policy even if a function compromises the guest.

Inbound policy is `ACCEPT` as requested: SSH and application listeners are reachable from any source that already has a route to the private address. Internet clients still cannot reach an RFC1918 address without an explicit router or tunnel route. Orva is published by an explicit DNS-only Cloudflare A record and Caddy reverse proxy; the router forwards HTTPS only to Caddy, not directly to VM 106.

Outbound policy allows public Internet destinations but blocks new VM-originated connections to LAN and all RFC1918 address space, Tailscale/CGNAT `100.64.0.0/10`, IPv4 link-local, and IPv6 ULA/link-local. The only internal outbound exception is TCP and UDP DNS to AdGuard `10.1.1.2:53`. Stateful replies to inbound SSH or application connections remain allowed.

`ipfilter` is deliberately disabled because QEMU guests require an explicitly populated `ipfilter-net0` set; enabling it without that set blocked all egress during validation. MAC filtering remains enabled. The datacenter firewall is enabled with `ACCEPT` host policies so the cluster hosts and unrelated guests retain their previous reachability. VM 106 supplies the restrictive guest-specific rules.

```sh
ssh orva 'getent hosts debian.org'
ssh orva 'curl -fsS https://www.debian.org/ >/dev/null'
ssh orva 'timeout 3 bash -c "</dev/tcp/10.1.1.8/9000"'   # must fail
ssh px20 'pve-firewall status; cat /etc/pve/firewall/106.fw'
```

Do not add a blanket outbound exception for a future function. Allow only the exact internal destination and port it requires, above the matching deny rule, and document why it is necessary.
