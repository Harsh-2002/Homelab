#!/usr/bin/env python3
"""Update one Portainer stack: edit the compose text and/or env, then redeploy.

Usage: stack.py ID [--sub OLD=NEW ...] [--env NAME=VALUE ...] [--dry-run]

Setup (never commit these files):
  mkdir -p ~/.cache/ptn && chmod 700 ~/.cache/ptn
  op item get Portainer --vault HomeLab --fields label=access-token --reveal > ~/.cache/ptn/key
  docker inspect portainer --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' > ~/.cache/ptn/ip
  chmod 600 ~/.cache/ptn/key

Reads the API key from ~/.cache/ptn/key and the Portainer IP from ~/.cache/ptn/ip.
The existing Env is always resent (Portainer drops it otherwise). Env values are
never printed. Saves the previous compose file next to this script as
backup-<id>-<timestamp>.yml (0600) so a change can be reverted.
"""
import argparse, json, os, sys, time, urllib.request

HOME = os.path.expanduser("~/.cache/ptn")
KEY = open(f"{HOME}/key").read().strip()
BASE = f"http://{open(f'{HOME}/ip').read().strip()}:9000/api"


def call(method, path, body=None, timeout=600):
    req = urllib.request.Request(BASE + path, method=method,
                                 headers={"X-API-Key": KEY, "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id", type=int)
    ap.add_argument("--sub", action="append", default=[])
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    stack = call("GET", f"/stacks/{a.id}")
    content = call("GET", f"/stacks/{a.id}/file")["StackFileContent"]
    env = stack.get("Env") or []
    endpoint = stack["EndpointId"]

    new = content
    for s in a.sub:
        old, _, rep = s.partition("=")
        if old not in new:
            sys.exit(f"substitution target not found in compose: {old[:60]}")
        new = new.replace(old, rep)
    names = {e["name"]: e for e in env}
    for e in a.env:
        k, _, v = e.partition("=")
        if k not in names:
            sys.exit(f"env var not present in stack: {k}")
        names[k]["value"] = v
    env = list(names.values())

    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = f"{HOME}/backup-{a.id}-{stamp}.yml"
    with open(backup, "w") as fh:
        fh.write(content)
    os.chmod(backup, 0o600)

    print(f"stack {a.id} '{stack['Name']}' endpoint {endpoint}: "
          f"compose {'changed' if new != content else 'unchanged'}, env keys {len(env)}")
    print(f"previous compose saved: {backup}")
    if a.dry_run:
        return
    call("PUT", f"/stacks/{a.id}?endpointId={endpoint}",
         {"stackFileContent": new, "env": env, "prune": False, "pullImage": True})
    print("redeploy requested")


if __name__ == "__main__":
    main()
