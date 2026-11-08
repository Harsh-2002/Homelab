FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 SHELL=/bin/bash

RUN apt-get update && apt-get install -y --no-install-recommends \
    dbus dbus-x11 polkitd sudo procps \
    plasma-desktop plasma-workspace kwin-x11 konsole dolphin kdialog \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    xdotool scrot imagemagick x11-utils x11-xserver-utils wmctrl xclip \
    at-spi2-core python3-pyatspi \
    chromium fonts-dejavu fonts-liberation fonts-noto-color-emoji \
    libva2 libva-drm2 vainfo intel-media-va-driver mesa-va-drivers libgl1-mesa-dri \
    synaptic librsvg2-common shared-mime-info \
    git curl wget ca-certificates iproute2 net-tools less nano jq \
    htop tree unzip zip rsync vim-tiny file lsof tmux ncdu p7zip-full xz-utils \
    iputils-ping dnsutils xdg-utils desktop-file-utils xdg-user-dirs \
    python3 python3-venv python3-pip nodejs npm bash-completion \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash -G sudo,video,render,audio os

COPY sudoers-os /etc/sudoers.d/90-os
COPY polkit-os.rules /etc/polkit-1/rules.d/49-os-admin.rules
COPY chromium-wrapper.sh /usr/local/bin/chromium-wrapper.sh
COPY start-desktop.sh /usr/local/bin/start-desktop
COPY refresh-menu.sh /usr/local/bin/refresh-menu
COPY chromium.desktop /usr/share/applications/chromium.desktop
COPY synaptic.desktop /usr/share/applications/synaptic.desktop
COPY refresh-menu.desktop /usr/share/applications/refresh-menu.desktop
COPY panel-appletsrc /usr/share/os-desktop/panel-appletsrc

RUN chmod 440 /etc/sudoers.d/90-os \
 && chmod 644 /usr/share/applications/chromium.desktop /usr/share/applications/synaptic.desktop /usr/share/applications/refresh-menu.desktop \
 && chmod 755 /usr/local/bin/start-desktop /usr/local/bin/chromium-wrapper.sh /usr/local/bin/refresh-menu \
 && ln -sf /usr/local/bin/chromium-wrapper.sh /usr/local/bin/browser \
 && ln -sf /usr/bin/vim.tiny /usr/local/bin/vim \
 && update-desktop-database /usr/share/applications 2>/dev/null || true

EXPOSE 6080 5901

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s CMD curl -fsS http://127.0.0.1:6080/ || exit 1

STOPSIGNAL SIGTERM

CMD ["/usr/local/bin/start-desktop"]
