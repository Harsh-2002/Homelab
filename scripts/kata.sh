#!/bin/sh
# =============================================================================
# kata-setup.sh  —  Kata Containers installer / updater  (latest by default)
# Hypervisors   : Cloud Hypervisor (CLH)  +  QEMU  — both installed & tested
# Runtimes      : runtime-rs (Rust) for CLH  |  Go runtime for QEMU
# Distros       : Debian · Ubuntu · Alpine · RHEL/Rocky/CentOS/Fedora · Arch
#
# USAGE:
#   sudo ./kata-setup.sh              install OR update to the LATEST release + test
#   sudo ./kata-setup.sh --force      reinstall even if already on latest
#   sudo ./kata-setup.sh --uninstall  remove all files and Docker config
#   sudo ./kata-setup.sh --test-only  smoke-test an existing install
#   sudo ./kata-setup.sh --help
#
#   Pin a specific version (skips auto-detect):
#     KATA_VERSION=3.30.0 sudo ./kata-setup.sh
#
# VALIDATE:
#   run: shellcheck -s sh ./kata-setup.sh
# =============================================================================
# shellcheck shell=sh
set -eu

# ─── version (auto-detected unless KATA_VERSION is set in the environment) ────
# Empty  => resolve_version() queries GitHub for the latest release.
# Set    => that exact version is used (e.g. KATA_VERSION=3.30.0).
KATA_VERSION="${KATA_VERSION:-}"

# Recommended version for Docker hosts (QEMU on the Go runtime; no known
# runtime-rs regressions). Used only for advisory messages — the DEFAULT is
# still "latest". Override the default by exporting KATA_VERSION.
RECOMMENDED_VERSION="3.30.0"

# Space-separated list of versions with known runtime-rs <-> Docker breakage.
# When one of these is selected the script warns and pauses (non-blocking), so
# you can Ctrl-C and pin RECOMMENDED_VERSION instead. Remove a version here once
# upstream fixes it (e.g. when 3.32.0 lands).
KNOWN_BAD_VERSIONS="3.31.0"

# Derived after the version is known (see resolve_version):
TARBALL=""
DOWNLOAD_URL=""
RELEASE_API="https://api.github.com/repos/kata-containers/kata-containers/releases/latest"
RELEASE_LATEST="https://github.com/kata-containers/kata-containers/releases/latest"

# ─── fixed paths ──────────────────────────────────────────────────────────────
readonly KATA_DIR="/opt/kata"
readonly RUST_SHIM="${KATA_DIR}/runtime-rs/bin/containerd-shim-kata-v2"
readonly GO_SHIM="${KATA_DIR}/bin/containerd-shim-kata-v2"
readonly CLH_CONFIG="${KATA_DIR}/share/defaults/kata-containers/configuration-clh.toml"
readonly QEMU_CONFIG="${KATA_DIR}/share/defaults/kata-containers/configuration-qemu.toml"

readonly SYM_RS="/usr/local/bin/containerd-shim-kata-v2-rs"
readonly SYM_GO="/usr/local/bin/containerd-shim-kata-v2"
readonly SYM_RT="/usr/local/bin/kata-runtime"

readonly DOCKER_DAEMON="/etc/docker/daemon.json"

# ─── runtime state ────────────────────────────────────────────────────────────
DAEMON_BACKUP=""
TMPDIR=""
MODE="install"
FORCE=0

# Install step flags — each set to 1 on completion, checked by do_rollback
S_EXTRACTED=0
S_SYMLINKS=0
S_DAEMON=0
S_DOCKER_RESTARTED=0

# Set to 1 once the install proper is finished (after Docker restart).
# After this point, a failure (e.g. smoke test) must NOT trigger rollback —
# the install is correct and on-disk; the problem is environmental and the
# files must stay put so the host can be debugged (kata-runtime check, logs).
INSTALL_COMPLETE=0

# Detected environment (populated by detect_env)
PKG_MANAGER=""
SVC_MANAGER=""
DISTRO_ID=""

# ─── colours (TTY-aware) ──────────────────────────────────────────────────────
ESC=$(printf '\033')
if [ -t 1 ]; then
    CG="${ESC}[0;32m" CY="${ESC}[1;33m" CR="${ESC}[0;31m"
    CC="${ESC}[0;36m" CB="${ESC}[1m"    CN="${ESC}[0m"
else
    CG="" CY="" CR="" CC="" CB="" CN=""
fi

# ─── logging ──────────────────────────────────────────────────────────────────
log()    { printf '%s[+]%s %s\n' "$CG" "$CN" "$*"; }
info()   { printf '%s[i]%s %s\n' "$CC" "$CN" "$*"; }
warn()   { printf '%s[!]%s %s\n' "$CY" "$CN" "$*"; }
ok()     { printf '%s[✓]%s %s\n' "$CG" "$CN" "$*"; }
fail()   { printf '%s[✗]%s %s\n' "$CR" "$CN" "$*" >&2; }
header() { printf '\n%s%s── %s ──%s\n' "$CB" "$CC" "$*" "$CN"; }

die() {
    fail "$*"
    # Roll back ONLY if we are mid-install. Once INSTALL_COMPLETE=1 the files
    # are correct and staying put; a later failure is environmental and the
    # install must be preserved for debugging.
    if [ "$MODE" = "install" ] && [ "$INSTALL_COMPLETE" = "0" ]; then
        do_rollback
    fi
    exit 1
}

# ─── cleanup/rollback ─────────────────────────────────────────────────────────
do_cleanup() {
    [ -n "$TMPDIR" ] && rm -rf "$TMPDIR"
}
trap 'do_cleanup' EXIT

