import asyncio
import importlib.util
import json
import pathlib
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock


path = pathlib.Path(__file__).with_name("session_commit_processor.py")
spec = importlib.util.spec_from_file_location("queue_read_guard", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Filesystem:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.acquired = 0
        self.released = 0
        self._async_agfs = self

    def _uri_to_path(self, uri, ctx):
        return "/test/session"

    async def pathlock_acquire_exact(self, path, timeout_secs):
        await asyncio.wait_for(self.lock.acquire(), timeout_secs)
        self.acquired += 1
        return "test-lease"

    async def pathlock_release(self, lease):
        assert lease == "test-lease"
        self.released += 1
        self.lock.release()


class GuardTests(unittest.IsolatedAsyncioTestCase):
    def make_processor(self, load):
        self.fs = Filesystem()
        self.session = SimpleNamespace(
            _viking_fs=self.fs,
            exists=AsyncMock(return_value=True),
            load=AsyncMock(side_effect=load),
            resume_queued_commit=AsyncMock(return_value=True),
        )
        service = SimpleNamespace(session=lambda *args, **kwargs: self.session)
        return module.SessionCommitProcessor(service)

    def message(self):
        return {"data": json.dumps({
            "task_id": "test-task",
            "session_id": "test-session",
            "session_uri": "viking://user/test/sessions/test-session",
            "archive_uri": "viking://user/test/sessions/test-session/history/archive_001",
            "user": {"account_id": "test", "user_id": "test"},
        })}

    async def test_reader_waits_for_phase1_writer(self):
        async def load():
            self.assertTrue(self.fs.lock.locked())

        processor = self.make_processor(load)
        await self.fs.lock.acquire()
        reader = asyncio.create_task(processor.on_dequeue(self.message()))
        await asyncio.sleep(0.05)
        self.session.load.assert_not_awaited()
        self.fs.lock.release()
        await asyncio.wait_for(reader, 2)
        self.session.load.assert_awaited_once()
        self.assertEqual((self.fs.acquired, self.fs.released), (1, 1))
        self.session.resume_queued_commit.assert_awaited_once()
        self.assertFalse(self.fs.lock.locked())

    async def test_read_error_releases_lock_without_hiding_error(self):
        processor = self.make_processor(json.JSONDecodeError("invalid", "", 0))
        with self.assertRaises(json.JSONDecodeError):
            await processor.on_dequeue(self.message())
        self.assertEqual((self.fs.acquired, self.fs.released), (1, 1))
        self.session.resume_queued_commit.assert_not_awaited()
        self.assertFalse(self.fs.lock.locked())

    async def test_phase2_runs_without_holding_root_lock(self):
        processor = self.make_processor(None)

        async def resume(msg):
            self.assertFalse(self.fs.lock.locked())
            return True

        self.session.resume_queued_commit.side_effect = resume
        await processor.on_dequeue(self.message())
        self.assertEqual((self.fs.acquired, self.fs.released), (1, 1))


if __name__ == "__main__":
    unittest.main()
