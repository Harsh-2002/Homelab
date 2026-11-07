#!/bin/sh
set -eu
export XDG_RUNTIME_DIR=/run/user/0
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
xfconf-query -c xfwm4 -p /general/use_compositing -s false 2>/dev/null || true

cleanup() { kill 0 2>/dev/null || true; }
trap cleanup TERM INT

/usr/bin/Xvnc :1 -geometry 1600x900 -depth 24 -rfbport 5901 \
  -SecurityTypes None -ac -AlwaysShared -localhost=0 &
sleep 1

DISPLAY=:1 dbus-launch --exit-with-session /usr/bin/startxfce4 &
sleep 1

/usr/bin/websockify --web=/usr/share/novnc 6080 localhost:5901 &

wait -n 2>/dev/null || wait
