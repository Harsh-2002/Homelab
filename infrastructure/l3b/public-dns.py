#!/usr/bin/env python3
"""Audit or explicitly apply exact public-zone mappings; never an unattended sync.

Run as root for the existing restricted Cloudflare token. Only --apply creates
missing current private A records and deletes the single reviewed apex wildcard.
All other records, especially historical public exceptions, are preserved.
"""
import argparse
import json
from pathlib import Path
import urllib.request

PRIVATE_NAMES = ['l3b.cc.cd', 'auth.l3b.cc.cd', 'login.l3b.cc.cd',
                 'portainer.l3b.cc.cd', 'dns.l3b.cc.cd', 'memory.l3b.cc.cd', 'oc.l3b.cc.cd']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    env = dict(line.split('=', 1) for line in Path('/data/apps/caddy/runtime.env').read_text().splitlines()
               if '=' in line)
    headers = {'Authorization': 'Bearer ' + env['CF_API_TOKEN'].strip('"\''),
               'Content-Type': 'application/json'}

    def request(method, path, body=None):
        req = urllib.request.Request('https://api.cloudflare.com/client/v4/' + path, method=method,
                                     headers=headers, data=json.dumps(body).encode() if body else None)
        with urllib.request.urlopen(req, timeout=45) as response:
            data = json.load(response)
        assert data['success'], 'Cloudflare operation failed; private output withheld'
        return data

    zones = request('GET', 'zones?name=l3b.cc.cd')['result']
    assert len(zones) == 1
    base = 'zones/' + zones[0]['id'] + '/dns_records'

    def records():
        data = request('GET', base + '?per_page=100')
        assert data['result_info']['total_pages'] == 1, 'Review pagination before changing a larger zone'
        return data['result']

    before = records()
    missing = []
    for name in PRIVATE_NAMES:
        matches = [r for r in before if r['name'] == name and r['type'] in ['A', 'AAAA', 'CNAME']]
        if not matches:
            missing.append(name)
        else:
            assert len(matches) == 1 and matches[0]['type'] == 'A'
            assert matches[0]['content'] == '10.1.1.10' and not matches[0]['proxied'], name
    wildcards = [r for r in before if '*' in r['name']]
    assert all(r['name'] == '*.l3b.cc.cd' and r['type'] == 'CNAME' and
               r['content'] == 'l3b.cc.cd' for r in wildcards), 'Unexpected wildcard; review before changing'
    if args.apply:
        for name in missing:
            request('POST', base, {'type': 'A', 'name': name, 'content': '10.1.1.10',
                                   'proxied': False, 'ttl': 300})
        # Verify all replacements exist before removing wildcard coverage.
        interim = records()
        for name in PRIVATE_NAMES:
            assert any(r['name'] == name and r['type'] == 'A' and r['content'] == '10.1.1.10'
                       and not r['proxied'] for r in interim)
        for wildcard in wildcards:
            request('DELETE', base + '/' + wildcard['id'])
    after = records()
    if args.apply:
        assert not any('*' in r['name'] for r in after)
        preserved = {r['id']: r for r in before if r not in wildcards}
        actual = {r['id']: r for r in after}
        for identity, old in preserved.items():
            assert all(actual[identity].get(k) == old.get(k)
                       for k in ['name', 'type', 'content', 'ttl', 'proxied'])
    address_records = [{k: r[k] for k in ['type', 'name', 'content', 'proxied', 'ttl']}
                       for r in after if r['type'] in ['A', 'AAAA', 'CNAME']]
    print(json.dumps({'applied': args.apply, 'missingBefore': missing,
                      'wildcardsBefore': len(wildcards), 'wildcardsAfter': sum('*' in r['name'] for r in after),
                      'privateNames': PRIVATE_NAMES, 'nameServers': zones[0]['name_servers'],
                      'records': address_records}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Public DNS operation stopped; inspect selected records, not credentials/configuration') from None
