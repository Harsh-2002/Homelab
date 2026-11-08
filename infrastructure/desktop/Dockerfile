FROM debian:trixie-slim
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN apt-get update && apt-get install -y --no-install-recommends \
    dbus dbus-x11 \
    plasma-desktop plasma-workspace kwin-x11 konsole dolphin kdialog \
    tigervnc-standalone-server tigervnc-common \
    novnc websockify \
    xdotool scrot imagemagick x11-utils x11-xserver-utils wmctrl xclip \
    at-spi2-core python3-pyatspi dbus-x11 \
    chromium fonts-dejavu fonts-liberation fonts-noto-color-emoji \
    git curl ca-certificates sudo procps iproute2 net-tools less nano jq \
    python3 python3-venv python3-pip nodejs npm \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /root/.config && printf '[Compositing]\nEnabled=false\n' > /root/.config/kwinrc \
 && printf '[General]\nDelayStart=false\n' > /root/.config/plasma-localerc \
 && (printf '[Baloo]\nIndexing-Enabled=false\n' > /root/.config/baloofilerc || true)
COPY chromium-wrapper.sh /usr/local/bin/chromium-wrapper.sh
COPY start-desktop.sh /usr/local/bin/start-desktop
RUN chmod 755 /usr/local/bin/start-desktop /usr/local/bin/chromium-wrapper.sh \
 && ln -sf /usr/local/bin/chromium-wrapper.sh /usr/local/bin/browser
STOPSIGNAL SIGTERM
CMD ["/usr/local/bin/start-desktop"]
