"""Classic+ patch-Z is built from our sources plus the creator's own tables (tools/sync_patchz.py,
tools/classicplus_dbc.py); no game file is kept in git."""
import os
import struct
import subprocess
import sys
import tempfile
import shutil
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import classicplus_dbc  # noqa: E402
import sync_patchz  # noqa: E402
from modelport import mpq  # noqa: E402

srci = classicplus_dbc.srci


def stock_tables(folder, pairs, skills):
    """Small stand-in "stock" tables: CharBaseInfo with `pairs`, SkillRaceClassInfo with one row per skill
    (all races of class 1 only), written as .orig like the realm keeps them."""
    cbi = struct.pack("<4s4I", b"WDBC", len(pairs), 2, 2, 1) + b"".join(struct.pack("<BB", *p) for p in pairs) + b"\0"
    with open(os.path.join(folder, "CharBaseInfo.dbc.orig"), "wb") as f:
        f.write(cbi)
    rows = [[i + 1, s, 0, 1, 0, 0, 0, 0] for i, s in enumerate(sorted(skills))]
    srci.write_dbc(os.path.join(folder, "SkillRaceClassInfo.dbc.orig"), rows, b"\0")


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="patchz-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        skills = set().union(*srci.class_skills(os.path.join(ROOT, "realm", "classicplus", "classicplus_weapons.sql")).values())
        stock_tables(self.tmp, [(1, 1), (2, 1), (5, 4)], skills)

    def test_tables_are_stock_plus_our_deltas(self):
        t = classicplus_dbc.build(self.tmp)
        ours = classicplus_dbc.read_pairs(os.path.join(classicplus_dbc.DELTAS, "client_pairs.txt"))
        path = os.path.join(self.tmp, "out.dbc")
        with open(path, "wb") as f:
            f.write(t["CharBaseInfo.dbc"])
        self.assertEqual(srci.read_combos(path), sorted(set(ours) | {(1, 1), (2, 1), (5, 4)}))
        with open(path, "wb") as f:
            f.write(t["SkillRaceClassInfo.dbc"])
        rows, _ = srci.read_dbc(path)
        skills = srci.class_skills(os.path.join(ROOT, "realm", "classicplus", "classicplus_weapons.sql"))
        self.assertEqual(list(srci.gaps(rows, ours, skills)), [])     # every pair keeps its class's weapon skills
        self.assertEqual(len(ours), 58)

    def test_missing_stock_table_is_an_error_not_a_guess(self):
        os.remove(os.path.join(self.tmp, "CharBaseInfo.dbc.orig"))
        with self.assertRaises(FileNotFoundError):
            classicplus_dbc.build(self.tmp)

    def test_patchz_with_and_without_tables(self):
        bare = sync_patchz.build_files(None)
        self.assertFalse([n for n in bare if n.lower().startswith("dbfilesclient\\")])
        self.assertIn("interface\\glues\\common\\glues-wow-logo.blp", {n.lower() for n in bare})
        full = sync_patchz.build_files(self.tmp)
        self.assertEqual(sorted(n for n in full if n.lower().startswith("dbfilesclient\\")),
                         ["DBFilesClient\\CharBaseInfo.dbc", "DBFilesClient\\SkillRaceClassInfo.dbc"])
        out = os.path.join(self.tmp, "patch-Z.MPQ")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_patchz.py"), "--dbc-dir", self.tmp, "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(set(mpq.Archive(out).names()), set(full))
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_patchz.py"), "--check", "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_no_game_tables_or_client_patch_in_git(self):
        files = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True).stdout.split("\n")
        self.assertNotIn("realm/classicplus/patch-Z.MPQ", files)
        self.assertFalse([f for f in files if f.lower().endswith(".dbc")])
        for rel in ("realm/warfront/patch-Z.MPQ", "realm/duels/patch-Z.MPQ"):
            names = mpq.Archive(os.path.join(ROOT, rel)).names()
            self.assertFalse([n for n in names if n.lower().startswith("dbfilesclient\\")], rel)


if __name__ == "__main__":
    unittest.main()
