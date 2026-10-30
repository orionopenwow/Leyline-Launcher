"""tools/rename/leyline_rename.py: renaming orionopenwow/OpenVanilla to orionopenwow/Leyline-Launcher with the
PC's gh sign-in. A fake gh/git stands in for GitHub; nothing here touches the network.

    python -m unittest tests.test_leyline_rename -v
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "rename"))

import leyline_rename as R  # noqa: E402

TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


class FakeGitHub:
    """gh + git for one repo: renames, edits and remote URLs are remembered, every call is logged."""

    def __init__(self, login="orionopenwow", name="OpenVanilla", description="old", homepage="https://openvanilla.app",
                 origin="https://github.com/orionopenwow/openvanilla", other_new=False, fail_rename=False):
        self.login, self.name, self.desc, self.home = login, name, description, homepage
        self.origin, self.other_new, self.fail_rename = origin, other_new, fail_rename
        self.calls = []

    def repo(self, name):
        if self.other_new and name == "Leyline-Launcher":
            return {"id": 999, "full_name": "orionopenwow/Leyline-Launcher", "description": "", "homepage": ""}
        if name.lower() in (self.name.lower(), "openvanilla"):   # GitHub redirects the old name
            return {"id": 1, "full_name": "orionopenwow/" + self.name, "description": self.desc, "homepage": self.home}
        return None

    def __call__(self, cmd, cwd=None):
        self.calls.append(cmd)
        if cmd[0] == "gh":
            a = cmd[1:]
            if a[:2] == ["api", "user"]:
                return (0, self.login) if self.login else (1, "not logged in")
            if a[0] == "api" and a[1].startswith("repos/orionopenwow/"):
                r = self.repo(a[1].split("/", 2)[2])
                return (0, json.dumps(r)) if r else (1, "HTTP 404: Not Found")
            if a[:2] == ["repo", "rename"]:
                if self.fail_rename:
                    return 1, "HTTP 403 " + TOKEN
                self.name = a[2]
                return 0, ""
            if a[:2] == ["repo", "edit"]:
                if "--description" in a:
                    self.desc = a[a.index("--description") + 1]
                if "--homepage" in a:
                    self.home = a[a.index("--homepage") + 1]
                return 0, ""
        if cmd[0] == "git" and cmd[3:5] == ["remote", "get-url"]:
            return 0, self.origin
        if cmd[0] == "git" and cmd[3:5] == ["remote", "set-url"]:
            self.origin = cmd[6]
            return 0, ""
        return 1, "unexpected " + " ".join(cmd)

    def ran(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


def go(fake, clone="/pc/OpenVanilla", dry=False):
    lines = []
    rc = R.Renamer(clone=clone, runner=fake, out=lines.append, dry_run=dry).main()
    return rc, lines


class RenameTests(unittest.TestCase):
    def test_first_run_renames_edits_and_moves_origin(self):
        f = FakeGitHub()
        rc, lines = go(f)
        self.assertEqual(rc, 0)
        self.assertEqual(f.name, "Leyline-Launcher")
        self.assertEqual(f.ran("gh", "repo", "rename"),
                         [["gh", "repo", "rename", "Leyline-Launcher", "--repo", "orionopenwow/OpenVanilla", "--yes"]])
        self.assertEqual(f.desc, R.DESCRIPTION)
        self.assertEqual(f.home, "https://play.openvanilla.app/wrath/leyline")
        self.assertEqual(f.origin, "https://github.com/orionopenwow/Leyline-Launcher")
        self.assertIn("Done.", lines[-1])

    def test_second_run_changes_nothing(self):
        f = FakeGitHub()
        go(f)
        f.calls.clear()
        rc, lines = go(f)
        self.assertEqual(rc, 0)
        self.assertEqual(f.ran("gh", "repo"), [], "no rename or edit the second time")
        self.assertEqual([c for c in f.calls if "set-url" in c], [])
        self.assertEqual(sum("skipped" in l for l in lines), 3)

    def test_dry_run_changes_nothing(self):
        f = FakeGitHub()
        rc, lines = go(f, dry=True)
        self.assertEqual(rc, 0)
        self.assertEqual((f.name, f.desc, f.origin), ("OpenVanilla", "old", "https://github.com/orionopenwow/openvanilla"))
        self.assertTrue(any("would rename" in l for l in lines))
        self.assertTrue(any("would set origin" in l for l in lines))

    def test_refuses_chumpton_before_anything(self):
        for who in ("Chumpton", "chumpton", "CHUMPTON"):
            f = FakeGitHub(login=who)
            with self.assertRaises(R.RenameError) as e:
                R.Renamer(clone="/pc/x", runner=f, out=lambda s: None).main()
            self.assertIn("never used", str(e.exception))
            self.assertEqual(len(f.calls), 1, "only the sign-in check ran")

    def test_refuses_other_accounts_and_no_sign_in(self):
        with self.assertRaises(R.RenameError):
            R.Renamer(runner=FakeGitHub(login="someone"), out=lambda s: None).main()
        with self.assertRaises(R.RenameError) as e:
            R.Renamer(runner=FakeGitHub(login=""), out=lambda s: None).main()
        self.assertIn("gh auth login", str(e.exception))

    def test_refuses_when_new_name_is_another_repo(self):
        f = FakeGitHub(other_new=True)
        with self.assertRaises(R.RenameError) as e:
            R.Renamer(runner=f, out=lambda s: None).main()
        self.assertIn("different repo", str(e.exception))
        self.assertEqual(f.ran("gh", "repo", "rename"), [])

    def test_never_prints_a_token(self):
        f = FakeGitHub(fail_rename=True, origin=f"https://x-access-token:{TOKEN}@github.com/orionopenwow/OpenVanilla.git")
        lines = []
        with self.assertRaises(R.RenameError) as e:
            R.Renamer(clone="/pc/x", runner=f, out=lines.append).main()
        self.assertNotIn(TOKEN, R.redact(str(e.exception)))
        f2 = FakeGitHub(origin=f"https://x-access-token:{TOKEN}@github.com/orionopenwow/OpenVanilla.git")
        lines = []
        R.Renamer(clone="/pc/x", runner=f2, out=lines.append).main()
        self.assertNotIn(TOKEN, "\n".join(lines))
        self.assertEqual(f2.origin, f"https://x-access-token:{TOKEN}@github.com/orionopenwow/Leyline-Launcher.git",
                         "the remote keeps its own credential part; only the printed copy is redacted")
        src = open(os.path.join(ROOT, "tools", "rename", "leyline_rename.py"), encoding="utf-8").read()
        self.assertNotIn('"auth", "token"', src, "never asks gh for a token")

    def test_origin_of_another_repo_is_left_alone(self):
        f = FakeGitHub(origin="https://github.com/someone/else.git")
        with self.assertRaises(R.RenameError):
            R.Renamer(clone="/pc/x", runner=f, out=lambda s: None).main()
        self.assertEqual(f.origin, "https://github.com/someone/else.git")

    def test_no_clone_still_renames(self):
        f = FakeGitHub()
        rc, lines = go(f, clone=None)
        self.assertEqual((rc, f.name), (0, "Leyline-Launcher"))
        self.assertTrue(any("no clone" in l for l in lines))


class UrlTests(unittest.TestCase):
    def test_new_remote_url_keeps_scheme_and_suffix(self):
        self.assertEqual(R.new_remote_url("https://github.com/orionopenwow/OpenVanilla"),
                         "https://github.com/orionopenwow/Leyline-Launcher")
        self.assertEqual(R.new_remote_url("https://github.com/orionopenwow/openvanilla.git"),
                         "https://github.com/orionopenwow/Leyline-Launcher.git")
        self.assertEqual(R.new_remote_url("git@github.com:orionopenwow/OpenVanilla.git"),
                         "git@github.com:orionopenwow/Leyline-Launcher.git")
        self.assertIsNone(R.new_remote_url("C:/somewhere/else"))

    def test_is_ours(self):
        self.assertTrue(R.is_ours("https://github.com/orionopenwow/openvanilla"))
        self.assertTrue(R.is_ours("git@github.com:orionopenwow/Leyline-Launcher.git"))
        self.assertFalse(R.is_ours("https://github.com/orionopenwow/Leyline"))
        self.assertFalse(R.is_ours("https://github.com/Chumpton/OpenVanilla"))

    def test_redact(self):
        self.assertEqual(R.redact("https://u:p@github.com/a/b"), "https://github.com/a/b")
        self.assertNotIn(TOKEN, R.redact("token " + TOKEN))


class FindCloneTests(unittest.TestCase):
    def test_finds_the_clone_by_its_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = os.path.join(tmp, "Other")
            ov = os.path.join(tmp, "OpenVanilla")
            for d in (other, ov):
                os.makedirs(os.path.join(d, ".git"))

            def runner(cmd, cwd=None):
                return 0, ("https://github.com/orionopenwow/OpenVanilla" if cmd[2] == ov else "https://github.com/x/y")
            self.assertEqual(R.find_clone([os.path.join(tmp, "missing"), other, ov], runner), ov)
            self.assertIsNone(R.find_clone([other], runner))

    def test_candidates(self):
        c = R.clone_candidates(wu=r"/home/p/Desktop/WrathUnleashed", env={"HOME": "/home/p", "OPENVANILLA_DIR": "/x/ov"})
        self.assertEqual(c[0], "/x/ov")
        self.assertIn(os.path.join("/home/p/Desktop", "OpenVanilla"), c)
        self.assertIn(os.path.join("/home/p", "Documents", "GitHub", "OpenVanilla"), c)


class BatTests(unittest.TestCase):
    def test_bat_calls_the_helper_and_checks_tools(self):
        bat = open(os.path.join(ROOT, "tools", "rename", "Rename to Leyline Launcher.bat"), encoding="utf-8").read()
        self.assertIn('leyline_rename.py" --clone', bat)
        for need in ("where gh", "where git", "GIT_TERMINAL_PROMPT=0"):
            self.assertIn(need, bat)
        self.assertNotIn("auth token", bat)


if __name__ == "__main__":
    unittest.main()
