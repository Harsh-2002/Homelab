#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/0
# expose the accessibility tree so agents can inspect apps without pixel guessing
export QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1
export GTK_MODULES=gail:atk-bridge
export NO_AT_BRIDGE=0
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
trap 'kill 0 2>/dev/null || true' TERM INT
# make the wrapped Chromium the default handler so menu and links both work as root
if [ ! -f /root/.config/mimeapps.list ]; then
  mkdir -p /root/.config
  printf '[Default Applications]\nx-scheme-handler/http=chromium.desktop\nx-scheme-handler/https=chromium.desktop\ntext/html=chromium.desktop\n' > /root/.config/mimeapps.list
fi
# no lock screen and no display blanking: access is already gated by Caddy/Tinyauth
mkdir -p /root/.config
printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > /root/.config/kscreenlockerrc
printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > /etc/xdg/kscreenlockerrc
mkdir -p /etc/xdg
printf '[PowerButton][AC]\nAction=1\n' > /etc/xdg/powerdevilrc
printf '[Daemon]\nAutolock=false\n' > /etc/xdg/kscreenlockerrc
# seed a modern dark default once; later user changes are preserved
mkdir -p /root/.config
if ! grep -qs "ColorScheme" /root/.config/kdeglobals; then
  cat > /root/.config/kdeglobals <<'CFG'
[General]
ColorScheme=BreezeDark
[KDE]
LookAndFeelPackage=org.kde.breezedark.desktop
[Icons]
Theme=breeze-dark
CFG
fi
[ -f /root/.config/kwinrc ] || printf '[Compositing]\nEnabled=false\n' > /root/.config/kwinrc
[ -f /root/.config/baloofilerc ] || printf '[Baloo]\nIndexing-Enabled=false\n' > /root/.config/baloofilerc
/usr/bin/Xvnc :1 -geometry 1600x900 -depth 24 -rfbport 5901 \
  -SecurityTypes None -ac -AlwaysShared -localhost=0 &
sleep 1
DISPLAY=:1 dbus-launch --exit-with-session /usr/bin/startplasma-x11 &
sleep 2
DISPLAY=:1 xset s off -dpms s noblank >/dev/null 2>&1 || true
/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5901 &
wait -n 2>/dev/null || wait
