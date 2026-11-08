#!/bin/bash
export DISPLAY="${DISPLAY:-:20}"
declare -A seen
while true; do
  for w in $(xdotool search --onlyvisible --name "." 2>/dev/null); do
    [ -n "${seen[$w]}" ] && continue
    t=$(xprop -id $w _NET_WM_WINDOW_TYPE 2>/dev/null)
    case "$t" in *NORMAL*) ;; *) seen[$w]=1; continue;; esac
    cls=$(xdotool getwindowclassname $w 2>/dev/null)
    case "$cls" in plasma*|kwin*|xsettings*|kded*|kglobalaccel*) seen[$w]=1; continue;; esac
    wmctrl -i -r "$w" -b add,maximized_vert,maximized_horz 2>/dev/null || true
    seen[$w]=1
  done
  sleep 0.4
done
