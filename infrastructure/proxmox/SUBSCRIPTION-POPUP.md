# Subscription popup preference

On 2026-09-30, all three nodes ran PVE 9.2.20 with the original JavaScript subscription-popup comparison and no persistent removal script or APT hook. The live evidence cannot establish exactly when an earlier patch was lost. A package upgrade can overwrite this package-owned file.

The owner explicitly approved hiding the login popup. This is an unsupported UI customization, not a subscription, fake key, repository change, or authorization bypass. The real subscription status remains unchanged.

The tracked [patch script](pve-remove-nag.sh) is installed on px10, px20 and px30 as `/usr/local/bin/pve-remove-nag.sh`. The tracked [APT hook](no-nag-script) is installed as `/etc/apt/apt.conf.d/no-nag-script`. It follows the desktop approach in [Community Scripts](https://github.com/community-scripts/ProxmoxVE/blob/main/tools/pve/post-pve-install.sh), but narrows the replacement to the first login-popup comparison and leaves the second subscription/repository status comparison intact. No mobile DOM-injection script was installed.

The script is idempotent and keeps one `/usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js.orig` rollback copy. It expects the tested upstream structure. If that structure changes, it emits a warning and leaves the new code alone instead of applying a broad substitution or blocking APT. The backup is the version at first application; it is not necessarily the current package after later upgrades.

Reinstall from this repository:

```sh
scp infrastructure/proxmox/pve-remove-nag.sh infrastructure/proxmox/no-nag-script px10:/tmp/
ssh px10 'install -m 0755 /tmp/pve-remove-nag.sh /usr/local/bin/pve-remove-nag.sh && install -m 0644 /tmp/no-nag-script /etc/apt/apt.conf.d/no-nag-script && /usr/local/bin/pve-remove-nag.sh && rm /tmp/pve-remove-nag.sh /tmp/no-nag-script'
```

Repeat for px20 and px30. No host, guest, or `pveproxy` restart was required: each node immediately served the patched static JavaScript over its existing HTTPS listener. Use Cmd+Shift+R on macOS if the browser cached the old file.

Validation on every node:

```sh
apt-config dump | grep pve-remove-nag
grep -n NoMoreNagging /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
curl -ks https://127.0.0.1:8006/proxmoxlib.js | grep -m1 NoMoreNagging
/usr/local/bin/pve-remove-nag.sh
```

All checks passed on all three nodes, including a second application with no further changes. This verifies hook registration and the served file, not a simulated full package upgrade or authenticated browser login. Check again after an upstream toolkit change.

To revert, remove only the two installed customization files and reinstall the current toolkit package:

```sh
rm /etc/apt/apt.conf.d/no-nag-script /usr/local/bin/pve-remove-nag.sh
apt-get install --reinstall proxmox-widget-toolkit
```

Hard-refresh the browser. Once satisfied, the single `.orig` rollback file may also be removed. Do not restore an old `.orig` over a newer toolkit version.
