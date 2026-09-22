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
getent ahostsv4 px10.l3b.cc.cd
getent ahostsv4 github.com
dig @1.1.1.1 example.com A +short
```

For model-specific firmware package mapping, the sequential USB update
procedure, validation gates, and the 2026-09-22 fwupd cleanup record, see
[`BIOS-UPGRADE.md`](BIOS-UPGRADE.md).

## Intel I219-V transmit-hang workaround

`px10` and `px20` use the same Intel I219-V revision 10 NIC (`8086:15bc`)
with the in-kernel `e1000e` driver. Both hosts have repeatedly logged
`Detected Hardware Unit Hang` during sustained bridged network transfers.
The NIC then stops transmitting, Corosync loses quorum, and Proxmox HA
correctly watchdog-fences the isolated node. The reboot is therefore the
consequence of the NIC failure, not the original fault.

The problem reproduced after the BIOS update and on kernels
`7.0.14-17-pve` and `7.0.14-19-pve`, so BIOS and kernel updates alone are not
a sufficient correction. `px30` has a different I219-LM revision and no
recorded hangs.

The persistent workaround on `px10` and `px20` disables TSO, GSO, GRO, and
EEE while retaining checksum offload. This avoids the affected large-packet
segmentation path and has negligible practical cost on the 1 Gb/s links.
Deploy or restore it with:

```bash
scp infrastructure/proxmox/e1000e-stability.service px10:/etc/systemd/system/
scp infrastructure/proxmox/e1000e-stability.service px20:/etc/systemd/system/
ssh px10 'systemctl daemon-reload && systemctl enable --now e1000e-stability.service'
ssh px20 'systemctl daemon-reload && systemctl enable --now e1000e-stability.service'
```

Validate the active state and counters:

```bash
ethtool -k nic0 | grep -E 'tcp-segmentation|generic-segmentation|generic-receive|tx-checksumming'
ethtool --show-eee nic0
ethtool -S nic0 | grep -E 'tx_timeout_count|tx_dma_failed|rx_dma_failed|tx_errors|rx_errors'
journalctl -k -g 'Hardware Unit Hang|NETDEV WATCHDOG|Reset adapter'
```

On 2026-09-23 an 8 GiB `ctr` (px20) to `dev` (px10) transfer sustained
approximately 115 MB/s after applying the workaround. Both NICs retained
zero errors, DMA failures, and transmit timeouts. Continue monitoring; if a
hang ever recurs with these offloads disabled, the definitive next step is
to move cluster/VM traffic to a separate supported NIC rather than disabling
additional checksum features blindly.
