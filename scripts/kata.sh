#!/bin/sh
# Kata Containers setup script for Debian/Ubuntu + Docker
# POSIX-compliant (/bin/sh)
#
# Run when Kata >= 3.32.0 is released (fixes Docker 29+ time namespace bug
# https://github.com/kata-containers/kata-containers/issues/13080)
#
# Usage:
#   sudo ./kata-setup.sh             # interactive
#   sudo KATA_VERSION=3.32.0 ./kata-setup.sh  # pin to a version
#   sudo ASSUME_YES=1 ./kata-setup.sh         # non-interactive (uses defaults)

set -eu

INSTALL_DIR="/opt/kata"
LOCAL_CONFIG_DIR="/etc/kata-containers"
DOCKER_DAEMON_JSON="/etc/docker/daemon.json"
KATA_VERSION="${KATA_VERSION:-}"
ASSUME_YES="${ASSUME_YES:-0}"

# Colors
if [ -t 1 ]; then
  C_RED="$(printf '\033[31m')"; C_GREEN="$(printf '\033[32m')"
  C_YELLOW="$(printf '\033[33m')"; C_CYAN="$(printf '\033[36m')"; C_RESET="$(printf '\033[0m')"
else
  C_RED=""; C_GREEN=""; C_YELLOW=""; C_CYAN=""; C_RESET=""
fi

log()  { printf "%s[INFO]%s  %s\n" "$C_GREEN"  "$C_RESET" "$*"; }
warn() { printf "%s[WARN]%s  %s\n" "$C_YELLOW" "$C_RESET" "$*"; }
err()  { printf "%s[ERROR]%s %s\n" "$C_RED"    "$C_RESET" "$*" >&2; }
die()  { err "$*"; exit 1; }

prompt_yn() {
  if [ "$ASSUME_YES" = "1" ]; then return 0; fi
  printf "%s [y/N]: " "$1"
  read -r ans
  case "$ans" in y|Y|yes|YES) return 0 ;; *) return 1 ;; esac
}

# Preflight
preflight() {
  log "Preflight checks"
  [ "$(id -u)" -eq 0 ] || die "Run as root (sudo)"
  for cmd in curl jq tar zstd systemctl docker awk sed; do
    command -v "$cmd" >/dev/null 2>&1 || die "Missing dependency: $cmd"
  done
  [ -e /dev/kvm ] || die "/dev/kvm not found - KVM required"
  systemctl is-active docker >/dev/null 2>&1 || die "Docker service not running"
  log "All checks passed"
}

# Hypervisor selection
select_hypervisor() {
  printf "\n%sSelect hypervisor:%s\n" "$C_CYAN" "$C_RESET"
  printf "  1) qemu         (default, most compatible, ~1s boot)\n"
  printf "  2) clh          (Cloud Hypervisor, ~250ms boot)\n"
  printf "  3) fc           (Firecracker, ~125ms boot, AWS Lambda style)\n"
  printf "  4) dragonball   (Alibaba experimental, ~150ms boot)\n"
  if [ "$ASSUME_YES" = "1" ]; then
    HYPERVISOR="qemu"
    log "Auto-selected: qemu"
  else
    printf "Choice [1]: "
    read -r choice
    case "${choice:-1}" in
      1|qemu)        HYPERVISOR="qemu" ;;
      2|clh)         HYPERVISOR="clh"  ;;
      3|fc)          HYPERVISOR="fc"   ;;
      4|dragonball)  HYPERVISOR="dragonball" ;;
      *) die "Invalid choice: $choice" ;;
    esac
  fi
  CONFIG_FILE="configuration-${HYPERVISOR}.toml"
  log "Selected hypervisor: $HYPERVISOR"
}

