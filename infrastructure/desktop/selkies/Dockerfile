FROM ghcr.io/selkies-project/selkies/base:main-ubuntu26.04

USER 0
SHELL ["/bin/sh", "-c"]
RUN selkies-privileged-files release

USER 1000
SHELL ["/usr/bin/fakeroot", "--", "/bin/sh", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    plasma-desktop plasma-workspace kwin-x11 konsole dolphin kdialog \
    synaptic librsvg2-common shared-mime-info \
    htop tree unzip zip rsync vim-tiny file lsof tmux ncdu p7zip-full xz-utils \
    iputils-ping dnsutils xdg-utils desktop-file-utils xdg-user-dirs \
    fonts-dejavu fonts-liberation fonts-noto-color-emoji \
 && apt-get clean
RUN curl -fsSL -o /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y --no-install-recommends /tmp/chrome.deb \
 && rm -f /tmp/chrome.deb \
 && apt-get clean

USER 0
SHELL ["/bin/sh", "-c"]
RUN selkies-privileged-files restore

COPY --chown=1000:1000 services/ /etc/service/
COPY --chown=1000:1000 seed-desktop.sh /usr/local/bin/seed-desktop
COPY --chown=1000:1000 panel-appletsrc /usr/share/os-desktop/panel-appletsrc

RUN find /etc/service -name run -exec chmod -f 755 {} + \
 && chmod 755 /usr/local/bin/seed-desktop

USER 1000
SHELL ["/usr/bin/fakeroot", "--", "/bin/sh", "-c"]
RUN apt-get update

USER 1000
ENV SHELL=/bin/bash USER=ubuntu HOME=/home/ubuntu
WORKDIR /home/ubuntu

EXPOSE 8080

ENTRYPOINT ["/etc/container-entrypoint.sh"]
