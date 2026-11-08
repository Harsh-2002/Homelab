#!/bin/bash
set -u
H="${HOME:-/home/ubuntu}"
C="$H/.config"
mkdir -p "$C"
if ! grep -qs ColorScheme "$C/kdeglobals"; then
  cat > "$C/kdeglobals" <<'CFG'
[General]
ColorScheme=BreezeDark
[KDE]
LookAndFeelPackage=org.kde.breezedark.desktop
[Icons]
Theme=breeze-dark
CFG
fi
printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > "$C/kscreenlockerrc"
[ -f "$C/kwinrc" ] || printf '[Compositing]\nEnabled=false\n' > "$C/kwinrc"
[ -f "$C/baloofilerc" ] || printf '[Baloo]\nIndexing-Enabled=false\n' > "$C/baloofilerc"
[ -f "$C/mimeapps.list" ] || printf '[Default Applications]\nx-scheme-handler/http=google-chrome.desktop\nx-scheme-handler/https=google-chrome.desktop\ntext/html=google-chrome.desktop\n' > "$C/mimeapps.list"
[ -f "$C/plasma-org.kde.plasma.desktop-appletsrc" ] || cp /usr/share/os-desktop/panel-appletsrc "$C/plasma-org.kde.plasma.desktop-appletsrc"
exit 0
