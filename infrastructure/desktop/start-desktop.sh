#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/0
mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
trap 'kill 0 2>/dev/null || true' TERM INT
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
/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5901 &
wait -n 2>/dev/null || wait