do_rollback() {
    warn "Rolling back — restoring pre-install state..."

    # Reverse order: docker → daemon.json → symlinks → /opt/kata

    if [ "$S_DOCKER_RESTARTED" = "1" ]; then
        warn "  Restarting Docker with restored config..."
        svc_restart_docker 2>/dev/null || true
        S_DOCKER_RESTARTED=0
    fi

    if [ "$S_DAEMON" = "1" ] && [ -n "$DAEMON_BACKUP" ] && [ -f "$DAEMON_BACKUP" ]; then
        warn "  Restoring $DOCKER_DAEMON from $DAEMON_BACKUP..."
        cp "$DAEMON_BACKUP" "$DOCKER_DAEMON" || true
        S_DAEMON=0
    fi

    if [ "$S_SYMLINKS" = "1" ]; then
        warn "  Removing symlinks..."
        rm -f "$SYM_RS" "$SYM_GO" "$SYM_RT" 2>/dev/null || true
        S_SYMLINKS=0
    fi

    if [ "$S_EXTRACTED" = "1" ]; then
        warn "  Removing $KATA_DIR..."
        rm -rf "$KATA_DIR" 2>/dev/null || true
        S_EXTRACTED=0
    fi

    warn "Rollback complete."
}

# ═════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT DETECTION
# ═════════════════════════════════════════════════════════════════════════════

detect_env() {
    header "Environment"

    # ── distro ID ──────────────────────────────────────────────────────────────
    if [ -f /etc/os-release ]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
    else
        DISTRO_ID="unknown"
    fi

    # ── package manager ────────────────────────────────────────────────────────
    if   command -v apt-get  > /dev/null 2>&1; then PKG_MANAGER="apt-get"
    elif command -v apk      > /dev/null 2>&1; then PKG_MANAGER="apk"
    elif command -v dnf      > /dev/null 2>&1; then PKG_MANAGER="dnf"
    elif command -v yum      > /dev/null 2>&1; then PKG_MANAGER="yum"
    elif command -v pacman   > /dev/null 2>&1; then PKG_MANAGER="pacman"
    elif command -v zypper   > /dev/null 2>&1; then PKG_MANAGER="zypper"
    else                                            PKG_MANAGER="unknown"
    fi

    # ── service manager ────────────────────────────────────────────────────────
    # systemctl check must confirm it is actually talking to a daemon (not --user)
    if command -v systemctl > /dev/null 2>&1 && systemctl list-units > /dev/null 2>&1; then
        SVC_MANAGER="systemd"
    elif command -v rc-service > /dev/null 2>&1; then
        SVC_MANAGER="openrc"
    elif command -v service > /dev/null 2>&1; then
        SVC_MANAGER="sysv"
    else
        SVC_MANAGER="unknown"
    fi

    info "Distro       : $DISTRO_ID"
    info "Pkg manager  : $PKG_MANAGER"
    info "Svc manager  : $SVC_MANAGER"
    info "Kernel       : $(uname -r)"
    info "Arch         : $(uname -m)"

    [ "$(uname -m)" = "x86_64" ] || die "Kata static tarball requires x86_64; got $(uname -m)"
}

# ─── package manager abstraction ─────────────────────────────────────────────
pkg_install() {
    case "$PKG_MANAGER" in
        apt-get) apt-get install -y -q "$@" ;;
        apk)     apk add --quiet --no-cache "$@" ;;
        dnf)     dnf install -y -q "$@" ;;
        yum)     yum install -y -q "$@" ;;
        pacman)  pacman -S --noconfirm --needed "$@" ;;
        zypper)  zypper --quiet install -y "$@" ;;
        *)
            warn "Unknown package manager — install manually: $*"
            return 1
            ;;
    esac
}

# ─── service manager abstraction ─────────────────────────────────────────────
svc_restart_docker() {
    case "$SVC_MANAGER" in
        systemd) systemctl restart docker ;;
        openrc)  rc-service docker restart ;;
        sysv)    service docker restart ;;
        *)       docker_daemon_reload_fallback ;;
    esac
}

svc_is_docker_active() {
    case "$SVC_MANAGER" in
        systemd) systemctl is-active --quiet docker ;;
        openrc)  rc-service docker status 2>/dev/null | grep -q started ;;
        sysv)    service docker status > /dev/null 2>&1 ;;
        # Generic: just ask Docker directly
        *)       docker info > /dev/null 2>&1 ;;
    esac
}

docker_daemon_reload_fallback() {
    # Last resort: send SIGHUP to dockerd to reload config,
    # then SIGTERM+restart if needed
    DOCKERD_PID=$(pgrep dockerd 2>/dev/null | head -1) || true
    if [ -n "$DOCKERD_PID" ]; then
        kill -HUP "$DOCKERD_PID" 2>/dev/null || true
        sleep 2
    fi
}

# ═════════════════════════════════════════════════════════════════════════════
# PREREQUISITE CHECKS
# ═════════════════════════════════════════════════════════════════════════════

check_root() {
    [ "$(id -u)" = "0" ] || die "Must run as root: sudo $0"
    ok "Running as root"
}

