#!/bin/bash
export DISPLAY="${DISPLAY:-:20}"
declare -A seen
while true; do
  read -r SW SH < <(xdotool getdisplaygeometry 2>/dev/null)
  [ -z "${SW:-}" ] && { sleep 1; continue; }
  W=$((SW * 82 / 100)); H=$((SH * 82 / 100))
  X=$(((SW - W) / 2)); Y=$(((SH - H) / 2))
  for w in $(xdotool search --onlyvisible --name "." 2>/dev/null); do
    [ -n "${seen[$w]}" ] && continue
    t=$(xprop -id $w _NET_WM_WINDOW_TYPE 2>/dev/null)
    case "$t" in *NORMAL*) ;; *) seen[$w]=1; continue;; esac
    cls=$(xdotool getwindowclassname $w 2>/dev/null)
    case "$cls" in plasma*|kwin*|xsettings*|kded*|kglobalaccel*) seen[$w]=1; continue;; esac
    xdotool windowsize $w $W $H
    xdotool windowmove $w $X $Y
    seen[$w]=1
  done
  sleep 0.4
done
