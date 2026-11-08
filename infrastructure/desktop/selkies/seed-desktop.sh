#!/bin/bash
set -u
H="${HOME:-/home/ubuntu}"
C="$H/.config"
mkdir -p "$C"
if ! grep -qs "\[Colors:View\]" "$C/kdeglobals"; then
  cat /usr/share/color-schemes/BreezeDark.colors > "$C/kdeglobals"
  printf "\n[Icons]\nTheme=breeze-dark\n\n[KDE]\nLookAndFeelPackage=org.kde.breezedark.desktop\n" >> "$C/kdeglobals"
fi
printf '[Daemon]\nAutolock=false\nLockOnResume=false\n' > "$C/kscreenlockerrc"
[ -f "$C/kwinrc" ] || printf '[Compositing]\nEnabled=false\n' > "$C/kwinrc"
[ -f "$C/baloofilerc" ] || printf '[Baloo]\nIndexing-Enabled=false\n' > "$C/baloofilerc"
[ -f "$C/konsolerc" ] || printf '[MainWindow]\nMenuBar=Enabled\n' > "$C/konsolerc"
[ -f "$C/mimeapps.list" ] || printf '[Default Applications]\nx-scheme-handler/http=google-chrome.desktop\nx-scheme-handler/https=google-chrome.desktop\ntext/html=google-chrome.desktop\n' > "$C/mimeapps.list"
[ -f "$C/plasma-org.kde.plasma.desktop-appletsrc" ] || cp /usr/share/os-desktop/panel-appletsrc "$C/plasma-org.kde.plasma.desktop-appletsrc"
exit 0