check_kvm() {
    header "KVM"
    if [ ! -e /dev/kvm ]; then
        warn "/dev/kvm absent — attempting module load..."
        modprobe kvm 2>/dev/null || true
        modprobe kvm_intel 2>/dev/null || modprobe kvm_amd 2>/dev/null || true
        sleep 1
    fi

    if [ ! -e /dev/kvm ]; then
        fail "KVM unavailable. Kata cannot start microVMs without it."
        cat <<'EOF'

Bare-metal host — load the KVM module:
  modprobe kvm_intel         # Intel CPU
  modprobe kvm_amd           # AMD CPU
  # Persist across reboots:
  echo kvm_intel >> /etc/modules    # Debian/Ubuntu
  echo kvm_intel >> /etc/modules-load.d/kvm.conf  # RHEL/Fedora/Alpine

Running inside a VM? Enable nested virtualisation on the HOST:
  KVM host:
    echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm-intel.conf
    modprobe -r kvm_intel && modprobe kvm_intel
  VMware:  VM Settings → Processors → Enable "Virtualize Intel VT-x/EPT"
  VirtualBox: VBoxManage modifyvm <name> --nested-hw-virt on
EOF
        die "Fix KVM and re-run"
    fi
    ok "/dev/kvm present: $(ls -la /dev/kvm)"

    # ── nested virt sanity (Atlas-style guest VMs) ─────────────────────────────
    # /dev/kvm can exist while nested VM *creation* still fails. If the CPU
    # exposes no virt flags, KVM acceleration inside this guest won't work.
    if ! grep -Eq '(vmx|svm)' /proc/cpuinfo; then
        warn "CPU exposes no vmx/svm flags — this looks like a VM without nested virt."
        warn "Kata may fail to boot guests. On the KVM HOST enable nested virt:"
        warn "  echo 'options kvm_intel nested=1' > /etc/modprobe.d/kvm-intel.conf"
        warn "  modprobe -r kvm_intel && modprobe kvm_intel   (and use host-passthrough CPU)"
    else
        info "CPU virt flags present (nested virt available)"
    fi

    # ── vhost modules: REQUIRED for Kata ───────────────────────────────────────
    # vhost_vsock = runtime<->agent channel (without it, the guest boots but the
    #   container launch hangs/fails — common on Debian 'cloud' kernels).
    # vhost_net   = guest networking acceleration.
    log "Loading vhost modules (vhost_vsock, vhost_net)..."
    VHOST_OK=1
    if modprobe vhost_vsock 2>/dev/null && [ -e /dev/vhost-vsock ]; then
        info "vhost_vsock loaded → /dev/vhost-vsock present"
    else
        VHOST_OK=0
        warn "vhost_vsock unavailable — kata-agent comms will FAIL on this kernel."
        warn "  Your kernel: $(uname -r)"
        warn "  Debian 'cloud' kernels often lack it. Install the standard kernel:"
        warn "    apt-get install linux-image-amd64 && reboot"
    fi
    if modprobe vhost_net 2>/dev/null; then
        info "vhost_net loaded"
    else
        warn "vhost_net not loaded (networking may be degraded)"
    fi

    # Persist module loading across reboots (best effort)
    if [ -d /etc/modules-load.d ]; then
        printf 'vhost_vsock\nvhost_net\nkvm\n' > /etc/modules-load.d/kata.conf 2>/dev/null || true
    fi

    [ "$VHOST_OK" = "1" ] || warn "Continuing, but expect container launch to fail without vhost_vsock."
}

check_docker() {
    header "Docker"
    if ! command -v docker > /dev/null 2>&1; then
        fail "Docker not installed."
        cat <<'EOF'

Install Docker (choose your distro):
  Debian/Ubuntu : curl -fsSL https://get.docker.com | sh
  Alpine        : apk add docker docker-cli && rc-update add docker boot && rc-service docker start
  RHEL/Rocky    : dnf install -y docker-ce; systemctl enable --now docker
  Fedora        : dnf install -y docker-ce; systemctl enable --now docker
  Arch          : pacman -S docker; systemctl enable --now docker
EOF
        die "Install Docker and re-run"
    fi

    if ! svc_is_docker_active; then
        fail "Docker is not running."
        case "$SVC_MANAGER" in
            systemd) die "Start it: systemctl start docker" ;;
            openrc)  die "Start it: rc-service docker start" ;;
            *)       die "Start Docker and re-run" ;;
        esac
    fi

    DOCKER_VER=$(docker info --format '{{.ServerVersion}}' 2>/dev/null || echo "unknown")
    ok "Docker ${DOCKER_VER} running"
}

install_deps() {
    header "Dependencies"

    # zstd     — .tar.zst decompression (format used since Kata 3.30.0)
    # wget     — tarball download
    # python3  — JSON editing of daemon.json
    # jq       — daemon.json validation and uninstall cleanup
    # kmod/tar — Alpine-specific extras (BusyBox tar lacks zstd; kmod provides modprobe)

    case "$PKG_MANAGER" in
        apt-get)
            apt-get install -y -q zstd wget curl python3 jq \
                || die "apt-get install failed"
            ;;
        apk)
            # gnu tar needed because BusyBox tar doesn't support --use-compress-program
            # kmod needed because BusyBox's modprobe is limited
            apk add --quiet --no-cache zstd wget curl python3 jq tar kmod \
                || die "apk add failed"
            ;;
        dnf)
            dnf install -y -q zstd wget curl python3 jq \
                || die "dnf install failed"
            ;;
        yum)
            # jq may need EPEL on older RHEL
            yum install -y -q zstd wget curl python3 \
                || die "yum install failed"
            yum install -y -q jq 2>/dev/null || \
                warn "jq not found via yum — install EPEL or ignore (non-critical)"
            ;;
        pacman)
            pacman -S --noconfirm --needed zstd wget curl python jq \
                || die "pacman install failed"
            ;;
        zypper)
            zypper --quiet install -y zstd wget curl python3 jq \
                || die "zypper install failed"
            ;;
        *)
            warn "Unknown package manager — ensure zstd, wget, python3, jq are installed"
            ;;
    esac

    # Hard-fail on truly required tools
    for tool in zstd wget python3; do
        command -v "$tool" > /dev/null 2>&1 \
            || die "Required tool not available after install: $tool"
    done
    # jq is optional (used in uninstall) — warn only
    command -v jq > /dev/null 2>&1 || warn "jq not found — uninstall will use Python3 fallback"

    ok "Dependencies ready"
}

# ═════════════════════════════════════════════════════════════════════════════
# VERSION RESOLUTION  (latest by default; pinned via KATA_VERSION env)
# ═════════════════════════════════════════════════════════════════════════════

# Fetch a URL to stdout using whatever is available (curl or wget).
http_get() {
    if command -v curl > /dev/null 2>&1; then
        curl -fsSL -H "Accept: application/vnd.github+json" "$1" 2>/dev/null
    else
        wget -qO- --header="Accept: application/vnd.github+json" "$1" 2>/dev/null
    fi
}

# Fetch only response headers (for the redirect fallback).
http_head() {
    if command -v curl > /dev/null 2>&1; then
        curl -fsSI "$1" 2>/dev/null
    else
        wget -q -S --spider "$1" 2>&1
    fi
}

