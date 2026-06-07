#!/bin/bash
# ts-setup.sh — tailscale homelab node setup
# Usage: sudo bash ts-setup.sh
#
# Pre-approved devices: set "Pre-authorized" on the auth key at
# https://login.tailscale.com/admin/settings/keys — no flag needed here.
# Route approval (subnet + exit node) is still manual in admin console
# unless you configure autoApprovers in the ACL policy.

set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "run as root: sudo bash ts-setup.sh"; exit 1; }

# ============================================================
# config
# ============================================================
ADVERTISE_ROUTES=true
ADVERTISE_EXIT_NODE=true
ENABLE_SSH=true
ACCEPT_ROUTES=false
ACCEPT_DNS=false
# ============================================================

read -rp "Tailscale auth key: " AUTH_KEY
echo ""

# detect interface carrying the default route
MAIN_IFACE=$(ip route get 1.1.1.1 2>/dev/null | grep -o 'dev [^ ]*' | awk '{print $2}' | head -1)
[[ -z "$MAIN_IFACE" ]] && { echo "error: could not detect main interface"; exit 1; }
echo "==> main interface: $MAIN_IFACE"

# derive subnet from main interface route table
SUBNET=$(ip route show dev "$MAIN_IFACE" proto kernel | awk '{print $1}' | head -1)
[[ -z "$SUBNET" ]] && { echo "error: could not detect subnet on $MAIN_IFACE"; exit 1; }
echo "==> subnet: $SUBNET"

# install / upgrade (handles both fresh and existing)
echo "==> installing tailscale"
if command -v tailscale &>/dev/null; then
  echo "    existing install detected — taking down before upgrade"
  tailscale down 2>/dev/null || true
fi
curl -fsSL https://tailscale.com/install.sh | sh

# ip forwarding — idempotent overwrite
echo "==> enabling ip forwarding"
tee /etc/sysctl.d/99-tailscale.conf << 'SYSCTL'
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
SYSCTL
sysctl -p /etc/sysctl.d/99-tailscale.conf

# build tailscale up args dynamically
TS_ARGS=(
  --authkey="$AUTH_KEY"
  --hostname="$(hostname | tr '[:upper:]' '[:lower:]')"
  --accept-routes="$ACCEPT_ROUTES"
  --accept-dns="$ACCEPT_DNS"
  --accept-risk=lose-ssh
)

[[ "$ADVERTISE_ROUTES"    == true ]] && TS_ARGS+=(--advertise-routes="$SUBNET")
[[ "$ADVERTISE_EXIT_NODE" == true ]] && TS_ARGS+=(--advertise-exit-node)
[[ "$ENABLE_SSH"          == true ]] && TS_ARGS+=(--ssh)

echo "==> bringing up tailscale"
tailscale up "${TS_ARGS[@]}"
tailscale set --auto-update

# gro fix on detected interface — persistent via systemd
echo "==> fixing udp gro forwarding on $MAIN_IFACE"
ethtool -K "$MAIN_IFACE" rx-udp-gro-forwarding on 2>/dev/null || \
  echo "    warning: ethtool failed on $MAIN_IFACE — skipping (non-fatal)"

tee /etc/systemd/system/tailscale-gro-fix.service << UNIT
[Unit]
Description=Fix UDP GRO forwarding for Tailscale on ${MAIN_IFACE}
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/ethtool -K ${MAIN_IFACE} rx-udp-gro-forwarding on
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

systemctl enable --now tailscale-gro-fix.service

echo ""
echo "==> done"
printf "    node : %s\n" "$(hostname | tr '[:upper:]' '[:lower:]')"
printf "    ts ip: %s\n" "$(tailscale ip -4 2>/dev/null || echo 'pending')"
echo ""
tailscale status
