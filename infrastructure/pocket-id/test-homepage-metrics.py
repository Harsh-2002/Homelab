#!/usr/bin/env python3
"""Counts adapter checks, including uncheckpointed WAL and fail-closed behavior."""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('homepage_metrics', Path(__file__).with_name('homepage-metrics.py'))
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


class CountsTests(unittest.TestCase):
    def test_wal_snapshot_and_read_only(self):
        with tempfile.TemporaryDirectory(prefix='pocket-metrics-test-') as directory:
            database = Path(directory)/'pocket-id.db'
            writer = sqlite3.connect(database)
            writer.execute('PRAGMA journal_mode=WAL')
            writer.execute('PRAGMA wal_autocheckpoint=0')
            writer.executescript('CREATE TABLE users(id INTEGER); CREATE TABLE oidc_clients(id INTEGER);')
            writer.execute('INSERT INTO users VALUES(1)')
            writer.executemany('INSERT INTO oidc_clients VALUES(?)', [(1,), (2,)])
            writer.commit()
            connect = sqlite3.connect
            def readonly(*args, **kwargs):
                self.assertIn('?mode=ro', args[0])
                connection = connect(*args, **kwargs)
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute('INSERT INTO users VALUES(999)')
                connection.rollback()
                return connection
            with patch.object(metrics.sqlite3, 'connect', readonly):
                self.assertEqual(metrics.counts(database), {'users':1, 'clients':2})
            writer.close()

    def test_missing_database_not_created(self):
        with tempfile.TemporaryDirectory(prefix='pocket-metrics-test-') as directory:
            database = Path(directory)/'missing.db'
            with self.assertRaises(sqlite3.OperationalError):
                metrics.counts(database)
            self.assertFalse(database.exists())


if __name__ == '__main__':
    unittest.main()