resolve_version() {
    header "Version"

    if [ -n "$KATA_VERSION" ]; then
        info "Version pinned via KATA_VERSION=$KATA_VERSION (skipping auto-detect)"
    else
        log "Detecting latest Kata Containers release..."

        # Primary: GitHub releases API → "tag_name"
        KATA_VERSION=$(http_get "$RELEASE_API" \
            | grep '"tag_name"' | head -1 \
            | sed -E 's/.*"tag_name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/') || KATA_VERSION=""

        # Fallback: follow the /releases/latest redirect and read the tag from Location:
        if [ -z "$KATA_VERSION" ]; then
            warn "GitHub API gave nothing (rate-limited?) — trying redirect fallback..."
            KATA_VERSION=$(http_head "$RELEASE_LATEST" \
                | grep -i '^[[:space:]]*location:' | tail -1 \
                | sed -E 's#.*/tag/([^[:space:]/]+).*#\1#' | tr -d '\r') || KATA_VERSION=""
        fi

        [ -n "$KATA_VERSION" ] || die "Could not determine latest version. Pin it: KATA_VERSION=${RECOMMENDED_VERSION} sudo $0"
        info "Latest release: $KATA_VERSION"
    fi

    # Derive the artifact name + URL now that the version is known
    TARBALL="kata-static-${KATA_VERSION}-amd64.tar.zst"
    DOWNLOAD_URL="https://github.com/kata-containers/kata-containers/releases/download/${KATA_VERSION}/${TARBALL}"
    ok "Target version: $KATA_VERSION"

    # ── advisory: warn (but don't block) on versions known-broken with Docker ──
    for bad in $KNOWN_BAD_VERSIONS; do
        if [ "$KATA_VERSION" = "$bad" ]; then
            printf '\n'
            warn "Kata $KATA_VERSION has KNOWN runtime-rs issues with Docker:"
            warn "  • config ships 'cdh_api_timeout' but the binary wants 'cdh_api_timeout_ms' (CLH fails to start)"
            warn "  • QEMU runs on runtime-rs and rejects Docker's cgroup namespace ('invalid namespace type')"
            warn "  Recommended for Docker:  KATA_VERSION=${RECOMMENDED_VERSION} sudo $0 --force"
            warn "  (Kubernetes/containerd users may be unaffected.)"
            warn "Continuing with $KATA_VERSION in 6s — press Ctrl-C now to abort and pin instead."
            sleep 6
            break
        fi
    done
}

# Compare installed vs target; on a re-run this turns the script into an updater.
check_existing_version() {
    header "Existing install"
    if [ -f "${KATA_DIR}/VERSION" ]; then
        CURRENT=$(tr -d '[:space:]' < "${KATA_DIR}/VERSION" 2>/dev/null || echo "unknown")
        info "Installed : $CURRENT"
        info "Target    : $KATA_VERSION"

        if [ "$CURRENT" = "$KATA_VERSION" ]; then
            if [ "$FORCE" = "1" ]; then
                warn "Already on $KATA_VERSION — reinstalling because --force was given"
            else
                ok "Already on the target version ($KATA_VERSION) — nothing to update."
                info "Options:  --force (reinstall)   |   --test-only (re-run smoke tests)"
                # Clean exit; nothing installed yet, so no rollback concerns.
                exit 0
            fi
        else
            log "Update available: $CURRENT  →  $KATA_VERSION"
        fi
    else
        info "No existing Kata install detected — performing a fresh install of $KATA_VERSION"
    fi
}

# ═════════════════════════════════════════════════════════════════════════════
# INSTALL STEPS
# ═════════════════════════════════════════════════════════════════════════════

backup_daemon() {
    header "Backup"
    if [ -f "$DOCKER_DAEMON" ]; then
        DAEMON_BACKUP="${DOCKER_DAEMON}.kata-bak.$(date +%Y%m%d%H%M%S)"
        cp "$DOCKER_DAEMON" "$DAEMON_BACKUP" \
            || die "Cannot backup $DOCKER_DAEMON"
        ok "daemon.json → $DAEMON_BACKUP"
    else
        # Ensure parent dir exists (edge case on minimal installs)
        mkdir -p "$(dirname "$DOCKER_DAEMON")"
        printf '{}\n' > "$DOCKER_DAEMON" \
            || die "Cannot create $DOCKER_DAEMON"
        DAEMON_BACKUP=""
        info "Created fresh $DOCKER_DAEMON (no prior config)"
    fi
}

clean_old() {
    header "Clean"
    if [ -d "$KATA_DIR" ]; then
        warn "Removing existing $KATA_DIR..."
        rm -rf "$KATA_DIR" || die "Cannot remove $KATA_DIR"
    fi
    rm -f "$SYM_RS" "$SYM_GO" "$SYM_RT" 2>/dev/null || true
    ok "Old install removed"
}

download_kata() {
    header "Download"
    TMPDIR=$(mktemp -d) || die "mktemp -d failed"

    # ── tarball cache: avoid re-downloading 1.5 GB on repeat runs ──────────────
    CACHE_DIR="/var/cache/kata-setup"
    CACHE_FILE="${CACHE_DIR}/${TARBALL}"
    mkdir -p "$CACHE_DIR" 2>/dev/null || true

    # Reuse cache only if it exists and is a plausible size (>500 MB)
    if [ -f "$CACHE_FILE" ]; then
        CACHE_BYTES=$(wc -c < "$CACHE_FILE" 2>/dev/null || echo 0)
        if [ "$CACHE_BYTES" -gt 524288000 ]; then
            info "Using cached tarball: $CACHE_FILE ($(du -sh "$CACHE_FILE" | cut -f1))"
            cp "$CACHE_FILE" "${TMPDIR}/${TARBALL}" || die "Cannot copy cached tarball"
            ok "Cache hit — skipping download"
            return 0
        fi
        warn "Cached tarball too small ($CACHE_BYTES bytes) — re-downloading"
        rm -f "$CACHE_FILE"
    fi

    log "Downloading Kata Containers ${KATA_VERSION} (~1.5 GB compressed)..."
    info "URL: $DOWNLOAD_URL"

    wget --quiet --show-progress \
         --tries=3 --timeout=30 \
         -O "${TMPDIR}/${TARBALL}" \
         "$DOWNLOAD_URL" \
        || die "Download failed. Check assets at: https://github.com/kata-containers/kata-containers/releases/tag/${KATA_VERSION}"

    # Populate cache for next time (best effort)
    if cp "${TMPDIR}/${TARBALL}" "$CACHE_FILE" 2>/dev/null; then
        info "Cached for future runs: $CACHE_FILE"
    fi

    DLSIZE=$(du -sh "${TMPDIR}/${TARBALL}" | cut -f1)
    ok "Downloaded ${DLSIZE}"
}

