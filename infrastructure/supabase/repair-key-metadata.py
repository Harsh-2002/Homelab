"""One-time compatibility repair; preserves all existing signing key material."""
import json
import pathlib
import re
import sys

env = pathlib.Path(sys.argv[1])
text = env.read_text()
for name, private in [("JWT_KEYS", True), ("JWT_JWKS", False)]:
    match = re.search(rf"^{name}=(.+)$", text, re.M)
    value = json.loads(match.group(1))
    for key in value if private else value["keys"]:
        if key["kty"] == "EC":
            key.update(ext=True, key_ops=["sign", "verify"] if private else ["verify"])
    text = text[:match.start(1)] + json.dumps(value, separators=(",", ":")) + text[match.end(1):]
env.write_text(text)
env.chmod(0o600)
print("Repaired JWK operation metadata; signing keys unchanged")
