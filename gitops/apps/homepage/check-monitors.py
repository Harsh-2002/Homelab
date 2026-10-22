#!/usr/bin/env python3
"""Check every configured card using Homepage's own HTTP monitoring handler.

Read-only: no credentials, configuration mutations or service interruptions.
Requires kubectl access to context k8s and local PyYAML.
"""
import json
import subprocess
import sys

import yaml


def main():
    config = json.loads(subprocess.check_output([
        "kubectl", "--context", "k8s", "--request-timeout=15s", "-n", "homepage",
        "get", "configmap", "homepage-config", "-o", "json",
    ], text=True))
    cards = []
    for group in yaml.safe_load(config["data"]["services.yaml"]):
        for group_name, services in group.items():
            for service in services:
                for name, settings in service.items():
                    if not settings.get("siteMonitor") or "ping" in settings:
                        raise SystemExit(f"Missing HTTP monitor or legacy ping: {group_name}/{name}")
                    cards.append({"group": group_name, "name": name})

    script = r"""
const cards = JSON.parse(process.argv[2]);
let failures = 0;
async function check(card) {
  try {
    const query = new URLSearchParams({groupName: card.group, serviceName: card.name});
    const response = await fetch(`http://127.0.0.1:3000/api/siteMonitor?${query}`, {
      headers: {Host: 'l3b.cc.cd'}, signal: AbortSignal.timeout(20000),
    });
    const result = await response.json();
    // Match Homepage v2.4.0: HTTP 401/403 means the app answered with auth required.
    const ok = response.ok && Number.isInteger(result.status) &&
      result.status >= 200 && result.status <= 403;
    if (!ok) failures++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${card.group}/${card.name}: HTTP ${result.status ?? 'ERROR'} (${Math.round(result.latency ?? 0)} ms)`);
  } catch (error) {
    failures++;
    console.log(`FAIL ${card.group}/${card.name}: ${error.name}`);
  }
}
(async () => {
  for (let i = 0; i < cards.length; i += 6) {
    await Promise.all(cards.slice(i, i + 6).map(check));
  }
  console.log(`${cards.length - failures}/${cards.length} HTTP monitors responding`);
  process.exitCode = failures ? 1 : 0;
})();
"""
    result = subprocess.run([
        "kubectl", "--context", "k8s", "-n", "homepage", "exec", "-i",
        "deploy/homepage", "--", "node", "-", json.dumps(cards),
    ], input=script, text=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