extract_kata() {
    header "Extract"
    log "Extracting via streaming pipe (no extra disk needed)..."

    # Use a FIFO so we can independently check zstd and tar exit codes.
    # This is more portable than 'tar --use-compress-program' (unavailable
    # on BusyBox tar shipped by Alpine) and avoids storing ~4 GB on disk.
    FIFO=$(mktemp -u "${TMPDIR}/katafifo.XXXXXX")
    mkfifo "$FIFO" || die "mkfifo failed"

    # zstd writes decompressed stream into FIFO in background
    zstd --decompress --quiet \
         --stdout "${TMPDIR}/${TARBALL}" > "$FIFO" &
    ZSTD_PID=$!

    # tar reads from FIFO; if it fails, kill zstd and die
    if ! tar -xf "$FIFO" -C /; then
        kill "$ZSTD_PID" 2>/dev/null || true
        wait "$ZSTD_PID" 2>/dev/null || true
        rm -f "$FIFO"
        die "tar extraction failed"
    fi

    # Confirm zstd also succeeded
    wait "$ZSTD_PID"
    ZSTD_RC=$?
    rm -f "$FIFO"
    [ "$ZSTD_RC" = "0" ] || die "zstd decompression failed (exit: $ZSTD_RC)"

    S_EXTRACTED=1
    info "Kata version : $(cat "${KATA_DIR}/VERSION" 2>/dev/null || echo 'n/a')"
    ok "Extracted to $KATA_DIR"
}

