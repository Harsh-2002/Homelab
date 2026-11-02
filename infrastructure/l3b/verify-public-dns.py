#!/usr/bin/env python3
"""Read-only public exact/private wildcard policy checks. Run as root for API audit."""
import json
from pathlib import Path
import subprocess
import sys
import uuid


def main():
    def run(*args):
        return subprocess.check_output(args, text=True, timeout=60).strip()

    data = json.loads(run(sys.executable, str(Path(__file__).with_name('public-dns.py'))))
    assert data['wildcardsAfter'] == 0 and not data['missingBefore']
    for server in data['nameServers']:
        for name in data['privateNames']:
            answer = run('dig', '@' + server, name, 'A', '+short')
            assert answer == '10.1.1.10', name
        unknown = 'dns-policy-' + uuid.uuid4().hex + '.l3b.cc.cd'
        answer = run('dig', '@' + server, unknown, 'A', '+noall', '+comments', '+answer')
        assert 'status: NXDOMAIN' in answer
        internal = run('dig', '@10.1.1.10', unknown, 'A', '+short')
        assert internal.splitlines()[-1] == '10.1.1.10'
    for name in data['privateNames']:
        answer = run('dig', '@10.1.1.10', name, 'A', '+short')
        assert answer.splitlines()[-1] == '10.1.1.10'
    result = {'checkedOn': '2026-11-02', 'checks': {
        'cloudflareHasNoWildcardRecords': True,
        'sevenCurrentPrivateOriginsHaveExactDnsOnlyARecords': True,
        'authoritativeNameserversMatchInternalForCurrentOrigins': True,
        'unknownPublicNameIsNxdomain': True, 'unknownInternalNameStillUsesWildcard': True},
        'privateOrigins': data['privateNames'],
        'limits': ['Existing exact historical public/direct-host records preserved, not newly approved or activated',
                   'Recursive caches may retain former wildcard answers until TTL expiry',
                   'Wildcard TLS certificate and Caddy hostname matcher are not public wildcard DNS']}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
