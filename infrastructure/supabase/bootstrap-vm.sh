#!/bin/sh
set -eu
test "$(id -u)" = 0
base=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git jq openssl sudo nodejs python3 qemu-guest-agent
if ! id supabase >/dev/null 2>&1; then
    adduser --disabled-password --gecos '' supabase
fi
usermod -aG sudo supabase
install -d -m 700 -o supabase -g supabase /home/supabase/.ssh
if [ ! -s /home/supabase/.ssh/authorized_keys ]; then
    install -m 600 -o supabase -g supabase /root/.ssh/authorized_keys /home/supabase/.ssh/authorized_keys
fi
install -m 440 "$base/supabase.sudoers" /etc/sudoers.d/supabase
visudo -cf /etc/sudoers.d/supabase
install -m 600 "$base/ssh-key-only.conf" /etc/ssh/sshd_config.d/00-key-only.conf
sshd -t
systemctl reload ssh
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://raw.githubusercontent.com/docker/docker-install/ada7a567e59b3935bd601bb21e422da50e80e376/install.sh -o /run/supabase-install-docker.sh
    sh /run/supabase-install-docker.sh
fi
install -d -m 755 /etc/docker
if [ -e /etc/docker/daemon.json ]; then
    echo 'Existing Docker daemon configuration found; review before replacing.' >&2
    exit 1
fi
install -m 644 "$base/daemon.json" /etc/docker/daemon.json
dockerd --validate --config-file=/etc/docker/daemon.json
systemctl enable --now docker qemu-guest-agent
systemctl restart docker
install -d -m 755 /srv
docker version --format '{{.Server.Version}}'
docker compose version
