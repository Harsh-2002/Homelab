#!/bin/sh
set -eu
action=${1:-up}
chain=L3B-WG
ipt() { /usr/sbin/iptables -w 10 "$@"; }
case "$action" in
  up)
    ip link show wg0 >/dev/null 2>&1 || exit 0
    mode=$(/usr/bin/python3 -c 'import json; print(json.load(open("/etc/wireguard/l3b.json"))["mode"])')
    ipt -N "$chain" 2>/dev/null || true
    ipt -F "$chain"
    ipt -A "$chain" -i wg0 -s 10.1.2.0/24 -o eno1 -d 10.1.1.0/24 -j ACCEPT
    ipt -A "$chain" -o wg0 -d 10.1.2.0/24 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    ipt -A "$chain" -i wg0 -s 10.1.2.0/24 -o br+ -m conntrack --ctstate DNAT -j RETURN
    ipt -A "$chain" -i wg0 -j DROP
    ipt -A "$chain" -o wg0 -j DROP
    if ipt -nL DOCKER-USER >/dev/null 2>&1; then parent=DOCKER-USER; else parent=FORWARD; fi
    for c in FORWARD DOCKER-USER; do
      while ipt -C "$c" -j "$chain" 2>/dev/null; do ipt -D "$c" -j "$chain"; done
    done
    ipt -I "$parent" 1 -j "$chain"
    while ipt -t nat -C POSTROUTING -s 10.1.2.0/24 -d 10.1.1.0/24 -o eno1 -j MASQUERADE 2>/dev/null; do
      ipt -t nat -D POSTROUTING -s 10.1.2.0/24 -d 10.1.1.0/24 -o eno1 -j MASQUERADE
    done
    if [ "$mode" = nat ]; then ipt -t nat -A POSTROUTING -s 10.1.2.0/24 -d 10.1.1.0/24 -o eno1 -j MASQUERADE; fi
    ;;
  down)
    for c in FORWARD DOCKER-USER; do
      while ipt -C "$c" -j "$chain" 2>/dev/null; do ipt -D "$c" -j "$chain"; done
    done
    if ipt -nL "$chain" >/dev/null 2>&1; then ipt -F "$chain"; ipt -X "$chain"; fi
    while ipt -t nat -C POSTROUTING -s 10.1.2.0/24 -d 10.1.1.0/24 -o eno1 -j MASQUERADE 2>/dev/null; do
      ipt -t nat -D POSTROUTING -s 10.1.2.0/24 -d 10.1.1.0/24 -o eno1 -j MASQUERADE
    done
    ;;
  *) echo 'Usage: l3b-wg-firewall up|down' >&2; exit 2 ;;
esac
