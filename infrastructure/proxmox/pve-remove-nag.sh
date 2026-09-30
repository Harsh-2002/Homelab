#!/bin/sh
set -eu

web_js=/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
original="res.data.status.toLowerCase() !== 'active'"
patched="res.data.status.toLowerCase() === 'NoMoreNagging'"

[ -s "$web_js" ] || exit 0
grep -Fq "$patched" "$web_js" && exit 0
count=$(grep -Fc "$original" "$web_js" || true)
if [ "$count" -ne 2 ] || ! grep -F -A4 "$original" "$web_js" | grep -Fq "title: gettext('No valid subscription')"; then
    echo 'Subscription popup patch skipped: upstream JavaScript changed; review required.' >&2
    exit 0
fi

# Keep one rollback copy, and change only the first (login popup) comparison.
[ -e "$web_js.orig" ] || cp -p "$web_js" "$web_js.orig"
sed -i "0,/$original/s/$original/$patched/" "$web_js"
grep -Fq "$patched" "$web_js"
echo 'Patched Proxmox login subscription popup; subscription state is unchanged.'