# In 3.31.0 the runtime-rs config ships a stale field `cdh_api_timeout` under
# [agent.kata] that the runtime-rs binary rejects (it expects `cdh_api_timeout_ms`),
# producing: "unknown field `cdh_api_timeout`". Comment it out so the binary's
# built-in default applies. Commenting (vs renaming) avoids a seconds/ms unit
# mismatch. Idempotent and harmless if the field is already gone or already fixed.
patch_runtime_rs_config() {
    header "Patch runtime-rs config"
    RS_CFG_DIR="${KATA_DIR}/share/defaults/kata-containers/runtime-rs"
    PATCHED=0

    if [ -d "$RS_CFG_DIR" ]; then
        for cfg in "$RS_CFG_DIR"/*.toml; do
            [ -f "$cfg" ] || continue
            # Match `cdh_api_timeout =` but NOT `cdh_api_timeout_ms =`
            if grep -Eq '^[[:space:]]*cdh_api_timeout[[:space:]]*=' "$cfg"; then
                sed -i -E 's/^([[:space:]]*)cdh_api_timeout([[:space:]]*=)/\1# cdh_api_timeout\2/' "$cfg"
                info "Commented stale 'cdh_api_timeout' in $(basename "$cfg")"
                PATCHED=1
            fi
        done
    fi

    if [ "$PATCHED" = "1" ]; then
        ok "runtime-rs config patched (cdh_api_timeout → default)"
    else
        info "No stale cdh_api_timeout field found — config already clean"
    fi
}

validate_install() {
    header "Validate"

    # Required for CLH path
    for f in "$RUST_SHIM" "$CLH_CONFIG"; do
        [ -f "$f" ] || die "Missing (CLH): $f"
        info "OK (CLH)  : $f"
    done

    # Required for QEMU path
    for f in "$GO_SHIM" "$QEMU_CONFIG"; do
        [ -f "$f" ] || die "Missing (QEMU): $f"
        info "OK (QEMU) : $f"
    done

    info "Available hypervisor configs:"
    for cfg in "${KATA_DIR}/share/defaults/kata-containers/configuration"*.toml; do
        [ -f "$cfg" ] && printf '    %s\n' "$cfg"
    done

    ok "Both CLH and QEMU assets present"
}

setup_symlinks() {
    header "Symlinks"
    ln -sf "$RUST_SHIM" "$SYM_RS"           || die "Cannot create $SYM_RS"
    ln -sf "$GO_SHIM"   "$SYM_GO"           || die "Cannot create $SYM_GO"
    if [ -f "${KATA_DIR}/bin/kata-runtime" ]; then
        ln -sf "${KATA_DIR}/bin/kata-runtime" "$SYM_RT" || true
    fi
    S_SYMLINKS=1
    info "$SYM_RS  →  $RUST_SHIM"
    info "$SYM_GO  →  $GO_SHIM"
    ok "Symlinks created"
}

configure_docker() {
    header "Docker Config"
    log "Patching $DOCKER_DAEMON..."

    # Pass all paths as argv so the heredoc stays single-quoted
    # (prevents accidental shell expansion inside the Python code)
    python3 - \
        "$DOCKER_DAEMON" \
        "$RUST_SHIM"    \
        "$CLH_CONFIG"   \
        "$GO_SHIM"      \
        "$QEMU_CONFIG"  \
    <<'PYEOF' || die "Failed to update daemon.json"
import json, os, sys

daemon_file = sys.argv[1]
rust_shim   = sys.argv[2]
clh_cfg     = sys.argv[3]
go_shim     = sys.argv[4]
qemu_cfg    = sys.argv[5]

with open(daemon_file) as fh:
    cfg = json.load(fh)

# ── cgroup-v2 fix (REQUIRED for Kata on Docker v20.10+ on cgroup-v2 hosts) ──
# On cgroup-v2 systems Docker defaults to a PRIVATE cgroup namespace, which
# Kata's runtime-rs OCI parser rejects with "invalid namespace type".
# Forcing host cgroup ns makes both runtimes work. Startup-only flag → the
# script uses `systemctl restart` (not reload) after writing this.
cfg["default-cgroupns-mode"] = "host"

cfg.setdefault("runtimes", {})

# ── kata-clh : Cloud Hypervisor via runtime-rs (Rust) shim ─────────────────
# NOTE: in Kata 3.x the runtime-rs shim ignores Docker's options.ConfigPath
# and loads its own /opt/kata/share/defaults/kata-containers/runtime-rs/*.toml.
# ConfigPath is kept here for documentation/compat; per Kata docs, Docker v26+
# is officially tested with QEMU only, so treat CLH as best-effort.
cfg["runtimes"]["kata-clh"] = {
    "runtimeType": rust_shim,
    "options": {"ConfigPath": clh_cfg}
}

# ── kata-qemu : QEMU (the officially-supported VMM for modern Docker) ───────
cfg["runtimes"]["kata-qemu"] = {
    "runtimeType": go_shim,
    "options": {"ConfigPath": qemu_cfg}
}

tmp = daemon_file + ".new"
with open(tmp, "w") as fh:
    json.dump(cfg, fh, indent=2)
    fh.write("\n")
os.replace(tmp, daemon_file)
print(json.dumps(cfg, indent=2))
PYEOF

    S_DAEMON=1
    ok "daemon.json updated"
}

restart_docker() {
    header "Restart Docker"
    svc_restart_docker || die "Docker restart failed"
    S_DOCKER_RESTARTED=1
    # Give Docker time to re-read config and re-register shims
    sleep 3

    svc_is_docker_active || die "Docker did not come back up after restart"
    ok "Docker running with new config"

    # Install proper is done. From here, failures (host check, smoke tests)
    # must NOT roll back — the install is correct and needed for debugging.
    INSTALL_COMPLETE=1
}

# ── Kata's own canonical host validator — runs BEFORE container smoke tests ───
# This pinpoints nested-virt / missing-module problems with a precise message,
# unlike a swallowed `docker run` error.
kata_host_check() {
    header "Kata host check (kata-runtime check)"
    if [ ! -x "${KATA_DIR}/bin/kata-runtime" ]; then
        warn "kata-runtime binary not found — skipping host check"
        return 0
    fi

    # Do NOT redirect stderr to /dev/null — we want to SEE failures.
    CHK_OUT=$(KATA_CONF_FILE="$QEMU_CONFIG" "${KATA_DIR}/bin/kata-runtime" check 2>&1) || {
        fail "kata-runtime check reported problems:"
        printf '%s\n' "$CHK_OUT" | sed 's/^/    /'
        warn "Most common causes: no nested virt, missing vhost_vsock, or /dev/kvm perms."
        # Non-fatal: continue to the smoke tests, which will show the docker-side error too
        return 1
    }

    printf '%s\n' "$CHK_OUT" | sed 's/^/    /'
    ok "kata-runtime check passed"
    return 0
}

# ═════════════════════════════════════════════════════════════════════════════
# SMOKE TESTS  —  both runtimes tested independently, both must pass
# ═════════════════════════════════════════════════════════════════════════════

test_one_runtime() {
    # Args: $1=runtime-name  $2=label  $3=config-path
    RT="$1"
    LABEL="$2"
    CONF="$3"
    RT_PASS=0
    RT_FAIL=0

    printf '\n  %s%s[Runtime: %s]%s\n' "$CB" "$CC" "$LABEL" "$CN"

    # ── T-A: runtime registered in Docker ─────────────────────────────────────
    printf '    %-40s' "registered in docker info?"
    if docker info 2>/dev/null | grep -q "$RT"; then
        printf '%s PASS%s\n' "$CG" "$CN"
        RT_PASS=$((RT_PASS + 1))
    else
        printf '%s FAIL%s\n' "$CR" "$CN"
        RT_FAIL=$((RT_FAIL + 1))
    fi

    # ── T-B: container boots, returns guest kernel ────────────────────────────
    printf '    %-40s' "container launches (uname -r)?"
    HOST_KERNEL=$(uname -r)
    # Capture stderr to a file so we can DISPLAY the real Kata/Docker error
    # on failure instead of swallowing it. (Previous versions hid this.)
    ERRFILE="${TMPDIR:-/tmp}/kata_run_err.$$"
    GUEST_KERNEL=$(docker run --runtime "$RT" --rm ubuntu:24.04 uname -r 2>"$ERRFILE") || {
        printf '%s FAIL%s\n' "$CR" "$CN"
        RT_FAIL=$((RT_FAIL + 1))
        GUEST_KERNEL=""
        if [ -s "$ERRFILE" ]; then
            warn "    --- actual error ---"
            sed 's/^/    /' "$ERRFILE" >&2
            warn "    --------------------"
        fi
        warn "    More: journalctl -u docker -n 40 --no-pager   (and: journalctl -t kata)"
    }
    rm -f "$ERRFILE" 2>/dev/null || true

    if [ -n "$GUEST_KERNEL" ]; then
        printf '%s PASS%s\n' "$CG" "$CN"
        RT_PASS=$((RT_PASS + 1))
        info "    host  kernel : $HOST_KERNEL"
        info "    guest kernel : $GUEST_KERNEL"
        if [ "$GUEST_KERNEL" = "$HOST_KERNEL" ]; then
            warn "    kernels match — OK only if nested-virt uses the same kernel version"
        else
            info "    kernel isolation confirmed"
        fi
    fi

    # ── T-C: PID namespace isolation ──────────────────────────────────────────
    printf '    %-40s' "PID namespace isolated?"
    HOST_PID1=$(cat /proc/1/comm 2>/dev/null || printf 'unknown')
    GUEST_PID1=$(docker run --runtime "$RT" --rm ubuntu:24.04 \
        sh -c 'cat /proc/1/comm 2>/dev/null || printf unknown' 2>/dev/null) || GUEST_PID1="error"

    if [ "$GUEST_PID1" != "error" ]; then
        printf '%s PASS%s\n' "$CG" "$CN"
        RT_PASS=$((RT_PASS + 1))
        info "    host  PID1 : $HOST_PID1"
        info "    guest PID1 : $GUEST_PID1 (expected: kata-agent or init)"
    else
        printf '%s FAIL%s\n' "$CR" "$CN"
        RT_FAIL=$((RT_FAIL + 1))
    fi

    # ── T-D: correct hypervisor binary reported ────────────────────────────────
    printf '    %-40s' "hypervisor path in kata-env?"
    if [ -x "${KATA_DIR}/bin/kata-runtime" ] && [ -f "$CONF" ]; then
        HV_PATH=$(KATA_CONF_FILE="$CONF" \
            "${KATA_DIR}/bin/kata-runtime" kata-env 2>/dev/null \
            | grep -i "HypervisorPath" | head -1 \
            | sed 's/.*= *//') || HV_PATH=""
        if [ -n "$HV_PATH" ]; then
            printf '%s PASS%s\n' "$CG" "$CN"
            RT_PASS=$((RT_PASS + 1))
            info "    hypervisor : $HV_PATH"
        else
            printf '%sSKIP%s\n' "$CY" "$CN"
            warn "    kata-env returned no HypervisorPath (version-dependent output)"
        fi
    else
        printf '%sSKIP%s\n' "$CY" "$CN"
        info "    kata-runtime not in PATH — skipped"
    fi

    # ── per-runtime summary ───────────────────────────────────────────────────
    if [ "$RT_FAIL" = "0" ]; then
        ok "  $LABEL : all ${RT_PASS} checks passed"
        return 0
    else
        fail "  $LABEL : ${RT_FAIL} check(s) failed, ${RT_PASS} passed"
        return 1
    fi
}

