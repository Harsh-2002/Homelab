FROM debian:trixie-slim
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd systemd-sysv dbus dbus-x11 \
    xfce4 xfce4-terminal thunar \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    xdotool scrot imagemagick x11-utils x11-xserver-utils \
    chromium fonts-dejavu fonts-liberation fonts-noto-color-emoji \
    git curl ca-certificates sudo procps iproute2 net-tools less nano jq \
    python3 python3-venv python3-pip nodejs npm \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
COPY xstartup /root/.vnc/xstartup
COPY start-desktop.sh /usr/local/bin/start-desktop
COPY chromium-wrapper.sh /usr/local/bin/chromium-wrapper.sh
COPY vncserver.service desktop.service novnc.service /etc/systemd/system/
RUN chmod 755 /root/.vnc/xstartup /usr/local/bin/start-desktop /usr/local/bin/chromium-wrapper.sh && ln -sf /usr/local/bin/chromium-wrapper.sh /usr/local/bin/browser
STOPSIGNAL SIGTERM
CMD ["/usr/local/bin/start-desktop"]