# Resolve version
resolve_version() {
  if [ -z "$KATA_VERSION" ]; then
    log "Fetching latest Kata release tag"
    KATA_VERSION=$(curl -fsSL https://api.github.com/repos/kata-containers/kata-containers/releases/latest | jq -r .tag_name)
    [ -n "$KATA_VERSION" ] && [ "$KATA_VERSION" != "null" ] || die "Could not resolve latest version"
  fi
  log "Kata version: $KATA_VERSION"
}

# Cleanup any existing install
cleanup_existing() {
  if [ -d "$INSTALL_DIR" ] || [ -e /usr/bin/containerd-shim-kata-v2 ]; then
    warn "Existing Kata installation detected"
    prompt_yn "Remove and reinstall?" || die "Aborted by user"
    pkill -f containerd-shim-kata 2>/dev/null || true
    pkill -f kata-runtime 2>/dev/null || true
    sleep 1
    rm -rf "$INSTALL_DIR" "$LOCAL_CONFIG_DIR"
    rm -f /usr/bin/containerd-shim-kata-v2 /usr/bin/kata-runtime /usr/bin/kata-collect-data.sh /usr/bin/kata-monitor
  fi
}

# Download tarball
download_kata() {
  TARBALL="kata-static-${KATA_VERSION}-amd64.tar.zst"
  URL="https://github.com/kata-containers/kata-containers/releases/download/${KATA_VERSION}/${TARBALL}"
  TMP_TARBALL="/tmp/${TARBALL}"
  log "Downloading from $URL"
  curl -fL --progress-bar "$URL" -o "$TMP_TARBALL"
  [ -s "$TMP_TARBALL" ] || die "Download failed or empty file"
}

# Extract to /
install_kata() {
  log "Extracting to $INSTALL_DIR"
  tar --zstd -C / -xf "$TMP_TARBALL"
  rm -f "$TMP_TARBALL"
  [ -x "$INSTALL_DIR/bin/kata-runtime" ] || die "Extraction did not produce expected binaries"
  log "Creating symlinks in /usr/bin"
  for bin in containerd-shim-kata-v2 kata-runtime kata-collect-data.sh; do
    [ -f "$INSTALL_DIR/bin/$bin" ] && ln -sf "$INSTALL_DIR/bin/$bin" "/usr/bin/$bin"
  done
}

# Activate chosen hypervisor config
configure_hypervisor() {
  log "Configuring hypervisor: $HYPERVISOR"
  SRC="$INSTALL_DIR/share/defaults/kata-containers/$CONFIG_FILE"
  [ -f "$SRC" ] || die "Config file not found: $SRC"
  mkdir -p "$LOCAL_CONFIG_DIR"
  install -m 0644 "$SRC" "$LOCAL_CONFIG_DIR/$CONFIG_FILE"
  ln -sf "$LOCAL_CONFIG_DIR/$CONFIG_FILE" "$LOCAL_CONFIG_DIR/configuration.toml"
  log "Active config: $(readlink "$LOCAL_CONFIG_DIR/configuration.toml")"
}

# Load required kernel module (silently OK if already loaded)
load_kernel_modules() {
  log "Loading kernel modules (vhost_vsock, vhost_net)"
  modprobe vhost_vsock 2>/dev/null || warn "vhost_vsock load failed"
  modprobe vhost_net   2>/dev/null || warn "vhost_net load failed (not always required)"
  # Persist
  echo "vhost_vsock" > /etc/modules-load.d/kata.conf
  echo "vhost_net"  >> /etc/modules-load.d/kata.conf
}

# Configure Docker daemon.json
configure_docker() {
  log "Configuring Docker daemon"
  mkdir -p /etc/docker
  [ -f "$DOCKER_DAEMON_JSON" ] || echo '{}' > "$DOCKER_DAEMON_JSON"
  cp "$DOCKER_DAEMON_JSON" "$DOCKER_DAEMON_JSON.pre-kata.$(date +%Y%m%d-%H%M%S)"
  TMP=$(mktemp)
  jq '.runtimes.kata = {"runtimeType": "/usr/bin/containerd-shim-kata-v2"}' "$DOCKER_DAEMON_JSON" > "$TMP"
  mv "$TMP" "$DOCKER_DAEMON_JSON"
  log "Reloading Docker"
  systemctl reload docker || systemctl restart docker
  sleep 2
}

# Verify install
verify() {
  log "Verifying installation"
  /usr/bin/kata-runtime --version || die "kata-runtime binary failed"
  log "Running kata-runtime check"
  /usr/bin/kata-runtime check >/dev/null 2>&1 \
    && log "kata-runtime check: PASS" \
    || warn "kata-runtime check: some warnings (see 'sudo kata-runtime check -v')"
  log "Active Docker runtimes:"
  docker info --format '{{json .Runtimes}}' | jq 'keys'
  if prompt_yn "Run a test container now?"; then
    log "Pulling ubuntu:24.04 and running with --runtime kata"
    docker run --runtime kata --rm ubuntu:24.04 uname -r \
      || warn "Test container failed - check Docker version compatibility"
  fi
}

# Summary
summary() {
  HOST_KERNEL=$(uname -r)
  cat <<EOF

${C_GREEN}=== Kata Containers Setup Complete ===${C_RESET}

Version:        $KATA_VERSION
Hypervisor:     $HYPERVISOR
Install dir:    $INSTALL_DIR
Config:         $LOCAL_CONFIG_DIR/configuration.toml -> $CONFIG_FILE
Docker runtime: kata

Host kernel:    $HOST_KERNEL

Usage:
  docker run --runtime kata --rm ubuntu:24.04 uname -r
  docker run --runtime io.containerd.kata.v2 --rm ubuntu:24.04 uname -r

To switch hypervisor later, re-run this script and pick a different option.
To uninstall, see the companion cleanup script.

EOF
}

main() {
  cat <<'BANNER'
=========================================
  Kata Containers + Docker Setup
=========================================
This will:
  1. Install Kata Containers to /opt/kata
  2. Set the chosen hypervisor as active
  3. Register 'kata' runtime in Docker
  4. Reload Docker

BANNER
  preflight
  prompt_yn "Continue with setup?" || die "Aborted"
  select_hypervisor
  resolve_version
  cleanup_existing
  download_kata
  install_kata
  load_kernel_modules
  configure_hypervisor
  configure_docker
  verify
  summary
}

main "$@"