run_tests() {
    # Run Kata's own host validator first — gives a precise reason if the
    # host can't run microVMs at all (nested virt, vhost, kvm perms).
    kata_host_check || true

    header "Smoke Tests (both runtimes)"

    CLH_FAIL=0
    QEMU_FAIL=0

    test_one_runtime "kata-clh"  "CLH  (runtime-rs + Cloud Hypervisor)" "$CLH_CONFIG"  \
        || CLH_FAIL=1

    test_one_runtime "kata-qemu" "QEMU (Go runtime + QEMU)"             "$QEMU_CONFIG" \
        || QEMU_FAIL=1

    printf '\n'
    if [ "$CLH_FAIL" = "0" ] && [ "$QEMU_FAIL" = "0" ]; then
        printf '%s%s  Both runtimes OK — kata-clh and kata-qemu are operational  %s\n\n' "$CG" "$CB" "$CN"
    elif [ "$QEMU_FAIL" = "0" ] && [ "$CLH_FAIL" = "1" ]; then
        # QEMU is the officially-supported VMM for Docker v26+; CLH is "best effort".
        printf '%s%s  QEMU works; CLH failed  %s\n' "$CY" "$CB" "$CN"
        warn "Docker v26+ is only officially tested with QEMU as the VMM."
        warn "CLH failing under modern Docker is a known limitation, not a broken install."
        warn "Use:  docker run --runtime kata-qemu ..."
    else
        printf '%s%s  Smoke tests failed  (CLH_FAIL=%s QEMU_FAIL=%s)  %s\n' "$CR" "$CB" "$CLH_FAIL" "$QEMU_FAIL" "$CN"
        warn "The install is intact at $KATA_DIR (NOT rolled back) so you can debug."
        warn "Read the actual error printed above, then check:"
        warn "  ${KATA_DIR}/bin/kata-runtime check"
        warn "  journalctl -u docker -n 50 --no-pager"
        warn "  ls -l /dev/vhost-vsock /dev/kvm"
        # Exit non-zero WITHOUT rollback (INSTALL_COMPLETE=1 guards die()).
        die "One or both runtimes failed their smoke test"
    fi

    printf '\n%s%sUsage:%s\n' "$CB" "$CC" "$CN"
    printf '  docker run --runtime kata-clh  <image> <cmd>   Cloud Hypervisor (Rust runtime)\n'
    printf '  docker run --runtime kata-qemu <image> <cmd>   QEMU            (Go  runtime)\n\n'
    [ -n "$DAEMON_BACKUP" ] && info "daemon.json backup: $DAEMON_BACKUP"
}

# ═════════════════════════════════════════════════════════════════════════════
# UNINSTALL
# ═════════════════════════════════════════════════════════════════════════════

