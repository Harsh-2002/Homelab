#!/usr/bin/env python3
"""Local stdio adapter for Parallel's Streamable HTTP endpoint."""

import json
from pathlib import Path
import subprocess
import sys
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def main():
    helper = Path(__file__).resolve().parents[2] / "scripts/op-sa"
    item = subprocess.run([str(helper), "item", "get", "Parallel API Key",
                           "--vault", "HomeLab", "--format", "json"],
                          capture_output=True, check=True, timeout=25)
    key = next(f["value"] for f in json.loads(item.stdout)["fields"]
               if f["id"] == "credential")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    opener = build_opener(NoRedirect)
    for line in sys.stdin:
        msg = json.loads(line)
        try:
            req = Request("https://mcp.parallel.ai/mcp", data=line.encode(), headers=headers)
            with opener.open(req, timeout=300) as response:
                if session := response.headers.get("Mcp-Session-Id"):
                    headers["Mcp-Session-Id"] = session
                if response.status in (202, 204):
                    continue
                if response.headers.get_content_type() == "text/event-stream":
                    for part in response:
                        if part.startswith(b"data:"):
                            data = json.loads(part[5:])
                            if "id" in data and data["id"] == msg.get("id"):
                                break
                    else:
                        raise ValueError("Missing response")
                else:
                    data = json.load(response)
                if msg.get("method") == "initialize":
                    version = data.get("result", {}).get("protocolVersion")
                    if version:
                        headers["MCP-Protocol-Version"] = version
                print(json.dumps(data), flush=True)
        except Exception as error:
            if "id" in msg:
                status = getattr(error, "code", None)
                print(json.dumps({"jsonrpc": "2.0", "id": msg["id"], "error": {
                    "code": -32000, "message": f"Parallel request failed ({status or type(error).__name__})"
                }}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit("Parallel MCP could not start; check HomeLab vault access.")
