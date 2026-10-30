# Netgear switch discovery and px30 network investigation

Verified 2026-10-29 by passive LLDP on px10's physical NIC, the live device login
page, and the owner's authenticated dashboard/port/MAC-table copies.

- Model: **GS110TPv3**, name `home`, firmware **7.1.1.13**.
- Management address: **192.168.0.239**, separate from the ordinary LAN subnet.
- The dashboard's displayed January 2025 clock is not reliable event timing.
- No switch settings, VLANs, port negotiation, firmware or password were changed.
- No device serial, password or authentication session is committed here.

## Verified physical connections

| Switch port | Connected device/path | Evidence |
| --- | --- | --- |
| g1 | Hikvision camera | Learned camera MAC matches live LAN ARP; 100 Mbps full duplex |
| g5 | px10 and its VM/LXC MACs | LLDP on px10 + owner's learned table; 1 Gbps full duplex |
| g6 | px20 and its VM/LXC MACs | Host MAC and guest MACs match live ARP; 1 Gbps full duplex |
| g7 | Replacement px30, owner-confirmed cable | 1 Gbps link; no learned source MAC in supplied table |
| g10 | Uplink carrying router and downstream clients | Router, bulb, AC, ASUS and client MACs learned there; 1 Gbps physical status reported |

The g10 observation does not prove whether an intermediary exists or establish
all downstream cabling. The repeated switch port MAC in Port Configuration is
not the connected hosts' MAC. Use the dynamic/learned address table instead.
The camera's 100 Mbps connection is not the router uplink.

## Discovery and access used

Nmap 7.95 was installed from Debian packages on dev. It is a shared host CLI,
not an MCP/plugin or per-agent configuration change. A TCP SYN scan of the top
1000 ports with light version detection covered all256 addresses in the LAN /24:
26 hosts were up, elapsed193.41s. Raw scan output/fingerprints are retained only
under /tmp/homelab-switch-discovery-top1000.* and summary.json, outside Git.
These are dated observations, not permanent inventory or a full65535-port scan.

The scan did not include the switch's different management subnet. Netgear NSDP
read-only broadcasts from dev and px10 returned no device. Passive LLDP on px10
provided the model, management IP and local switch port g5. Do not conclude an
unresponsive NSDP query means a switch is unmanaged.

Temporary access, **not persistent configuration**:

```bash
# On px10, a secondary address was added without changing its LAN IP/gateway.
ip address add 192.168.0.250/24 dev vmbr0 label vmbr0:ng

# On dev, this SSH tunnel remains in the troubleshooting terminal session.
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 10.1.1.5:18080:192.168.0.239:80 px10
```

Owner-facing login: **http://10.1.1.5:18080/**. Confirmed HTTP200 from px20 and
opened the actual Netgear GS110TPv3 login page in the browser. The owner logged
in from their browser and supplied tables. The agent's separate browser session
remains unauthenticated. No Netgear item was found by title in the HomeLab vault;
use a concealed vault item if subsequent direct authenticated administration is
needed, not a password pasted in chat.

The tunnel binds only dev's private LAN address. No Caddy/public-domain route,
router forwarding, service unit or reboot-persistent alias was added. When the
investigation is finished, stop only this SSH tunnel, then remove the secondary
address from px10:

```bash
ip address del 192.168.0.250/24 dev vmbr0
```

Do not reset/reboot the switch or change its management address merely to fix
px30. A permanent management-address change needs a separately planned access
cutover. Keep the temporary URL available while the owner is using it.

## px30 finding and limits

Update October30: both drives are back on the old7040 and SSH/quorum/pools were
verified, including a controlled reboot after repair. The previous boot journal
confirms the attempted replacement's NIC became`eno1` while vmbr0 required`nic0`.
An onboard PCI-path rule now replaces the MAC dependency and is included in both
boot images. The next replacement's actual path/hardware must still be checked;
see [current preparation checkpoint](../proxmox/PX30-HARDWARE-SWAP.md).
The following describes the earlier investigation, not current host reachability.

The replacement is reported powered on but unreachable at its preserved static
LAN address. It is no longer accurate to describe the physical machine as still
powered off. Hardware/boot identity remains unverified remotely. px10 and px20
are quorate and all evacuated HA resources remain started on their temporary hosts.

The owner confirmed px30's cable is in g7. That port negotiates1Gbps, but no source
MAC was learned there in the supplied dynamic table. A link light can blink from
incoming broadcasts; it does not prove DHCP, a usable IP or a completed OS boot.
A learned entry could also have aged out. No new SSH/Proxmox endpoint identifying
px30 at another address was found. The old MAC-pinned nic0 configuration is a
known candidate cause, not a confirmed diagnosis without host evidence.

Recovery options remain a visible console/offline disk repair or an experimental
Pi4B USB-Ethernet gadget presenting the old host-side MAC to satisfy the existing
link mapping. The latter requires a booted Proxmox OS, prepared/reachable Pi,
correct USB data path and stable power; it is not a video console or proven fix.
The owner has Pi4B and Pi3B; the Pi4B's USB-C supports device mode, the Pi3B's
external USB ports do not provide the required gadget role. No Pi deployment,
gadget configuration or persistent px30 network repair has been completed.

See [chassis-swap state and required restoration](../proxmox/PX30-HARDWARE-SWAP.md).

Sources: [NETGEAR management-IP behavior](https://kb.netgear.com/30418/What-is-the-default-IP-address-of-my-NETGEAR-Smart-Managed-Plus-Smart-Managed-Pro-or-Insight-Managed-Smart-Cloud-switch),
[NCC read-only NSDP discovery](https://github.com/nccgroup/nsdp-discover),
[Nmap port selection](https://nmap.org/book/man-port-specification.html),
[Raspberry Pi USB gadget support](https://github.com/raspberrypi/rpi-usb-gadget).
