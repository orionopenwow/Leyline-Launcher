"""Play Solo: keep the solo world running after the game closes (Settings), and jump straight back in."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import play_local as pl  # noqa: E402


class FakeGame:
    def __init__(self):
        self.polls = 0

    def poll(self):
        self.polls += 1
        return None if self.polls < 2 else 0


class KeepRunningTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.paths = pl.SoloPaths(self.root)
        os.makedirs(self.paths.root, exist_ok=True)
        self.alive = {11, 12, 13}

    def record(self, detached=True, pids=(11, 12, 13)):
        pl.write_json(self.paths.run_file, {"controller": 1, "detached": detached,
                                            "servers": dict(zip(("mangosd", "realmd", "mariadb"), pids))})

    def test_running_only_when_detached_and_all_alive(self):
        self.assertFalse(pl.solo_world_running(self.paths, alive=lambda p: p in self.alive))
        self.record(detached=False)
        self.assertFalse(pl.solo_world_running(self.paths, alive=lambda p: p in self.alive))
        self.record()
        self.assertTrue(pl.solo_world_running(self.paths, alive=lambda p: p in self.alive))
        self.record(pids=(11, 12, 99))
        self.assertFalse(pl.solo_world_running(self.paths, alive=lambda p: p in self.alive))

    def test_setting_read_from_settings(self):
        self.assertTrue(pl.SoloSession(root=self.root, settings={"solo_keep_running": True}).keep_after_game)
        self.assertFalse(pl.SoloSession(root=self.root, settings={}).keep_after_game)
        self.assertFalse(pl.SoloSession(root=self.root, settings=None).keep_after_game)

    def test_detach_marks_the_record_and_keeps_running(self):
        s = pl.SoloSession(root=self.root, settings={"solo_keep_running": True}, reporter=pl.Reporter())
        self.record(detached=False)
        s._detach()
        self.assertTrue(s.keep_running)
        self.assertTrue(pl.read_json(self.paths.run_file)["detached"])

    def test_shutdown_keeps_servers_but_restores_the_realmlist(self):
        s = pl.SoloSession(root=self.root, settings={"solo_keep_running": True}, reporter=pl.Reporter())
        s.keep_running = True
        stopped, restored = [], []
        s.servers = type("S", (), {"stop": lambda self, r=None: stopped.append(1)})()
        s.shutdown(lambda: restored.append(1))
        self.assertEqual(stopped, [])
        self.assertEqual(restored, [1])

    def _resume(self, keep):
        s = pl.SoloSession(root=self.root, settings={"solo_keep_running": keep}, reporter=pl.Reporter(),
                           popen=lambda *a, **k: FakeGame())
        s.state = {}
        calls = []
        orig = (pl.find_client, pl.point_client_at_solo, pl.cleanup_stale, pl.time.sleep)
        pl.find_client = lambda *a, **k: ("exe", os.path.join(self.root, "WoW.exe"), self.root)
        pl.point_client_at_solo = lambda folder, state: (lambda: calls.append("restore"))
        pl.cleanup_stale = lambda *a, **k: calls.append("stop") or True
        pl.time.sleep = lambda x: None
        try:
            self.assertEqual(s._resume(), 0)
        finally:
            pl.find_client, pl.point_client_at_solo, pl.cleanup_stale, pl.time.sleep = orig
        return s, calls

    def test_resume_with_setting_on_keeps_the_world(self):
        s, calls = self._resume(True)
        self.assertEqual(calls, ["restore"])
        self.assertTrue(s.keep_running)

    def test_resume_with_setting_off_stops_the_world_after_the_game(self):
        s, calls = self._resume(False)
        self.assertEqual(calls, ["restore", "stop"])

    def test_run_resumes_without_starting_servers(self):
        self.record()
        s = pl.SoloSession(root=self.root, settings={"solo_keep_running": True}, reporter=pl.Reporter())
        orig_running, orig_cleanup = pl.solo_world_running, pl.cleanup_stale
        pl.solo_world_running = lambda paths, alive=None: True
        pl.cleanup_stale = lambda *a, **k: self.fail("a running world must not be stopped first")
        s._resume = lambda: "resumed"
        try:
            self.assertEqual(s.run(), "resumed")
        finally:
            pl.solo_world_running, pl.cleanup_stale = orig_running, orig_cleanup


if __name__ == "__main__":
    unittest.main()
