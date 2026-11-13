"""Regression checks for ordered automatic subagent permission profiles."""
from pathlib import Path
from fnmatch import fnmatchcase
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('forge', 'scout', 'vouch', 'shield', 'juror')


def rules(name):
    return yaml.safe_load((ROOT / 'agents' / f'{name}.md').read_text().split('---', 2)[1])['permissions']


def effect(name, action, resource):
    result = 'ask'
    # Simulate a restrictive ordinary workspace policy before agent rules.
    for rule in [{'action': '*', 'resource': '*', 'effect': 'ask'}, *rules(name)]:
        if fnmatchcase(action, rule['action']) and fnmatchcase(resource, rule['resource']):
            result = rule['effect']
    return result


class Permissions(unittest.TestCase):
    def test_automatic_tools(self):
        for name in NAMES:
            for action in ('read', 'glob', 'grep', 'skill', 'webfetch', 'execute', 'context7_query_docs'):
                with self.subTest(name=name, action=action):
                    self.assertEqual(effect(name, action, 'ordinary-resource'), 'allow')
            self.assertFalse(any(r['effect'] == 'ask' for r in rules(name)))

    def test_roles(self):
        for name in NAMES:
            self.assertEqual(effect(name, 'subagent', 'forge'), 'deny')
            self.assertEqual(effect(name, 'edit', 'src/main.py'), 'allow' if name == 'forge' else 'deny')
            self.assertEqual(effect(name, 'shell', 'git status --short'), 'deny' if name in ('scout', 'juror') else 'allow')

    def test_shield_secrets(self):
        for path in ('app/.env', 'app/.env.local', 'app/secrets/token', 'app/key.pem', 'app/key.key', '~/.ssh/id_ed25519', '~/.config/opencode/auth.json'):
            with self.subTest(path=path):
                self.assertEqual(effect('shield', 'read', path), 'deny')
        self.assertEqual(effect('shield', 'read', 'app/.env.example'), 'allow')


if __name__ == '__main__':
    unittest.main()
