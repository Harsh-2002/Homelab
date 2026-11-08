#!/bin/sh
set -eu
USER_NAME=os
UID_N=1000
export XDG_RUNTIME_DIR=/run/user/$UID_N
install -d -m 700 -o $USER_NAME -g $USER_NAME "$XDG_RUNTIME_DIR"
install -d -m 1777 /tmp/.X11-unix

mkdir -p /run/dbus
[ -S /run/dbus/system_bus_socket ] || dbus-daemon --system --fork 2>/dev/null || true
pgrep -x polkitd >/dev/null 2>&1 || /usr/lib/polkit-1/polkitd --no-debug >/tmp/polkitd.log 2>&1 &

HOME_DIR=/home/$USER_NAME
mkdir -p "$HOME_DIR/.config"
if ! grep -qs "ColorScheme" "$HOME_DIR/.config/kdeglobals"; then
  cat > "$HOME_DIR/.config/kdeglobals" <<'CFG'
[General]
ColorScheme=BreezeDark
[KDE]
LookAndFeelPackage=org.kde.breezedark.desktop
[Icons]
Theme=breeze-dark
CFG
fi
printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > "$HOME_DIR/.config/kscreenlockerrc"
[ -f "$HOME_DIR/.config/kwinrc" ] || printf '[Compositing]\nEnabled=false\n' > "$HOME_DIR/.config/kwinrc"
[ -f "$HOME_DIR/.config/baloofilerc" ] || printf '[Baloo]\nIndexing-Enabled=false\n' > "$HOME_DIR/.config/baloofilerc"
if [ ! -f "$HOME_DIR/.config/mimeapps.list" ]; then
  printf '[Default Applications]\nx-scheme-handler/http=chromium.desktop\nx-scheme-handler/https=chromium.desktop\ntext/html=chromium.desktop\n' > "$HOME_DIR/.config/mimeapps.list"
fi
chown -R $USER_NAME:$USER_NAME "$HOME_DIR" 2>/dev/null || true

trap 'kill 0 2>/dev/null || true' TERM INT

/usr/bin/Xvnc :1 -geometry 1600x900 -depth 24 -rfbport 5901 \
  -SecurityTypes None -ac -AlwaysShared -localhost=0 &
sleep 1

runuser -u $USER_NAME -- env DISPLAY=:1 XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
  QT_LINUX_ACCESSIBILITY_ALWAYS_ON=1 GTK_MODULES=gail:atk-bridge NO_AT_BRIDGE=0 \
  dbus-launch --exit-with-session /usr/bin/startplasma-x11 &
sleep 2

DISPLAY=:1 xset s off -dpms s noblank >/dev/null 2>&1 || true
/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5901 &

wait -n 2>/dev/null || wait