do_uninstall() {
    header "Uninstall Kata Containers"
    check_root

    # ── 1. strip kata entries from daemon.json ─────────────────────────────────
    if [ -f "$DOCKER_DAEMON" ]; then
        log "Removing kata-clh / kata-qemu from $DOCKER_DAEMON..."
        UNI_BACKUP="${DOCKER_DAEMON}.pre-uninstall.$(date +%Y%m%d%H%M%S)"
        cp "$DOCKER_DAEMON" "$UNI_BACKUP" || die "Cannot backup daemon.json"
        info "Backup: $UNI_BACKUP"

        if command -v jq > /dev/null 2>&1; then
            # jq path: clean and explicit
            jq 'del(.runtimes["kata-clh"]) | del(.runtimes["kata-qemu"]) | del(.runtimes["kata"])
                | if .runtimes == {} then del(.runtimes) else . end' \
                "$DOCKER_DAEMON" > "${DOCKER_DAEMON}.new" \
                || die "jq failed to update daemon.json"
            mv "${DOCKER_DAEMON}.new" "$DOCKER_DAEMON" \
                || die "mv failed replacing daemon.json"
        else
            # python3 fallback (jq might not be installed on all distros)
            python3 - "$DOCKER_DAEMON" <<'PYEOF' || die "Python3 failed"
import json, os, sys
daemon_file = sys.argv[1]
with open(daemon_file) as fh:
    cfg = json.load(fh)
runtimes = cfg.get("runtimes", {})
for key in ("kata-clh", "kata-qemu", "kata"):
    runtimes.pop(key, None)
if runtimes:
    cfg["runtimes"] = runtimes
else:
    cfg.pop("runtimes", None)
tmp = daemon_file + ".new"
with open(tmp, "w") as fh:
    json.dump(cfg, fh, indent=2)
    fh.write("\n")
os.replace(tmp, daemon_file)
print(json.dumps(cfg, indent=2))
PYEOF
        fi
        ok "Kata runtimes removed from daemon.json"
    else
        warn "$DOCKER_DAEMON not found — nothing to patch"
        UNI_BACKUP=""
    fi

    # ── 2. restart Docker ─────────────────────────────────────────────────────
    if svc_is_docker_active 2>/dev/null; then
        log "Restarting Docker..."
        svc_restart_docker || warn "Docker restart failed — may need manual restart"
        ok "Docker restarted"
    fi

    # ── 3. remove /opt/kata ───────────────────────────────────────────────────
    if [ -d "$KATA_DIR" ]; then
        log "Removing $KATA_DIR..."
        rm -rf "$KATA_DIR" || die "Cannot remove $KATA_DIR"
        ok "$KATA_DIR removed"
    else
        warn "$KATA_DIR not found — already removed?"
    fi

    # ── 4. remove symlinks ────────────────────────────────────────────────────
    log "Removing symlinks..."
    for sym in "$SYM_RS" "$SYM_GO" "$SYM_RT"; do
        if [ -L "$sym" ]; then
            rm -f "$sym" && info "  Removed: $sym"
        fi
    done
    ok "Symlinks removed"

    printf '\n%s%s[✓] Kata Containers fully uninstalled.%s\n' "$CG" "$CB" "$CN"
    [ -n "${UNI_BACKUP:-}" ] && info "daemon.json backup: $UNI_BACKUP"
    printf '\n'
}

# ═════════════════════════════════════════════════════════════════════════════
# USAGE / MAIN
# ═════════════════════════════════════════════════════════════════════════════

usage() {
    cat <<EOF

${CB}kata-setup.sh${CN} — Kata Containers installer / updater (latest by default)

${CB}USAGE:${CN}
  sudo $0                   install OR update to the LATEST release, then test
  sudo $0 --force           reinstall even if already on the latest version
  sudo $0 --uninstall       remove all files and Docker config
  sudo $0 --test-only       smoke-test an existing install
  sudo $0 --help            this help

${CB}PIN A VERSION (skip auto-detect):${CN}
  KATA_VERSION=3.30.0 sudo $0     # specific version
  Default with no env var = the latest GitHub release.

${CB}VERSION GUIDANCE (for Docker hosts):${CN}
  Recommended : ${RECOMMENDED_VERSION}   (QEMU on the Go runtime; no known issues)
  Avoid       : 3.31.0  (runtime-rs cdh_api_timeout + cgroup-namespace bugs)
  The script warns automatically if a known-broken version is selected.

${CB}RUNTIMES INSTALLED:${CN}
  kata-clh   Rust (runtime-rs) + Cloud Hypervisor  →  $CLH_CONFIG
  kata-qemu  Go runtime        + QEMU               →  $QEMU_CONFIG

${CB}UPDATING:${CN}
  Re-running auto-detects the latest release. If a newer version exists it is
  installed over the old one; if you are already current it exits without change
  (use --force to reinstall anyway). The downloaded tarball is cached under
  /var/cache/kata-setup/ so repeat runs are fast.

${CB}ROLLBACK:${CN}
  A failure DURING install undoes all changes. A failure AFTER install completes
  (e.g. a smoke test) leaves the install in place so you can debug it.
  daemon.json backup: ${DOCKER_DAEMON}.kata-bak.<timestamp>

${CB}SUPPORTED DISTROS:${CN}
  Debian, Ubuntu, Alpine, RHEL/Rocky/CentOS, Fedora, Arch Linux

EOF
}

# ─── arg parsing ──────────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
    case "$1" in
        --uninstall|-u) MODE="uninstall" ;;
        --test-only|-t) MODE="test" ;;
        --force|-f)     FORCE=1 ;;
        --help|-h)      usage; exit 0 ;;
        *) fail "Unknown option: $1"; usage; exit 1 ;;
    esac
    shift
done

# ─── banner ───────────────────────────────────────────────────────────────────
printf '\n%s%s' "$CB" "$CC"
printf '╔══════════════════════════════════════════════════════╗\n'
printf '║  Kata Containers  —  installer / updater             ║\n'
printf '║  CLH (runtime-rs) + QEMU (Go)  —  both runtimes      ║\n'
printf '╚══════════════════════════════════════════════════════╝\n'
printf '%s\n' "$CN"

case "$MODE" in
    install)
        check_root
        detect_env
        check_kvm
        check_docker
        install_deps             # provides wget/curl needed by resolve_version
        resolve_version          # determine latest (or use pinned KATA_VERSION)
        check_existing_version   # fresh install vs update vs already-latest
        backup_daemon
        clean_old
        download_kata
        extract_kata
        validate_install
        patch_runtime_rs_config
        setup_symlinks
        configure_docker
        restart_docker
        run_tests
        ;;
    test)
        check_root
        detect_env
        check_docker
        # Show what's installed (version-independent test paths)
        if [ -f "${KATA_DIR}/VERSION" ]; then
            info "Testing installed Kata $(tr -d '[:space:]' < "${KATA_DIR}/VERSION")"
        else
            die "No Kata install found at ${KATA_DIR} — run without --test-only first"
        fi
        run_tests
        ;;
    uninstall)
        detect_env
        do_uninstall
        ;;
    *)
        die "Unknown mode: $MODE"
        ;;
esac
